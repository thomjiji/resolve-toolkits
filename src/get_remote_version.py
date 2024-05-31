"""
To know which clip is using remote version, find them and copy remote to local
to lock the image once it's approved by the client.
"""

from dri.color_group import TimelineItem
from dri.resolve import Resolve

resolve = Resolve.resolve_init()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()
current_timeline = project.GetCurrentTimeline()

clips_in_timeline: list[TimelineItem] = current_timeline.GetItemListInTrack("video", 1)

for i, clip in enumerate(clips_in_timeline):
    # print(clip.GetCurrentVersion())
    if clip.GetCurrentVersion().get("versionType") == 1:
        print(f"clip {i+1} has remote version enabled.")
