import os
import sys
import re
import time
import shutil
import msvcrt
import ctypes
import urllib.parse
import libtorrent as lt

# Enable Windows Console Virtual Terminal Processing for ANSI colors
try:
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
except Exception:
    pass

# Import search_engine from current directory
import search_engine

# Determine default output directory
WORKSPACE_DIR = r"d:\Downloads\Videos"
if not os.path.exists(WORKSPACE_DIR):
    WORKSPACE_DIR = os.path.join(os.path.expanduser('~'), 'Downloads')

VERSION = "1.1"

def format_size(bytes_val):
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.1f} GB"

def interactive_select(options, prompt):
    if not options:
        return None
    selected = 0
    while True:
        os.system('cls')
        print(f"\033[1;35m{prompt} (v{VERSION})\033[0m")
        print("\033[1;30m" + "=" * len(prompt) + "\033[0m")
        print("\033[33mUse Up/Down Arrow keys to navigate, Enter to select, Esc to cancel.\033[0m\n")
        
        for idx, opt in enumerate(options):
            label = opt if isinstance(opt, str) else opt.get('label', '')
            if idx == selected:
                print(f" \033[1;36m-> {label}\033[0m")
            else:
                print(f"    {label}")
                
        key = msvcrt.getch()
        if key == b'\xe0' or key == b'\x00':  # Arrow key prefix
            sub_key = msvcrt.getch()
            if sub_key == b'H':  # Up
                selected = (selected - 1) % len(options)
            elif sub_key == b'P':  # Down
                selected = (selected + 1) % len(options)
        elif key == b'\r':  # Enter
            return options[selected]
        elif key == b'\x1b':  # Esc
            return None

def search_season_pack(show_title, season_num=None):
    if season_num is None:
        queries = [
            f"{show_title} Complete",
            f"{show_title} S01 S08",
            f"{show_title} Season 1 2 3 4"
        ]
    else:
        queries = [
            f"{show_title} Season {season_num}",
            f"{show_title} S{season_num:02d}",
            f"{show_title} Season {season_num:02d}"
        ]
        
    all_results = []
    for q in queries:
        url = f"https://apibay.org/q.php?q={urllib.parse.quote(q)}"
        results = search_engine.query_api(url)
        if not results or not isinstance(results, list) or (len(results) == 1 and results[0].get('id') == '0'):
            results = search_engine.search_via_proxies(q)
        if results and isinstance(results, list):
            all_results.extend(results)
            
    valid_torrents = []
    for item in all_results:
        name = item.get('name', '')
        cat = item.get('category', '')
        if cat in ['205', '208', '201', '207'] and search_engine.is_correct_title(name, show_title):
            if season_num is not None:
                s_pattern = re.compile(rf'(season\s*{season_num}\b|s{season_num:02d}\b|s{season_num}\b)', re.IGNORECASE)
                if not s_pattern.search(name):
                    continue
            else:
                pack_keywords = ['complete', 'season 1', 's01', 's1', 'seasons']
                if not any(kw in name.lower() for kw in pack_keywords):
                    continue
                    
            size_bytes = int(item.get('size', 0))
            valid_torrents.append({
                'id': item.get('id'),
                'name': name,
                'info_hash': item.get('info_hash'),
                'seeders': int(item.get('seeders', 0)),
                'leechers': int(item.get('leechers', 0)),
                'size': size_bytes
            })
            
    if not valid_torrents:
        return None
        
    for t in valid_torrents:
        name_lower = t['name'].lower()
        score = min(t['seeders'], 100)
        
        if '720p' in name_lower:
            score += 300
        elif '480p' in name_lower or '360p' in name_lower or ('x264' in name_lower and '1080p' not in name_lower):
            score += 200
        elif '1080p' in name_lower:
            score -= 50
        elif '2160p' in name_lower or '4k' in name_lower:
            score -= 500
            
        if any(codec in name_lower for codec in ['x265', 'h265', 'hevc', 'av1', '10bit', '10-bit']):
            score -= 500
            
        if any(codec in name_lower for codec in ['x264', 'h264', 'h.264']):
            score += 150
            
        if 'mp4' in name_lower:
            score += 50
            
        t['score'] = score
        
    valid_torrents.sort(key=lambda x: (x['score'], x['seeders']), reverse=True)
    return valid_torrents[0]

def download_torrent(info_hash, torrent_name, target_dir, staging_dir):
    os.makedirs(staging_dir, exist_ok=True)
    ses = lt.session({
        'listen_interfaces': '0.0.0.0:6881',
        'enable_upnp': True,
        'enable_natpmp': True,
        'enable_dht': True,
        'enable_lsd': True,
        'download_rate_limit': 0,
        'upload_rate_limit': 0,
        'connections_limit': 300
    })
    
    magnet_link = (
        f"magnet:?xt=urn:btih:{info_hash}"
        f"&dn={urllib.parse.quote(torrent_name)}"
        f"&tr=udp://tracker.opentrackr.org:1337/announce"
        f"&tr=udp://tracker.coppersurfer.tk:6969/announce"
    )
    
    params = lt.parse_magnet_uri(magnet_link)
    params.save_path = staging_dir
    
    print(f"\n\033[1;34m[*] Connecting to peers and fetching metadata...\033[0m")
    handle = ses.add_torrent(params)
    
    while not handle.has_metadata():
        s = handle.status()
        print(f"\rPeers: {s.num_peers} | State: fetching metadata...", end="", flush=True)
        time.sleep(1)
        
    tor_info = handle.get_torrent_info()
    total_size = tor_info.total_size()
    print(f"\n\033[1;32m[+] Connected! Downloading: {tor_info.name()} ({format_size(total_size)})\033[0m")
    
    last_print = 0
    try:
        while True:
            s = handle.status()
            progress = s.progress * 100
            speed = s.download_rate / (1024 * 1024)
            peers = s.num_peers
            
            if time.time() - last_print >= 1.5:
                print(f"\rProgress: {progress:.2f}% | Speed: {speed:.2f} MB/s | Peers: {peers} | Done: {format_size(s.total_done)}", end="", flush=True)
                last_print = time.time()
                
            if s.state == lt.torrent_status.seeding or progress >= 100.0:
                print("\n\033[1;32m[+] Download finished!\033[0m")
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\033[1;31m[!] Download paused/cancelled.\033[0m")
        ses.remove_torrent(handle)
        return False
        
    handle.pause()
    time.sleep(1.5)
    ses.remove_torrent(handle)
    return True

def post_process_files(staging_dir, dest_dir, is_movie=False):
    print(f"\n\033[1;34m[*] Sorting and renaming files to {dest_dir}...\033[0m")
    os.makedirs(dest_dir, exist_ok=True)
    video_extensions = ['.mp4', '.mkv', '.avi', '.m4v', '.mov']
    pattern = re.compile(r'S(\d{2})E(\d{2})', re.IGNORECASE)
    
    renamed = 0
    for root, dirs, files in os.walk(staging_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in video_extensions:
                src_path = os.path.join(root, file)
                if is_movie:
                    new_filename = file
                    dest_path = os.path.join(dest_dir, new_filename)
                else:
                    match = pattern.search(file)
                    if match:
                        s = int(match.group(1))
                        e = int(match.group(2))
                        new_filename = f"S_{s:02d}_E_{e:02d}{ext}"
                        dest_path = os.path.join(dest_dir, new_filename)
                    else:
                        dest_path = os.path.join(dest_dir, file)
                        
                print(f"  -> Moving: '{file}' to '{os.path.basename(dest_path)}'")
                if os.path.exists(dest_path):
                    try: os.remove(dest_path)
                    except: pass
                try:
                    shutil.move(src_path, dest_path)
                    renamed += 1
                except Exception as e:
                    print(f"  [!] Error moving file: {e}")
                    
    # Clean staging
    try:
        shutil.rmtree(staging_dir)
    except:
        pass
    print(f"\033[1;32m[+] Finished organizing {renamed} files.\033[0m")

def prompt_output_path():
    print(f"\n\033[1;35m[?] Where would you like to save the files?\033[0m")
    print(f"\033[1;30m(Press Enter to use default: {WORKSPACE_DIR})\033[0m")
    user_path = input("Path: ").strip()
    if user_path:
        # Expand environment variables or ~ paths
        expanded = os.path.abspath(os.path.expanduser(user_path))
        print(f"\033[32m[+] Target directory set to: {expanded}\033[0m")
        return expanded
    return WORKSPACE_DIR

def main():
    print(f"\033[1;35mMovies & Shows CLI Downloader (v{VERSION})\033[0m")
    print("\033[1;30m" + "=" * 40 + "\033[0m")
    
    if len(sys.argv) < 2:
        query = input("\033[1;35mEnter the movie or TV show name to search: \033[0m").strip()
    else:
        query = " ".join(sys.argv[1:])
        
    if not query:
        print("\033[1;31mError: No search query provided.\033[0m")
        return
        
    print(f"\033[1;34m[*] Searching for '{query}'...\033[0m")
    
    results = []
    # Search TVmaze
    shows = search_engine.search_tv_shows(query)
    for s in shows:
        results.append({
            'type': 'show',
            'title': s['title'],
            'year': s['year'],
            'id': s['id'],
            'imdb_id': s['imdb_id'],
            'label': f"[TV Show] {s['title']} ({s['year']})"
        })
        
    # Search Movies
    movies = search_engine.search_movies(query)
    for m in movies:
        results.append({
            'type': 'movie',
            'title': m['title'],
            'info_hash': m['info_hash'],
            'size_gb': m['size_gb'],
            'seeders': m['seeders'],
            'label': f"[Movie] {m['title']} ({m['size_gb']}, {m['seeders']} seeders)"
        })
        
    if not results:
        print("\033[1;31mNo matching shows or movies found.\033[0m")
        return
        
    selection = interactive_select(results, f"Search Results for '{query}'")
    if not selection:
        print("\033[1;31mCancelled.\033[0m")
        return
        
    # Process Selection
    if selection['type'] == 'show':
        # TV Show Selected - Ask for Season
        show_title = selection['title']
        show_id = selection['id']
        
        print(f"\033[1;34m[*] Loading episodes for '{show_title}'...\033[0m")
        episodes = search_engine.get_show_episodes(show_id)
        if not episodes:
            print("\033[1;31mCould not fetch episodes for this show.\033[0m")
            return
            
        seasons = sorted(list(set(ep['season'] for ep in episodes)))
        season_options = [{'label': 'All Seasons (Complete Pack)', 'val': None}]
        for s in seasons:
            season_options.append({'label': f"Season {s:02d}", 'val': s})
            
        season_sel = interactive_select(season_options, f"Select Season for '{show_title}'")
        if not season_sel:
            print("\033[1;31mCancelled.\033[0m")
            return
            
        target_season = season_sel['val']
        
        # Prompt for target path
        dest_workspace = prompt_output_path()
        
        # Search Season Pack
        print(f"\033[1;34m[*] Searching for season/series pack on APIBay...\033[0m")
        torrent_pack = search_season_pack(show_title, target_season)
        
        if torrent_pack:
            # We found a pack!
            show_folder_name = show_title
            if target_season is not None:
                show_folder_name = f"{show_title} - Season {target_season:02d}"
                
            show_folder_name = re.sub(r'[\\/*?:"<>|]', "", show_folder_name)
            dest_dir = os.path.join(dest_workspace, show_folder_name)
            staging_dir = os.path.join(dest_workspace, "staging_temp_" + str(int(time.time())))
            
            success = download_torrent(torrent_pack['info_hash'], torrent_pack['name'], dest_dir, staging_dir)
            if success:
                post_process_files(staging_dir, dest_dir, is_movie=False)
        else:
            # Fallback to individual episodes
            print("\033[1;33m[!] No complete season pack found. Downloading individual episodes sequentially...\033[0m")
            target_eps = [ep for ep in episodes if target_season is None or ep['season'] == target_season]
            
            show_folder_name = show_title
            if target_season is not None:
                show_folder_name = f"{show_title} - Season {target_season:02d}"
            show_folder_name = re.sub(r'[\\/*?:"<>|]', "", show_folder_name)
            dest_dir = os.path.join(dest_workspace, show_folder_name)
            
            print(f"[*] Queueing {len(target_eps)} episodes...")
            for idx, ep in enumerate(target_eps, 1):
                ep_num = ep['number']
                ep_season = ep['season']
                print(f"\n\033[1;34m[*] [{idx}/{len(target_eps)}] Searching for S{ep_season:02d}E{ep_num:02d}...\033[0m")
                ep_torrent = search_engine.find_best_episode_torrent(show_title, ep_season, ep_num, imdb_id=selection['imdb_id'])
                
                if ep_torrent:
                    staging_dir = os.path.join(dest_workspace, f"staging_temp_ep_{ep_season:02d}_{ep_num:02d}")
                    success = download_torrent(ep_torrent['info_hash'], ep_torrent['name'], dest_dir, staging_dir)
                    if success:
                        post_process_files(staging_dir, dest_dir, is_movie=False)
                else:
                    print(f"\033[1;31m[!] Episode S{ep_season:02d}E{ep_num:02d} not found on trackers.\033[0m")
                    
    elif selection['type'] == 'movie':
        # Movie Selected
        movie_title = selection['title']
        info_hash = selection['info_hash']
        
        # Prompt for target path
        dest_workspace = prompt_output_path()
        
        movie_folder_name = re.sub(r'[\\/*?:"<>|]', "", movie_title)
        dest_dir = os.path.join(dest_workspace, movie_folder_name)
        staging_dir = os.path.join(dest_workspace, "staging_temp_" + str(int(time.time())))
        
        success = download_torrent(info_hash, movie_title, dest_dir, staging_dir)
        if success:
            post_process_files(staging_dir, dest_dir, is_movie=True)

if __name__ == "__main__":
    main()
