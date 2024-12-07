import os
import shutil

# Define the source and destination directories
source_dir = "checkout"
dest_dir = "jar_files"
not_built_path = "./ant_build/not_built.txt"
not_built = []
with open(not_built_path, 'r') as f:
    for bug in f:
        not_built.append(bug.strip())
print(not_built)

# Create the destination directory if it doesn't exist
os.makedirs(dest_dir, exist_ok=True)

# Iterate through directories in the source directory
for item in os.listdir(source_dir):
    item_path = os.path.join(source_dir, item)
    if item.startswith("Math_") and os.path.isdir(item_path) and item_path not in not_built:
        target_path = os.path.join(item_path, "target")
        for content in os.listdir(target_path):
            source_file = os.path.join(target_path, content)
            if os.path.isfile(source_file):
                dest_path = os.path.join(dest_dir, item)
                os.makedirs(dest_path, exist_ok=True)
                print(source_file)
                print(dest_path)
                shutil.copy(source_file, dest_path)
                print(f"Copied {source_file} to {dest_path}")
