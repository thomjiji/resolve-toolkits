#!/usr/bin/env python3

import argparse
import subprocess

# Changeable parameters
EXCLUSIONS = [
    ".DS_Store",
    "_gsdata_",
    ".*",
]

RSYNC_OPTIONS = [
    "-a",  # archive mode; equals -rlptgoD (no -H)
    "-v",  # verbose; increase verbosity
    "-i",  # itemize changes; output a change-summary for all updates
    "-P",  # equivalent to --partial --progress; shows progress during transfer and keeps partially transferred files
    "-h",  # human-readable; output numbers in a human-readable format
    "--update",  # skip files that are newer on the receiver
]


# Function to build exclusion options
def build_exclude_opts():
    exclude_opts = []
    for item in EXCLUSIONS:
        exclude_opts.append(f"--exclude={item}")
    return exclude_opts


# Function to build rsync command
def build_rsync_cmd(action):
    cmd = ["rsync"] + RSYNC_OPTIONS + build_exclude_opts()
    if action == "run":
        cmd.append("--info=progress2")
    else:
        cmd.append("-n")  # dry-run
    return cmd


# Function to execute rsync
def execute_rsync(source, target, action):
    cmd = build_rsync_cmd(action)
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

    # Parse arguments
    args = parser.parse_args()

    # Execute rsync
    execute_rsync(args.source, args.target, args.action)


if __name__ == "__main__":
    main()
