from pprint import pprint

from pybmd.media_pool_item import MediaPoolItem
from python_get_resolve import GetResolve
from typing import List, Union
import sys

media_path: str = sys.argv[1]

resolve = GetResolve()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()
sub_folders_full_path: List[str] = media_storage.GetSubFolderList(media_path)


def get_sub_folder_name(full_path: List[str]) -> List[str]:
    """
    Extract sub-folder name from media storage full path.
    For creating sub-folder in the media pool.
    """
    sub_folder_name: List[str] = []
    for i in full_path:
        split_full_path = i.split("/")
        sub_folder_name.append(split_full_path[-1])
    return sub_folder_name


# 1. Create sub-folder in media pool.
sub_folders_name: List[str] = get_sub_folder_name(sub_folders_full_path)
for i in sub_folders_name:
    media_pool.AddSubFolder(root_folder, i)
media_pool.AddSubFolder(root_folder, "_Timeline")

# 2. Import footage from media storage into the corresponding sub-folder of the media pool.
for count, sub_folder in enumerate(root_folder.GetSubFolderList()):
    media_pool.SetCurrentFolder(sub_folder)
    if sub_folder.GetName() == "_Timeline":
        break
    media_storage.AddItemListToMediaPool(sub_folders_full_path[count])

# 3. 新建多条时间线 TODO
for sub_folder in root_folder.GetSubFolderList():
    # 排除 _Timeline 这个 Bin
    if sub_folder.GetName() == "_Timeline":
        break

    sub_folder_name = sub_folder.GetName()

    for clip in sub_folder.GetClipList():
        clip_width: int = int(clip.GetClipProperty()["Resolution"].split("x")[0])
        clip_height: int = int(clip.GetClipProperty()["Resolution"].split("x")[1])
        if clip_height == 1080:
            timeline_name = f"{sub_folder_name}_{str(clip_width)}x{str(clip_height)}"
            # media_pool.SetCurrentFolder("_Timeline")
            media_pool.CreateEmptyTimeline(timeline_name)
            project.SetCurrentTimeline(timeline_name)
            current_timeline = project.GetCurrentTimeline()
            current_timeline.SetSetting("useCustomSettings", "1")
            current_timeline.SetSetting("timelineResolutionWidth", str(int(clip_width)))
            current_timeline.SetSetting("timelineResolutionHeight", str(int(clip_height)))
            current_timeline.SetSetting("timelineFrameRate", str(float(25)))
            media_pool.AppendToTimeline(clip)
        elif clip_width > 1080:
            timeline_name = f"{sub_folder_name}_{str(int(clip_width / 2))}x{str(int(clip_height / 2))}"
            # media_pool.SetCurrentFolder("_Timeline")
            media_pool.CreateEmptyTimeline(timeline_name)

            timeline_number = project.GetTimelineCount()
            for i in range(timeline_number):
                timeline = project.GetTimelineByIndex(i + 1)
                if timeline.GetSetting()["timelineResolutionWidth"] == str(int(clip_width / 2)):
                    while project.SetCurrentTimeline(timeline):
                        print("successful")
                        break

            current_timeline = project.GetCurrentTimeline()
            print(current_timeline.GetName())
            current_timeline.SetSetting("useCustomSettings", "1")
            current_timeline.SetSetting("timelineResolutionWidth", str(int(clip_width / 2)))
            current_timeline.SetSetting("timelineResolutionHeight", str(int(clip_height / 2)))
            current_timeline.SetSetting("timelineFrameRate", str(float(25)))
            media_pool.AppendToTimeline(clip)