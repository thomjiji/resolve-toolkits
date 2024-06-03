"""
To know which clip is using remote version, find them and copy remote to local
(manually) to lock the image once it's approved by the client.
"""

import argparse
from tabulate import tabulate
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

    # Collect clips data
    clips_data = []
    for i, clip in enumerate(clips_in_timeline):
        current_version = clip.GetCurrentVersion()
        if current_version.get("versionType") == 1:
            clips_data.append(
                [i + 1, clip.GetName(), current_version.get("versionName")]
            )

    # Print the table
    if clips_data:
        print(
            f'The following clips have remote version enabled in timeline "{current_timeline.GetName()}":\n\n'
            f'{tabulate( clips_data, headers=["Clip Number", "Clip Name", "Version Name"], tablefmt="simple")}'
        )
    else:
        print(
            f'No clips with remote version enabled found in timeline "{current_timeline.GetName()}".'
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to check clips in current timeline with remote versions."
    )

    args = parser.parse_args()
    main()
