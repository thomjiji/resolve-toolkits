import argparse
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

MOUNT_POINT = "/Users/thom/Desktop/remote-filesystem"


def replace_special_characters(drive_name: str) -> str:
    """
    Replace special characters in the drive name with their percent-encoded values.

    Parameters
    ----------
    drive_name
        The drive name to be encoded.

    Returns
    -------
    str
        The encoded drive name.
    """
    replacements = {"#": "%23", "@": "%40", ".": "%2E", " ": "%20"}
    for char, encoded_char in replacements.items():
        drive_name = drive_name.replace(char, encoded_char)
    return drive_name


def extract_drive_and_server(file_path: str) -> dict:
    """
    Extract drive names and their corresponding servers (for example gsj-1, gsj-2, ...)
    from a text file.

    Parameters
    ----------
    file_path
        Path to the text file containing drive and server information.

    Returns
    -------
    dict
        A dictionary mapping server names to their corresponding drive names.
    """
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


def mount_smbfs(drives: dict, username: str, password: str) -> None:
    """
    Mount SMB drives based on the provided drive and server information.

    Parameters
    ----------
    drives
        A dictionary mapping server names to their corresponding drive names.
    username
        Username for accessing the SMB drives.
    password
        Password for accessing the SMB drives.
    """
    for server, drive_name in drives.items():
        server_dir = Path(MOUNT_POINT) / server
        (server_dir / drive_name).mkdir(parents=True, exist_ok=True)
        encoded_drive_name = replace_special_characters(drive_name)

        logging.info(f"Connecting to server {server}...")

        command = f'mount_smbfs -f 0755 -d 0755 //{username}:{password}@{server}/{encoded_drive_name} "{server_dir / drive_name}"'
        result = subprocess.run(command, shell=True, capture_output=True)

        if result.returncode == 0:
            logging.info(f"Successfully connected to server {server}.")
        else:
            logging.error(
                f"Failed to connect to server {server}. \n\tError: {result.stderr.decode('utf-8')}"
            )


def umount_smbfs(drives: dict) -> None:
    """
    Unmount all mounted SMB drives.

    Parameters
    ----------
    drives
        A dictionary mapping server names to their corresponding drive names.
    """
    for server, drive_name in drives.items():
        server_dir = Path(MOUNT_POINT) / server
        command = f'umount "{server_dir / drive_name}"'
        result = subprocess.run(command, shell=True, capture_output=True)

        if result.returncode == 0:
            logging.info(
                f"Successfully unmounted drive {drive_name} from server {server}."
            )
        else:
            logging.error(
                f"Failed to unmount drive {drive_name} from server {server}. \n\tError: {result.stderr.decode('utf-8')}"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mount SMB drives from a text file.")
    parser.add_argument(
        "-i",
        "--file_path",
        type=str,
        help="Path to the text file containing drive and server information.",
        required=True,
    )
    parser.add_argument(
        "-u",
        "--username",
        type=str,
        help="Username for accessing the SMB drives.",
        required=True,
    )
    parser.add_argument(
        "-p",
        "--password",
        type=str,
        help="Password for accessing the SMB drives.",
        required=True,
    )
    parser.add_argument(
        "-um",
        "--umount_all",
        action="store_true",
        help="Unmount all mounted SMB drives.",
    )
    args = parser.parse_args()
    drives = extract_drive_and_server(args.file_path)

    if args.umount_all:
        umount_smbfs(drives)
    else:
        mount_smbfs(drives, args.username, args.password)
