import gdown
import os

# Google Drive folder ID
folder_id = "1dYkP8aEHVf2o1M7vqjbI5GvCIRi_5oMR"

# Output folder
output_dir = "data"
os.makedirs(output_dir, exist_ok=True)

# Download entire folder
os.system(f"gdown --folder https://drive.google.com/drive/folders/{folder_id} -O {output_dir}")

print("✅ Download complete! Files saved in 'data/' folder.")
