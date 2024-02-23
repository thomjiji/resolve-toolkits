"""
Check if the files in the source footage folder correspond one-to-one with the files in
the proxy folder.
"""

import argparse
import csv
from pathlib import Path

from tabulate import tabulate

VALID_EXT = ["MP4", "MOV", "MXF"]
# ANSI escape code for red color
RED = "\033[91m"
# ANSI escape code for bold text
BOLD = "\033[1m"
# ANSI escape code to reset text formatting
RESET = "\033[0m"


def save_to_csv(data: list, filename: str) -> None:
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Filename", "Absolute Path"])
        writer.writerows(data)


def get_filenames_with_paths(directory: str) -> dict[str, str]:
    filenames_with_paths = {}
    for p in Path(directory).rglob("*"):
        if (
            p.is_file()
            and p.suffix[1:].upper() in VALID_EXT
            and not p.name.startswith("._")
        ):
            filenames_with_paths[p.stem] = str(p.resolve())
    return filenames_with_paths


def check_filenames_exist(source_dir: str, target_dir: str, to_csv=False) -> None:
    source_dict = get_filenames_with_paths(source_dir)
    target_dict = get_filenames_with_paths(target_dir)

    missing_in_target = set(source_dict.keys()) - set(target_dict.keys())
    missing_in_source = set(target_dict.keys()) - set(source_dict.keys())

    if missing_in_target:
        missing_in_target_with_path = [
            (filename, source_dict[filename]) for filename in missing_in_target
        ]
        print(
            f"{RED}The following files are {BOLD}missing in the proxy directory:{RESET}\n"
        )
        print(
            tabulate(
                missing_in_target_with_path,
                headers=["Filename", "Absolute Path"],
                tablefmt="simple",
            )
        )
        if to_csv:
            csv_filename = "target_missing_files.csv"
            save_to_csv(missing_in_target_with_path, "target_missing_files.csv")
            print(
                f"\nCSV file '{csv_filename}' containing missing files information has been saved to current directory.\n"
            )

    if missing_in_source:
        missing_in_source_with_path = [
            (filename, target_dict[filename]) for filename in missing_in_source
        ]
        print(
            f"{RED}The following files are present in the proxy directory but {BOLD}missing in the source directory:{RESET}\n"
        )
        print(
            tabulate(
                missing_in_source_with_path,
                headers=["Filename", "Absolute Path"],
                tablefmt="simple",
            )
        )
        if to_csv:
            csv_filename = "source_missing_files.csv"
            save_to_csv(missing_in_source_with_path, csv_filename)
            print(
                f"\nCSV file '{csv_filename}' containing missing files information has been saved to current directory."
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check if the files in the source footage folder correspond one-to-one with the files in the proxy folder."
    )
    parser.add_argument("source_directory", type=Path, help="Source path")
    parser.add_argument("target_directory", type=Path, help="Proxy path")
    parser.add_argument(
        "-csv",
        action="store_true",
        help="Output missing files information to a CSV file",
    )
    args = parser.parse_args()

    check_filenames_exist(args.source_directory, args.target_directory, args.csv)
