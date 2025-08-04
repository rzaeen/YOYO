#!/usr/bin/env python3
import os
import sys
import time
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# === الإعدادات العامة ===
DESKTOP = Path.home() / "Desktop"
if not DESKTOP.exists():
    DESKTOP = Path.home()  # fallback

BACKUP_DIR = DESKTOP / "YOYO_USB_Backups"
REPORT_DIR = DESKTOP / "YOYO_USB_Reports"

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# === وظيفة الطباعة الملونة ===
def print_color(text, color="white"):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(colors.get(color, "") + text + colors["reset"])

# === شاشة الترحيب ===
def show_banner():
    os.system('clear' if os.name != 'nt' else 'cls')
    banner = """
    ██████╗  █████╗ ████████╗███████╗██╗    ██╗
    ██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██║    ██║  Tool: YOYO v3.4
    ██████╔╝███████║   ██║   █████╗  ██║ █╗ ██║  Mode: Full USB Backup
    ██╔══██╗██╔══██║   ██║   ██╔══╝  ██║███╗██║  Status: Ready
    ██║  ██║██║  ██║   ██║   ███████╗╚███╔███╔╝
    ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚══╝╚══╝  Nothing left behind.
    """
    print_color(banner, "cyan")
    print_color("    [+] YOYO – Professional USB Forensics & Backup Tool", "green")
    print_color("    [+] Supports all file types, hidden files, and large files.\n", "yellow")

# === اكتشاف الأجهزة (يدعم لينكس بدون os.getlogin) ===
def scan_usb_now():
    print_color("\n🔍 Scanning for connected USB devices...", "yellow")
    drives = []

    if os.name == 'nt':  # ويندوز
        try:
            import string
            import win32file  # يتطلب: pip install pywin32
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    dtype = win32file.GetDriveType(drive)
                    if dtype == 2:  # قرص قابل للإزالة
                        drives.append(drive)
        except ImportError:
            print_color("  ❌ Install 'pywin32': pip install pywin32", "red")
        except Exception as e:
            print_color(f"  ❌ Error: {e}", "red")
    else:  # لينكس
        possible_paths = []
        # جمع كل المجلدات في /media/*
        try:
            media = Path("/media")
            if media.exists() and media.is_dir():
                for user_dir in media.iterdir():
                    if user_dir.is_dir():
                        for item in user_dir.iterdir():
                            if item.is_dir() and item.name != "lost+found":
                                possible_paths.append(item)
        except Exception as e:
            print_color(f"  ⚠️  Cannot read /media: {e}", "yellow")

        # أضف /mnt أيضًا
        try:
            mnt = Path("/mnt")
            if mnt.exists() and mnt.is_dir():
                for item in mnt.iterdir():
                    if item.is_dir():
                        possible_paths.append(item)
        except:
            pass

        # تحقق من الصلاحيات ونوع الجهاز
        for path in possible_paths:
            p = str(path)
            if os.path.ismount(p) or os.access(p, os.R_OK):
                try:
                    # تجربة قراءة أول ملف للتأكد
                    next(os.walk(p))
                    drives.append(p)
                except:
                    continue

    # إزالة التكرار
    drives = list(dict.fromkeys(drives))

    if not drives:
        print_color("  ❌ No USB devices found. Check connection and mounting.", "red")
        return None

    print_color("  ✅ Devices detected:", "green")
    for i, d in enumerate(drives, 1):
        try:
            total, used, free = shutil.disk_usage(d)
            size_gb = total // (1024**3)
            print(f"  [{i}] {d} ({size_gb} GB)")
        except:
            print(f"  [{i}] {d} (size unknown)")

    while True:
        try:
            choice = input(f"\n  Choose device [1-{len(drives)}] or 0 to cancel: ").strip()
            if choice == '0':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(drives):
                return drives[idx]
            else:
                print_color("  ❌ Invalid number. Try again.", "red")
        except ValueError:
            print_color("  ❌ Please enter a number.", "red")

# === نسخ الملفات بالقطع (يدعم ملفات >4GB) ===
def copy_file_chunked(src, dst, chunk_size=65536):
    try:
        with open(src, 'rb') as fsrc:
            with open(dst, 'wb') as fdst:
                while True:
                    chunk = fsrc.read(chunk_size)
                    if not chunk:
                        break
                    fdst.write(chunk)
        return True
    except Exception as e:
        print_color(f"  ❌ Failed to copy '{os.path.basename(src)}': {e}", "red")
        return False

# === جمع معلومات الجهاز ===
def get_usb_info(mount_point):
    info = {
        "name": os.path.basename(mount_point.rstrip('/\\')) or "Unknown_Device",
        "mount": mount_point,
        "total_gb": 0,
        "used_gb": 0,
        "free_gb": 0,
        "file_count": 0,
        "folder_count": 0,
        "hidden_files": 0,
        "large_files": [],  # >1GB
        "sensitive_files": [],
        "errors": []
    }

    try:
        total, used, free = shutil.disk_usage(mount_point)
        info["total_gb"] = round(total / (1024**3), 2)
        info["used_gb"] = round(used / (1024**3), 2)
        info["free_gb"] = round(free / (1024**3), 2)
    except Exception as e:
        info["errors"].append(f"Usage info failed: {e}")

    patterns = [b"password=", b"secret=", b"key=", b"token="]

    for root, dirs, files in os.walk(mount_point, followlinks=False):
        try:
            info["folder_count"] += len(dirs)
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, mount_point)

                info["file_count"] += 1

                # ملفات مخفية
                if file.startswith('.'):
                    info["hidden_files"] += 1

                # ملفات كبيرة
                try:
                    size = os.path.getsize(file_path)
                    if size > 1 * 1024**3:
                        info["large_files"].append(f"{rel_path} ({size//(1024**3)} GB)")
                except:
                    pass

                # تحليل محتوى
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read(2048)
                        for pattern in patterns:
                            if pattern.lower() in content.lower():
                                info["sensitive_files"].append(rel_path)
                                break
                except:
                    pass

        except PermissionError:
            info["errors"].append(f"Access denied: {root}")
        except Exception as e:
            info["errors"].append(f"Error reading {root}: {e}")

    return info

# === نسخ كامل لكل الملفات ===
def backup_usb(mount_point, info):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"Backup_{info['name']}_{timestamp}"
    backup_path = BACKUP_DIR / folder_name
    os.makedirs(backup_path, exist_ok=True)

    print_color(f"  📥 Starting full backup to: {backup_path}", "yellow")
    copied = 0
    skipped = 0

    for root, dirs, files in os.walk(mount_point):
        try:
            rel_root = os.path.relpath(root, mount_point)
            dst_root = backup_path / rel_root
            os.makedirs(dst_root, exist_ok=True)

            for file in files:
                src_file = os.path.join(root, file)
                dst_file = dst_root / file

                if os.path.exists(src_file) and os.access(src_file, os.R_OK):
                    if copy_file_chunked(src_file, dst_file):
                        copied += 1
                    else:
                        skipped += 1
                else:
                    skipped += 1
        except Exception as e:
            print_color(f"  ⚠️  Error in {root}: {e}", "yellow")
            skipped += 1

    print_color(f"  ✅ Backup completed: {copied} files copied.", "green")
    if skipped:
        print_color(f"    ⚠️  {skipped} files skipped.", "yellow")
    return backup_path

# === إنشاء تقرير على سطح المكتب ===
def generate_report(info, backup_path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_name = f"YOYO_USB_Report_{info['name']}_{int(time.time())}.txt"
    report_file = REPORT_DIR / report_name

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("=== YOYO FULL USB FORENSIC REPORT ===\n\n")
        f.write(f"Device Name: {info['name']}\n")
        f.write(f"Mount Point: {info['mount']}\n")
        f.write(f"Total Size: {info['total_gb']} GB\n")
        f.write(f"Used Space: {info['used_gb']} GB\n")
        f.write(f"Free Space: {info['free_gb']} GB\n")
        f.write(f"Files Copied: {info['file_count']}\n")
        f.write(f"Folders: {info['folder_count']}\n")
        f.write(f"Hidden Files: {info['hidden_files']}\n")
        f.write(f"Backup Location: {backup_path}\n")
        f.write(f"Scan Time: {timestamp}\n\n")

        if info['large_files']:
            f.write("Large Files (>1GB):\n")
            for lf in info['large_files']:
                f.write(f"  • {lf}\n")
            f.write("\n")

        f.write("Sensitive Keywords Found:\n")
        if info['sensitive_files']:
            for sf in info['sensitive_files']:
                f.write(f"  🔍 {sf}\n")
        else:
            f.write("  None\n")
        f.write("\n")

        if info['errors']:
            f.write("Errors Encountered:\n")
            for err in info['errors']:
                f.write(f"  ⚠️  {err}\n")
        f.write("\n")
        f.write("YOYO v3.4 — Full USB Backup & Forensics Tool\n")
        f.write("All files backed up. Silent mode active.\n")

    print_color(f"  📄 Report saved: {report_file}", "green")

# === القائمة الرئيسية ===
def main():
    while True:
        show_banner()
        print("    [1] 🔍 Scan & Backup USB Now")
        print("    [2] 🚪 Exit")
        print()
        choice = input("    Choose [1-2] > ").strip()

        if choice == "1":
            mount_point = scan_usb_now()
            if mount_point:
                info = get_usb_info(mount_point)
                backup_path = backup_usb(mount_point, info)
                generate_report(info, backup_path)
                print_color(f"\n  ✅ FULL BACKUP COMPLETED for '{info['name']}'", "cyan")
            input("\n    Press Enter to continue...")
        elif choice == "2":
            print_color("\n  🔐 YOYO closed. Stay secure.", "green")
            break
        else:
            print_color("  ❌ Invalid choice. Try again.", "red")
            time.sleep(1)

# === نقطة البدء ===
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_color("\n\n  ⚠️  YOYO stopped by user.", "yellow")
    except Exception as e:
        print_color(f"\n  ❌ Critical error: {e}", "red")
        input("Press Enter to exit...")