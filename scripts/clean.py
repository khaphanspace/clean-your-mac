#!/usr/bin/env python3
import os, sys, subprocess, time, shutil
from concurrent.futures import ThreadPoolExecutor

# Config
FILE_EXPIRY_DAYS = {
    "dmg": 1,
    "media": 1,
    "images": 3,
    "documents": 5,
    "archives": 7,
    "other": 30,
}
LARGE_FILE_EXPIRY_DAYS, LARGE_FILE_MIN_SIZE_MB = 7, 500
STATS = {
    "packages": 0,
    "empty_folders": 0,
    "large_files": 0,
    "bytes_saved": 0,
    "caches": 0,
    "trash": 0,
    "files_removed": 0,
}
TRASH_PATHS, CACHE_PATHS = ["/.Trash/*"], [
    "~/Library/Caches/*",
    "~/.cache/*",
    "/Library/Caches/*",
]
PACKAGE_MANAGERS = {
    "brew": "brew cleanup --prune=all",
    "pip3": "pip3 cache purge",
    "npm": "npm cache clean --force",
    "docker": "docker system prune -af --volumes",
}
FILE_EXTENSIONS = {
    "dmg": (".dmg",),
    "media": (".mov", ".mp4", ".m4a", ".wav", ".mp3", ".aac"),
    "images": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"),
    "documents": (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"),
    "archives": (".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"),
    "other": (),
}
SYSTEM_PATHS_TO_SKIP = [".app/", ".framework/", ".dylib", ".kext", "/System/"]
DIRS_TO_SKIP = ["node_modules", "vendor", "build", ".git", ".Trash"]


# Utils
def run_cmd(cmd, silent=False):
    try:
        r = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if r.stderr and not silent:
            print(f"  → Warning: {r.stderr.strip()}")
        return r.stdout.strip()
    except:
        return ""


def get_disk_space():
    df = run_cmd("df -h /").split("\n")
    return (
        {"total": df[1].split()[1], "free": df[1].split()[3]}
        if len(df) > 1
        else {"total": "?", "free": "?"}
    )


def fmt_size(b):
    if b <= 0:
        return "0 B"
    u, i, s = ["B", "Ki", "Mi", "Gi", "Ti"], 0, float(b)
    while s >= 1024 and i < 4:
        s, i = s / 1024, i + 1
    return f"{s:.2f}{u[i]}"


def parse_size(s):
    try:
        n, u = (
            "".join(c for c in s if c.isdigit() or c == "."),
            "".join(c for c in s if c.isalpha()).upper(),
        )
        return (
            int(
                float(n)
                * {
                    "TI": 1024**4,
                    "GI": 1024**3,
                    "MI": 1024**2,
                    "KI": 1024,
                    "": 1,
                }.get(u, 1)
            )
            if n
            else None
        )
    except:
        return None


# Cleanup
def clean_trash():
    print("\n🗑️ Emptying trash...")
    p = (
        TRASH_PATHS
        + [
            f"/Users/{u}/.Trash/*"
            for u in os.listdir("/Users")
            if os.path.exists(f"/Users/{u}/.Trash")
        ]
        if os.path.exists("/Users")
        else TRASH_PATHS
    )
    for x in p:
        s = parse_size(run_cmd(f"du -sh {x} 2>/dev/null | cut -f1") or "0") or 0
        if s:
            run_cmd(f"rm -rf {x}", silent=True)
            STATS["trash"] += 1
            STATS["bytes_saved"] += s
    run_cmd("osascript -e 'tell app \"Finder\" to empty trash'", silent=True)


def clean_caches():
    print("🗑️ Cleaning caches...")
    for p in CACHE_PATHS:
        s = (
            parse_size(
                run_cmd(
                    f"du -sh {p} 2>/dev/null | awk '{{print $1}}' | sort -hr | head -n1"
                )
                or "0"
            )
            or 0
        )
        if s:
            run_cmd(f"rm -rf {p}", silent=True)
            STATS["caches"] += 1
            STATS["bytes_saved"] += s


def clean_packages():
    print("🧹 Cleaning package managers...")
    for c, k in PACKAGE_MANAGERS.items():
        if run_cmd(f"which {c}"):
            run_cmd(k, silent=True)
            STATS["packages"] += 1


def process_user_directory(d):
    t, lt, ls = (
        time.time(),
        time.time() - LARGE_FILE_EXPIRY_DAYS * 86400,
        LARGE_FILE_MIN_SIZE_MB * 1024 * 1024,
    )
    ct = {g: t - x * 86400 for g, x in FILE_EXPIRY_DAYS.items()}
    fr, fb, lr, lb, ef = 0, 0, 0, 0, 0
    for r, dirs, f in os.walk(d, topdown=True):
        dirs[:] = [x for x in dirs if x not in DIRS_TO_SKIP]
        for fn in f:
            fp = os.path.join(r, fn)
            try:
                print(f"\r→ Scanning: {fp}", end="", flush=True)
                fs = os.stat(fp)
                s, at = fs.st_size, fs.st_atime
                ft = next(
                    (g for g, e in FILE_EXTENSIONS.items() if fp.lower().endswith(e)),
                    "other",
                )
                if t - at > ct[ft]:
                    os.remove(fp)
                    fr += 1
                    fb += s
                elif (
                    s > ls
                    and t - at > lt
                    and not any(p in fp for p in SYSTEM_PATHS_TO_SKIP)
                ):
                    os.remove(fp)
                    lr += 1
                    lb += s
            except:
                pass
        if r != d and not os.path.basename(r).startswith(".") and "/Library/" not in r:
            try:
                print(f"\r→ Scanning: {r}", end="", flush=True)
                c = os.listdir(r)
                if not c or (len(c) == 1 and c[0] == ".DS_Store"):
                    shutil.rmtree(r, ignore_errors=True)
                    ef += 1
            except:
                pass
    return fr, fb, lr, lb, ef


def process_user_directories():
    print("🔍 Scanning user directories...")
    if not os.path.exists("/Users"):
        return
    ud = [
        os.path.join("/Users", d)
        for d in os.listdir("/Users")
        if os.path.isdir(os.path.join("/Users", d)) and not d.startswith(".")
    ]
    ts = [0, 0, 0, 0, 0]
    with ThreadPoolExecutor(max_workers=min(4, len(ud))) as ex:
        for fr, fb, lr, lb, ef in ex.map(process_user_directory, ud):
            ts[0] += fr
            ts[1] += fb
            ts[2] += lr
            ts[3] += lb
            ts[4] += ef
    print("\r" + " " * 80 + "\r", end="", flush=True)
    STATS["files_removed"], STATS["large_files"], STATS["empty_folders"] = (
        ts[0],
        ts[2],
        ts[4],
    )
    STATS["bytes_saved"] += ts[1] + ts[3]
    if ts[0]:
        print(f"→ Removed {ts[0]} files ({fmt_size(ts[1])})")
    if ts[2]:
        print(f"→ Removed {ts[2]} large files ({fmt_size(ts[3])})")
    if ts[4]:
        print(f"→ Removed {ts[4]} empty folders")


# Main
def main():
    if os.geteuid() != 0:
        print("Needs root. Run with: sudo python3 cleanup.py")
        sys.exit(1)
    print(
        f"----\n🚀 MacOS Cleanup Script\n→ Total: {get_disk_space()['total']}\n→ Free: {get_disk_space()['free']}"
    )
    clean_trash()
    clean_caches()
    clean_packages()
    process_user_directories()
    print("\n============\n📊 SUMMARY\n============")
    for k, l in [
        ("trash", "Trash"),
        ("caches", "Caches"),
        ("packages", "Packages"),
        ("files_removed", "Files"),
        ("large_files", "Large Files"),
        ("empty_folders", "Folders"),
    ]:
        if STATS[k]:
            print(f"✓ {l}: {STATS[k]}")
    print(
        f"---------------\nSPACE SAVED: {fmt_size(STATS['bytes_saved'])}\n============\n✅ Done\n----"
    )


if __name__ == "__main__":
    main()
