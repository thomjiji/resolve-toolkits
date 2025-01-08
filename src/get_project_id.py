from dri import Resolve
from tabulate import tabulate
import csv

# Initialize Resolve and project manager
resolve = Resolve.resolve_init()
project_manager = resolve.GetProjectManager()

# Initialize a list to store project details
project_data = []

# Loop through all projects in the current folder
for project_name in project_manager.GetProjectListInCurrentFolder():
    project = project_manager.LoadProject(project_name)
    if project:
        project_id = project.GetUniqueId()
        project_data.append([project_name, project_id])
        project_manager.CloseProject(project)
    else:
        project_data.append([project_name, "project id retreive failed"])

# Create a table-like output in the terminal using tabulate
headers = ["Project Name", "Project ID"]
print(tabulate(project_data, headers=headers, tablefmt="simple"))

# Write project details to a CSV file
csv_filename = "project_list.csv"
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # Write the header
    writer.writerow(headers)
    # Write each project data row
    writer.writerows(project_data)

print(f"Project IDs has been written to {csv_filename}")
