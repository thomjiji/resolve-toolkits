"""
Really slow, don't use.
"""

import argparse
import shutil
from pathlib import Path


def is_hidden_file(filename):
    return (
        filename.name.startswith(".")
        or filename.name.startswith("._")
        or filename.name == ".DS_Store"
    )


def rename_files(source_dir, target_dir):
    source_dir = Path(source_dir)
    target_dir = Path(target_dir)

    for source_file in source_dir.glob("**/*"):
        if source_file.is_file() and not is_hidden_file(source_file):
            target_file = None
            for file in target_dir.glob("**/*"):
                if (
                    file.is_file()
                    and not is_hidden_file(file)
                    and file.stat().st_size == source_file.stat().st_size
                    and file.stat().st_mtime == source_file.stat().st_mtime
                ):
                    target_file = file
                    break
            if target_file:
                new_filename = target_file.name
                new_path = source_file.with_name(new_filename)
                shutil.move(source_file, new_path)


def main():
    parser = argparse.ArgumentParser(
        description="Rename files in source directory to match filenames in target directory."
    )
    parser.add_argument("source_dir", type=str, help="Path to the source directory")
    parser.add_argument("target_dir", type=str, help="Path to the target directory")

    args = parser.parse_args()
    rename_files(args.source_dir, args.target_dir)


if __name__ == "__main__":
    main()
