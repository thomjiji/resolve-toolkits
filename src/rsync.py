#!/usr/bin/env python3

import argparse
import datetime
import logging
import subprocess
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Changeable parameters
EXCLUSIONS = [".DS_Store", "_gsdata_", ".*"]

CHECKSUM_ALGO = "xxh128"

RSYNC_OPTIONS = [
    "-a",  # archive mode; equals -rlptgoD (no -H)
    "-v",  # verbose; increase verbosity
    "-i",  # itemize changes; output a change-summary for all updates
    "-P",  # equivalent to --partial --progress; shows progress during transfer and keeps partially transferred files
    "-h",  # human-readable; output numbers in a human-readable format
    # "--update",  # skip files that are newer on the receiver
    "--info=progress2",  # shows detailed progress information
    "--info=name0",  # shows the name of the current file being transferred
    "--info=stats2",  # shows detailed statistics at the end
]


def build_exclude_opts():
    """
    Build a list of rsync exclusion options based on the EXCLUSIONS list.

    Returns
    -------
    list of str
        List of --exclude options for rsync.
    """
    exclude_opts = []
    for item in EXCLUSIONS:
        exclude_opts.append(f"--exclude={item}")
    return exclude_opts


def build_rsync_cmd(action: str, checksum=False, log_file_name=None):
    """
    Build the rsync command with the specified options.

    Parameters
    ----------
    action : str
        The action to perform ('run' for actual sync, otherwise dry-run).
    checksum : bool, optional
        Whether to include the --checksum flag in the rsync command.
    log_file_name : str or None, optional
        The log file name to use for --log-file. If None, do not log to file.

    Returns
    -------
    list of str
        The complete rsync command as a list suitable for subprocess.
    """
    cmd = ["rsync"] + RSYNC_OPTIONS + build_exclude_opts()
    if checksum:
        cmd.append("--checksum")
        cmd.append(f"--cc={CHECKSUM_ALGO}")
    if action != "run":
        cmd.append("-n")  # dry-run
    # Only add log file and log-file-format if requested
    if log_file_name:
        cmd.append(f"--log-file={log_file_name}")
        cmd.append("--out-format=%i %n%L %C")
        cmd.append("--log-file-format=%i %n%L %C")
    return cmd


def execute_rsync(
    source: str, target: str, action: str, checksum=False, log_file_name=None
):
    """
    Execute the rsync command to synchronize files from source to target.

    Parameters
    ----------
    source : str
        The source directory or file path.
    target : str
        The target directory or file path.
    action : str
        The action to perform ('run' for actual sync, otherwise dry-run).
    checksum : bool, optional
        Whether to include the --checksum flag in the rsync command.
    log_file_name : str or None, optional
        The log file name to use for --log-file. If None, do not log to file.
    """
    # Colorize paths using ANSI escape codes
    source_colored = f"\033[94m{source}\033[0m"  # Blue
    target_colored = f"\033[92m{target}\033[0m"  # Green
    logging.info(
        f"Synchronizing from '{source_colored}' to '{target_colored}' (action: {action})"
    )

    source_path = Path(source)
    if source_path.is_dir():
        source = str(source_path) + "/"
    cmd = build_rsync_cmd(action, checksum=checksum, log_file_name=log_file_name)
    cmd.append(source)
    cmd.append(target)

    if action == "run":
        subprocess.run(cmd)
    else:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        subprocess.run(["less"], input=result.stdout, text=True)
        logging.info(result.stdout)


def main():
    parser = argparse.ArgumentParser(
        description="Synchronize files from one or more SOURCE paths to TARGET with rsync."
    )
    parser.add_argument(
        "-i",
        "--inputs",
        nargs="+",
        required=True,
        help="One or more source directories or files to rsync from.",
    )
    parser.add_argument(
        "-o", "--output", required=True, help="The target directory to rsync to."
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="dry-run",
        help="Specify 'run' to perform the actual rsync with verbose output. Omit or use any other value for a dry run.",
    )
    parser.add_argument(
        "--swap",
        action="store_true",
        help="Swap source and target to verify synchronization in the reverse direction. (Not supported with multiple inputs)",
    )
    parser.add_argument(
        "--checksum",
        action="store_true",
        help="Use the rsync built-in --checksum flag to compare files based on checksums.",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Write rsync output to a log file.",
    )
    parser.add_argument(
        "--log-path",
        default=None,
        help="Path to write the log file. If not provided, writes to current working directory.",
    )

    args = parser.parse_args()

    # Determine log file name if logging is enabled
    log_file_name = None
    if args.log:
        import os

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = args.log_path or os.getcwd()
        log_file_name = str(Path(log_dir) / f"rsync_{timestamp}.log")

    # Log whether checksum is enabled
    logging.info(f"Checksum enabled: {args.checksum}")
    if args.checksum:
        logging.info(f"Checksum algorithm: {CHECKSUM_ALGO}")
    if args.log:
        logging.info(f"Logging enabled. Log file: {log_file_name}")
    else:
        logging.info("Logging disabled.")

    # For each input path, sync to the same target
    for source in args.inputs:
        logging.info(f"Processing input: {source}")
        execute_rsync(
            source,
            args.output,
            args.action,
            checksum=args.checksum,
            log_file_name=log_file_name,
        )


if __name__ == "__main__":
    main()
