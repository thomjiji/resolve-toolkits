#!/usr/bin/env python3

import argparse
import re
import sys
from typing import Union
import os
import logging
from proxy import Proxy
from resolve import Resolve

DROP_FRAME_FPS = [23.98, 29.97, 59.94, 119.88]

# Set up logger
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# Create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter(
    "%(name)s %(levelname)s %(asctime)s at %(lineno)s: %(message)s",
    datefmt="%H:%M:%S",
)

# Add formatter to ch
ch.setFormatter(formatter)

# Add ch to logger
log.addHandler(ch)


def absolute_file_paths(path: str) -> list:
    """Get the absolute paths of all files under a given path."""
    absolute_file_path_list = []
    for directory_path, _, filenames in os.walk(path):
        for filename in filenames:
            if filename.split(".")[-1] != "DS_Store":
                absolute_file_path_list.append(
                    os.path.abspath(os.path.join(directory_path, filename))
                )
    return absolute_file_path_list


def get_subfolders_name(path: list[str]) -> list[str]:
    """
    Extract sub-folder name from media storage full path. For creating
    sub-folder in the media pool.

    Parameters
    ----------
    path
        The next directory level of current media storage path lists.

    Returns
    -------
    list
        Containing subfolders name.

    """
    return [os.path.split(i)[1] for i in path]


def is_camera_dir(text: str) -> bool:
    """
    Is the given text a cam dir? Yes or no based on GSJ camera name
    specification. For example: FX6#1, FX3#2...

    Parameters
    ----------
    text
        Text to be checked.

    Returns
    -------
    bool
        Yes or no

    """
    matched = re.search(r"^.+#\d$", text)
    if matched:
        return True
    else:
        return False


class QC(Resolve):
    def __init__(self, input_path: str):
        """
        Parameters
        ----------
        input_path
            The path of the source clips.

        """
        super().__init__()
        self.media_parent_path = input_path
        self.proxy = Proxy(self.media_parent_path)
        self.camera_log_dict = {
            "S-Gamut3.Cine/S-Log3": ["A7S3", "FX3", "FX6", "FX9", "FS7", "Z90"],
            "Panasonic V-Gamut/V-Log": ["GH5", "GH5M2", "S1H", "GH5S", "S5"],
            "ARRI LogC3": ["ALEXA_Mini", "ALEXA_Mini_LF", "AMIRA"],
            "ARRI LogC4": ["ALEXA_35"],
            "DJI D-Gamut/D-Log": ["Ronin_4D", "航拍", "Mavic", "MavicPro"],
            "Rec.709 Gamma 2.4": ["Others"],
        }

    def create_and_change_timeline(
        self,
        timeline_name: str,
        width: int,
        height: int,
        fps: Union[int, float],
    ) -> bool:
        """
        Simply create empty timeline and change its resolution to inputs
        width and height, and its frame rate to input fps. Used for
        `create_new_timeline()` function.

        Parameters
        ----------
        timeline_name
            The name of the timeline that will be created.
        width
            The width of the timeline that will be created.
        height
            The height of the timeline that will be created.
        fps
            The frame rate of the timeline that will be created.

        Returns
        -------
        bool
            If `SetSetting()` is all right, it will return True, otherwise it
            will be False.

        """
        self.media_pool.CreateEmptyTimeline(timeline_name)
        current_timeline = self.project.GetCurrentTimeline()
        # TODO: Needs a mechanism to track SetSetting() status
        current_timeline.SetSetting("useCustomSettings", "1")
        current_timeline.SetSetting("timelineResolutionWidth", str(width))
        current_timeline.SetSetting("timelineResolutionHeight", str(height))
        return current_timeline.SetSetting("timelineFrameRate", str(fps))

    def create_timeline_qc(self):
        """
        In the Timeline bin under each camera bin of the media pool, create
        a new timeline based on the resolution and frame rate of the clips under
        that bin.
        """
        for subfolder in self.root_folder.GetSubFolderList():
            for folder in subfolder.GetSubFolderList():
                self.media_pool.SetCurrentFolder(folder)
                res_fps_dict = self.get_bin_res_and_fps(subfolder.GetName())
                for res, fps in res_fps_dict.items():
                    if fps in DROP_FRAME_FPS:
                        timeline_name = f"{subfolder.GetName()}_{res}_{fps}p"
                        self.create_and_change_timeline(
                            timeline_name,
                            int(res.split("x")[0]),
                            int(res.split("x")[1]),
                            fps,
                        )
                    else:
                        timeline_name = (
                            f"{subfolder.GetName()}_{res}_{int(fps)}p"
                        )
                        self.create_and_change_timeline(
                            timeline_name,
                            int(res.split("x")[0]),
                            int(res.split("x")[1]),
                            int(fps),
                        )

    def get_bin_res_and_fps(self, bin_name: str) -> dict[str, float]:
        """
        Get the resolution and frame rate of all clips under the given bin,
        return a dict.

        Parameters
        ----------
        bin_name
            The existing camera bin in the media pool.

        Returns
        -------
        dict
            Containing the resolution and frame rate of all shots under the
            camera bin in the media pool, used by `create_timeline_qc()`.

        """
        current_bin = self.get_subfolder_by_name(bin_name)
        bin_res_fps_dict = {
            clip.GetClipProperty("Resolution"): clip.GetClipProperty("FPS")
            for clip in current_bin.GetClipList()  # type: ignore
        }

        return bin_res_fps_dict

    def create_bin(self, subfolders_name_list: list):
        """
        Create camera bin in media pool, create Timeline bin in each camera bin.

        Parameters
        ----------
        subfolders_list
            The name of subfolders to be created in media pool.

        """
        for i in subfolders_name_list:
            self.media_pool.AddSubFolder(self.root_folder, i)
            if is_camera_dir(i):
                self.media_pool.AddSubFolder(
                    self.get_subfolder_by_name(i), "Timeline"
                )

    def append_to_timeline(self):
        """
        For each clip in camera bin, after doing some checks, we get the name of
        the timeline that the clip should be appended to by their properties,
        then `SetCurrentTimeline()` to it and finally append the clip to this
        timeline. Set clip input colorspace (see `set_clip_colorspace()`) and so
        on.

        """
        for subfolder in self.root_folder.GetSubFolderList():
            self.media_pool.SetCurrentFolder(subfolder)
            for clip in subfolder.GetClipList():
                if (
                    clip.GetClipProperty("type") == "Video"
                    or clip.GetClipProperty("type") == "Video + Audio"
                ):
                    res = clip.GetClipProperty("Resolution")
                    fps = clip.GetClipProperty("FPS")
                    if fps in DROP_FRAME_FPS:
                        current_timeline_name = (
                            f"{subfolder.GetName()}_{res}_{fps}p"
                        )
                        current_timeline = self.get_timeline_by_name(
                            current_timeline_name
                        )
                    else:
                        current_timeline_name = (
                            f"{subfolder.GetName()}_{res}_{int(fps)}p"
                        )
                        current_timeline = self.get_timeline_by_name(
                            current_timeline_name
                        )

                    if not self.project.SetCurrentTimeline(current_timeline):
                        log.debug(
                            f"append_to_timeline() project.SetCurrentTimeline() failed. Current timeline is {current_timeline}"
                        )
                    self.media_pool.AppendToTimeline(clip)
                    self.set_clip_colorspace(clip)

    def set_project_color_management(self):
        """
        Notes
        -----
        DaVinici Resolve has no so much API for ACES, so we use DaVinci YRGB
        Color Managed instead.

        -   `isAutoColorManage`: 0. Set to False ("0").
        -   `useCATransform`: Use white point adaptation. Set to True ("1").
        -   `useColorSpaeAwareGradingTools`: Use color space aware grading 
            tools. Set to True ("1").

        """
        self.project.SetSetting("colorScienceMode", "davinciYRGBColorManagedv2")
        self.project.SetSetting("isAutoColorManage", "0")
        self.project.SetSetting("colorSpaceTimeline", "DaVinci WG/Intermediate")
        self.project.SetSetting("colorSpaceInput", "Rec.709 Gamma 2.4")
        self.project.SetSetting("colorSpaceOutput", "Rec.709 Gamma 2.4")
        self.project.SetSetting("timelineWorkingLuminanceMode", "SDR 100")
        self.project.SetSetting("timelineWorkingLuminanceMode", "SDR 100")
        self.project.SetSetting("inputDRT", "DaVinci")
        self.project.SetSetting("outputDRT", "DaVinci")
        self.project.SetSetting("useCATransform", "1")
        self.project.SetSetting("useColorSpaceAwareGradingTools", "1")

    def set_clip_colorspace(self, clip):

        # By looking at which folder this clip comes from, we can compare it
        # with the `camera_log_dict` in QC attribute to get its color space
        # information.
        clip_path = clip.GetClipProperty("File Path")
        if sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
            cam_name = clip_path.split("\\")[
                clip_path.split("\\").index(
                    os.path.basename(self.media_parent_path)
                )
                + 1
            ].split("#")[0]
        else:
            cam_name = clip_path.split("/")[
                clip_path.split("/").index(
                    os.path.basename(self.media_parent_path)
                )
                + 1
            ].split("#")[0]
        camera_log_key = list(self.camera_log_dict.keys())
        camera_log_val = list(self.camera_log_dict.values())
        try:
            position = camera_log_val.index(
                [value for value in camera_log_val if cam_name in value][0]
            )
            color_space = camera_log_key[position]
        except IndexError:
            color_space = camera_log_key[-1]
        if clip.SetClipProperty("Input Color Space", color_space):
            log.info(
                f"Set input color space {color_space} for {clip.GetName()} "
                f"succeed. "
            )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="qc is a commandline tool to automate media import, "
        "Bin, Timeline creation and color management setting in DaVinci "
        "Resolve.",
    )
    parser.add_argument(
        "path",
        help="Source media absolute path",
        action="store",
        type=str,
    )

    return parser


def main():
    parser = create_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    media_parent_path = parser.parse_args().path

    qc = QC(media_parent_path)

    # 从 media storage 得到 bin 名称之后，以此在 media pool 分辨新建对应的 bin。
    # 导入素材到对应的 bin
    subfolders_name = get_subfolders_name(
        qc.media_storage.GetSubFolderList(media_parent_path)
    )
    qc.create_bin(subfolders_name)
    qc.proxy.import_clip(one_by_one=True)

    # 创建基于 media pool 下各 camera bin 里素材的分辨率帧率的时间线
    qc.create_timeline_qc()

    # 导入素材到对应时间线
    qc.append_to_timeline()

    qc.set_project_color_management()


if __name__ == "__main__":
    main()
