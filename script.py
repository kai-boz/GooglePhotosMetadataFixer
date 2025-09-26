import os
import shutil
import re
import json
from datetime import datetime

# Supported media extensions
MEDIA_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.mp4', '.mov']

# Minimum length when truncating for messy filenames
MIN_TRUNCATE_LENGTH = 3

# Log file
LOG_FILENAME = "media_json_match_log.txt"

def clean_filename(name):
    """Remove trailing (1), (2), etc., before the extension"""
    return re.sub(r'\(\d+\)', '', name)

def base_without_trailing_dots(name):
    """Remove trailing dots before extension"""
    return re.sub(r'\.+$', '', name)

def scan_folder(folder):
    """Recursively scan folder and return all files"""
    files_list = []
    for root, _, files in os.walk(folder):
        for file in files:
            files_list.append(os.path.join(root, file))
    return files_list

def set_file_time(file_path, timestamp):
    """Set modified and access time (cross-platform)"""
    os.utime(file_path, (timestamp, timestamp))

def main():
    source_folder = input("Enter the full path of the source folder: ").strip()
    processed_folder = os.path.join(source_folder, "processed")
    error_folder = os.path.join(source_folder, "error_files")
    os.makedirs(processed_folder, exist_ok=True)
    os.makedirs(error_folder, exist_ok=True)

    # Clear previous log
    log_path = os.path.join(source_folder, LOG_FILENAME)
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write("Media-JSON Matching Log\n")
        log_file.write("="*50 + "\n")

    all_files = scan_folder(source_folder)

    # Separate media and JSON files
    media_files = [f for f in all_files if os.path.splitext(f)[1].lower() in MEDIA_EXTENSIONS]
    json_files = [f for f in all_files if f.lower().endswith('.json')]

    for media_path in media_files:
        media_name = os.path.basename(media_path)
        media_dir = os.path.dirname(media_path)
        media_clean = clean_filename(media_name)
        name_part, ext = os.path.splitext(media_clean)
        matched_json = None

        # Step 1: Exact JSON replacement (e.g., 077.json)
        simple_json_name = os.path.join(media_dir, name_part + '.json')
        if simple_json_name in json_files:
            matched_json = simple_json_name
        else:
            # Step 2: Standard Takeout JSON (media.jpg.suffix.json)
            for json_file in json_files:
                if os.path.basename(json_file).startswith(media_clean + "."):
                    matched_json = json_file
                    break

            # Step 3: Progressive truncation for messy filenames
            if not matched_json:
                truncated_name = name_part
                while len(truncated_name) > MIN_TRUNCATE_LENGTH:
                    for json_file in json_files:
                        json_base = os.path.splitext(os.path.basename(json_file))[0]
                        json_base = base_without_trailing_dots(json_base)
                        if json_base.startswith(truncated_name):
                            matched_json = json_file
                            break
                    if matched_json:
                        break
                    truncated_name = truncated_name[:-1]

        # Determine processed file path
        rel_path = os.path.relpath(media_dir, source_folder)
        target_dir = os.path.join(processed_folder, rel_path)
        os.makedirs(target_dir, exist_ok=True)
        processed_media_path = os.path.join(target_dir, media_name)

        # Copy file first
        shutil.copy2(media_path, processed_media_path)

        # Logging and timestamp update
        with open(log_path, 'a', encoding='utf-8') as log_file:
            if matched_json:
                log_file.write(f"Found: {media_path}\n")
                log_file.write(f"Found corresponding JSON file: {matched_json}\n")

                # Update timestamp from JSON if possible
                try:
                    with open(matched_json, 'r', encoding='utf-8') as jf:
                        data = json.load(jf)
                    if 'photoTakenTime' in data and 'timestamp' in data['photoTakenTime']:
                        ts = int(data['photoTakenTime']['timestamp'])
                        set_file_time(processed_media_path, ts)
                        dt_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                        log_file.write(f"Updated timestamp to: {dt_str}\n")
                        print(f"Updated {media_name} timestamp to {dt_str}")
                    else:
                        log_file.write("No photoTakenTime found in JSON.\n")
                        print(f"No photoTakenTime in JSON for {media_name}")
                except Exception as e:
                    log_file.write(f"Error reading JSON for timestamp: {e}\n")
                    print(f"Error processing JSON for {media_name}: {e}")

                log_file.write("\n")
                print(f"Found: {media_name}")
                print(f"Found corresponding JSON file: {os.path.basename(matched_json)}\n")
            else:
                log_file.write(f"Exception: no valid JSON file found for {media_path}\n\n")
                print(f"Found: {media_name}")
                print(f"Exception: no valid JSON file found for {media_name}")
                # Move unmatched media to error folder (original files)
                error_target_dir = os.path.join(error_folder, rel_path)
                os.makedirs(error_target_dir, exist_ok=True)
                shutil.move(media_path, os.path.join(error_target_dir, media_name))

if __name__ == "__main__":
    main()

import os
import shutil
import re
import json
from datetime import datetime
import sys

# Supported media extensions
MEDIA_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.mp4', '.mov']

# Minimum length when truncating for messy filenames
MIN_TRUNCATE_LENGTH = 3

# Log file
LOG_FILENAME = "media_json_match_log.txt"

def clean_filename(name):
    """Remove trailing (1), (2), etc., before the extension"""
    return re.sub(r'\(\d+\)', '', name)

def base_without_trailing_dots(name):
    """Remove trailing dots before extension"""
    return re.sub(r'\.+$', '', name)

def scan_folder(folder):
    """Recursively scan folder and return all files"""
    files_list = []
    for root, _, files in os.walk(folder):
        for file in files:
            files_list.append(os.path.join(root, file))
    return files_list

def set_file_time(file_path, timestamp):
    """
    Set modified, access, and creation time.
    On Windows, creation time is updated using pywin32.
    """
    # Set access & modified time
    os.utime(file_path, (timestamp, timestamp))

    # Set creation time on Windows
    if sys.platform == 'win32':
        try:
            import pywintypes
            import win32file
            import win32con

            file_handle = win32file.CreateFile(
                file_path, win32con.GENERIC_WRITE,
                0, None, win32con.OPEN_EXISTING,
                win32con.FILE_ATTRIBUTE_NORMAL, None
            )
            pytime = pywintypes.Time(timestamp)
            win32file.SetFileTime(file_handle, pytime, pytime, pytime)
            file_handle.close()
        except ImportError:
            print("pywin32 not installed, creation time not updated on Windows.")
        except Exception as e:
            print(f"Failed to update creation time for {file_path}: {e}")

def main():
    source_folder = input("Enter the full path of the source folder: ").strip()
    processed_folder = os.path.join(source_folder, "processed")
    error_folder = os.path.join(source_folder, "error_files")
    os.makedirs(processed_folder, exist_ok=True)
    os.makedirs(error_folder, exist_ok=True)

    # Clear previous log
    log_path = os.path.join(source_folder, LOG_FILENAME)
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write("Media-JSON Matching Log\n")
        log_file.write("="*50 + "\n")

    all_files = scan_folder(source_folder)

    # Separate media and JSON files
    media_files = [f for f in all_files if os.path.splitext(f)[1].lower() in MEDIA_EXTENSIONS]
    json_files = [f for f in all_files if f.lower().endswith('.json')]

    for media_path in media_files:
        media_name = os.path.basename(media_path)
        media_dir = os.path.dirname(media_path)
        media_clean = clean_filename(media_name)
        name_part, ext = os.path.splitext(media_clean)
        matched_json = None

        # Step 1: Exact JSON replacement (e.g., 077.json)
        simple_json_name = os.path.join(media_dir, name_part + '.json')
        if simple_json_name in json_files:
            matched_json = simple_json_name
        else:
            # Step 2: Standard Takeout JSON (media.jpg.suffix.json)
            for json_file in json_files:
                if os.path.basename(json_file).startswith(media_clean + "."):
                    matched_json = json_file
                    break

            # Step 3: Progressive truncation for messy filenames
            if not matched_json:
                truncated_name = name_part
                while len(truncated_name) > MIN_TRUNCATE_LENGTH:
                    for json_file in json_files:
                        json_base = os.path.splitext(os.path.basename(json_file))[0]
                        json_base = base_without_trailing_dots(json_base)
                        if json_base.startswith(truncated_name):
                            matched_json = json_file
                            break
                    if matched_json:
                        break
                    truncated_name = truncated_name[:-1]

        # Determine processed file path
        rel_path = os.path.relpath(media_dir, source_folder)
        target_dir = os.path.join(processed_folder, rel_path)
        os.makedirs(target_dir, exist_ok=True)
        processed_media_path = os.path.join(target_dir, media_name)

        # Copy file first
        shutil.copy2(media_path, processed_media_path)

        # Logging and timestamp update
        with open(log_path, 'a', encoding='utf-8') as log_file:
            if matched_json:
                log_file.write(f"Found: {media_path}\n")
                log_file.write(f"Found corresponding JSON file: {matched_json}\n")

                # Update timestamp from JSON if possible
                try:
                    with open(matched_json, 'r', encoding='utf-8') as jf:
                        data = json.load(jf)
                    if 'photoTakenTime' in data and 'timestamp' in data['photoTakenTime']:
                        ts = int(data['photoTakenTime']['timestamp'])
                        set_file_time(processed_media_path, ts)
                        dt_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                        log_file.write(f"Updated timestamp to: {dt_str}\n")
                        print(f"Updated {media_name} timestamps to {dt_str}")
                    else:
                        log_file.write("No photoTakenTime found in JSON.\n")
                        print(f"No photoTakenTime in JSON for {media_name}")
                except Exception as e:
                    log_file.write(f"Error reading JSON for timestamp: {e}\n")
                    print(f"Error processing JSON for {media_name}: {e}")

                log_file.write("\n")
            else:
                log_file.write(f"Exception: no valid JSON file found for {media_path}\n\n")
                print(f"Exception: no valid JSON file found for {media_name}")
                # Move unmatched media to error folder (original files)
                error_target_dir = os.path.join(error_folder, rel_path)
                os.makedirs(error_target_dir, exist_ok=True)
                shutil.move(media_path, os.path.join(error_target_dir, media_name))

if __name__ == "__main__":
    main()

