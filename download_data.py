import gdown
import os

# Google Drive folder IDs
tif_folder_id = "1dYkP8aEHVf2o1M7vqjbI5GvCIRi_5oMR"  # Your TIF files folder
png_folder_id = "1MLQ_VhBdaAWu4_608ceUASRTMOkNnD95"  # Your preview PNGs folder

# Output directories
tif_output_dir = "data"
png_output_dir = os.path.join("static", "previews")

os.makedirs(tif_output_dir, exist_ok=True)
os.makedirs(png_output_dir, exist_ok=True)

print("Downloading TIF files...")
gdown.download_folder(f"https://drive.google.com/drive/folders/{tif_folder_id}", output=tif_output_dir, quiet=False, use_cookies=False)

print("Downloading PNG preview files...")
gdown.download_folder(f"https://drive.google.com/drive/folders/{png_folder_id}", output=png_output_dir, quiet=False, use_cookies=False)

print("✅ All files downloaded successfully!")
