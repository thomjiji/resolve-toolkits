from pprint import pprint
from python_get_resolve import GetResolve
from typing import List, Union
import sys

# testing
sys.argv[1] = '/Users/thom/Movies/Videos/Footages/悠长假期'

media_path: str = sys.argv[1]

resolve = GetResolve()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()

sub_folders_full_path = media_storage.GetSubFolderList(media_path)


def get_sub_folder_name(folder_full_path: List[str]) -> List[str]:
    """Get folder name from media storage."""
    folder_name_list = []
    for i in folder_full_path:
        split_folder_path_list = i.split("/")
        folder_name_list.append(split_folder_path_list[-1])
    return folder_name_list


# Create subfolder in media pool.
sub_folder_name = get_sub_folder_name(sub_folders_full_path)
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()
for i in sub_folder_name:
    media_pool.AddSubFolder(root_folder, i)

# Import footage from media storage.
all_clips = []  # a list of MediaPoolItems.
for count, sub_folder in enumerate(root_folder.GetSubFolderList()):
    media_pool.SetCurrentFolder(sub_folder)
    all_clips.append(media_storage.AddItemListToMediaPool(sub_folders_full_path[count]))

# Get FPS info of all the shots that have been imported into the media pool.
for camera in all_clips:
    for clip in camera:
        print(clip.GetClipProperty()["FPS"])

project.SetSetting("timelineFrameRate", "25")
project.SetSetting("timelineResolutionWidth", "3840")
project.SetSetting("timelineResolutionHeight", "2160")
media_pool.CreateTimelineFromClips("tmp", [all_clips[0][0], all_clips[0][1]])