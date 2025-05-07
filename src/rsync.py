#!/usr/bin/env python3

import argparse
import subprocess
from pathlib import Path

# Changeable parameters
EXCLUSIONS = [".DS_Store", "_gsdata_", ".*"]

RSYNC_OPTIONS = [
    "-a",  # archive mode; equals -rlptgoD (no -H)
    "-v",  # verbose; increase verbosity
    "-i",  # itemize changes; output a change-summary for all updates
    "-P",  # equivalent to --partial --progress; shows progress during transfer and keeps partially transferred files
    "-h",  # human-readable; output numbers in a human-readable format
    "--update",  # skip files that are newer on the receiver
    "--info=progress2",  # shows detailed progress information
    "--info=name0",  # shows the name of the current file being transferred
    "--info=stats2",  # shows detailed statistics at the end
]


# Function to build exclusion options
def build_exclude_opts():
    exclude_opts = []
    for item in EXCLUSIONS:
        exclude_opts.append(f"--exclude={item}")
    return exclude_opts


# Function to build rsync command
def build_rsync_cmd(action, checksum=False):
    cmd = ["rsync"] + RSYNC_OPTIONS + build_exclude_opts()
    if checksum:
        cmd.append("--checksum")
    if action != "run":
        cmd.append("-n")  # dry-run
    return cmd


# Function to execute rsync
def execute_rsync(source, target, action, checksum=False):
    # Colorize paths using ANSI escape codes
    source_colored = f"\033[94m{source}\033[0m"  # Blue
    target_colored = f"\033[92m{target}\033[0m"  # Green
    print(
        f"Synchronizing from '{source_colored}' to '{target_colored}' (action: {action})"
    )

    source_path = Path(source)
    if source_path.is_dir():
        source = str(source_path) + "/"
    cmd = build_rsync_cmd(action, checksum=checksum)
    cmd.append(source)
    cmd.append(target)

    if action == "run":
        subprocess.run(cmd)
    else:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        subprocess.run(["less"], input=result.stdout, text=True)
        print(result.stdout)


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Synchronize files from SOURCE to TARGET with rsync."
    )
    parser.add_argument("source", help="The source directory to rsync from.")
    parser.add_argument("target", help="The target directory to rsync to.")
    parser.add_argument(
        "action",
        nargs="?",
        default="dry-run",
        help="Specify 'run' to perform the actual rsync with verbose output. Omit or use any other value for a dry run.",
    )
    parser.add_argument(
        "--swap",
        action="store_true",
        help="Swap source and target to verify synchronization in the reverse direction.",
    )
    parser.add_argument(
        "--checksum",
        action="store_true",
        help="Use the rsync built-in --checksum flag to compare files based on checksums.",
    )

    # Parse arguments
    args = parser.parse_args()

    # Swap source and target if --swap is provided
    source = args.target if args.swap else args.source
    target = args.source if args.swap else args.target

    # Execute rsync
    execute_rsync(source, target, args.action, checksum=args.checksum)


if __name__ == "__main__":
    main()
