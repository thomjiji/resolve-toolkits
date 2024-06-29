"""
Don't use this script (it's slow), use Rsync instead: `rsync -avPih --include '*/'
--exclude '*' videos/ ~/Desktop/videos-dummy/`.

Create dummy directories to mimic the structure and files of another directory. Create
puppet directory to mimic the structure and files of another directory (source
directory). The files are all 0 bytes, the original suffix and modification time will be
retained.
"""

import argparse
import os
from pathlib import Path


def create_dummy_folders(original_dir, dummy_dir):
    for source_path in Path(original_dir).rglob("*"):
        relative_path = source_path.relative_to(original_dir)
        dummy_path = Path(dummy_dir, relative_path)
        dummy_path.parent.mkdir(parents=True, exist_ok=True)

        if source_path.is_file():
            dummy_path.touch()
            st = source_path.stat()
            os.utime(dummy_path, (st.st_atime, st.st_mtime))
            os.chmod(dummy_path, st.st_mode & 0o777)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create dummy directories to mimic the structure and files of the source directory."
    )
    parser.add_argument("source", type=Path, help="Source directory")
    parser.add_argument("dummy", type=Path, help="Create dummy directories to")
    args = parser.parse_args()

    # create_dummy_folders(args.source, args.dummy)
