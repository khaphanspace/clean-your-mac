# clean-your-mac

A high-performance macOS cleanup utility that frees disk space by removing unused files and caches.

## Why You Need It
- **Lightning Fast:** Concurrent processing with ThreadPoolExecutor for parallel scanning
- **Resource Efficient:** Native OS commands via subprocess with minimal memory footprint
- **Zero Bloat:** Pure Python implementation with no external dependencies
- **Smart & Safe:** Intelligent filtering to avoid critical system paths
- **Highly Configurable:** Easy-to-adjust expiry thresholds and file categories
- **Smart Cleaning:** Removes trash, caches, package manager debris, and unused files based on configurable age thresholds
- **Type-Based Expiry:** Different retention periods for DMG installers (1d), media (1d), images (3d), documents (5d), archives (7d), and other files (30d)

## ⚠️ Warning
This script permanently deletes files. Always backup important data before running. Use at your own risk.

## Usage

#### Run directly from URL
```bash
curl -s https://gist.githubusercontent.com/nhatkha1407/5079867caede3c39c39d8c67a5ed9cb0/raw/clean-your-mac.py | sudo python3
```
#### Or clone and run
```bash
git clone https://github.com/nhatkha1407/clean-your-mac.git
cd clean-your-mac

sudo ./scripts/clean.py
```

## Requirements
- Python 3.x
- macOS
- Root privileges

## How It Works

### Cleanup Areas
- **System:** Trash bins, application caches, package manager caches
- **User Files:** Files based on last access time and type (per table below)
- **Empty Directories:** Empty folders across user directories
- **Package Managers:** Homebrew, pip3, npm, and Docker caches

### File Removal Conditions

| File Type | Extensions | Not Accessed In | Notes |
|-----------|------------|-----------------|-------|
| DMG | .dmg | 1 day | macOS disk image installers |
| Media | .mov, .mp4, .m4a, .wav, .mp3, .aac | 1 day | Audio and video files |
| Images | .jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp | 3 days | Image files |
| Documents | .pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx, .txt | 5 days | Document files |
| Archives | .zip, .rar, .7z, .tar, .gz, .bz2 | 7 days | Compressed files |
| Large Files | Any | 7 days | Files larger than 500MB |
| Other | All other extensions | 30 days | Files not in other categories |

## Output Example
```
🚀 MacOS Cleanup Script
→ Total: 460Gi
→ Free: 243Gi

🗑️ Emptying trash...
🗑️ Cleaning caches...
🧹 Cleaning package managers...
🔍 Scanning user directories...
→ Removed 5 files (1.20Gi)
→ Removed 2 large files (2.00Gi)
→ Removed 3 empty folders

============
📊 SUMMARY
============
✓ Trash: 2
✓ Caches: 3
✓ Packages: 4
✓ Files: 5
✓ Large Files: 2
✓ Folders: 3
---------------
SPACE SAVED: 3.20Gi
============
✅ Done
```

## License
WTFPL - Do What The Fuck You Want To Public License. See [LICENSE](LICENSE).
