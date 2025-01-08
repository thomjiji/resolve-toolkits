import argparse
import csv
import sys

from dri import Resolve
from tabulate import tabulate


def fetch_project_data():
    """
    Fetch project names and their unique IDs from DaVinci Resolve in the current folder.
    """
    # Initialize Resolve and project manager
    resolve = Resolve.resolve_init()
    project_manager = resolve.GetProjectManager()

    # Fetch projects from the current folder
    project_list = project_manager.GetProjectListInCurrentFolder()

    if not project_list:
        raise ValueError("No projects found in the current folder.")

    # Initialize a list to store project details
    project_data = []

    # Loop through all projects in the folder
    for project_name in project_list:
        try:
            project = project_manager.LoadProject(project_name)
            if project:
                project_id = project.GetUniqueId()
                project_data.append([project_name, project_id])
                project_manager.CloseProject(project)
            else:
                project_data.append([project_name, "Project ID retrieval failed"])
        except Exception as e:
            project_data.append([project_name, f"Error: {str(e)}"])

    return project_data


def write_to_csv(data, filename):
    """Write project data to a CSV file."""
    headers = ["Project Name", "Project ID"]
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            # Write the header
            writer.writerow(headers)
            # Write each project data row
            writer.writerows(data)
        print(f"Project IDs have been written to {filename}")
    except Exception as e:
        print(f"Error writing to CSV file: {e}")
        sys.exit(1)


def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Fetch DaVinci Resolve project details and save to CSV."
    )
    parser.add_argument(
        "-c",
        "--csv",
        type=str,
        default="project_ids.csv",
        help="Specify the output CSV filename.",
    )

    args = parser.parse_args()

    try:
        # Fetch project data from the current folder
        project_data = fetch_project_data()

        # Print the data in a table format
        headers = ["Project Name", "Project ID"]
        print(tabulate(project_data, headers=headers, tablefmt="simple"))

        # Write data to CSV
        write_to_csv(project_data, args.csv)

    except ValueError as ve:
        print(f"Error: {ve}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
