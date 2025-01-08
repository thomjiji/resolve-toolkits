"""
This script removes non-video clips from the media pool in DaVinci Resolve
and optionally removes empty subfolders.
"""

import argparse
from dri import Resolve


def remove_non_video_clips(folder):
    items_to_be_removed = []

    for clip in folder.GetClipList():
        clip_name = clip.GetName()
        clip_type = clip.GetClipProperty("Type")
        is_timeline = clip.GetClipProperty("Type") == "Timeline"

        if (
            clip_type not in ("Video + Audio", "Video")
            and not clip_name.endswith(".exr")
            and not is_timeline
        ):
            items_to_be_removed.append(clip)

    if items_to_be_removed:
        print(f"Removing non video items in {folder.GetName()}")
        media_pool.DeleteClips(items_to_be_removed)

    for subfolder in folder.GetSubFolderList():
        remove_non_video_clips(subfolder)


def remove_empty_subfolders(folder, recursive=False):
    subfolders = folder.GetSubFolderList()

    for subfolder in subfolders:
        remove_empty_subfolders(subfolder, recursive)

    if not folder.GetSubFolderList() and not folder.GetClipList():
        print(f"Removing bin {folder.GetName()}")
        media_pool.DeleteFolders([folder])
    elif folder.GetName() == "SUB":
        print(f"Removing SUB bin {folder.GetName()}")
        media_pool.DeleteFolders([folder])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Remove non-video clips and optionally empty subfolders."
    )
    parser.add_argument(
        "--remove-empty-bin",
        action="store_true",
        help="Remove empty subfolders under the current folder.",
    )
    parser.add_argument(
        "--remove-all-empty-bin",
        action="store_true",
        help="Remove all empty subfolders recursively, including in subfolders of the current folder.",
    )
    args = parser.parse_args()

    resolve = Resolve.resolve_init()
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    current_folder = media_pool.GetCurrentFolder()

    # Default behavior: Remove non-video items
    remove_non_video_clips(current_folder)

    # Optionally remove empty folders if user explicitly request.
    if args.remove_all_empty_bin:
        remove_empty_subfolders(root_folder, recursive=True)
    elif args.remove_empty_bin:
        remove_empty_subfolders(current_folder, recursive=False)
