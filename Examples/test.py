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

# Import footages from media storage.
for count, sub_folder in enumerate(root_folder.GetSubFolderList()):
    media_pool.SetCurrentFolder(sub_folder)
    media_storage.AddItemListToMediaPool(sub_folders_full_path[count])