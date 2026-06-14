import urllib.request
import urllib.parse
import json
import re
import html

def normalize_string(text):
    text = text.lower()
    # Replace separators (dots, dashes, underscores, slashes, pluses) with spaces
    text = re.sub(r'[._\-+/]', ' ', text)
    # Remove all other punctuation
    text = re.sub(r'[^a-z0-9\s]', '', text)
    # Merge single characters recursively (e.g. "s h i e l d" -> "shield", "u s a" -> "usa")
    prev = ""
    while prev != text:
        prev = text
        text = re.sub(r'\b([a-z0-9])\s+([a-z0-9])\b', r'\1\2', text)
    # Clean up duplicate spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_correct_title(torrent_name, title):
    # Clean leading release group brackets e.g. [Group] or (Group)
    t_name = re.sub(rf'^(\[[^\]]+\]|\([^\)]+\))[.\s_-]*', '', torrent_name)
    
    # Extract base show title by removing trailing parentheses e.g. "The Office (US)" -> "The Office"
    title_clean = re.sub(r'\s*\([^)]*\)', '', title)
    
    # Normalize both
    t_name_norm = normalize_string(t_name)
    title_norm = normalize_string(title_clean)
    
    title_words = title_norm.split()
    torrent_words = t_name_norm.split()
    
    if len(torrent_words) < len(title_words) or not title_words:
        return False
        
    # Check if the first N words of torrent match title
    match_start = True
    for i in range(len(title_words)):
        if torrent_words[i] != title_words[i]:
            match_start = False
            break
            
    # Handle "The" prefix optional match
    if not match_start and title_words[0] == 'the' and len(title_words) > 1:
        # Try matching without "the"
        title_words_no_the = title_words[1:]
        if len(torrent_words) >= len(title_words_no_the):
            match_start = True
            for i in range(len(title_words_no_the)):
                if torrent_words[i] != title_words_no_the[i]:
                    match_start = False
                    break
            if match_start:
                title_words = title_words_no_the
                
    if not match_start:
        return False
        
    # If it matched the prefix exactly
    if len(torrent_words) == len(title_words):
        return True
        
    # Check the word immediately following the title in the torrent name
    next_word = torrent_words[len(title_words)]
    
    # Check if next_word is a season/episode code, a year, or a valid quality tag
    if re.match(r'^(s\d+e\d+|s\d+|e\d+|\d+x\d+|\d{4})$', next_word):
        return True
        
    valid_following_tags = {
        '720p', '1080p', '2160p', '4k', 'x264', 'h264', 'x265', 'h265', 'hevc', 
        'web', 'webrip', 'webdl', 'web-dl', 'brrip', 'bdrip', 'bluray', 'hdtv', 
        'dsr', 'pdtv', 'dvdrip', 'dvdr', 'r5', 'cam', 'ts', 'tc', 'complete', 
        'season', 'seasons', 'episode', 'episodes', 'series', 'us', 'uk', 'ca'
    }
    
    if next_word in valid_following_tags:
        return True
        
    return False

def clean_html(raw_html):
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return html.unescape(cleantext)

def query_api(url, headers=None):
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=25) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error querying URL {url}: {e}")
        return None

def search_tv_shows(query):
    """
    Search for TV Shows using TVmaze API
    Returns a list of dictionaries with show details
    """
    url = f"https://api.tvmaze.com/search/shows?q={urllib.parse.quote(query)}"
    results = query_api(url)
    if not results:
        return []
    
    shows = []
    for item in results:
        show_data = item.get('show', {})
        show_id = show_data.get('id')
        name = show_data.get('name')
        
        # Extract year
        premiered = show_data.get('premiered') or ""
        year = premiered.split('-')[0] if '-' in premiered else "N/A"
        
        summary = clean_html(show_data.get('summary') or "")
        
        images = show_data.get('image') or {}
        poster_url = images.get('medium') or images.get('original') or ""
        
        shows.append({
            'id': show_id,
            'title': name,
            'year': year,
            'summary': summary,
            'poster_url': poster_url,
            'type': 'show',
            'genres': ", ".join(show_data.get('genres', []))
        })
    return shows

def get_show_episodes(show_id):
    """
    Fetch all episodes of a TV show using TVmaze API
    """
    url = f"https://api.tvmaze.com/shows/{show_id}/episodes"
    results = query_api(url)
    if not results:
        return []
    
    episodes = []
    for ep in results:
        episodes.append({
            'id': ep.get('id'),
            'name': ep.get('name', 'No Title'),
            'season': ep.get('season', 1),
            'number': ep.get('number', 1),
            'summary': clean_html(ep.get('summary') or "")
        })
    return episodes

def search_movies(query):
    """
    Search for movies on apibay.org (The Pirate Bay API)
    Filters results by category 201 (Movies) and 207 (HD - Movies)
    """
    url = f"https://apibay.org/q.php?q={urllib.parse.quote(query)}"
    results = query_api(url)
    if not results or not isinstance(results, list):
        return []
    
    # Filter out empty results (apibay returns a single item list [{'id': '0', ...}] if nothing found)
    if len(results) == 1 and results[0].get('id') == '0':
        return []
        
    movies = []
    for item in results:
        cat = item.get('category', '')
        # 201: Movies, 202: Movies DVDR, 207: HD - Movies
        if cat in ['201', '202', '207'] and is_correct_title(item.get('name', ''), query):
            size_bytes = int(item.get('size', 0))
            size_gb = size_bytes / (1024 * 1024 * 1024)
            
            movies.append({
                'id': item.get('id'),
                'title': item.get('name'),
                'info_hash': item.get('info_hash'),
                'size_gb': f"{size_gb:.2f} GB",
                'seeders': int(item.get('seeders', 0)),
                'leechers': int(item.get('leechers', 0)),
                'type': 'movie',
                'size': size_bytes
            })
            
    # Filter out dead torrents if any seeded torrents exist to avoid metadata hangs
    if movies:
        has_seeded = any(m['seeders'] > 0 for m in movies)
        if has_seeded:
            has_healthy = any(m['seeders'] >= 3 for m in movies)
            if has_healthy:
                movies = [m for m in movies if m['seeders'] >= 3]
            else:
                movies = [m for m in movies if m['seeders'] > 0]
            
    # Calculate score for each movie to prefer 720p and smaller sizes
    for m in movies:
        name_lower = m['title'].lower()
        score = min(m['seeders'], 100)
        
        if '720p' in name_lower:
            score += 300
        elif '480p' in name_lower or 'dvdrip' in name_lower or 'brrip' in name_lower or 'bdrip' in name_lower:
            score += 200
        elif '1080p' in name_lower:
            score -= 50
        elif '2160p' in name_lower or '4k' in name_lower:
            score -= 500
            
        size_mb = m['size'] / (1024 * 1024)
        if 600 <= size_mb <= 1800:
            score += 150
        elif size_mb > 3500:
            score -= 200
            
        # Penalize x265, h265, hevc, av1, 10bit (incompatible video codecs on native iPad player)
        if any(codec in name_lower for codec in ['x265', 'h265', 'hevc', 'av1', '10bit', '10-bit']):
            score -= 500
            
        # Prefer x264/h264
        if any(codec in name_lower for codec in ['x264', 'h264', 'h.264']):
            score += 150
            
        # Prefer mp4 container
        if 'mp4' in name_lower:
            score += 50
            
        m['score'] = score
            
    # Sort by score descending, then by seeders descending
    movies.sort(key=lambda x: (x.get('score', 0), x['seeders']), reverse=True)
    return movies

def find_best_episode_torrent(show_name, season, episode, all_candidates=False):
    """
    Finds the best torrent for a specific show episode (e.g. S01E01)
    """
    # Search formats: "Show Name S01E01"
    query = f"{show_name} S{season:02d}E{episode:02d}"
    url = f"https://apibay.org/q.php?q={urllib.parse.quote(query)}"
    
    results = query_api(url)
    if not results or not isinstance(results, list):
        return None
        
    if len(results) == 1 and results[0].get('id') == '0':
        return None
        
    valid_torrents = []
    # Pattern to match current season and episode
    # e.g., matches s01e01, 1x01, s1e1, s01.e01, etc.
    s_ep_pattern = re.compile(rf'(s{season:02d}e{episode:02d}|s{season}e{episode}|{season}x{episode:02d}|{season}x{episode})', re.IGNORECASE)
    
    for item in results:
        name = item.get('name', '')
        if s_ep_pattern.search(name) and is_correct_title(name, show_name):
            size_bytes = int(item.get('size', 0))
            size_mb = size_bytes / (1024 * 1024)
            
            # Filters: Episode size usually between 40MB and 2.5GB
            if 40 < size_mb < 2500:
                valid_torrents.append({
                    'id': item.get('id'),
                    'name': name,
                    'info_hash': item.get('info_hash'),
                    'seeders': int(item.get('seeders', 0)),
                    'leechers': int(item.get('leechers', 0)),
                    'size': size_bytes
                })
                
    if not valid_torrents:
        # Fallback: if no size filter matched, take the most seeded overall matching name
        for item in results:
            name = item.get('name', '')
            if s_ep_pattern.search(name) and is_correct_title(name, show_name):
                valid_torrents.append({
                    'id': item.get('id'),
                    'name': name,
                    'info_hash': item.get('info_hash'),
                    'seeders': int(item.get('seeders', 0)),
                    'leechers': int(item.get('leechers', 0)),
                    'size': int(item.get('size', 0))
                })
                
    if not valid_torrents:
        return None
        
    # Filter out dead torrents if any seeded torrents exist to avoid metadata hangs
    has_seeded = any(t['seeders'] > 0 for t in valid_torrents)
    if has_seeded:
        has_healthy = any(t['seeders'] >= 3 for t in valid_torrents)
        if has_healthy:
            valid_torrents = [t for t in valid_torrents if t['seeders'] >= 3]
        else:
            valid_torrents = [t for t in valid_torrents if t['seeders'] > 0]
        
    # Calculate score for each torrent to prefer 720p and smaller sizes
    for t in valid_torrents:
        name_lower = t['name'].lower()
        size_mb = t['size'] / (1024 * 1024)
        
        # Base score based on seeders
        score = min(t['seeders'], 100)
        
        # Prefer 720p and 480p
        if '720p' in name_lower:
            score += 300
        elif '480p' in name_lower or ('x264' in name_lower and '1080p' not in name_lower):
            score += 200
        elif '1080p' in name_lower:
            score -= 100
        elif '2160p' in name_lower or '4k' in name_lower:
            score -= 500
            
        # Prefer sizes between 80MB and 600MB
        if 80 <= size_mb <= 600:
            score += 150
        elif size_mb > 1000:
            score -= 200
            
        # Penalize x265, h265, hevc, av1, 10bit (incompatible video codecs on native iPad player)
        if any(codec in name_lower for codec in ['x265', 'h265', 'hevc', 'av1', '10bit', '10-bit']):
            score -= 500
            
        # Prefer x264/h264
        if any(codec in name_lower for codec in ['x264', 'h264', 'h.264']):
            score += 150
            
        # Prefer mp4 container
        if 'mp4' in name_lower:
            score += 50
            
        t['score'] = score
        
    # Sort by score descending, then by seeders descending
    valid_torrents.sort(key=lambda x: (x['score'], x['seeders']), reverse=True)
    if all_candidates:
        return valid_torrents
    return valid_torrents[0]

def search_archive_org(query):
    """
    Fallback method to search legal videos on Archive.org
    """
    params = {
        'q': f'({query}) AND mediatype:(movies)',
        'fl[]': 'identifier,title,downloads,description,btih',
        'sort[]': 'downloads desc',
        'output': 'json',
        'rows': 15
    }
    url = 'https://archive.org/advancedsearch.php?' + urllib.parse.urlencode(params)
    
    try:
        data = query_api(url)
        if not data:
            return []
        docs = data.get('response', {}).get('docs', [])
        
        results = []
        for doc in docs:
            # We look for a btih (BitTorrent Info Hash) or download links
            results.append({
                'id': doc.get('identifier'),
                'title': doc.get('title'),
                'info_hash': doc.get('btih'),
                'description': clean_html(doc.get('description') or ""),
                'type': 'archive',
                'downloads': doc.get('downloads', 0)
            })
        return results
    except Exception as e:
        print(f"Error searching Archive.org: {e}")
        return []
