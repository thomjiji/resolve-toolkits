# Import modules for Resolve native API
import os
import sys
from typing import List

from resolve_api_init.python_get_resolve import GetResolve

media_path: str = sys.argv[1]
INVALID_EXTENSION = ["DS_Store", "JPG", "JPEG", "SRT"]  # TODO, 小写的情况还待考虑进去

# Initialize Resolve native API
resolve = GetResolve()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()

sub_folders_full_path = media_storage.GetSubFolderList(media_path)


def absolute_file_paths(directory) -> list:
    absolute_file_path_list = []
    for directory_path, _, filenames in os.walk(directory):
        for f in filenames:
            absolute_file_path_list.append(os.path.abspath(os.path.join(directory_path, f)))
    return absolute_file_path_list


def get_sub_folder_name(source_media_full_path: List[str]) -> List[str]:
    """
    Extract sub-folder name from media storage full path.
    For creating sub-folder in the media pool.
    """
    sub_folders_name: List[str] = []
    for i in source_media_full_path:
        split_full_path = i.split("/")
        sub_folders_name.append(split_full_path[-1])
    return sub_folders_name


def create_bin(sub_folders_name: list) -> None:
    """Create sub-folder in media pool."""
    for i in sub_folders_name:
        media_pool.AddSubFolder(root_folder, i)
    media_pool.AddSubFolder(root_folder, "_Timeline")


def import_clip() -> None:
    """Import footage from media storage into the corresponding sub-folder of the media pool root folder."""
    for count, sub_folder in enumerate(root_folder.GetSubFolderList()):
        media_pool.SetCurrentFolder(sub_folder)
        # 导入素材的时候排除 _Timeline 这个目的地 Bin
        if sub_folder.GetName() == "_Timeline":
            break
        media_storage.AddItemListToMediaPool(sub_folders_full_path[count])


def import_clip_new() -> None:
    media_full_path_list = absolute_file_paths(media_path)
    filename_and_fullpath_dict = {os.path.splitext(path)[0].replace(".", "").split('/')[-1]: path for path in
                                  media_full_path_list}

    filename_and_fullpath_keys = list(filename_and_fullpath_dict.keys())
    filename_and_fullpath_keys.sort()
    filename_and_fullpath_value = [filename_and_fullpath_dict.get(i) for i in filename_and_fullpath_keys]

    for path in filename_and_fullpath_value:
        if path.split(".")[-1] not in INVALID_EXTENSION:
            current_folder = get_sub_folder_by_name(f"{path.split('/')[path.split('/').index('素材') + 1]}")
            media_pool.SetCurrentFolder(current_folder)
            media_pool.ImportMedia(path)


def get_resolution() -> list:
    """Get all clips resolution, return a list consist of all resolution string."""
    all_clips_resolution = []
    for bin in root_folder.GetSubFolderList():
        # 排除 _Timeline bin
        if bin.GetName() == "_Timeline":
            break

        for clip in bin.GetClipList():
            all_clips_resolution.append(clip.GetClipProperty("Resolution"))
        all_clips_resolution = list(dict.fromkeys(all_clips_resolution))

    return all_clips_resolution


def create_and_change_timeline(timeline_name: str, width: str, height: str) -> None:
    """
    Simply create empty timeline and change its resolution to inputs width and height.
    Used for create_new_timeline() function.
    """
    media_pool.CreateEmptyTimeline(timeline_name)
    current_timeline = project.GetCurrentTimeline()
    current_timeline.SetSetting("useCustomSettings", "1")
    current_timeline.SetSetting("timelineResolutionWidth", str(width))
    current_timeline.SetSetting("timelineResolutionHeight", str(height))
    current_timeline.SetSetting("timelineFrameRate", str(float(25)))


def get_all_timeline() -> list:
    """Get all existing timelines. Return a list containing timeline object."""
    all_timeline = []
    for timeline_index in range(1, project.GetTimelineCount() + 1, 1):
        all_timeline.append(project.GetTimelineByIndex(timeline_index))
    return all_timeline


def create_new_timeline(timeline_name: str, width: int, height: int) -> bool:
    """
    Create new timeline in the _Timeline bin (the last folder under root folder).
    Check timeline duplication.
    """
    media_pool.SetCurrentFolder(root_folder.GetSubFolderList()[-1])  # SetCurrentFolder 到 _Timeline bin 把时间线都建在这

    if project.GetTimelineCount() == 0:
        create_and_change_timeline(timeline_name, str(width), str(height))
        return True
    else:
        existing_timeline_resolution = []
        for existing_timeline in get_all_timeline():
            existing_timeline_resolution.append(
                f"{existing_timeline.GetSetting('timelineResolutionWidth')}x{existing_timeline.GetSetting('timelineResolutionHeight')}")
        if f"{str(width)}x{str(height)}" not in existing_timeline_resolution:
            create_and_change_timeline(timeline_name, str(width), str(height))
        else:
            current_timeline = project.GetCurrentTimeline()
            new_name = f"{current_timeline.GetName()}_{str(width)}x{str(height)}"
            current_timeline.SetName(new_name)


def get_timeline_by_name(timeline_name: str):
    """Get timeline object by name."""
    all_timeline = get_all_timeline()
    timeline_dict = {timeline.GetName(): timeline for timeline in all_timeline}
    return timeline_dict.get(timeline_name, "")


def get_sub_folder_by_name(sub_folder_name: str):
    """Get folder object by name."""
    all_sub_folder = root_folder.GetSubFolderList()
    sub_folder_dict = {sub_folder.GetName(): sub_folder for sub_folder in all_sub_folder}
    return sub_folder_dict.get(sub_folder_name, "")


def append_to_timeline() -> None:
    """Append to timeline"""
    all_timeline_name = [timeline.GetName() for timeline in get_all_timeline()]
    for sub_folder in root_folder.GetSubFolderList():
        for clip in sub_folder.GetClipList():
            if clip.GetClipProperty("type") == "Video" or clip.GetClipProperty("type") == "Video + Audio":
                clip_width = clip.GetClipProperty("Resolution").split("x")[0]
                clip_height = clip.GetClipProperty("Resolution").split("x")[1]
                for name in all_timeline_name:
                    if f"{clip_width}x{clip_height}" in name:
                        project.SetCurrentTimeline(get_timeline_by_name(name))
                        media_pool.AppendToTimeline(clip)


if __name__ == "__main__":
    # 从 media storage 得到 bin 名称之后，以此在 media pool 分辨新建对应的 bin。导入素材到对应的 bin。
    sub_folders_name = get_sub_folder_name(sub_folders_full_path)
    create_bin(sub_folders_name)
    import_clip_new()

    # 根据媒体池所有的素材分辨率新建不同的时间线。
    for res in get_resolution():
        if "x" not in res:
            continue
        if int(res.split("x")[1]) <= 1080:
            timeline_width = (res.split("x")[0])
            timeline_height = (res.split("x")[1])
            create_new_timeline(res, timeline_width, timeline_height)
        else:
            timeline_width = int(int(res.split("x")[0]) / 2)
            timeline_height = int(int(res.split("x")[1]) / 2)
            create_new_timeline(res, timeline_width, timeline_height)

    # 导入素材到对应时间线
    append_to_timeline()