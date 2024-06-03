"""
To know which clip is using remote version, find them and copy remote to local
to lock the image once it's approved by the client.
"""

import argparse
from dri.color_group import TimelineItem
from dri.resolve import Resolve


def main() -> None:
    # Initialize Resolve and get project-related objects
    resolve = Resolve.resolve_init()
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    media_storage = resolve.GetMediaStorage()
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    current_timeline = project.GetCurrentTimeline()

    # Get list of clips in the timeline
    clips_in_timeline: list[TimelineItem] = current_timeline.GetItemListInTrack(
        "video", 1
    )

    # Iterate over clips and check if they have remote version enabled
    for i, clip in enumerate(clips_in_timeline):
        if clip.GetCurrentVersion().get("versionType") == 1:
            print(f"clip {i+1} has remote version enabled.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to check clips in current timeline with remote versions."
    )

    args = parser.parse_args()
    main()
