from dri import Resolve
from dri.dri import Gallery
from pprint import pprint

resolve = Resolve.resolve_init()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()
current_timeline = project.GetCurrentTimeline()

# 获取时间线的起始帧
start_frame = current_timeline.GetStartFrame()
print(f"Timeline start frame: {start_frame}")

# 获取所有的 markers
markers = current_timeline.GetMarkers()
pprint(markers)

# 遍历 markers，筛选蓝色的 marker，计算实际帧位置并抓取静帧
for timecode, marker_data in markers.items():
    if marker_data["color"] == "Blue":
        # 计算实际帧位置
        adjusted_timecode = timecode + start_frame
        print(
            f"Setting timecode to {adjusted_timecode} for blue marker '{marker_data['name']}'"
        )

        # 移动播放头并抓取静帧
        current_timeline.SetCurrentTimecode(str(adjusted_timecode))
        still = current_timeline.GrabStill()

        if still:
            print(
                f"Grabbed still for blue marker '{marker_data['name']}' at timecode {adjusted_timecode}"
            )
        else:
            print(
                f"Failed to grab still for blue marker '{marker_data['name']}' at timecode {adjusted_timecode}"
            )

