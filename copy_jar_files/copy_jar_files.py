import os
import shutil

# Define the source and destination directories
source_dir = "checkout"
dest_dir = "jar_files"

# Create the destination directory if it doesn't exist
os.makedirs(dest_dir, exist_ok=True)

# Iterate through directories in the source directory
for item in os.listdir(source_dir):
    item_path = os.path.join(source_dir, item)
    if item.startswith("Chart_") and os.path.isdir(item_path):
        lib_path = os.path.join(item_path, "lib")
        if os.path.exists(lib_path) and os.path.isdir(lib_path):
            # Construct the destination path
            dest_path = os.path.join(dest_dir, item, "lib")
            os.makedirs(dest_path, exist_ok=True)

            # Copy the lib directory
            shutil.copytree(lib_path, dest_path, dirs_exist_ok=True)
            print(f"Copied {lib_path} to {dest_path}")
