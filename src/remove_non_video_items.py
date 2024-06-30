"""
This script removes non-video clips from the media pool in DaVinci Resolve
and optionally removes empty subfolders.

Usage:
    python remove_non_video_items.py [--remove-empty]

Options:
    --remove-empty   Remove empty subfolders after removing non-video clips.
"""

import argparse
from dri import Resolve


def remove_non_video_clips(folder):
    items_to_be_deleted = []

    for clip in folder.GetClipList():
        clip_name = clip.GetName()
        clip_type = clip.GetClipProperty("Type")
        is_timeline = clip.GetClipProperty("Type") == "Timeline"

        if (
            clip_type not in ("Video + Audio", "Video")
            and not clip_name.endswith(".exr")
            and not is_timeline
        ):
            items_to_be_deleted.append(clip)

    if items_to_be_deleted:
        print(f"Deleting clips in {folder.GetName()}")
        media_pool.DeleteClips(items_to_be_deleted)

    for subfolder in folder.GetSubFolderList():
        remove_non_video_clips(subfolder)


def remove_empty_subfolders(folder):
    subfolders = folder.GetSubFolderList()

    for subfolder in subfolders:
        remove_empty_subfolders(subfolder)

    if not folder.GetSubFolderList() and not folder.GetClipList():
        print(f"Deleting folder {folder.GetName()}")
        media_pool.DeleteFolders([folder])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Remove non-video clips and optionally empty subfolders."
    )
    parser.add_argument(
        "--remove-empty",
        action="store_true",
        help="Remove empty subfolders after removing clips.",
    )
    args = parser.parse_args()

    resolve = Resolve.resolve_init()
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()

    remove_non_video_clips(root_folder)

    if args.remove_empty:
        remove_empty_subfolders(root_folder)
