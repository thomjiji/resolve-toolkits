import argparse
from pprint import pprint

from dri import Resolve

resolve = Resolve.resolve_init()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()
current_timeline = project.GetCurrentTimeline()


def main():
    parser = argparse.ArgumentParser(
        description="Grab stills for markers of a specific color from the current timeline."
    )
    parser.add_argument(
        "--color",
        choices=[
            "All",
            "Blue",
            "Cyan",
            "Green",
            "Yellow",
            "Red",
            "Pink",
            "Purple",
            "Fuchsia",
            "Rose",
            "Lavender",
            "Sky",
            "Mint",
            "Lemon",
            "Sand",
            "Cocoa",
            "Cream",
        ],
        default="Blue",
        help="Specify the color of the markers to grab. Use 'All' to grab all markers regardless of color.",
    )
    args = parser.parse_args()

    selected_color = args.color

    # 获取时间线的起始帧
    start_frame = current_timeline.GetStartFrame()
    print(f"Timeline start frame: {start_frame}")

    # 获取所有的 markers
    markers = current_timeline.GetMarkers()
    pprint(markers)

    # 遍历 markers，筛选指定颜色的 marker，计算实际帧位置并抓取静帧
    for timecode, marker_data in markers.items():
        if selected_color == "All" or marker_data["color"] == selected_color:
            # 计算实际帧位置
            adjusted_timecode = timecode + start_frame
            print(
                f"Setting timecode to {adjusted_timecode} for {marker_data['color']} marker '{marker_data['name']}'"
            )

            # 移动播放头并抓取静帧
            current_timeline.SetCurrentTimecode(str(adjusted_timecode))
            still = current_timeline.GrabStill()

            if still:
                print(
                    f"Grabbed still for {marker_data['color']} marker '{marker_data['name']}' at timecode {adjusted_timecode}"
                )
            else:
                print(
                    f"Failed to grab still for {marker_data['color']} marker '{marker_data['name']}' at timecode {adjusted_timecode}"
                )


if __name__ == "__main__":
    main()
