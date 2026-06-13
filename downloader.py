import libtorrent as lt
import time
import os
import threading
import shutil
import re
import urllib.parse

class TorrentDownloader:
    def __init__(self, progress_callback=None, completion_callback=None, zip_complete_callback=None):
        """
        progress_callback: function(job_name, progress_pct, speed_mb, peers, state_str)
        completion_callback: function(job_name, success, output_file_or_error)
        zip_complete_callback: function(final_output_dir)  -- Triggered when a batch completes
        """
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.zip_complete_callback = zip_complete_callback
        self.queue = []
        self.current_job = None
        self.is_running = False
        self.thread = None
        self.session = None
        self.cancel_current = False
        self.staging_dir = os.path.join(os.path.expanduser('~'), '.gemini', 'antigravity', 'staging')
        os.makedirs(self.staging_dir, exist_ok=True)
        
    def start(self):
        if not self.is_running:
            self.is_running = True
            # Enable high-speed peer discovery features (UPnP, NAT-PMP, DHT, LSD) and connection limits
            self.session = lt.session({
                'listen_interfaces': '0.0.0.0:6881',
                'enable_upnp': True,
                'enable_natpmp': True,
                'enable_dht': True,
                'enable_lsd': True,
                'download_rate_limit': 0,
                'upload_rate_limit': 0,
                'connections_limit': 300
            })
            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()
            
    def stop(self):
        self.is_running = False
        self.cancel_current = True
            
    def add_job(self, info_hash, torrent_name, display_name, show_name=None, season=None, episode=None, is_movie=False, batch_id=None, output_dir=None, alternatives=None):
        job = {
            'info_hash': info_hash,
            'torrent_name': torrent_name,
            'display_name': display_name,
            'show_name': show_name,
            'season': season,
            'episode': episode,
            'is_movie': is_movie,
            'batch_id': batch_id,
            'output_dir': output_dir,
            'status': 'queued',
            'alternatives': alternatives or []
        }
        self.queue.append(job)
        return job

    def cancel_active_job(self):
        self.cancel_current = True

    def _worker(self):
        while self.is_running:
            if not self.queue:
                time.sleep(1)
                continue
                
            job = self.queue[0]
            self.current_job = job
            self.cancel_current = False
            job['status'] = 'downloading'
            
            # Define final destination directory early so it's always available (prevents UnboundLocalError on failure)
            if job['is_movie']:
                final_dest_dir = job['output_dir']
            else:
                show_clean = re.sub(r'[\\/*?:"<>|]', "", job['show_name'] or "TV Show")
                final_dest_dir = os.path.join(job['output_dir'], f"{show_clean} - Season {job['season']:02d}")
            
            success = False
            result_path = None
            
            # Auto-retry loop to cycle through alternatives if the primary magnet fails (no seeders/peers)
            while True:
                temp_download_dir = os.path.join(self.staging_dir, f"temp_{job['info_hash']}")
                os.makedirs(temp_download_dir, exist_ok=True)
                handle = None
                
                try:
                    # Add torrent
                    magnet_link = f"magnet:?xt=urn:btih:{job['info_hash']}&dn={urllib.parse.quote(job['torrent_name'])}&tr=udp://tracker.opentrackr.org:1337/announce&tr=udp://tracker.coppersurfer.tk:6969/announce&tr=udp://open.demonii.com:1337/announce&tr=udp://tracker.openbittorrent.com:80"
                    params = lt.parse_magnet_uri(magnet_link)
                    params.save_path = temp_download_dir
                    
                    handle = self.session.add_torrent(params)
                    
                    # Wait for metadata (timeout set to 25s to fail fast if no seeders)
                    metadata_timeout = 25
                    start_time = time.time()
                    while not handle.has_metadata():
                        if self.cancel_current or not self.is_running:
                            break
                        if time.time() - start_time > metadata_timeout:
                            break
                        
                        if self.progress_callback:
                            self.progress_callback(job['display_name'], 0.0, 0.0, handle.status().num_peers, "Fetching Metadata...")
                        time.sleep(1)
                        
                    if not handle.has_metadata():
                        raise Exception("Failed to retrieve torrent metadata (no seeders/peers found)")
                        
                    if self.cancel_current or not self.is_running:
                        raise Exception("Job cancelled by user")
                        
                    # Download torrent
                    torrent_info = handle.get_torrent_info()
                    print(f"Metadata loaded. Downloading {torrent_info.name()}...")
                    
                    while handle.status().state != lt.torrent_status.seeding:
                        if self.cancel_current or not self.is_running:
                            break
                        
                        s = handle.status()
                        state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume'][s.state]
                        
                        progress_pct = s.progress * 100
                        speed_mb = s.download_rate / (1024 * 1024)
                        peers = s.num_peers
                        
                        if self.progress_callback:
                            self.progress_callback(job['display_name'], progress_pct, speed_mb, peers, state_str)
                        
                        if s.progress >= 1.0:
                            break
                            
                        time.sleep(1)
                        
                    if self.cancel_current or not self.is_running:
                        raise Exception("Job cancelled by user")
                        
                    # Download complete! Locate the main video file
                    video_extensions = ['.mp4', '.mkv', '.avi', '.m4v', '.mov', '.ts']
                    largest_file = None
                    largest_size = 0
                    
                    for root, dirs, files in os.walk(temp_download_dir):
                        for file in files:
                            ext = os.path.splitext(file)[1].lower()
                            if ext in video_extensions:
                                file_path = os.path.join(root, file)
                                file_size = os.path.getsize(file_path)
                                if file_size > largest_size:
                                    largest_size = file_size
                                    largest_file = file_path
                                    
                    if not largest_file:
                        raise Exception("No video file found in downloaded torrent content")
                        
                    # Pause the torrent and wait to release Windows file handle locks before copy
                    try:
                        handle.pause()
                        time.sleep(1.0)
                    except Exception as pause_err:
                        print(f"Error pausing torrent: {pause_err}")
                        
                    # Post-processing: Copy file as-is (preserving original quality and audio tracks)
                    clean_name = self._generate_clean_filename(job, os.path.splitext(largest_file)[1])
                    
                    os.makedirs(final_dest_dir, exist_ok=True)
                    target_file_path = os.path.join(final_dest_dir, clean_name)
                    
                    if self.progress_callback:
                        self.progress_callback(job['display_name'], 100.0, 0.0, 0, "Saving file...")
                        
                    print(f"Copying file {largest_file} to {target_file_path}")
                    shutil.copy2(largest_file, target_file_path)
                    result_path = target_file_path
                    success = True
                    break # Success! Exit the retry loop
                    
                except Exception as e:
                    print(f"Error processing torrent {job['info_hash']} for job {job['display_name']}: {e}")
                    result_path = str(e)
                    
                finally:
                    # Remove torrent from session and delete temporary files
                    try:
                        if handle:
                            self.session.remove_torrent(handle, lt.session.delete_files)
                    except Exception as clean_err:
                        print(f"Error removing torrent: {clean_err}")
                    
                    # Small wait for file systems to release and delete temp dir
                    time.sleep(0.5)
                    if os.path.exists(temp_download_dir):
                        try:
                            shutil.rmtree(temp_download_dir)
                        except Exception as clean_err:
                            print(f"Error cleaning temp directory: {clean_err}")
                            
                # If we got here and failed, try the next alternative if any exist
                if self.cancel_current or not self.is_running:
                    break
                    
                if job.get('alternatives'):
                    alt = job['alternatives'].pop(0)
                    job['info_hash'] = alt['info_hash']
                    job['torrent_name'] = alt.get('name') or alt.get('title')
                    print(f"Retrying job {job['display_name']} with alternative torrent: {job['torrent_name']}")
                    if self.progress_callback:
                        self.progress_callback(job['display_name'], 0.0, 0.0, 0, "Retrying with alt...")
                    time.sleep(1.0)
                else:
                    break
            
            # Notify GUI of completion
            if self.completion_callback:
                self.completion_callback(job['display_name'], success, result_path)
                
            # Update job status
            job['status'] = 'completed' if success else 'failed'
            job['output_path'] = result_path if success else None
            
            # Remove from queue
            self.queue.pop(0)
            
            # If batch is complete (no more queued items with the same batch_id)
            if job['batch_id'] and job['output_dir']:
                same_batch_queued = any(j['batch_id'] == job['batch_id'] and j['status'] in ['queued', 'downloading'] for j in self.queue)
                if not same_batch_queued:
                    # Trigger batch complete callback
                    if self.zip_complete_callback:
                        self.zip_complete_callback(final_dest_dir)
                    
        self.current_job = None
        
    def _generate_clean_filename(self, job, original_ext):
        """
        Generates a clean naming convention:
        TV: Show Name - S01E01 - Episode Title.ext
        Movie: Movie Name (Year).ext
        """
        title = job['display_name']
        title_clean = re.sub(r'[\\/*?:"<>|]', "", title)
        return title_clean + original_ext
