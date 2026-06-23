import os
import sys
import re
import time
import shutil
import ctypes
import urllib.parse
import json
import tempfile
import libtorrent as lt
import requests
import search_engine

# Enable Windows Console Virtual Terminal Processing for ANSI colors
try:
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
except Exception:
    pass

# Determine default output directory
WORKSPACE_DIR = r"d:\Downloads\Videos"
if not os.path.exists(WORKSPACE_DIR):
    WORKSPACE_DIR = os.path.join(os.path.expanduser('~'), 'Downloads')

VERSION = "3.1"

CURATED_SHOWS = [
    {"title": "The Last of Us", "year": "2023", "id": 46562, "rating": 8.8, "genres": ["Action", "Adventure", "Drama", "Sci-Fi", "Thriller"], "imdb_id": "tt1424942"},
    {"title": "Succession", "year": "2018", "id": 30784, "rating": 8.8, "genres": ["Drama"], "imdb_id": "tt7660850"},
    {"title": "The Bear", "year": "2022", "id": 61491, "rating": 8.6, "genres": ["Comedy", "Drama"], "imdb_id": "tt14452778"},
    {"title": "Severance", "year": "2022", "id": 45182, "rating": 8.7, "genres": ["Drama", "Sci-Fi", "Mystery", "Thriller"], "imdb_id": "tt11280740"},
    {"title": "Shogun", "year": "2024", "id": 37945, "rating": 8.8, "genres": ["Drama", "History", "War", "Action", "Adventure"], "imdb_id": "tt8887038"},
    {"title": "The Boys", "year": "2019", "id": 35741, "rating": 8.7, "genres": ["Action", "Sci-Fi", "Thriller", "Adventure"], "imdb_id": "tt1190634"},
    {"title": "Stranger Things", "year": "2016", "id": 2993, "rating": 8.7, "genres": ["Drama", "Fantasy", "Horror", "Mystery", "Sci-Fi", "Thriller"], "imdb_id": "tt5013056"},
    {"title": "Fargo", "year": "2014", "id": 27, "rating": 8.9, "genres": ["Drama", "Crime", "Thriller"], "imdb_id": "tt2802850"},
    {"title": "Better Call Saul", "year": "2015", "id": 618, "rating": 8.9, "genres": ["Drama", "Crime"], "imdb_id": "tt3032476"},
    {"title": "The White Lotus", "year": "2021", "id": 51336, "rating": 8.0, "genres": ["Comedy", "Drama"], "imdb_id": "tt13406094"},
    {"title": "House of the Dragon", "year": "2022", "id": 44778, "rating": 8.4, "genres": ["Action", "Adventure", "Drama", "Fantasy"], "imdb_id": "tt11198330"},
    {"title": "Mr. Robot", "year": "2015", "id": 180, "rating": 8.5, "genres": ["Drama", "Crime", "Thriller"], "imdb_id": "tt4158110"},
    {"title": "Invincible", "year": "2021", "id": 37906, "rating": 8.7, "genres": ["Action", "Adventure", "Sci-Fi", "Fantasy"], "imdb_id": "tt6741478"},
    {"title": "Ted Lasso", "year": "2020", "id": 45595, "rating": 8.8, "genres": ["Comedy", "Drama"], "imdb_id": "tt10986410"},
    {"title": "Dark", "year": "2017", "id": 25043, "rating": 8.7, "genres": ["Drama", "Mystery", "Sci-Fi", "Thriller"], "imdb_id": "tt5753856"},
    {"title": "Arcane", "year": "2021", "id": 44855, "rating": 9.0, "genres": ["Action", "Adventure", "Sci-Fi", "Fantasy"], "imdb_id": "tt11126994"},
    {"title": "Yellowstone", "year": "2018", "id": 30715, "rating": 8.7, "genres": ["Drama", "Western"], "imdb_id": "tt4236770"},
    {"title": "Peaky Blinders", "year": "2013", "id": 269, "rating": 8.8, "genres": ["Drama", "Crime"], "imdb_id": "tt2442522"},
    {"title": "Andor", "year": "2022", "id": 44754, "rating": 8.4, "genres": ["Action", "Adventure", "Sci-Fi"], "imdb_id": "tt9461280"},
    {"title": "Fallout", "year": "2024", "id": 49334, "rating": 8.4, "genres": ["Action", "Adventure", "Sci-Fi"], "imdb_id": "tt12637874"},
    {"title": "True Detective", "year": "2014", "id": 5, "rating": 8.9, "genres": ["Drama", "Crime", "Mystery", "Thriller"], "imdb_id": "tt2356777"},
    {"title": "The Queen's Gambit", "year": "2020", "id": 42312, "rating": 8.6, "genres": ["Drama"], "imdb_id": "tt10048342"},
    {"title": "Mindhunter", "year": "2017", "id": 13264, "rating": 8.6, "genres": ["Drama", "Crime", "Thriller"], "imdb_id": "tt5290382"},
    {"title": "The Mandalorian", "year": "2019", "id": 38963, "rating": 8.7, "genres": ["Action", "Adventure", "Sci-Fi", "Fantasy"], "imdb_id": "tt8111088"},
    {"title": "Chernobyl", "year": "2019", "id": 30770, "rating": 9.4, "genres": ["Drama", "History"], "imdb_id": "tt8162467"},
    {"title": "Black Mirror", "year": "2011", "id": 305, "rating": 8.7, "genres": ["Drama", "Sci-Fi", "Thriller"], "imdb_id": "tt2085059"},
    {"title": "Rick and Morty", "year": "2013", "id": 216, "rating": 9.1, "genres": ["Comedy", "Sci-Fi", "Adventure"], "imdb_id": "tt2861424"},
    {"title": "The Crown", "year": "2016", "id": 2678, "rating": 8.6, "genres": ["Drama", "History"], "imdb_id": "tt4786824"},
    {"title": "Reacher", "year": "2022", "id": 46422, "rating": 8.1, "genres": ["Action", "Crime", "Thriller"], "imdb_id": "tt9288030"},
    {"title": "Slow Horses", "year": "2022", "id": 45330, "rating": 8.1, "genres": ["Drama", "Thriller"], "imdb_id": "tt5875444"},
]

# Queue Paths
QUEUE_DIR = os.path.join(os.path.expanduser('~'), '.downloadcc')
QUEUE_PATH = os.path.join(QUEUE_DIR, 'queue.json')
LOCK_PATH = os.path.join(QUEUE_DIR, 'downloadcc.lock')

def init_queue_dir():
    os.makedirs(QUEUE_DIR, exist_ok=True)
    if not os.path.exists(QUEUE_PATH):
        save_queue({"queue": []})

def load_queue():
    init_queue_dir()
    try:
        with open(QUEUE_PATH, 'r') as f:
            return json.load(f)
    except:
        return {"queue": []}

def save_queue(q_data):
    init_queue_dir()
    try:
        temp_path = QUEUE_PATH + ".tmp"
        with open(temp_path, 'w') as f:
            json.dump(q_data, f, indent=2)
        os.replace(temp_path, QUEUE_PATH)
    except Exception as e:
        print(f"Error saving queue: {e}")

_lock_file = None

def acquire_lock():
    global _lock_file
    init_queue_dir()
    try:
        if os.path.exists(LOCK_PATH):
            try:
                os.remove(LOCK_PATH)
            except OSError:
                return False
        _lock_file = open(LOCK_PATH, 'w')
        _lock_file.write(str(os.getpid()))
        _lock_file.flush()
        return True
    except:
        return False

def release_lock():
    global _lock_file
    if _lock_file:
        try:
            _lock_file.close()
            if os.path.exists(LOCK_PATH):
                os.remove(LOCK_PATH)
        except:
            pass
        _lock_file = None

def is_downloader_running():
    lock_path = os.path.join(QUEUE_DIR, 'downloadcc.lock')
    if not os.path.exists(lock_path):
        return False
    try:
        temp_rename_path = lock_path + ".test"
        os.rename(lock_path, temp_rename_path)
        os.rename(temp_rename_path, lock_path)
        return False
    except OSError:
        return True

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
        
    print(f"\n\033[1;35m{prompt} (v{VERSION})\033[0m")
    print("\033[1;30m" + "=" * (len(prompt) + 7) + "\033[0m")
    
    for idx, opt in enumerate(options, 1):
        label = opt if isinstance(opt, str) else opt.get('label', '')
        print(f"  \033[1;36m[{idx}]\033[0m {label}")
        
    print(f"  \033[1;31m[c]\033[0m Cancel / Go Back")
    
    while True:
        try:
            choice = input(f"\n\033[1;35mSelect an option (1-{len(options)} or c): \033[0m").strip().lower()
            if choice == 'c':
                return None
            val = int(choice)
            if 1 <= val <= len(options):
                return options[val - 1]
            print(f"\033[1;31mInvalid choice. Please enter a number between 1 and {len(options)}, or 'c'.\033[0m")
        except ValueError:
            print("\033[1;31mInvalid input. Please enter a valid number or 'c'.\033[0m")

def get_compatibility_badge(item):
    if item['type'] == 'show':
        return "", 0
        
    name = item['title'].lower()
    seeders = item['seeders']
    
    size_str = item.get('size_gb', '0 GB')
    try:
        size_gb = float(size_str.split()[0])
    except:
        size_gb = 0.0
        
    is_x265 = any(codec in name for codec in ['x265', 'h265', 'hevc', 'av1', '10bit', '10-bit'])
    is_h264 = any(codec in name for codec in ['x264', 'h264', 'h.264', 'mp4'])
    
    if seeders < 3:
        return "\033[1;30m[Slow - Low Seeds]\033[0m", 4
    elif is_x265:
        return "\033[1;36m[Requires VLC (x265)]\033[0m", 3
    elif is_h264:
        if size_gb < 1.0:
            return "\033[1;33m[Compatible - Low Quality]\033[0m", 2
        elif size_gb > 9.0:
            return "\033[1;33m[Compatible - Large File]\033[0m", 2
        else:
            return "\033[1;32m[Best iPad Compatibility]\033[0m", 1
    else:
        if size_gb > 0:
            return "\033[1;37m[Compatible - Unknown Codec]\033[0m", 2
        return "", 2

def search_season_pack(show_title, season_num=None, max_season=None):
    if season_num is None:
        if max_season:
            queries = [
                f"{show_title} Complete Series",
                f"{show_title} S01 S{max_season:02d}",
                f"{show_title} Season 1-{max_season}",
                f"{show_title} Seasons 1 to {max_season}",
                f"{show_title} Complete"
            ]
        else:
            queries = [
                f"{show_title} Complete Series",
                f"{show_title} Complete"
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
        
        # Fallback to SolidTorrents if results are empty or low
        if not results or len(results) < 3:
            try:
                solid_res = search_engine.search_solidtorrents(q)
                if solid_res:
                    if not results or (len(results) == 1 and results[0].get('id') == '0'):
                        results = solid_res
                    else:
                        results.extend(solid_res)
            except Exception as e:
                print(f"SolidTorrents fallback failed: {e}")
                
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
                # We want a complete series pack, not a single season pack
                name_lower = name.lower()
                is_explicit_complete = any(kw in name_lower for kw in ['complete series', 'complete show', 'all seasons', 'complete boxset', 'full series', 'complete collection'])
                
                has_range = False
                if max_season:
                    range_patterns = [
                        rf's0?1\s*[-–to]\s*s0?{max_season}\b',
                        rf's0?1\s*[-–to]\s*0?{max_season}\b',
                        rf'season\s*0?1\s*[-–to]\s*0?{max_season}\b',
                        rf'seasons\s*0?1\s*[-–to]\s*0?{max_season}\b',
                        rf'seasons\s*0?1\s*and\s*0?{max_season}\b'
                    ]
                    for pattern in range_patterns:
                        if re.search(pattern, name_lower):
                            has_range = True
                            break
                            
                is_generic_complete = False
                if 'complete' in name_lower or 'seasons' in name_lower:
                    if max_season and max_season > 1:
                        # Exclude single season packs
                        seasons_mentioned = set()
                        for s_val in range(1, max_season + 1):
                            if re.search(rf'\b(season\s*{s_val}\b|s{s_val:02d}\b|s{s_val}\b)', name_lower):
                                seasons_mentioned.add(s_val)
                        if len(seasons_mentioned) == 1:
                            continue
                    is_generic_complete = True
                    
                if not (is_explicit_complete or has_range or is_generic_complete):
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

def download_torrent(info_hash, torrent_name, target_dir, staging_dir, item_idx=-1):
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
    
    meta_start = time.time()
    while not handle.has_metadata():
        s = handle.status()
        print(f"\rPeers: {s.num_peers} | State: fetching metadata...", end="", flush=True)
        if item_idx != -1 and time.time() - meta_start >= 1.5:
            q_data = load_queue()
            if item_idx < len(q_data['queue']):
                q_data['queue'][item_idx]['peers'] = s.num_peers
                q_data['queue'][item_idx]['eta'] = "Fetching Metadata"
                save_queue(q_data)
        if time.time() - meta_start > 60:
            print("\n\033[1;31m[!] Metadata fetch timed out (no seeders). Skipping...\033[0m")
            ses.remove_torrent(handle)
            return False
        time.sleep(1)
        
    tor_info = handle.get_torrent_info()
    total_size = tor_info.total_size()
    print(f"\n\033[1;32m[+] Connected! Downloading: {tor_info.name()} ({format_size(total_size)})\033[0m")
    
    last_print = 0
    stuck_start = None
    try:
        while True:
            s = handle.status()
            progress = s.progress * 100
            speed = s.download_rate / (1024 * 1024)
            peers = s.num_peers
            done = s.total_done
            
            # ETA Calculation
            remaining_bytes = total_size - done
            if s.download_rate > 0:
                eta_sec = remaining_bytes / s.download_rate
                hours = int(eta_sec // 3600)
                minutes = int((eta_sec % 3600) // 60)
                seconds = int(eta_sec % 60)
                if hours > 0:
                    eta_str = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    eta_str = f"{minutes}m {seconds}s"
                else:
                    eta_str = f"{seconds}s"
            else:
                eta_str = "Unknown"
                
            # Self healing (0 speed for 60s)
            if s.state == lt.torrent_status.downloading and speed == 0:
                if stuck_start is None:
                    stuck_start = time.time()
                elif time.time() - stuck_start > 60:
                    print("\n\033[1;31m[!] Download stuck with 0 speed for 60 seconds. Skipping...\033[0m")
                    ses.remove_torrent(handle)
                    return False
            else:
                stuck_start = None
                
            if time.time() - last_print >= 1.5:
                print(f"\rProgress: {progress:.2f}% | Speed: {speed:.2f} MB/s | Peers: {peers} | Done: {format_size(done)} | ETA: {eta_str}", end="", flush=True)
                last_print = time.time()
                
                # Write to queue file
                if item_idx != -1:
                    q_data = load_queue()
                    if item_idx < len(q_data['queue']):
                        q_data['queue'][item_idx]['progress'] = progress
                        q_data['queue'][item_idx]['speed_mb'] = speed
                        q_data['queue'][item_idx]['peers'] = peers
                        q_data['queue'][item_idx]['eta'] = eta_str
                        save_queue(q_data)
                        
            if s.state == lt.torrent_status.seeding or progress >= 100.0:
                print("\n\033[1;32m[+] Download finished!\033[0m")
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\033[1;31m[!] Download paused/cancelled.\033[0m")
        if item_idx != -1:
            q_data = load_queue()
            if item_idx < len(q_data['queue']):
                q_data['queue'][item_idx]['status'] = 'queued'
                save_queue(q_data)
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
                        season_folder_name = f"Season {s:02d}"
                        season_dir = os.path.join(dest_dir, season_folder_name)
                        os.makedirs(season_dir, exist_ok=True)
                        new_filename = f"S_{s:02d}_E_{e:02d}{ext}"
                        dest_path = os.path.join(season_dir, new_filename)
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
        expanded = os.path.abspath(os.path.expanduser(user_path))
        print(f"\033[32m[+] Target directory set to: {expanded}\033[0m")
        return expanded
    return WORKSPACE_DIR

def show_queue():
    q_data = load_queue()
    queue_list = q_data.get('queue', [])
    
    if not queue_list:
        print("\033[1;33mThe download queue is currently empty.\033[0m")
        return
        
    print(f"\n\033[1;35mActive Download Queue\033[0m")
    print("\033[1;30m" + "=" * 30 + "\033[0m")
    
    for idx, item in enumerate(queue_list, 1):
        status = item.get('status', 'queued')
        title = item.get('title', 'Unknown')
        torrent_name = item.get('torrent_name', 'Unknown')
        
        status_colors = {
            'queued': '\033[1;33m[Queued]\033[0m',
            'downloading': '\033[1;32m[Downloading]\033[0m',
            'completed': '\033[1;30m[Completed]\033[0m',
            'failed': '\033[1;31m[Failed]\033[0m'
        }
        status_str = status_colors.get(status, f"[{status}]")
        
        if status == 'downloading':
            progress = item.get('progress', 0.0)
            speed = item.get('speed_mb', 0.0)
            peers = item.get('peers', 0)
            eta = item.get('eta', 'Unknown')
            print(f"  \033[1;36m[{idx}]\033[0m {title} - {status_str}")
            print(f"      Progress: {progress:.2f}% | Speed: {speed:.2f} MB/s | Peers: {peers} | ETA: {eta}")
            print(f"      File: {torrent_name}")
        else:
            print(f"  \033[1;36m[{idx}]\033[0m {title} - {status_str}")
            print(f"      File: {torrent_name}")

def clear_queue():
    q_data = load_queue()
    q_data['queue'] = []
    save_queue(q_data)
    print("\033[1;32m[+] Download queue cleared successfully.\033[0m")

def remove_queue_item(val):
    q_data = load_queue()
    queue_list = q_data.get('queue', [])
    
    if not queue_list:
        print("\033[1;31mError: Queue is empty.\033[0m")
        return
        
    try:
        idx = int(val) - 1
        if 0 <= idx < len(queue_list):
            removed = queue_list.pop(idx)
            q_data['queue'] = queue_list
            save_queue(q_data)
            print(f"\033[1;32m[+] Removed '{removed['title']}' from the queue.\033[0m")
            return
    except ValueError:
        pass
        
    matched = []
    for item in queue_list:
        if val.lower() in item['title'].lower():
            matched.append(item)
            
    if not matched:
        print(f"\033[1;31mError: Item '{val}' not found in queue.\033[0m")
    elif len(matched) == 1:
        queue_list.remove(matched[0])
        q_data['queue'] = queue_list
        save_queue(q_data)
        print(f"\033[1;32m[+] Removed '{matched[0]['title']}' from the queue.\033[0m")
    else:
        print("\033[1;33mMultiple matches found. Please specify by item number:\033[0m")
        for idx, item in enumerate(queue_list, 1):
            if val.lower() in item['title'].lower():
                print(f"  [{idx}] {item['title']}")

def add_item_to_queue(query):
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
            'tier': 0,
            'label': f"[TV Show] {s['title']} ({s['year']})"
        })
        
    # Search Movies
    movies = search_engine.search_movies(query)
    for m in movies:
        badge, tier = get_compatibility_badge(m)
        results.append({
            'type': 'movie',
            'title': m['title'],
            'info_hash': m['info_hash'],
            'size_gb': m['size_gb'],
            'seeders': m['seeders'],
            'tier': tier,
            'label': f"[Movie] {m['title']} ({m['size_gb']}, {m['seeders']} seeders) {badge}"
        })
        
    if not results:
        print("\033[1;31mNo matching shows or movies found.\033[0m")
        return
        
    # Sort results based on compatibility tier
    results.sort(key=lambda x: x.get('tier', 2))
    
    selection = interactive_select(results, f"Search Results for '{query}'")
    if not selection:
        print("\033[1;31mCancelled.\033[0m")
        return
        
    new_item = {
        "id": str(int(time.time())),
        "type": selection['type'],
        "title": selection['title'],
        "status": "queued",
        "progress": 0.0,
        "speed_mb": 0.0,
        "peers": 0,
        "eta": "Unknown"
    }
    
    # Process Selection
    if selection['type'] == 'show':
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
        new_item["target_season"] = target_season
        new_item["max_season"] = seasons[-1] if seasons else None
        new_item["imdb_id"] = selection.get('imdb_id', '')
        
        dest_workspace = prompt_output_path()
        new_item["dest_workspace"] = dest_workspace
        
        # Search Season Pack
        print(f"\033[1;34m[*] Searching for season/series pack on APIBay...\033[0m")
        torrent_pack = search_season_pack(show_title, target_season, max_season=new_item["max_season"])
        
        show_folder_name = re.sub(r'[\\/*?:"<>|]', "", show_title)
        
        dest_dir = os.path.join(dest_workspace, show_folder_name)
        new_item["dest_dir"] = dest_dir
        
        if torrent_pack:
            new_item["torrent_name"] = torrent_pack['name']
            new_item["info_hash"] = torrent_pack['info_hash']
            new_item["staging_dir"] = os.path.join(dest_workspace, "staging_temp_" + new_item["id"])
        else:
            # Fallback to individual episodes
            target_eps = [ep for ep in episodes if target_season is None or ep['season'] == target_season]
            new_item["episodes"] = target_eps
            new_item["torrent_name"] = f"{show_title} (Individual Episodes)"
            new_item["info_hash"] = "fallback"
            
    else:
        # Movie Selected
        movie_title = selection['title']
        info_hash = selection['info_hash']
        
        dest_workspace = prompt_output_path()
        new_item["dest_workspace"] = dest_workspace
        
        movie_folder_name = re.sub(r'[\\/*?:"<>|]', "", movie_title)
        dest_dir = os.path.join(dest_workspace, movie_folder_name)
        new_item["dest_dir"] = dest_dir
        new_item["torrent_name"] = movie_title
        new_item["info_hash"] = info_hash
        new_item["is_movie"] = True
        new_item["staging_dir"] = os.path.join(dest_workspace, "staging_temp_" + new_item["id"])
        
    # Append to queue
    q_data = load_queue()
    q_data['queue'].append(new_item)
    save_queue(q_data)
    
    print(f"\033[1;32m[+] Added '{new_item['title']}' to download queue.\033[0m")
    
    if is_downloader_running():
        print("\033[1;33m[*] A download process is already running in the background. Your item will be downloaded sequentially.\033[0m")
    else:
        print("\033[1;32m[*] Queue is idle. Starting downloads now...\033[0m")
        process_queue_loop()

def process_queue_loop():
    if not acquire_lock():
        return
        
    try:
        while True:
            q_data = load_queue()
            active_item = None
            active_idx = -1
            
            for idx, item in enumerate(q_data.get('queue', [])):
                if item['status'] in ['queued', 'downloading']:
                    active_item = item
                    active_idx = idx
                    break
                    
            if not active_item:
                break
                
            success = download_queue_item(active_item, active_idx)
            
            # Update status
            q_data = load_queue()
            if active_idx < len(q_data['queue']):
                q_data['queue'][active_idx]['status'] = 'completed' if success else 'failed'
                save_queue(q_data)
    finally:
        release_lock()

def download_queue_item(item, item_idx):
    q_data = load_queue()
    if item_idx < len(q_data['queue']):
        q_data['queue'][item_idx]['status'] = 'downloading'
        save_queue(q_data)
        
    dest_dir = item['dest_dir']
    is_movie = item.get('is_movie', False)
    
    episodes = item.get('episodes', [])
    if episodes:
        print(f"\n\033[1;34m[*] Processing show: {item['title']} ({len(episodes)} episodes sequentially)\033[0m")
        all_success = True
        
        for idx, ep in enumerate(episodes, 1):
            ep_season = ep['season']
            ep_num = ep['number']
            
            # Self healing: check if episode file already exists
            already_done = False
            for ext in ['.mp4', '.mkv', '.avi', '.m4v', '.mov']:
                season_folder = f"Season {ep_season:02d}"
                if os.path.exists(os.path.join(dest_dir, season_folder, f"S_{ep_season:02d}_E_{ep_num:02d}{ext}")):
                    already_done = True
                    break
            if already_done:
                print(f"  -> Episode S{ep_season:02d}E{ep_num:02d} already completed. Skipping.")
                continue
                
            print(f"\n\033[1;34m[*] [{idx}/{len(episodes)}] Searching for S{ep_season:02d}E{ep_num:02d}...\033[0m")
            ep_torrent = search_engine.find_best_episode_torrent(item['title'], ep_season, ep_num, imdb_id=item.get('imdb_id'))
            
            if ep_torrent:
                staging_ep = os.path.join(item['dest_workspace'], f"staging_temp_ep_{ep_season:02d}_{ep_num:02d}")
                success = download_torrent(ep_torrent['info_hash'], ep_torrent['name'], dest_dir, staging_ep, item_idx=item_idx)
                if success:
                    post_process_files(staging_ep, dest_dir, is_movie=False)
                else:
                    all_success = False
            else:
                print(f"\033[1;31m[!] Episode S{ep_season:02d}E{ep_num:02d} not found on trackers.\033[0m")
                all_success = False
        return all_success
        
    else:
        info_hash = item['info_hash']
        torrent_name = item['torrent_name']
        staging_dir = item['staging_dir']
        success = download_torrent(info_hash, torrent_name, dest_dir, staging_dir, item_idx=item_idx)
        if success:
            post_process_files(staging_dir, dest_dir, is_movie=is_movie)
        return success

class ProgressFileWrapper:
    def __init__(self, filepath, callback):
        self.file = open(filepath, 'rb')
        self.total_size = os.path.getsize(filepath)
        self.callback = callback
        self.bytes_read = 0

    def read(self, size=-1):
        data = self.file.read(size)
        self.bytes_read += len(data)
        self.callback(self.bytes_read, self.total_size)
        return data

    def seek(self, offset, whence=0):
        self.file.seek(offset, whence)
        if offset == 0 and whence == 0:
            self.bytes_read = 0

    def tell(self):
        return self.file.tell()

    def __len__(self):
        return self.total_size

    def close(self):
        self.file.close()

def load_config():
    init_queue_dir()
    config_path = os.path.join(QUEUE_DIR, 'config.json')
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    init_queue_dir()
    config_path = os.path.join(QUEUE_DIR, 'config.json')
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

def get_upload_target(target_name=None):
    if target_name:
        if os.path.exists(target_name):
            return target_name
        workspace_path = os.path.join(WORKSPACE_DIR, target_name)
        if os.path.exists(workspace_path):
            return workspace_path
        cwd_path = os.path.abspath(target_name)
        if os.path.exists(cwd_path):
            return cwd_path
        print(f"\033[1;31mError: Target '{target_name}' not found.\033[0m")
        return None
        
    if not os.path.exists(WORKSPACE_DIR):
        print(f"\033[1;31mError: Workspace directory '{WORKSPACE_DIR}' does not exist.\033[0m")
        return None
        
    options = []
    for name in os.listdir(WORKSPACE_DIR):
        full_path = os.path.join(WORKSPACE_DIR, name)
        is_dir = os.path.isdir(full_path)
        label = f"[Dir] {name}" if is_dir else f"[File] {name} ({format_size(os.path.getsize(full_path))})"
        options.append({'label': label, 'path': full_path, 'name': name})
        
    if not options:
        print("\033[1;33mNo folders or files found in workspace to upload.\033[0m")
        return None
        
    selection = interactive_select(options, "Select Folder/File to Upload to VLC")
    if selection:
        return selection['path']
    return None

def run_vlc_upload(target_name=None):
    config = load_config()
    last_vlc_ip = config.get('last_vlc_ip', '')
    
    print(f"\n\033[1;35m--- VLC WiFi Sharing Uploader ---\033[0m")
    prompt_str = f"Enter the VLC WiFi Sharing URL/IP [{last_vlc_ip}]: " if last_vlc_ip else "Enter the VLC WiFi Sharing URL/IP (e.g. 192.168.1.100:8080): "
    vlc_ip = input(prompt_str).strip()
    if not vlc_ip:
        vlc_ip = last_vlc_ip
        
    if not vlc_ip:
        print("\033[1;31mError: No VLC WiFi Sharing URL/IP specified.\033[0m")
        return
        
    if not vlc_ip.startswith('http://') and not vlc_ip.startswith('https://'):
        vlc_ip = "http://" + vlc_ip
        
    config['last_vlc_ip'] = vlc_ip
    save_config(config)
    
    upload_target = get_upload_target(target_name)
    if not upload_target:
        return
        
    video_extensions = ['.mp4', '.mkv', '.avi', '.m4v', '.mov']
    files_to_upload = []
    if os.path.isdir(upload_target):
        for root, dirs, files in os.walk(upload_target):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in video_extensions:
                    files_to_upload.append(os.path.join(root, file))
    else:
        ext = os.path.splitext(upload_target)[1].lower()
        if ext in video_extensions:
            files_to_upload.append(upload_target)
            
    if not files_to_upload:
        print("\033[1;31mNo compatible video files found to upload.\033[0m")
        return
        
    upload_url = f"{vlc_ip.rstrip('/')}/upload"
    print(f"\033[1;34m[*] Connecting to VLC at {vlc_ip}...\033[0m")
    try:
        r = requests.get(vlc_ip, timeout=5)
        if r.status_code != 200:
            print(f"\033[1;31m[!] Warning: VLC returned status code {r.status_code}. Attempting upload anyway...\033[0m")
    except Exception as e:
        print(f"\033[1;31m[!] Error connecting to {vlc_ip}: {e}\033[0m")
        print("\033[1;31mMake sure VLC is open on your iPad and WiFi Sharing is enabled!\033[0m")
        return
        
    print(f"\n\033[1;34m[*] Uploading {len(files_to_upload)} files...\033[0m")
    for idx, filepath in enumerate(files_to_upload, 1):
        filename = os.path.basename(filepath)
        print(f"\n\033[1;36m[{idx}/{len(files_to_upload)}] {filename} ({format_size(os.path.getsize(filepath))})\033[0m")
        
        def progress_callback(bytes_read, total_size):
            progress = (bytes_read / total_size) * 100 if total_size > 0 else 0
            bar_len = 30
            filled_len = int(bar_len * bytes_read // total_size) if total_size > 0 else 0
            bar = '=' * filled_len + '-' * (bar_len - filled_len)
            print(f"\rUpload Progress: [{bar}] {progress:.1f}% | {format_size(bytes_read)}/{format_size(total_size)}", end="", flush=True)
            
        try:
            wrapped_file = ProgressFileWrapper(filepath, progress_callback)
            response = requests.post(upload_url, files={'file': (filename, wrapped_file, 'video/mp4')}, timeout=600)
            wrapped_file.close()
            
            if response.status_code in [200, 201, 204]:
                print(f"\n\033[1;32m[+] Successfully uploaded: {filename}\033[0m")
            else:
                print(f"\n\033[1;31m[!] Failed to upload {filename}. Status: {response.status_code}\033[0m")
        except Exception as e:
            print(f"\n\033[1;31m[!] Upload error for {filename}: {e}\033[0m")
            
    print(f"\n\033[1;32m[+] All uploads completed!\033[0m")

def show_suggestions(genre=None):
    print(f"\n\033[1;34m[*] Fetching top-rated movie and show suggestions...\033[0m")
    
    # 1. Fetch movies from YTS
    movies_list = []
    try:
        url = "https://yts.mx/api/v2/list_movies.json?sort_by=rating&minimum_rating=7.5&limit=25"
        if genre:
            url += f"&genre={urllib.parse.quote(genre.lower())}"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if res_data.get('status') == 'ok' and 'data' in res_data and 'movies' in res_data['data']:
                for movie in res_data['data']['movies']:
                    title = movie.get('title', 'Unknown Movie')
                    year = str(movie.get('year', ''))
                    rating = float(movie.get('rating', 0.0))
                    torrents = movie.get('torrents', [])
                    if torrents:
                        # Find the best quality torrent
                        best_tor = torrents[0]
                        for tor in torrents:
                            q = tor.get('quality', '')
                            if q in ['720p', '1080p']:
                                best_tor = tor
                                break
                        
                        movies_list.append({
                            "type": "movie",
                            "title": title,
                            "year": year,
                            "rating": rating,
                            "info_hash": best_tor.get('hash', '').lower(),
                            "size_bytes": best_tor.get('size_bytes', 0),
                            "seeders": best_tor.get('seeds', 0),
                            "label": f"[Movie] {title} ({year}) - Rating: {rating} ★ [YTS]"
                        })
    except Exception as e:
        print(f"\033[1;31m[!] Error fetching movie suggestions: {e}\033[0m")

    # 2. Filter TV shows from curated database
    shows_list = []
    for show in CURATED_SHOWS:
        if genre:
            if not any(g.lower() == genre.lower() for g in show["genres"]):
                continue
        shows_list.append({
            "type": "show",
            "title": show["title"],
            "year": show["year"],
            "rating": show["rating"],
            "id": show["id"],
            "imdb_id": show["imdb_id"],
            "label": f"[TV Show] {show['title']} ({show['year']}) - Rating: {show['rating']} ★"
        })

    # Combine both and sort by rating descending
    combined = movies_list + shows_list
    combined.sort(key=lambda x: x["rating"], reverse=True)

    if not combined:
        print(f"\033[1;33mNo suggestions found for genre '{genre}'\033[0m")
        return

    prompt_label = f"IMDb High Rated Suggestions (Genre: {genre.capitalize()})" if genre else "IMDb High Rated Suggestions (Recent Years)"
    selection = interactive_select(combined, prompt_label)
    if not selection:
        print("\033[1;31mCancelled.\033[0m")
        return

    # Process suggestion selection
    new_item = {
        "id": str(int(time.time())),
        "type": selection['type'],
        "title": selection['title'],
        "status": "queued",
        "progress": 0.0,
        "speed_mb": 0.0,
        "peers": 0,
        "eta": "Unknown"
    }

    if selection['type'] == 'show':
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
        new_item["target_season"] = target_season
        new_item["max_season"] = seasons[-1] if seasons else None
        new_item["imdb_id"] = selection.get('imdb_id', '')
        
        dest_workspace = prompt_output_path()
        new_item["dest_workspace"] = dest_workspace
        
        print(f"\033[1;34m[*] Searching for season/series pack on APIBay...\033[0m")
        torrent_pack = search_season_pack(show_title, target_season, max_season=new_item["max_season"])
        
        show_folder_name = re.sub(r'[\\/*?:"<>|]', "", show_title)
        dest_dir = os.path.join(dest_workspace, show_folder_name)
        new_item["dest_dir"] = dest_dir
        
        if torrent_pack:
            new_item["torrent_name"] = torrent_pack['name']
            new_item["info_hash"] = torrent_pack['info_hash']
            new_item["staging_dir"] = os.path.join(dest_workspace, "staging_temp_" + new_item["id"])
        else:
            target_eps = [ep for ep in episodes if target_season is None or ep['season'] == target_season]
            new_item["episodes"] = target_eps
            new_item["torrent_name"] = f"{show_title} (Individual Episodes)"
            new_item["info_hash"] = "fallback"
            
    else:
        movie_title = selection['title']
        info_hash = selection['info_hash']
        
        dest_workspace = prompt_output_path()
        new_item["dest_workspace"] = dest_workspace
        
        movie_folder_name = re.sub(r'[\\/*?:"<>|]', "", movie_title)
        dest_dir = os.path.join(dest_workspace, movie_folder_name)
        new_item["dest_dir"] = dest_dir
        new_item["torrent_name"] = movie_title
        new_item["info_hash"] = info_hash
        new_item["is_movie"] = True
        new_item["staging_dir"] = os.path.join(dest_workspace, "staging_temp_" + new_item["id"])

    # Append to queue
    q_data = load_queue()
    q_data['queue'].append(new_item)
    save_queue(q_data)
    
    print(f"\033[1;32m[+] Added '{new_item['title']}' to download queue.\033[0m")
    
    if is_downloader_running():
        print("\033[1;33m[*] A download process is already running in the background. Your item will be downloaded sequentially.\033[0m")
    else:
        print("\033[1;32m[*] Queue is idle. Starting downloads now...\033[0m")
        process_queue_loop()

def run_suggest_genre():
    genres = ["Action", "Adventure", "Comedy", "Crime", "Drama", "Fantasy", "Horror", "Mystery", "Sci-Fi", "Thriller"]
    genre_options = [{'label': g, 'val': g} for g in genres]
    sel = interactive_select(genre_options, "Select Genre for Recommendations")
    if sel:
        show_suggestions(genre=sel['val'])

def show_help():
    print(f"\n\033[1;35mdownloadcc (v{VERSION}) - Interactive Movies & TV Shows Downloader\033[0m")
    print("\033[1;30m" + "=" * 60 + "\033[0m")
    print("Usage: \033[1;36mdownloadcc [command] [args...]\033[0m\n")
    print("Commands:")
    print("  \033[1;32mdownloadcc\033[0m                  - Launch search and interactive downloader.")
    print("  \033[1;32mdownloadcc \"Query\"\033[0m          - Search and select a show/movie to download immediately.")
    print("  \033[1;32mdownloadcc queue\033[0m            - View active download status and all items in the queue.")
    print("  \033[1;32mdownloadcc add \"Query\"\033[0m      - Search and add a new item directly to the background queue.")
    print("  \033[1;32mdownloadcc remove <number>\033[0m  - Remove an item from the queue list by its index number.")
    print("  \033[1;32mdownloadcc clear\033[0m            - Clear all pending items from the download queue.")
    print("  \033[1;32mdownloadcc vlc [\"Target\"]\033[0m   - Upload a file/folder wirelessly to VLC on your iPad.")
    print("  \033[1;32mdownloadcc suggest\033[0m          - Show high-rated movie and TV show suggestions from recent years.")
    print("  \033[1;32mdownloadcc suggest genre\033[0m    - Show major genres, let you select one, and recommend matching titles.")
    print("  \033[1;32mdownloadcc help\033[0m             - Show this help menu.")
    print("\033[1;30m" + "=" * 60 + "\033[0m")

def main():
    init_queue_dir()
    
    args = sys.argv[1:]
    
    if len(args) > 0:
        cmd = args[0].lower()
        if cmd == 'queue':
            show_queue()
            return
        elif cmd == 'clear':
            clear_queue()
            return
        elif cmd == 'remove':
            if len(args) < 2:
                print("\033[1;31mError: Please specify the item number to remove.\033[0m")
                print("Usage: downloadcc remove <number>")
                return
            remove_queue_item(args[1])
            return
        elif cmd == 'add':
            if len(args) < 2:
                print("\033[1;31mError: Please specify the movie or TV show name to add.\033[0m")
                print("Usage: downloadcc add \"Name\"")
                return
            query = " ".join(args[1:])
            add_item_to_queue(query)
            return
        elif cmd == 'vlc':
            target_name = " ".join(args[1:]) if len(args) > 1 else None
            run_vlc_upload(target_name)
            return
        elif cmd == 'suggest':
            if len(args) > 1 and args[1].lower() == 'genre':
                run_suggest_genre()
            else:
                show_suggestions()
            return
        elif cmd in ['help', '--help', '-h']:
            show_help()
            return
            
    # Default behavior: run search and interactive selection
    if len(args) == 0:
        query = input("\033[1;35mEnter the movie or TV show name to search: \033[0m").strip()
    else:
        query = " ".join(args)
        
    if not query:
        print("\033[1;31mError: No search query provided.\033[0m")
        return
        
    add_item_to_queue(query)

if __name__ == "__main__":
    main()
