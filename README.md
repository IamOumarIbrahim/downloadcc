# Movies & TV Shows Downloader for iPad

A Python desktop application with a modern, dark-themed GUI (built using `customtkinter`) that allows users to search for movies and TV shows, manage a download queue, download content programmatically using a native BitTorrent library (`libtorrent`), and save files directly as-is in their original extensions, perfectly named and organized for local playback on iPad (best played using VLC).

## 🚀 Direct Download

You can download the compiled standalone Windows installer directly here:
👉 **[Download MoviesAndShowsInstaller.exe (24.4 MB)](https://github.com/IamOumarIbrahim/MoviesAndShowsInstaller/raw/master/MoviesAndShowsInstaller.exe)**

## Features

- **📺 TV Show Metadata (TVmaze API)**: Instantly search and browse TV shows, view show details, cover poster art, and dynamically load all seasons and episode lists.
- **🔍 Strict Title Validation**: Implements a word-boundary title matcher ensuring that search queries map to the correct show name (preventing incorrect matches, such as *Your Friends and Neighbors* when searching for *Friends*).
- **⚡ 720p/480p & H.264 Prioritization**: Torrent search algorithm ranks and selects the healthiest 720p or 480p torrents. It actively penalizes HEVC/x265, AV1, and 10-bit color formats while promoting highly compatible H.264 (x264) video tracks and `.mp4` containers, ensuring video plays natively in your iPad Files app.
- **🚀 High-Speed Peer Discovery**: Configures the `libtorrent` session to enable UPnP, NAT-PMP, DHT, and Local Service Discovery (LSD), letting the application bypass NAT firewalls and connect to much larger sets of local and global peers for optimized download throughput.
- **🔄 Self-Healing Auto-Retries**: If a torrent fails to download or has no active seeders (metadata fetching timeout), the downloader automatically cycles through alternative search results (ranks 2-5) and retries the download sequentially.
- **🔒 Safe File Copying (No Locks)**: Automatically pauses active torrent downloads before copying files. This flushes write caches and releases Windows file handle locks, preventing file sharing violations or incomplete files.
- **📁 Queue Sidebar**: Real-time left sidebar tracking queued and actively downloading items with progress status and individual file percentages.
- **💾 Direct Saving (No ZIP)**: Downloads save directly as-is to your selected directory (organized in folders like `Downloads/Friends - Season 01/`).
- **🔊 As-Is Quality Preservation**: Bypasses transcoding completely, saving video files exactly as they are seeded. This preserves 100% of the original video and multi-channel audio tracks (AC3/DTS/AAC) without silent audio errors.
- **🔔 Batch Complete Popups**: A success dialog prompts the user when all files in a download batch have successfully completed.
- **❌ Queue Cancellation**: A cancellation button next to the progress bar allows users to stop the active torrent, flush remaining items, and reset status immediately.

---

## Technical Stack & Libraries

- **Core Logic**: Python 3.12+
- **GUI Engine**: CustomTkinter (built on standard Tkinter)
- **Torrent Engine**: Native Python `libtorrent` binary bindings
- **Poster Rendering**: Pillow (PIL)
- **Metadata Source**: TVmaze REST API (Open & Keyless)
- **Index Search Engine**: apibay.org API (The Pirate Bay backend index)

---

## Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/IamOumarIbrahim/MoviesAndShowsInstaller.git
   cd MoviesAndShowsInstaller
   ```

2. **Install Dependencies**:
   ```bash
   pip install customtkinter requests beautifulsoup4 pillow pyinstaller
   pip install libtorrent
   ```

3. **Verify Installation**:
   Ensure python can import `libtorrent` and `customtkinter`:
   ```bash
   python -c "import libtorrent as lt; import customtkinter; print(lt.__version__)"
   ```

---

## How to Run

Launch the application directly using python:
```bash
python app.py
```

---

## Packaging & Distribution

### 1. Compile Standalone Executable (PyInstaller)
To compile the Python scripts into a single standalone Windows executable containing all dependencies:
```bash
pyinstaller --noconsole --name "MoviesAndShowsDownloader" --add-data "C:\Users\omarb\AppData\Local\Programs\Python\Python312\Lib\site-packages\customtkinter;customtkinter" app.py
```
This will generate the compiled files inside `dist/MoviesAndShowsDownloader/`.

### 2. Compile Windows Installer (Inno Setup)
An Inno Setup compilation script `installer.iss` is included in the project directory. Opening this file in Inno Setup and compiling it creates a standard setup installer `MoviesAndShowsInstaller.exe` that:
- Installs the standalone executable under your Program Files.
- Creates Start Menu and Desktop shortcuts.
- Provides a clean windows installer interface.

---

## Transferring and Watching on iPad

Since files are downloaded as-is:
1. **Transfer to iPad**:
   - **Cloud Sync**: Put the downloaded season folders directly into your iCloud Drive, OneDrive, or Google Drive folder on your PC. They will sync and appear in your iPad's **Files** app.
   - **Local Transfer**: Connect your iPad via USB, open the Apple Devices app or iTunes, go to **File Sharing**, and drag the folders directly into the **VLC** app.
2. **Watch with Audio**:
   - Open **VLC on iPad** (completely free on the App Store).
   - Navigate to the synced files. VLC natively supports all video formats (MKV, MP4, AVI) and all audio decoders (AC3/DTS/AAC), ensuring high-fidelity sound and smooth video playback on your iPad screen!
