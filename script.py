import os
import json
import shutil
import piexif
import subprocess
from PIL import Image
from datetime import datetime

# Ask for processing mode
print("Select processing mode:")
print("1 - Process only images")
print("2 - Process only videos")
print("3 - Process both images and videos")

while True:
    choice = input("Enter your choice (1/2/3): ").strip()
    if choice in ("1", "2", "3"):
        break
    print("Invalid choice. Please enter 1, 2, or 3.")

# Ask for the source folder
source_folder = input("Enter the source folder path: ").strip()
updated_folder = os.path.join(source_folder, "updated")  # Folder for updated images/videos
error_folder = os.path.join(source_folder, "error")  # Folder for unmatched images/videos

# Ensure the folders exist
os.makedirs(updated_folder, exist_ok=True)
os.makedirs(error_folder, exist_ok=True)

# Dictionary for Dutch-to-English month translation
MONTHS_DUTCH_TO_EN = {
    "jan": "Jan", "feb": "Feb", "mrt": "Mar", "apr": "Apr", "mei": "May", "jun": "Jun",
    "jul": "Jul", "aug": "Aug", "sep": "Sep", "okt": "Oct", "nov": "Nov", "dec": "Dec"
}

# Function to find matching JSON file
def find_json_for_file(file_name, json_files):
    """Find the corresponding JSON file for an image or video."""
    for json_file in json_files:
        if json_file.startswith(file_name) and json_file.endswith(".json"):
            return json_file
    return None

# Function to format EXIF date
def format_exif_date(date_str):
    """Convert '22 mei 2023, 13:41:27 UTC' to 'YYYY:MM:DD HH:MM:SS'"""
    try:
        for dutch, eng in MONTHS_DUTCH_TO_EN.items():
            if dutch in date_str.lower():
                date_str = date_str.lower().replace(dutch, eng)
                break
        dt = datetime.strptime(date_str, "%d %b %Y, %H:%M:%S UTC")
        return dt.strftime("%Y:%m:%d %H:%M:%S")
    except ValueError:
        print(f"Error parsing date: {date_str}")
        return None

# Function to update image metadata
def update_image_metadata(image_path, json_data):
    try:
        image = Image.open(image_path)
        exif_dict = piexif.load(image.info.get("exif", b"")) if "exif" in image.info else {"0th": {}, "Exif": {}}
        exif_dict.setdefault("0th", {})
        exif_dict.setdefault("Exif", {})

        # Update ImageDescription
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = json_data.get("description", "").encode()

        # Convert and set DateTimeOriginal
        if "photoTakenTime" in json_data and "formatted" in json_data["photoTakenTime"]:
            formatted_date = format_exif_date(json_data["photoTakenTime"]["formatted"])
            if formatted_date:
                exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = formatted_date.encode()

        # Save updated image
        exif_bytes = piexif.dump(exif_dict)
        updated_image_path = os.path.join(updated_folder, os.path.basename(image_path))
        image.save(updated_image_path, exif=exif_bytes)

        print(f"Updated metadata for image: {image_path}")

    except Exception as e:
        print(f"Failed to update image {image_path}: {e}")

# Function to update video metadata
def update_video_metadata(video_path, json_data):
    """Update video metadata using ExifTool."""
    try:
        if "photoTakenTime" in json_data and "formatted" in json_data["photoTakenTime"]:
            formatted_date = format_exif_date(json_data["photoTakenTime"]["formatted"])

            if formatted_date:
                updated_video_path = os.path.join(updated_folder, os.path.basename(video_path))

                # Run ExifTool command to set "Media Created"
                subprocess.run([
                    "ExifTool",
                    "-overwrite_original",
                    f"-MediaCreateDate={formatted_date}",
                    video_path
                ], check=True)

                # Move updated file to the updated folder
                shutil.move(video_path, updated_video_path)

                print(f"Updated 'Media Created' metadata for video: {video_path}")

    except Exception as e:
        print(f"Failed to update video {video_path}: {e}")

# Get all image and video files based on user's choice
image_extensions = ("jpg", "jpeg", "png", "gif", "bmp", "tiff")
video_extensions = ("mp4", "mov", "avi", "mkv")

if choice == "1":
    valid_extensions = image_extensions  # Process only images
elif choice == "2":
    valid_extensions = video_extensions  # Process only videos
else:
    valid_extensions = image_extensions + video_extensions  # Process both

all_files = [f for f in os.listdir(source_folder) if f.lower().endswith(valid_extensions)]
json_files = [f for f in os.listdir(source_folder) if f.lower().endswith(".json")]

# Process each file
for file in all_files:
    file_name = os.path.splitext(file)[0]
    json_file = find_json_for_file(file_name, json_files)

    file_path = os.path.join(source_folder, file)

    if json_file:
        json_path = os.path.join(source_folder, json_file)

        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        if file.lower().endswith(image_extensions):
            update_image_metadata(file_path, json_data)
        elif file.lower().endswith(video_extensions):
            update_video_metadata(file_path, json_data)
    else:
        # Move unmatched files to error folder
        error_path = os.path.join(error_folder, file)
        shutil.move(file_path, error_path)
        print(f"Moved {file} to error folder (No matching JSON found)")

print("Processing complete.")
