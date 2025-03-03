# Google Takeout Image Metadata Updater

This script updates the metadata (EXIF data) of images exported from Google Takeout by using the corresponding JSON metadata files. It modifies the image description and photo taken time based on the provided JSON data.

## Features
- Extracts metadata from Google Takeout JSON files.
- Updates image descriptions and timestamps in the EXIF metadata.
- Supports multiple image formats (JPG, PNG, GIF, BMP, TIFF).
- Moves images without matching JSON files to an error folder.
- Allows users to specify the source folder at runtime.

## Prerequisites
- Python 3.x
- Required Python libraries:
  ```bash
  pip install pillow piexif
  ```

## How It Works
1. The script prompts the user to enter the `source_folder` containing images and JSON files.
2. It attempts to find a matching JSON file for each image.
3. If a match is found, it extracts metadata and updates the image.
4. If no match is found, the image is moved to an `error` folder.

## Folder Structure
```
source_folder/
|-- image1.jpg
|-- image1.json
|-- image2.jpg
|-- image3.png
|-- updated/    (Processed images with updated metadata)
|-- error/      (Images without matching JSON files)
```

## Usage
1. Run the script:
   ```bash
   python script.py
   ```
2. Enter the path to the folder containing the images and JSON files when prompted.
3. Updated images will be saved in the `updated` folder.
4. Unmatched images will be moved to the `error` folder.

## Notes
- The script translates Dutch month names to English for proper date formatting.
- Handles variations in filenames (e.g., `_`, `(1)`, `.o.`) when searching for JSON files.
- Any errors during processing are logged in the console output.

## License
This project is open-source and available under the MIT License.

