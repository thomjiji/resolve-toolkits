"""
Create dummy directories to mimic the structure and files of another directory. Create
puppet directory to mimic the structure and files of another directory (source
directory). The files are all 0 bytes and the original suffix will be retained.
"""

import argparse
import os
from pathlib import Path


def create_dummy_folders(original_dir, dummy_dir):
    for root, dirs, files in os.walk(original_dir):
        # Create corresponding directories in the dummy directory
        relative_path = os.path.relpath(root, original_dir)
        dummy_subdir = os.path.join(dummy_dir, relative_path)
        os.makedirs(dummy_subdir, exist_ok=True)

        # Create empty files for real files encountered
        for file in files:
            original_file_path = os.path.join(root, file)
            dummy_file_path = os.path.join(dummy_subdir, file)
            # If it's a real file, touch it
            if os.path.isfile(original_file_path):
                open(dummy_file_path, "a").close()  # Create empty file
                os.utime(dummy_file_path, None)  # Update modification time
                os.chmod(dummy_file_path, 0o644)  # Set permissions to rw-r--r--


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create dummy directories to mimic the structure and files of the source directory."
    )
    parser.add_argument("source", type=Path, help="Source directory")
    parser.add_argument("dummy", type=Path, help="Create dummy directories to")
    args = parser.parse_args()

    create_dummy_folders(args.source, args.dummy)
