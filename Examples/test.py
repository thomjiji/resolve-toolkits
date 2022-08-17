from pprint import pprint
from pybmd.project import Project

# Import modules for Resolve native API
from python_get_resolve import GetResolve
from typing import List, Union
import sys

media_path: str = sys.argv[1]

# # Initialize pybmd objects
# resolve = Bmd()
# project_manager = resolve.get_project_manager()
# project = project_manager.get_current_project()
# media_storage = resolve.get_media_stroage()
# media_pool = project.get_media_pool()
# root_folder = media_pool.get_root_folder()
# sub_folders_full_path: List[str] = media_storage.get_sub_folder_list(media_path)

# Initialize Resolve native API
resolve = GetResolve()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()
sub_folders_full_path: List[str] = media_storage.GetSubFolderList(media_path)


# media_pool_sub_folder_list = root_folder.GetSubFolderList()


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


def create_new_timeline(timeline_name: str, width: int, height: int) -> None:
    """
    Create new timeline in the _Timeline bin (the last folder under root folder).
    """
    media_pool.SetCurrentFolder(root_folder.GetSubFolderList()[-1])  # SetCurrentFolder 到 _Timeline bin 把时间线都建在这

    """
    原理：
        新建时间线的时候，check 将要新建的时间线是否与已存在的时间线重复：如果将要新建的时间线名称与已存在时间线重复， 
        或者已存在时间线的长和宽与将新建时间线的长和宽重复的话，那么把 CurrentTimeline 设为已存在的那条时间线。
    
    Why?:
        同一个文件夹 Bin 当中有 2048x1080 的素材，也有 4096x2160 的素材。后者再除以 2 之后正好又等于前者。所以
        在先建立好 2048x2080 的时间线之后，遇到 4096x2160 的素材，create_new_timeline() 函数的
        CreatEmptyTimeline() 就不工作了，也就造成 project 的 currentTimeline 还是上一个建立好的时间线。
        那么函数之后的操作像 current_timeline.SetSetting() 会继续进行，但这次修改的是上一个建立好的时间线，
        也就是 project 的 currentTimeline。 
    """
    timeline_number = project.GetTimelineCount()
    for i in range(timeline_number):
        existing_timeline = project.GetTimelineByIndex(i + 1)
        if existing_timeline.GetName() == timeline_name or existing_timeline.GetSetting(
            'timelineResolutionWidth') == str(width) and existing_timeline.GetSetting(
            'timelineResolutionHeight') == str(height):
            project.SetCurrentTimeline(existing_timeline)

    media_pool.CreateEmptyTimeline(timeline_name)
    current_timeline = project.GetCurrentTimeline()
    current_timeline.SetSetting("useCustomSettings", "1")
    current_timeline.SetSetting("timelineResolutionWidth", width)
    current_timeline.SetSetting("timelineResolutionHeight", height)
    current_timeline.SetSetting("timelineFrameRate", str(float(25)))


# # 3. 新建多条时间线
# # 拿到机位 bin 下所有 clip 的分辨率信息，create new empty timeline.
# for sub_folder in root_folder.GetSubFolderList():
#     # 排除 _Timeline Bin
#     if sub_folder.GetName() == "_Timeline":
#         break
#
#     # 拿到机位 bin 下所有 clip 的分辨率信息 assign to all_clips_resolution 这个 list.
#     all_clips_resolution = []  # Camera 机位 bin 下所有 clip 的 resolution 信息
#     for clip in sub_folder.GetClipList():
#         all_clips_resolution.append(clip.GetClipProperty()["Resolution"])
#     all_clips_resolution: list[str] = list(dict.fromkeys(all_clips_resolution))  # 移除 list 中的重复项
#
#     # 根据 all_clips_resolution 里的分辨率信息新建时间线
#     for res in all_clips_resolution:
#         if res.split("x")[1] <= "1080":
#             timeline_name = f"{sub_folder.GetName()}_{res}"
#             create_new_timeline(timeline_name, res.split("x")[0], res.split("x")[1])
#         else:
#             clip_width = str(int(int(res.split('x')[0]) / 2))
#             clip_height = str(int(int(res.split('x')[1]) / 2))
#             timeline_name = f"{sub_folder.GetName()}_{clip_width}x{clip_height}"
#             create_new_timeline(timeline_name, clip_width, clip_height)
#
# # 4. 把每条素材 append 到对应的时间线
# for sub_folder in root_folder.GetSubFolderList():
#     # 排除 _Timeline Bin
#     if sub_folder.GetName() == "_Timeline":
#         break
#     # if sub_folder.GetName() == "Ronin_4D#1":
#     for clip in sub_folder.GetClipList():
#         clip_res: str = clip.GetClipProperty()["Resolution"]
#         # print(clip_res)
#
#         timeline_number = project.GetTimelineCount()
#         for i in range(timeline_number):
#             existing_timeline = project.GetTimelineByIndex(i + 1)
#             # print(existing_timeline.GetName())
#             if existing_timeline.GetName().split("x")[1] <= "1080":
#                 timeline_width = existing_timeline.GetSetting()['timelineResolutionWidth']
#                 timeline_height = existing_timeline.GetSetting()['timelineResolutionHeight']
#                 # print(f"timeline_width+timeline_height: {timeline_width}x{timeline_height}")
#                 if clip_res == f"{timeline_width}x{timeline_height}":
#                     project.SetCurrentTimeline(existing_timeline)
#                     media_pool.AppendToTimeline(clip)
#             else:
#                 timeline_width = str(int(existing_timeline.GetSetting()['timelineResolutionWidth']) * 2)
#                 timeline_height = str(int(existing_timeline.GetSetting()['timelineResolutionHeight']) * 2)
#                 if clip_res == f"{timeline_width}x{timeline_height}":
#                     project.SetCurrentTimeline(existing_timeline)
#                     media_pool.AppendToTimeline(clip)

if __name__ == "__main__":
    # sub_folders_name = get_sub_folder_name(sub_folders_full_path)
    # create_bin(sub_folders_name)
    # import_clip()

    for res in get_resolution():
        # create_new_timeline(res, res.split("x")[0], res.split("x")[1])
        print(f"RESOLUTION: {res}")
        if int(res.split("x")[1]) <= 1080:
            timeline_width = (res.split("x")[0])
            timeline_height = (res.split("x")[1])
            create_new_timeline(res, timeline_width, timeline_height)
        else:
            timeline_width = int(int(res.split("x")[0]) / 2)
            timeline_height = int(int(res.split("x")[1]) / 2)
            create_new_timeline(res, timeline_width, timeline_height)