import os
import time
import argparse
import csv
from tabulate import tabulate


def get_project_name(file_path):
    return os.path.basename(os.path.dirname(os.path.dirname(file_path)))


def get_prproj_name(file_path):
    return os.path.basename(file_path)


def get_file_modification_time(file_path):
    try:
        modification_time = os.path.getmtime(file_path)
        formatted_modification_time = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(modification_time)
        )
        return formatted_modification_time
    except FileNotFoundError:
        return None


def main(file_paths_file, output_format):
    with open(file_paths_file, "r") as file:
        file_lines = file.readlines()

    table_data = []
    current_computer = None
    for line in file_lines:
        line = line.strip()
        if line.startswith("#"):
            current_computer = line[1:].strip()  # Extract computer name
        elif line:
            project_name = get_project_name(line)
            prproj_name = get_prproj_name(line)
            modification_time = get_file_modification_time(line)
            if modification_time:
                table_data.append(
                    [current_computer, project_name, prproj_name, modification_time]
                )
            else:
                table_data.append(
                    [current_computer, project_name, prproj_name, "File not found"]
                )

    if output_format == "csv":
        with open("project_modification_time.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                ["Computer", "Project Name", "prproj Name", "Modification Time"]
            )
            writer.writerows(table_data)
    else:
        print(
            tabulate(
                table_data,
                headers=[
                    "Computer",
                    "Project Name",
                    "prproj Name",
                    "Modification Time",
                ],
                tablefmt="grid",
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve modification time of files.")
    parser.add_argument(
        "file_paths_file",
        help="Path to the text file containing file paths and computer names",
    )
    parser.add_argument("-csv", action="store_true", help="Output in CSV format")
    args = parser.parse_args()
    main(args.file_paths_file, "csv" if args.csv else "stdout")
