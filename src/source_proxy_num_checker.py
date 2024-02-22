import argparse
from pathlib import Path
from pprint import pprint

from tabulate import tabulate

VALID_EXT = ["MP4", "MOV", "MXF"]


def get_filenames_with_paths(directory):
    filenames_with_paths = {}
    for p in Path(directory).rglob("*"):
        if (
            p.is_file()
            and p.suffix[1:].upper() in VALID_EXT
            and not p.name.startswith("._")
        ):
            filenames_with_paths[p.stem] = str(p.resolve())
    return filenames_with_paths


def check_filenames_exist(source_dir, target_dir):
    source_dict = get_filenames_with_paths(source_dir)
    target_dict = get_filenames_with_paths(target_dir)

    missing_in_target = set(source_dict.keys()) - set(target_dict.keys())
    missing_in_source = set(target_dict.keys()) - set(source_dict.keys())

    if missing_in_target:
        missing_in_target_with_path = [
            (filename, source_dict[filename]) for filename in missing_in_target
        ]
        print("The following files are missing in the proxy directory:\n")
        print(
            tabulate(
                missing_in_target_with_path,
                headers=["Filename", "Absolute Path"],
                tablefmt="simple",
            )
        )

    if missing_in_source:
        missing_in_source_with_path = [
            (filename, target_dict[filename]) for filename in missing_in_source
        ]
        print(
            "The following fiels are present in the proxy directory but missing in the source directory:\n"
        )
        print(
            tabulate(
                missing_in_source_with_path,
                headers=["Filename", "Absolute Path"],
                tablefmt="simple",
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check if the files in the source footage folder correspond one-to-one with the files in the proxy folder."
    )
    parser.add_argument("source_directory", type=Path, help="Source path")
    parser.add_argument("target_directory", type=Path, help="Proxy path")
    args = parser.parse_args()

    check_filenames_exist(args.source_directory, args.target_directory)
