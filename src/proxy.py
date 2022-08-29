#!/usr/bin/env python3

# Import modules for Resolve native API
import os
import sys
from typing import List
from resolve_init import GetResolve

INVALID_EXTENSION = ["DS_Store", "JPG", "JPEG", "SRT"]  # TODO, 小写的情况还待考虑进去

# Initialize Resolve native API
resolve = GetResolve()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()


def absolute_file_paths(directory) -> list:
    absolute_file_path_list = []
    for directory_path, _, filenames in os.walk(directory):
        for f in filenames:
            absolute_file_path_list.append(os.path.abspath(os.path.join(directory_path, f)))
    return absolute_file_path_list


def get_subfolders_name(source_media_full_path: List[str]) -> List[str]:
    """
    Extract sub-folder name from media storage full path.
    For creating sub-folder in the media pool.
    """
    return [os.path.split(i)[1] for i in source_media_full_path]


def create_bin(subfolders_name: list) -> None:
    """Create sub-folder in media pool.

    Args:
        subfolders_name (list): The name of the bin to be created.

    Returns:
        None
    """
    for i in subfolders_name:
        media_pool.AddSubFolder(root_folder, i)
    if not get_subfolder_by_name("_Timeline"):
        media_pool.AddSubFolder(root_folder, "_Timeline")


def import_clip(path: str) -> None:
    """
    Import footage from media storage into the corresponding subfolder of the media
    pool root folder. Filter out the files with suffix in the INVALID_EXTENSION list
    before importing.

    Args:
        path (string): source media parent path, such as "素材".

    Returns:
        None
    """
    media_fullpath_list = media_storage.GetSubFolderList(path)

    for cam_path in media_fullpath_list:
        filename_and_fullpath_dict = {os.path.basename(os.path.splitext(path)[0]): path for path in
                                      absolute_file_paths(cam_path) if
                                      os.path.splitext(path)[-1].replace(".", "") not in INVALID_EXTENSION}
        filename_and_fullpath_keys = list(filename_and_fullpath_dict.keys())
        filename_and_fullpath_keys.sort()
        filename_and_fullpath_value = [filename_and_fullpath_dict.get(i) for i in filename_and_fullpath_keys]
        media_parent_dir = os.path.basename(path)

        if sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
            name = cam_path.split('\\')[cam_path.split('\\').index(media_parent_dir) + 1]
            current_folder = get_subfolder_by_name(name)
        else:
            current_folder = get_subfolder_by_name(
                f"{cam_path.split('/')[cam_path.split('/').index(media_parent_dir) + 1]}")

        media_pool.SetCurrentFolder(current_folder)
        media_storage.AddItemListToMediaPool(filename_and_fullpath_value)


def import_clip_new(path: str) -> None:
    """
    Import footage from media storage into the corresponding sub-folder of the media
    pool root folder one by one. Import speed is much lower.

    Args:
        path (string): source media parent path, such as "素材".

    Returns:
        None
    """
    filename_and_fullpath_dict = {os.path.basename(os.path.splitext(path)[0]): path for path in
                                  absolute_file_paths(path) if
                                  os.path.splitext(path)[-1].replace(".", "") not in INVALID_EXTENSION}
    filename_and_fullpath_keys = list(filename_and_fullpath_dict.keys())
    filename_and_fullpath_keys.sort()
    filename_and_fullpath_value = [filename_and_fullpath_dict.get(i) for i in filename_and_fullpath_keys]

    for abs_media_path in filename_and_fullpath_value:
        media_parent_dir = os.path.basename(path)

        if sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
            name = abs_media_path.split('\\')[abs_media_path.split('\\').index(media_parent_dir) + 1]
            current_folder = get_subfolder_by_name(name)
        else:
            current_folder = get_subfolder_by_name(
                f"{abs_media_path.split('/')[abs_media_path.split('/').index(media_parent_dir) + 1]}")

        media_pool.SetCurrentFolder(current_folder)
        media_pool.ImportMedia(abs_media_path)


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

    Args:
        timeline_name (string):
        width (integer):
        height (integer):

    Returns:
         Bool
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


def get_subfolder_by_name(subfolder_name: str):
    """Get subfolder (folder object) under the root folder in the media pool."""
    all_subfolder = root_folder.GetSubFolderList()
    subfolder_dict = {subfolder.GetName(): subfolder for subfolder in all_subfolder}
    return subfolder_dict.get(subfolder_name, "")


def append_to_timeline() -> None:
    """Append to timeline"""
    all_timeline_name = [timeline.GetName() for timeline in get_all_timeline()]
    for subfolder in root_folder.GetSubFolderList():
        for clip in subfolder.GetClipList():
            if clip.GetClipProperty("type") == "Video" or clip.GetClipProperty("type") == "Video + Audio":
                clip_width = clip.GetClipProperty("Resolution").split("x")[0]
                clip_height = clip.GetClipProperty("Resolution").split("x")[1]
                for name in all_timeline_name:
                    if f"{clip_width}x{clip_height}" in name:
                        project.SetCurrentTimeline(get_timeline_by_name(name))
                        media_pool.AppendToTimeline(clip)


def add_render_job():
    """Select a render preset, set the render path, add to render queue."""
    preset_list = project.GetRenderPresetList()
    if len(preset_list) < 32:
        print("Please pour in the H.265 render preset first.")
    elif len(preset_list) > 33:
        print("There are two many custom render preset, please specify it.")
    else:
        # 加载 H.265 渲染预设.
        proxy_preset = preset_list[-1]
        project.LoadRenderPreset(proxy_preset)

        # 把时间线分别添加到渲染队列
        for timeline in get_all_timeline():
            project.SetCurrentTimeline(timeline)
            try:
                os.mkdir(f"{proxy_parent_path}/{timeline.GetName()}")
            except FileExistsError:
                pass
            rendering_setting = {'TargetDir': f"{proxy_parent_path}/{timeline.GetName()}"}
            project.SetRenderSettings(rendering_setting)
            project.AddRenderJob()


if __name__ == "__main__":

    # 检查用户是否提供了正确的 argv。
    if len(sys.argv) < 3:
        print("Usage: python3 proxy.py [media path] [proxy.py path]\nPlease ensure this two directories exist.")
        sys.exit()
    else:
        media_parent_path: str = sys.argv[1]
        proxy_parent_path: str = sys.argv[2]
        if not os.path.exists(proxy_parent_path):
            print("Usage: python3 proxy.py [media path] [proxy.py path]\nPlease ensure this two directory exist.")
            sys.exit()
    media_fullpath_list = media_storage.GetSubFolderList(media_parent_path)

    # 从 media storage 得到 bin 名称之后，以此在 media pool 分辨新建对应的 bin。导入素材到对应的 bin。
    subfolders_name = get_subfolders_name(media_fullpath_list)
    create_bin(subfolders_name)
    import_clip(media_parent_path)

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

    # 将所有时间线以 H.265 的渲染预设添加到渲染队列
    add_render_job()

    # 开始渲染之前，暂停程序，向用户确认是否有添加 Burn-in，同时给用户时间确认其他参数是否正确。然后开始渲染。
    if input("The program is paused, please add burn-in manually, then enter 'y' to start rendering. Enter 'n' to "
             "exit the program. y/n?") == 'y':
        project.StartRendering(isInteractiveMode=True)

    # for render_job in project.GetRenderJobList():
    #     pprint(render_job)

    # # Job status check
    # job_id_list = [render_job.get('JobId') for render_job in project.GetRenderJobList()]
    # print(project.GetRenderJobStatus(job_id_list[1]))