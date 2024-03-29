import subprocess
from pathlib import Path


def replace_special_characters(drive_name):
    replacements = {"#": "%23", "@": "%40", ".": "%2E", " ": "%20"}
    for char, encoded_char in replacements.items():
        drive_name = drive_name.replace(char, encoded_char)
    return drive_name


def extract_drive_and_server(file_path):
    drives = {}
    with open(file_path, "r") as file:
        current_server = None
        for line in file:
            if line.startswith("#"):
                current_server = line.strip("#").strip()
            else:
                parts = line.strip().split("/")
                if len(parts) >= 2:
                    drive_name = parts[2]
                    drives[current_server] = drive_name
    return drives


def mount_smbfs(drives, username, password, mount_point):
    for server, drive_name in drives.items():
        server_dir = Path(mount_point) / server
        (server_dir / drive_name).mkdir(parents=True, exist_ok=True)
        encoded_drive_name = replace_special_characters(drive_name)
        command = f'mount_smbfs -f 0755 -d 0755 //{username}:{password}@{server}/{encoded_drive_name} "{server_dir / drive_name}"'
        print(command)
        subprocess.run(command, shell=True)


if __name__ == "__main__":
    file_path = "/Users/thom/Desktop/gsj_work/project_files copy.txt"
    username = "geekshootjack"
    password = "gsj"
    mount_point = "/Users/thom/Desktop/remote-filesystem"

    drives = extract_drive_and_server(file_path)
    mount_smbfs(drives, username, password, mount_point)
