from pprint import pprint
from python_get_resolve import GetResolve
from typing import List, Union
import sys

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

# # Get FPS info of all the shots that have been imported into the media pool.
# FPS_list = []
# for camera in all_clips:
#     for clip in camera:
#         FPS_list.append(clip.GetClipProperty()["FPS"])
# FPS_list = list(dict.fromkeys(FPS_list))

# Get the fps data of a clip in a specific camera directory
for sub_folder in root_folder.GetSubFolderList():
    FPS_list_camera = []
    for clip in sub_folder.GetClipList():
        FPS_list_camera.append(clip.GetClipProperty()["FPS"])
    FPS_list_camera = list(dict.fromkeys(FPS_list_camera))
    sub_folder_name = sub_folder.GetName()
    if len(FPS_list_camera) == 1:
        project.SetSetting("timelineResolutionWidth", "1920")
        project.SetSetting("timelineResolutionHeight", "1080")
        project.SetSetting("timelineFrameRate", str(FPS_list_camera[0]).split(".")[0])
        media_pool.CreateEmptyTimeline(sub_folder_name)
        for clip in sub_folder.GetClipList():
            media_pool.AppendToTimeline(clip)
    else:
        for i in FPS_list_camera:
            project.SetSetting("timelineResolutionWidth", "1920")
            project.SetSetting("timelineResolutionHeight", "1080")
            project.SetSetting("timelineFrameRate", str(i).split(".")[0])
            media_pool.CreateEmptyTimeline(f"{sub_folder_name}_{str(i).split('.')[0]}")
            for clip in sub_folder.GetClipList():
                media_pool.AppendToTimeline(clip)


# for index, fps in enumerate(FPS_list):
#     project.SetSetting("timelineFrameRate", fps)
#     project.SetSetting("timelineResolutionWidth", "1920")
#     project.SetSetting("timelineResolutionHeight", "1080")
#     media_pool.CreateTimelineFromClips(sub_folder_name[index], [all_clips[0][0], all_clips[0][1]])