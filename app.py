import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import urllib.request
import ssl
from PIL import Image
import tempfile
import search_engine
import downloader

# Set GUI theme and colors
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Movies & TV Shows Downloader for iPad")
        self.geometry("1250x700")
        self.minsize(1150, 600)
        
        # Initialize downloader
        self.dl = downloader.TorrentDownloader(
            progress_callback=self.on_download_progress,
            completion_callback=self.on_download_complete,
            zip_complete_callback=self.on_batch_complete
        )
        self.dl.start()
        
        # State variables
        self.current_search_results = []
        self.selected_item = None # Selected show or movie
        self.episodes_list = [] # List of episodes for the selected show
        self.checkboxes = [] # List of checkbox widgets
        self.temp_poster_path = None
        self.current_batch_id = 1
        self.active_progress = 0.0
        
        # Layout: Grid definition (3 Columns now)
        self.grid_columnconfigure(0, weight=2) # Column 0: Queue Sidebar (width: 250)
        self.grid_columnconfigure(1, weight=3) # Column 1: Search Panel (width: 350)
        self.grid_columnconfigure(2, weight=5) # Column 2: Details Panel (width: 550)
        self.grid_rowconfigure(0, weight=9)    # Main workspace
        self.grid_rowconfigure(1, weight=1)    # Progress bar footer
        
        # Left Queue Sidebar Frame
        self.queue_sidebar = ctk.CTkFrame(self, corner_radius=10)
        self.queue_sidebar.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self._init_queue_sidebar()
        
        # Middle Panel Frame (Search & Results)
        self.left_panel = ctk.CTkFrame(self, corner_radius=10)
        self.left_panel.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        self._init_left_panel()
        
        # Right Panel Frame (Details)
        self.right_panel = ctk.CTkFrame(self, corner_radius=10)
        self.right_panel.grid(row=0, column=2, padx=15, pady=15, sticky="nsew")
        self._init_right_panel()
        
        # Footer Progress Frame
        self.footer = ctk.CTkFrame(self, corner_radius=0, height=80)
        self.footer.grid(row=1, column=0, columnspan=3, sticky="ew")
        self._init_footer()
        
        # Default save path is user's Downloads folder
        default_save_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        if not os.path.exists(default_save_dir):
            default_save_dir = os.getcwd()
        self.save_path_entry.insert(0, default_save_dir)
        
    def _init_queue_sidebar(self):
        self.queue_sidebar.grid_columnconfigure(0, weight=1)
        self.queue_sidebar.grid_rowconfigure(1, weight=1)
        
        self.queue_title = ctk.CTkLabel(self.queue_sidebar, text="Download Queue", font=ctk.CTkFont(size=18, weight="bold"))
        self.queue_title.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")
        
        self.queue_scroll_frame = ctk.CTkScrollableFrame(self.queue_sidebar, label_text="Status List")
        self.queue_scroll_frame.grid(row=1, column=0, padx=15, pady=10, sticky="nsew")
        
    def refresh_queue_sidebar(self):
        # Clear previous widgets
        for widget in self.queue_scroll_frame.winfo_children():
            widget.destroy()
            
        # Draw active job if exists
        active = self.dl.current_job
        if active:
            job_frame = ctk.CTkFrame(self.queue_scroll_frame, fg_color="#1c3144", corner_radius=6)
            job_frame.pack(fill="x", padx=2, pady=4)
            
            lbl = ctk.CTkLabel(job_frame, text=f"⏳ {active['display_name']}", font=ctk.CTkFont(size=11, weight="bold"), anchor="w", justify="left", wraplength=210)
            lbl.pack(fill="x", padx=8, pady=(8, 2))
            
            pb = ctk.CTkProgressBar(job_frame, height=5)
            pb.pack(fill="x", padx=8, pady=(4, 8))
            pb.set(self.active_progress / 100.0)
            
        # Draw queued items
        for job in self.dl.queue:
            if job['status'] == 'queued':
                job_frame = ctk.CTkFrame(self.queue_scroll_frame, fg_color="#2b2b2b", corner_radius=6)
                job_frame.pack(fill="x", padx=2, pady=4)
                
                lbl = ctk.CTkLabel(job_frame, text=f"🕒 {job['display_name']}", font=ctk.CTkFont(size=11), anchor="w", justify="left", wraplength=210)
                lbl.pack(fill="x", padx=8, pady=8)
        
    def _init_left_panel(self):
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(2, weight=1)
        
        self.search_label = ctk.CTkLabel(self.left_panel, text="Search Movies & Shows", font=ctk.CTkFont(size=18, weight="bold"))
        self.search_label.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")
        
        self.search_row = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.search_row.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        self.search_row.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(self.search_row, placeholder_text="Enter show or movie keyword...")
        self.search_entry.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ew")
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        
        self.search_btn = ctk.CTkButton(self.search_row, text="Search", width=80, command=self.perform_search)
        self.search_btn.grid(row=0, column=1, padx=0, pady=0)
        
        self.results_list_frame = ctk.CTkScrollableFrame(self.left_panel, label_text="Search Results")
        self.results_list_frame.grid(row=2, column=0, padx=15, pady=10, sticky="nsew")
        
    def _init_right_panel(self):
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        
        self.save_row = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.save_row.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")
        self.save_row.grid_columnconfigure(1, weight=1)
        
        self.save_lbl = ctk.CTkLabel(self.save_row, text="Output Directory:")
        self.save_lbl.grid(row=0, column=0, padx=(0, 10), pady=0)
        
        self.save_path_entry = ctk.CTkEntry(self.save_row)
        self.save_path_entry.grid(row=0, column=1, padx=(0, 10), pady=0, sticky="ew")
        
        self.browse_btn = ctk.CTkButton(self.save_row, text="Browse", width=70, command=self.browse_output_dir)
        self.browse_btn.grid(row=0, column=2, padx=0, pady=0)
        
        self.details_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.details_frame.grid(row=1, column=0, padx=15, pady=10, sticky="nsew")
        
        self.details_frame.grid_columnconfigure(0, weight=3)
        self.details_frame.grid_columnconfigure(1, weight=7)
        self.details_frame.grid_rowconfigure(0, weight=1)
        
        self.left_details = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.left_details.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        self.left_details.grid_columnconfigure(0, weight=1)
        
        self.poster_label = ctk.CTkLabel(self.left_details, text="Select a Show/Movie", width=150, height=220, fg_color="#2b2b2b", corner_radius=8)
        self.poster_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.meta_label = ctk.CTkLabel(self.left_details, text="", font=ctk.CTkFont(size=12, slant="italic"), justify="left", wraplength=160)
        self.meta_label.grid(row=1, column=0, padx=5, pady=10, sticky="w")
        
        self.right_details = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.right_details.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        self.right_details.grid_columnconfigure(0, weight=1)
        self.right_details.grid_rowconfigure(2, weight=1)
        
        self.title_label = ctk.CTkLabel(self.right_details, text="Details Panel", font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=5, pady=(5, 5), sticky="w")
        
        self.desc_text = ctk.CTkTextbox(self.right_details, height=80, activate_scrollbars=True, wrap="word")
        self.desc_text.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.desc_text.insert("0.0", "Search and select a movie or show to display its description, episodes list, and download links here.")
        self.desc_text.configure(state="disabled")
        
        self.episode_area = ctk.CTkFrame(self.right_details, fg_color="transparent")
        self.episode_area.grid(row=2, column=0, padx=0, pady=5, sticky="nsew")
        self.episode_area.grid_columnconfigure(0, weight=1)
        self.episode_area.grid_rowconfigure(1, weight=1)
        
        self.ep_controls = ctk.CTkFrame(self.episode_area, fg_color="transparent")
        self.ep_controls.grid(row=0, column=0, padx=5, pady=(5, 5), sticky="ew")
        
        self.season_menu = ctk.CTkOptionMenu(self.ep_controls, values=["Season 1"], command=self.on_season_change)
        self.season_menu.grid(row=0, column=0, padx=(0, 10), pady=0)
        
        self.select_all_btn = ctk.CTkButton(self.ep_controls, text="Select All", width=80, command=self.select_all_episodes)
        self.select_all_btn.grid(row=0, column=1, padx=(0, 10), pady=0)
        
        self.clear_all_btn = ctk.CTkButton(self.ep_controls, text="Clear", width=60, command=self.clear_all_episodes)
        self.clear_all_btn.grid(row=0, column=2, padx=0, pady=0)
        
        self.episode_list_frame = ctk.CTkScrollableFrame(self.episode_area, label_text="Episodes List")
        self.episode_list_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        self.actions_row = ctk.CTkFrame(self.right_details, fg_color="transparent")
        self.actions_row.grid(row=3, column=0, padx=5, pady=(10, 5), sticky="ew")
        self.actions_row.grid_columnconfigure(0, weight=1)
        
        self.download_btn = ctk.CTkButton(self.actions_row, text="Download Selected Content", font=ctk.CTkFont(size=14, weight="bold"), height=35, command=self.start_download)
        self.download_btn.grid(row=0, column=0, padx=0, pady=0, sticky="ew")
        self.download_btn.configure(state="disabled")

    def _init_footer(self):
        self.footer.grid_columnconfigure(0, weight=1)
        self.footer.grid_columnconfigure(1, weight=0)
        
        self.footer_label = ctk.CTkLabel(self.footer, text="Queue status: Idle", font=ctk.CTkFont(size=13, weight="bold"))
        self.footer_label.grid(row=0, column=0, padx=20, pady=(10, 2), sticky="w")
        
        self.footer_progress = ctk.CTkProgressBar(self.footer, height=12)
        self.footer_progress.grid(row=1, column=0, padx=(20, 10), pady=2, sticky="ew")
        self.footer_progress.set(0)
        
        self.cancel_btn = ctk.CTkButton(self.footer, text="Cancel & Clear Queue", fg_color="#9e2a2b", hover_color="#c1121f", height=24, width=160, command=self.cancel_downloads)
        self.cancel_btn.grid(row=1, column=1, padx=(10, 20), pady=2)
        self.cancel_btn.configure(state="disabled")
        
        self.status_label = ctk.CTkLabel(self.footer, text="Speed: 0.00 MB/s | Peers: 0 | Progress: 0.0% | Status: waiting", font=ctk.CTkFont(size=11, slant="italic"))
        self.status_label.grid(row=2, column=0, padx=20, pady=(2, 10), sticky="w")

    def perform_search(self):
        query = self.search_entry.get().strip()
        if not query:
            return
            
        self.search_btn.configure(state="disabled", text="Searching...")
        
        def run():
            tv_results = search_engine.search_tv_shows(query)
            movie_results = search_engine.search_movies(query)
            combined = tv_results + movie_results
            self.after(0, lambda: self.show_search_results(combined))
            
        threading.Thread(target=run, daemon=True).start()
        
    def show_search_results(self, results):
        self.search_btn.configure(state="normal", text="Search")
        self.current_search_results = results
        
        for widget in self.results_list_frame.winfo_children():
            widget.destroy()
            
        if not results:
            no_lbl = ctk.CTkLabel(self.results_list_frame, text="No matches found.", font=ctk.CTkFont(slant="italic"))
            no_lbl.pack(pady=20)
            return
            
        for i, item in enumerate(results):
            if item['type'] == 'show':
                btn_text = f"📺 [TV] {item['title']} ({item['year']})"
            else:
                btn_text = f"🎬 [Movie] {item['title']} ({item['size_gb']})"
                
            btn = ctk.CTkButton(
                self.results_list_frame, 
                text=btn_text, 
                anchor="w",
                fg_color="#1f1f1f",
                hover_color="#2b2b2b",
                height=35,
                command=lambda idx=i: self.on_result_select(idx)
            )
            btn.pack(fill="x", padx=5, pady=4)
            
    def on_result_select(self, index):
        item = self.current_search_results[index]
        self.selected_item = item
        
        self.desc_text.configure(state="normal")
        self.desc_text.delete("0.0", "end")
        self.desc_text.insert("0.0", item.get('summary') or "No summary description available.")
        self.desc_text.configure(state="disabled")
        
        self.title_label.configure(text=f"{item['title']} ({item['year']})")
        if item['type'] == 'show':
            self.meta_label.configure(text=f"Type: TV Series\nGenres: {item['genres']}")
            self.episode_area.grid(row=2, column=0, padx=0, pady=5, sticky="nsew")
            self.download_btn.configure(state="normal", text="Download Selected Episodes")
            self.load_show_episodes(item['id'])
        else:
            self.meta_label.configure(text=f"Type: Movie\nSize: {item['size_gb']}\nSeeders: {item['seeders']}")
            self.episode_area.grid_forget()
            self.download_btn.configure(state="normal", text="Download Movie")
            
        if item.get('poster_url'):
            self.load_poster_image(item['poster_url'])
        else:
            self.poster_label.configure(text="No Poster", image=None)
            
    def load_poster_image(self, url):
        self.poster_label.configure(text="Loading poster...", image=None)
        
        def run():
            try:
                ctx = ssl._create_unverified_context()
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp_path = temp_file.name
                temp_file.close()
                
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, context=ctx, timeout=10) as response, open(temp_path, 'wb') as out_file:
                    out_file.write(response.read())
                    
                def update_gui(img_path):
                    try:
                        ctk_img = ctk.CTkImage(light_image=Image.open(img_path), size=(150, 220))
                        self.poster_label.configure(image=ctk_img, text="")
                        self.poster_image_ref = ctk_img
                        self.temp_poster_path = img_path
                    except Exception as err:
                        self.poster_label.configure(text="Poster Error")
                        print(f"PIL loading error: {err}")
                        
                self.after(0, lambda: update_gui(temp_path))
            except Exception as e:
                print(f"Error downloading poster: {e}")
                self.after(0, lambda: self.poster_label.configure(text="No Poster"))
                
        threading.Thread(target=run, daemon=True).start()

    def load_show_episodes(self, show_id):
        self.season_menu.configure(state="disabled", values=["Loading..."])
        for widget in self.episode_list_frame.winfo_children():
            widget.destroy()
            
        def run():
            episodes = search_engine.get_show_episodes(show_id)
            self.episodes_list = episodes
            seasons = sorted(list(set(ep['season'] for ep in episodes)))
            season_strings = [f"Season {s}" for s in seasons]
            self.after(0, lambda: self.update_season_menu(season_strings))
            
        threading.Thread(target=run, daemon=True).start()
        
    def update_season_menu(self, seasons):
        self.season_menu.destroy()
        if seasons:
            self.season_menu = ctk.CTkOptionMenu(self.ep_controls, values=seasons, command=self.on_season_change)
            self.season_menu.grid(row=0, column=0, padx=(0, 10), pady=0)
            self.season_menu.set(seasons[0])
            self.on_season_change(seasons[0])
        else:
            self.season_menu = ctk.CTkOptionMenu(self.ep_controls, values=["None"], command=self.on_season_change)
            self.season_menu.grid(row=0, column=0, padx=(0, 10), pady=0)
            self.season_menu.set("None")
            self.season_menu.configure(state="disabled")

    def cancel_downloads(self):
        if messagebox.askyesno("Cancel Download", "Are you sure you want to cancel the current download and clear the download queue?"):
            self.dl.cancel_active_job()
            self.dl.queue.clear()
            self.cancel_btn.configure(state="disabled")
            self.footer_label.configure(text="Queue status: Idle (Cancelled)")
            self.footer_progress.set(0)
            self.status_label.configure(text="Speed: 0.00 MB/s | Peers: 0 | Progress: 0.0% | Status: waiting")
            self.refresh_queue_sidebar()
            
    def on_season_change(self, season_str):
        for widget in self.episode_list_frame.winfo_children():
            widget.destroy()
        self.checkboxes = []
        
        try:
            season_num = int(season_str.replace("Season ", ""))
        except ValueError:
            return
            
        season_eps = [ep for ep in self.episodes_list if ep['season'] == season_num]
        for ep in season_eps:
            cb = ctk.CTkCheckBox(self.episode_list_frame, text=f"E{ep['number']:02d}: {ep['name']}")
            cb.pack(anchor="w", padx=10, pady=5, fill="x")
            self.checkboxes.append((cb, ep))
            
    def select_all_episodes(self):
        for cb, ep in self.checkboxes:
            cb.select()
            
    def clear_all_episodes(self):
        for cb, ep in self.checkboxes:
            cb.deselect()
            
    def browse_output_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path_entry.delete(0, "end")
            self.save_path_entry.insert(0, folder)
            
    def start_download(self):
        save_dir = self.save_path_entry.get().strip()
        if not save_dir or not os.path.exists(save_dir):
            messagebox.showerror("Error", "Please select a valid output directory.")
            return
            
        item = self.selected_item
        if not item:
            return
            
        batch_id = self.current_batch_id
        self.current_batch_id += 1
        
        if item['type'] == 'show':
            selected_eps = [ep for cb, ep in self.checkboxes if cb.get()]
            if not selected_eps:
                messagebox.showwarning("Warning", "Please select at least one episode to download.")
                return
                
            self.download_btn.configure(state="disabled", text="Adding to Queue...")
            
            def search_and_enqueue():
                added_count = 0
                for ep in selected_eps:
                    display_name = f"{item['title']} - S{ep['season']:02d}E{ep['number']:02d} - {ep['name']}"
                    
                    self.after(0, lambda name=display_name: self.footer_label.configure(
                        text=f"Searching torrent for: {name}"
                    ))
                    
                    torrents = search_engine.find_best_episode_torrent(item['title'], ep['season'], ep['number'], all_candidates=True)
                    if torrents:
                        best_torrent = torrents[0]
                        alternatives = torrents[1:5] # Keep up to 4 backup candidates
                        self.dl.add_job(
                            info_hash=best_torrent['info_hash'],
                            torrent_name=best_torrent['name'],
                            display_name=display_name,
                            show_name=item['title'],
                            season=ep['season'],
                            episode=ep['number'],
                            is_movie=False,
                            batch_id=batch_id,
                            output_dir=save_dir,
                            alternatives=alternatives
                        )
                        added_count += 1
                        self.after(0, self.refresh_queue_sidebar)
                    else:
                        print(f"No torrent found for episode: {display_name}")
                        
                def finalize_enqueue(count):
                    self.download_btn.configure(state="normal", text="Download Selected Episodes")
                    self.refresh_queue_sidebar()
                    if count > 0:
                        self.cancel_btn.configure(state="normal")
                        messagebox.showinfo("Success", f"Successfully added {count} episodes to download queue!\nFiles will be saved in subfolder:\n{item['title']} - Season {selected_eps[0]['season']:02d}")
                    else:
                        messagebox.showerror("Failed", "Could not locate any active torrent links for the selected episodes.")
                        
                self.after(0, lambda: finalize_enqueue(added_count))
                
            threading.Thread(target=search_and_enqueue, daemon=True).start()
            
        else:
            # It's a Movie
            self.download_btn.configure(state="disabled", text="Adding to Queue...")
            
            def enqueue_movie():
                display_name = f"{item['title']} ({item['year']})"
                
                # Fetch alternative torrents for the movie
                movie_torrents = search_engine.search_movies(item['title'])
                alternatives = [t for t in movie_torrents if t['info_hash'] != item['info_hash']][:4]
                
                self.dl.add_job(
                    info_hash=item['info_hash'],
                    torrent_name=item['title'],
                    display_name=display_name,
                    show_name=item['title'],
                    is_movie=True,
                    batch_id=batch_id,
                    output_dir=save_dir,
                    alternatives=alternatives
                )
                
                def finalize():
                    self.download_btn.configure(state="normal", text="Download Movie")
                    self.cancel_btn.configure(state="normal")
                    self.refresh_queue_sidebar()
                    messagebox.showinfo("Success", f"Added movie '{display_name}' to download queue.\nFile will be saved directly in:\n{save_dir}")
                    
                self.after(0, finalize)
                
            threading.Thread(target=enqueue_movie, daemon=True).start()
            
    # Downloader event handlers
    def on_download_progress(self, job_name, progress_pct, speed_mb, peers, state_str):
        def update():
            self.footer_label.configure(text=f"Downloading: {job_name}")
            self.cancel_btn.configure(state="normal")
            self.footer_progress.set(progress_pct / 100.0)
            self.status_label.configure(
                text=f"Speed: {speed_mb:.2f} MB/s | Peers: {peers} | Progress: {progress_pct:.1f}% | Status: {state_str}"
            )
            self.active_progress = progress_pct
            self.refresh_queue_sidebar()
        self.after(0, update)
        
    def on_download_complete(self, job_name, success, output_file_or_error):
        def update():
            if success:
                print(f"Download completed for: {job_name}. Saved path: {output_file_or_error}")
            else:
                if "cancelled" not in str(output_file_or_error).lower():
                    messagebox.showerror("Download Error", f"Download failed for '{job_name}':\n{output_file_or_error}")
                
            self.active_progress = 0.0
            self.refresh_queue_sidebar()
            
            if not self.dl.queue and not self.dl.current_job:
                self.cancel_btn.configure(state="disabled")
                self.footer_label.configure(text="Queue status: Idle")
                self.footer_progress.set(0)
                self.status_label.configure(text="Speed: 0.00 MB/s | Peers: 0 | Progress: 0.0% | Status: waiting")
                
        self.after(0, update)
        
    def on_batch_complete(self, final_output_dir):
        def update():
            messagebox.showinfo("Download Complete", f"All queued files successfully downloaded and saved directly to folder:\n{final_output_dir}")
        self.after(0, update)
        
    def destroy(self):
        self.dl.stop()
        if self.temp_poster_path and os.path.exists(self.temp_poster_path):
            try:
                os.remove(self.temp_poster_path)
            except:
                pass
        super().destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
