import os
import json
import shutil
import piexif
from PIL import Image
from datetime import datetime

# Define source and destination folders
source_folder = "" # Folder containing images and JSON files
updated_folder = os.path.join(source_folder, "updated") # Folder for updated images
error_folder = os.path.join(source_folder, "error")  # Folder for unmatched images

# Dictionary for Dutch-to-English month translation
MONTHS_DUTCH_TO_EN = {
    "jan": "Jan", "feb": "Feb", "mrt": "Mar", "apr": "Apr", "mei": "May", "jun": "Jun",
    "jul": "Jul", "aug": "Aug", "sep": "Sep", "okt": "Oct", "nov": "Nov", "dec": "Dec"
}

# ask for the source folder
source_folder = input("Enter the source folder path: ")

# Ensure the folders exist
os.makedirs(updated_folder, exist_ok=True)
os.makedirs(error_folder, exist_ok=True)

# Function to find matching JSON file
def find_json_for_image(image_name, json_files):
    for json_file in json_files:
        if json_file.startswith(image_name) and json_file.endswith(".json"):
            return json_file
        # if image_name ends with underscore, try without it
        elif image_name.endswith("_"):
            image_name = image_name[:-1]
            if json_file.startswith(image_name) and json_file.endswith(".json"):
                return json_file
        #if image ends with (1) add it before the extension add "(1).json"
        elif image_name.endswith("(1)"):
            image_name = image_name[:-3]
            if json_file.startswith(image_name) and json_file.endswith("(1).json"):
                return json_file
        elif image_name.endswith(".o."):
            image_name = image_name[:-3]
            if json_file.startswith(image_name) and json_file.endswith(".json"):
                return json_file
    return None

# Function to format EXIF date
def format_exif_date(date_str):
    """Convert localized date format ('22 mei 2023, 13:41:27 UTC') to 'YYYY:MM:DD HH:MM:SS'"""
    try:
        # Replace Dutch month names with English
        for dutch, eng in MONTHS_DUTCH_TO_EN.items():
            if dutch in date_str.lower():
                date_str = date_str.lower().replace(dutch, eng)
                break  # Replace only once

        # Convert to EXIF format
        dt = datetime.strptime(date_str, "%d %b %Y, %H:%M:%S UTC")
        return dt.strftime("%Y:%m:%d %H:%M:%S")

    except ValueError:
        print(f"Error parsing date: {date_str}")
        return None

# Function to update image metadata
def update_metadata(image_path, json_data):
    try:
        image = Image.open(image_path)

        # Load or initialize EXIF data
        exif_dict = piexif.load(image.info.get("exif", b"")) if "exif" in image.info else {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}

        # Ensure fields exist
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
        
        print(f"Updated metadata for: {image_path}")

    except Exception as e:
        print(f"Failed to update {image_path}: {e}")

# Get all image files and JSON files in the folder
image_extensions = ("jpg", "jpeg", "png", "gif", "bmp", "tiff")
image_files = [f for f in os.listdir(source_folder) if f.lower().endswith(image_extensions)]
json_files = [f for f in os.listdir(source_folder) if f.lower().endswith(".json")]

# Process each image
for image_file in image_files:
    image_name = os.path.splitext(image_file)[0]  # Get base name without extension
    json_file = find_json_for_image(image_name, json_files)

    image_path = os.path.join(source_folder, image_file)

    if json_file:
        json_path = os.path.join(source_folder, json_file)
        
        # Load JSON metadata
        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Update metadata and move image
        update_metadata(image_path, json_data)
    else:
        # Move images without a matching JSON file to the error folder
        error_path = os.path.join(error_folder, image_file)
        shutil.move(image_path, error_path)
        print(f"Moved {image_file} to error folder (No matching JSON found)")

print("Processing complete.")
