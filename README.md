# 📺 downloadcc: Interactive Movies & TV Shows Downloader

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![BitTorrent-libtorrent](https://img.shields.io/badge/BitTorrent-libtorrent-brightgreen.svg?style=flat-square)](https://libtorrent.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-3.5-purple.svg?style=flat-square)](https://github.com/IamOumarIbrahim/movies-shows-downloader/releases)

A lightweight, fully interactive terminal-based media downloader. Search for movies and TV shows, select seasons/episodes interactively, download via the native `libtorrent` engine, then wirelessly push files to VLC on your **iPad or iPhone** — all from the command line.

---

## 📖 Table of Contents
- [Direct Download](#-direct-download)
- [Key Features](#-key-features)
- [How to Install](#-how-to-install)
- [How to Use](#-how-to-use)
- [VLC Wireless Upload](#-vlc-wireless-upload)
- [Resuming & Self-Healing](#-resuming--self-healing)
- [Technical Stack](#-technical-stack)
- [Packaging & Distribution](#-packaging--distribution)
- [Transferring and Watching on iPad/iPhone](#-transferring-and-watching-on-ipadiphone)
- [File Structure](#-file-structure)
- [License](#-license)

---

## 🚀 Direct Download

Download the compiled standalone Windows installer directly:
👉 **[Download MoviesAndShowsInstaller.exe](https://github.com/IamOumarIbrahim/movies-shows-downloader/raw/master/MoviesAndShowsInstaller.exe)**

*(The installer automatically adds `downloadcc` to your system PATH, making it executable from any shell immediately.)*

---

## ⭐ Key Features

- **💻 100% Terminal-Based CLI**: Highly responsive interactive numbered-selection menus.
- **📺 TV Show Metadata Integration**: Interfaces with the TVmaze API to search shows, seasons, and episodes dynamically.
- **🔍 Strict Title Matching**: Custom regex validation ensures results exactly match your target.
- **⚡ iPad/iPhone-Compatible Video Profiles (H.264/AAC)**: Results prioritize H.264/`.mp4` and deprioritize HEVC/x265, AV1, and 10-bit formats for guaranteed out-of-the-box playback.
- **🚀 High-Speed Peer Discovery**: DHT, LSD, UPnP, and NAT-PMP enabled for maximum connectivity.
- **📁 Automatic Post-Processing**: Organizes files into season subfolders and renames them to the clean `S_XX_E_YY.ext` convention.
- **📱 Multi-Device VLC Wireless Upload**: Push files wirelessly to VLC on your **iPad or iPhone** with real-time progress bars. Device IPs are saved locally and never appear in source code.
- **🔁 Smart Retry**: Failed uploads are automatically logged. Run `downloadcc vlc retry` to re-upload only the failed files without restarting the whole batch.
- **⚙️ Persistent Queue**: Background download queue with live progress, auto-resume, and self-healing.

---

## ⚙️ How to Install

### Method A: Setup Installer (Recommended)
1. Download and run **[MoviesAndShowsInstaller.exe](https://github.com/IamOumarIbrahim/movies-shows-downloader/raw/master/MoviesAndShowsInstaller.exe)**.
2. Complete the installer (installs into AppData and registers `downloadcc` globally in User PATH).
3. Open a **new** PowerShell or Command Prompt and run:
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
3. Run directly:
   ```bash
   python downloadcc.py
   ```

---

## 🏃 How to Use

### All Commands

```
downloadcc                     Search and download a movie or TV show interactively.
downloadcc "Query"             Search by name and select immediately.
downloadcc queue               View active download with live stats + queued items.
downloadcc add "Query"         Add a new item to the background queue.
downloadcc remove <number>     Remove a queued item by its index number.
downloadcc clear               Clear all pending items from the queue.
downloadcc vlc ["Target"]      Upload a folder/file wirelessly to VLC on iPad or iPhone.
downloadcc vlc retry           Re-upload files that failed in the last batch.
downloadcc help                Show this help menu.
```

### Searching & Downloading

```bash
downloadcc "Mr. Robot"
```
1. **Select a result**: Type the number `[1]`, `[2]`, etc. and press **Enter** (or `c` to cancel). Results are sorted by iPad/iPhone compatibility.
2. **Select season**: For TV shows, pick a specific season or **All Seasons (Complete Pack)**.
3. **Live progress**: Real-time percentage, speed (MB/s), peer count, and ETA.

---

## 📱 VLC Wireless Upload

Upload downloaded files directly to **VLC for iOS** on your iPad or iPhone over WiFi — no cables needed.

### First-Time Setup

1. Open **VLC** on your iPad or iPhone.
2. Tap the **Network** tab → enable **Sharing via WiFi**.
3. Note the IP address displayed (e.g. `192.168.1.100`).
4. Run `downloadcc vlc` — select your device, then enter its IP when prompted. It will be **saved automatically** for all future sessions.

### Uploading

```bash
downloadcc vlc                         # Pick device interactively, then pick folder
downloadcc vlc "Vampire Diaries"       # Upload a specific folder directly
```

The device picker looks like this:
```
--- VLC WiFi Sharing Uploader ---

Select Target Device (v3.5)
============================
  [1] iPad    [http://192.168.1.100]
  [2] iPhone  [not set]
  [3] Custom IP / hostname
  [c] Cancel / Go Back
```
- Selecting a device with a **saved IP** shows a confirmation prompt — just press **Enter** to confirm, or type a new IP/hostname to update it permanently.
- Selecting a device with **[not set]** prompts you to enter its IP and saves it.
- Selecting **Custom** lets you enter any one-time address without saving.

> **Privacy note:** Device IPs are stored in `~/.downloadcc/config.json` on your local machine only — they are never included in the source code or committed to version control.

### Retrying Failed Uploads

If VLC disconnects mid-batch (screen lock, app backgrounded, etc.), failed files are logged automatically. Simply re-enable VLC WiFi Sharing and run:

```bash
downloadcc vlc retry
```

This re-uploads **only** the failed files. If any still fail, the log is updated and you can run retry again.

### Tips for Large Batches
- Keep your device **screen on** and **VLC in the foreground** during uploads.
- Use your device's **hostname** (e.g. `ipad.local` or `iphone.local`) instead of an IP if the IP changes between sessions.
- Upload one device at a time for best reliability.

---

## ⚡ Resuming & Self-Healing

- **Auto-Resuming**: If a download is interrupted, running `downloadcc` checks your staging folder, verifies existing pieces, and resumes exactly where it left off.
- **Self-Healing**: If a torrent fails to connect, has metadata timeout (> 60 seconds), or download speed stays at `0` for over 60 seconds, it automatically tries the next candidate or moves to the next queue item.

---

## 🛠️ Technical Stack

| Dependency | Purpose | Details |
| :--- | :--- | :--- |
| **Python** | Language Core | Version 3.12+ |
| **libtorrent** | Torrent Engine | Python bindings for rasterbar libtorrent |
| **Requests / BeautifulSoup4** | Web Crawlers | Torrent indexing & parsing |
| **TVmaze API** | TV Metadata | Season/episode metadata extraction |

---

## 📦 Packaging & Distribution

To recompile the CLI into a standalone executable and build the installer:

```bash
# 1. Compile with PyInstaller
pyinstaller --noconfirm --onefile --console --name downloadcc downloadcc.py

# 2. Build Inno Setup installer
& "C:\Users\omarb\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer.iss
```

---

## 📱 Transferring and Watching on iPad/iPhone

1. **Wireless** *(Recommended)*: Use `downloadcc vlc` as described above.
2. **Cloud Storage**: Copy files to iCloud Drive / Google Drive on PC, then open them via the iOS **Files** app or VLC's **Network** tab.
3. **USB**: Connect device via USB and transfer through the Apple Devices app (Windows) or Finder (Mac) into VLC's documents folder.
4. **Watch**: Open **VLC** (free on App Store). VLC natively supports all codecs (AC3, DTS, etc.) and plays everything seamlessly.

---

## 📁 File Structure

```
movies-shows-downloader/
├── .gitignore                   - Git ignore patterns
├── README.md                    - Project documentation (this file)
├── MoviesAndShowsInstaller.exe  - Compiled standalone Windows installer
├── downloadcc.py                - Main interactive CLI entry point
├── installer.iss                - Inno Setup compiler configuration
└── search_engine.py             - TVmaze and torrent indexer crawling engine
```

> **Note:** `~/.downloadcc/` (queue state, saved device IPs, failed upload logs) lives outside the repository and is never committed.

---

## 📄 License
This repository is licensed under the [MIT License](LICENSE).
