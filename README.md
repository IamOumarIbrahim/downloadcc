# 📺 downloadcc: Interactive Movies & TV Shows Downloader

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![BitTorrent-libtorrent](https://img.shields.io/badge/BitTorrent-libtorrent-brightgreen.svg?style=flat-square)](https://libtorrent.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

A lightweight, fully interactive terminal-based media downloader that allows users to search for movies and TV shows, select seasons/episodes interactively using keyboard arrow keys, download media using the native `libtorrent` library, and automatically save files organized and renamed for iPad local playback compatibility.

---

## 📖 Table of Contents
- [Direct Download](#-direct-download)
- [Key Features](#-key-features)
- [How to Install](#-how-to-install)
- [How to Use](#-how-to-use)
- [Technical Stack](#-technical-stack)
- [Packaging & Distribution](#-packaging--distribution)
- [Transferring and Watching on iPad](#-transferring-and-watching-on-ipad)
- [File Structure](#-file-structure)
- [License](#-license)

---

## 🚀 Direct Download

You can download the compiled standalone Windows installer directly here:
👉 **[Download MoviesAndShowsInstaller.exe](https://github.com/IamOumarIbrahim/movies-shows-downloader/raw/master/MoviesAndShowsInstaller.exe)**

*(Note: During installation, the installer will automatically add `downloadcc` to your user's system PATH, making it executable from any shell immediately).*

---

## ⭐ Key Features

- **💻 100% Terminal-Based CLI**: Highly responsive interactive keyboard-driven selection screen (use Up/Down arrow keys and Enter to navigate).
- **📺 TV Show Metadata Integration**: Automatically interfaces with the TVmaze API to load shows, search seasons, and list all episodes dynamically.
- **🔍 Strict Title Matching**: Implements custom regex validation to ensure your query results exactly match the target series.
- **⚡ iPad-Compatible Video Profiles (H.264/AAC)**: Search rankings prioritize H.264 video streams and `.mp4` containers. It deprioritizes HEVC/x265, AV1, and 10-bit color formats to guarantee out-of-the-box playback on iPad Files app.
- **🚀 High-Speed Peer Discovery**: Configures the underlying `libtorrent` session with DHT, Local Service Discovery (LSD), UPnP, and NAT-PMP enabled.
- **📁 Automatic Post-Processing**: Automatically organizes files into target folders (e.g. `{Show Name} - Season XX`) and renames video files to the clean `S_XX_E_YY.ext` convention.
- **💾 Custom Save Destination**: Prompts you to input your desired output save directory after confirming your selection (defaults to your downloads workspace if left blank).

---

## ⚙️ How to Install

### Method A: Setup Installer (Recommended)
1. Download and run **[MoviesAndShowsInstaller.exe](https://github.com/IamOumarIbrahim/movies-shows-downloader/raw/master/MoviesAndShowsInstaller.exe)**.
2. Complete the installer prompts (it will install into your AppData directory and register `downloadcc` globally in your User PATH).
3. Open a **new** PowerShell or Command Prompt session and run the tool:
   ```bash
   downloadcc
   ```

### Method B: Manual Python Environment
1. Clone the repository:
   ```bash
   git clone https://github.com/IamOumarIbrahim/movies-shows-downloader.git
   cd movies-shows-downloader
   ```
2. Install dependencies:
   ```bash
   pip install requests beautifulsoup4 libtorrent pyinstaller
   ```
3. Run the script:
   ```bash
   python downloadcc.py
   ```

---

## 🏃 How to Use

### Basic Commands

You can run `downloadcc` globally from any terminal session.

* **Search and Add**: Launch with or without a query to search and select media:
  ```bash
  downloadcc "Mr. Robot"
  ```
  1. **Numbered Selection**: Search results are classified and sorted by compatibility. Type the number `[1]`, `[2]`, etc. of the option you want and press **Enter** (or type `c` to cancel).
  2. **Select Season**: If a TV Show is selected, select a specific season (or choose **All Seasons (Complete Pack)**) using the same numbered prompt.
  3. **Choose Save Directory**: Input the absolute path where you want the files saved (or press Enter to use default).
  4. **Active Downloads**: Real-time progress percentage, speed (MB/s), active peer count, and dynamic **ETA** calculations are displayed.

* **Manage the Download Queue**:
  - **`downloadcc queue`**: Lists the actively downloading item (with speed, peers, progress, and ETA) and all pending items in the queue.
  - **`downloadcc add "Name"`**: Searches, selects, and appends a new item directly to the queue. If the downloader is idle, it starts downloading immediately. If it's busy, it queues it to start automatically once current downloads finish.
  - **`downloadcc remove <number>`**: Removes a pending item from the queue list by its queue index number.
  - **`downloadcc clear`**: Clears all pending items from the queue.
  - **`downloadcc vlc ["Folder or File"]`**: Launches the wireless uploader to push downloaded files directly to the VLC app on your iPad. If the folder/file is not specified, it lets you select from your workspace folders. Displays real-time progress bars for uploads.

* **Suggestions & Help**:
  - **`downloadcc suggest`**: Blends high-rated recent movies (live from YTS API) and popular TV shows (curated database) sorted by user rating, letting you select and add them to your queue.
  - **`downloadcc suggest genre`**: Displays a list of major genres (Action, Sci-Fi, Comedy, etc.), lets you choose one, and returns recommendations filtered by that genre.
  - **`downloadcc help`** / **`--help`**: Shows a detailed CLI help menu with usage guidelines and explanations of all commands.

---

## ⚡ Resuming & Self-Healing

* **Auto-Resuming**: If a download is closed or interrupted, running `downloadcc` will automatically check your staging folder, verify the existing pieces, and resume the download exactly where it left off.
* **Self-Healing**: If a torrent fails to connect, has metadata timeout (> 60 seconds), or download speed remains at `0` for over 60 seconds, the loop will automatically try the next candidate torrents, or skip to the next item in the queue.

---

## 🛠️ Technical Stack

| Dependency | Purpose | Details |
| :--- | :--- | :--- |
| **Python** | Language Core | Version 3.12+ |
| **libtorrent** | Torrent Engine | Python bindings for rasterbar libtorrent |
| **Requests / BeautifulSoup4** | Web Crawlers | Torrent indexing parsing |
| **TVmaze API** | TV Metadata | API client for metadata extraction |

---

## 📦 Packaging & Distribution

To re-compile the CLI script into a single-file executable and package it using Inno Setup:

```bash
# 1. Compile with PyInstaller
pyinstaller --noconfirm --onefile --console --name downloadcc downloadcc.py

# 2. Compile Inno Setup Script
& "C:\Users\omarb\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer.iss
```

---

## 📱 Transferring and Watching on iPad

1. **Transfer to iPad**:
   - **Wireless (VLC Command Line Upload)**: Open VLC on your iPad, enable **Sharing via WiFi**, and run `downloadcc vlc` (or `downloadcc vlc "Show Name"`) in your command prompt. It will upload files wirelessly with active progress bars.
   - **Cloud Storage**: Copy files to iCloud Drive / Google Drive on PC, then access them via the iPad's **Files** app.
   - **USB Transfer**: Connect iPad via USB and transfer files using the Apple Devices app or iTunes directly into the VLC documents folder.
2. **Watch**:
   - Open **VLC on iPad** (free on App Store). VLC natively supports all audio codecs (including AC3/DTS) and plays these files seamlessly!

---

## 📁 File Structure

```
movies-shows-downloader/
├── .gitignore                   - Git ignore patterns
├── README.md                    - Project documentation (this file)
├── MoviesAndShowsInstaller.exe  - Compiled standalone Windows installer
├── downloadcc.py                - Main interactive CLI program entry point
├── installer.iss                - Inno Setup compiler configuration
└── search_engine.py             - TVmaze and Pirate Bay crawling engine
```

---

## 📄 License
This repository is licensed under the [MIT License](LICENSE).
