#!/usr/bin/env python3

import argparse
import logging
import os
import re
import sys
from typing import AnyStr, Iterable

from deprecated.resolve import BaseResolve

INVALID_EXTENSION = ["DS_Store", "JPG", "JPEG", "SRT"]

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
    """
    Walk through the path, add the abs paths of all files under the given path
    to a list, and return that list.

    Parameters
    ----------
    path
        The input media path for parsing files under it.

    Returns
    -------
    list
        A list containing all the abs path (str) of files under input path.
    """
    absolute_file_path_list = []
    for directory_path, _, filenames in os.walk(path):
        for filename in filenames:
            absolute_file_path_list.append(
                os.path.abspath(os.path.join(directory_path, filename))
            )
    return absolute_file_path_list


def get_subfolders_name(source_media_full_path: list[str]) -> list[str]:
    """
    Extract subfolder name from media storage full path. For creating sub-folder in the
    media pool.

    Parameters
    ----------
    source_media_full_path
        Source media full path list.

    Returns
    -------
    list
        A list containing the name of the folders under the given path.
    """
    return [os.path.split(i)[1] for i in source_media_full_path]


def get_sorted_path(path: str) -> list:
    """
    Given a path, find the absolute paths of all files in that path. Filter out any
    files with an extension in INVALID_EXTENSION. Sort the remaining absolute paths
    alphabetically and return the sorted list of absolute paths.

    Parameters
    ----------
    path
        The input path. The abs paths of all files in its subdirectories will be sorted.

    Returns
    -------
    list
        A list containing all abs paths that have been sorted.
    """
    filename_and_fullpath_dict = {
        os.path.basename(os.path.splitext(path)[0]): path
        for path in absolute_file_paths(path)
        if os.path.splitext(path)[-1].replace(".", "") not in INVALID_EXTENSION
    }
    filename_and_fullpath_keys = list(filename_and_fullpath_dict.keys())
    filename_and_fullpath_keys.sort()
    filename_and_fullpath_value = [
        filename_and_fullpath_dict.get(i) for i in filename_and_fullpath_keys
    ]
    return filename_and_fullpath_value


class Proxy(BaseResolve):
    """
    Proxy class

    Attributes
    ----------
    media_parent_path
    proxy_parent_path
    """

    def __init__(self, input_path: str, output_path: str = ""):
        """
        Initialize some necessary objects.

        Parameters
        ----------
        input_path
            The media path.
        output_path
            The proxy path.
        """
        super().__init__()
        self.media_parent_path = input_path
        self.proxy_parent_path = output_path
        # self.media_fullpath_list = self.media_storage.GetSubFolderList(
        #     self.media_parent_path
        # )

    def create_bin(self, subfolders_list: Iterable[AnyStr]) -> None:
        """Create subfolder in the media pool root folder."""
        for i in subfolders_list:
            self.media_pool.AddSubFolder(self.root_folder, i)

        if not self.get_subfolder_by_name("_Timeline"):
            return self.media_pool.AddSubFolder(self.root_folder, "_Timeline")

    def import_clip(self, one_by_one=False) -> None:
        """
        Import footage from media storage into the corresponding subfolder of
        the media pool root folder.

        Filter out the files with suffix in the INVALID_EXTENSION list before
        importing. If one_by_one parameter is specified as True, then they will
        be imported one by one, which is relatively slow.

        Parameters
        ----------
        one_by_one
            If this parameter is specified a True, it will be imported one by
            one, which is relatively slow.
        """
        media_parent_dir = os.path.basename(self.media_parent_path)

        if not one_by_one:
            for cam_path in self.media_storage.GetSubFolderList(self.media_parent_path):
                filename_and_fullpath_value = get_sorted_path(cam_path)
                if sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
                    name = cam_path.split("\\")[
                        cam_path.split("\\").index(media_parent_dir) + 1
                    ]
                    current_folder = self.get_subfolder_by_name(name)
                else:
                    current_folder = self.get_subfolder_by_name(
                        f"{cam_path.split('/')[cam_path.split('/').index(media_parent_dir) + 1]}"
                    )

                self.media_pool.SetCurrentFolder(current_folder)
                self.media_storage.AddItemListToMediaPool(filename_and_fullpath_value)
        else:
            for abs_media_path in get_sorted_path(self.media_parent_path):
                if sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
                    name = abs_media_path.split("\\")[
                        abs_media_path.split("\\").index(media_parent_dir) + 1
                    ]
                    current_folder = self.get_subfolder_by_name(name)
                    self.media_pool.SetCurrentFolder(current_folder)
                    self.media_pool.ImportMedia(abs_media_path)
                else:
                    name = abs_media_path.split("/")[
                        abs_media_path.split("/").index(media_parent_dir) + 1
                    ]
                    current_folder = self.get_subfolder_by_name_recursively(name)
                    self.media_pool.SetCurrentFolder(current_folder)
                self.media_pool.ImportMedia(abs_media_path)

    def get_resolution(self) -> list[str]:
        """
        Get all clip's resolution, return a list consist all the resolution string.

        Returns
        -------
        list
            A list containing all the resolution information.
        """
        all_clips_resolution = []
        for subfolder in self.root_folder.GetSubFolderList():
            # 排除 _Timeline bin
            if subfolder.GetName() == "_Timeline":
                break

            for clip in subfolder.GetClipList():
                all_clips_resolution.append(clip.GetClipProperty("Resolution"))
            all_clips_resolution = list(dict.fromkeys(all_clips_resolution))

        return all_clips_resolution

    def create_and_change_timeline(
        self, timeline_name: str, width: int, height: int
    ) -> bool:
        """
        Simply create empty timeline and change its resolution to inputs
        width and height. Used for `create_new_timeline()` function.

        Parameters
        ----------
        timeline_name
            The name of the timeline that will be created.
        width
            The width of the timeline that will be created.
        height
            The height of the timeline that will be created.

        Returns
        -------
        bool
            If `SetSetting()` is all right, it will return True, otherwise it
            will be False.
        """
        self.media_pool.CreateEmptyTimeline(timeline_name)
        current_timeline = self.project.GetCurrentTimeline()
        current_timeline.SetSetting("useCustomSettings", "1")
        current_timeline.SetSetting("timelineResolutionWidth", str(width))
        current_timeline.SetSetting("timelineResolutionHeight", str(height))
        return current_timeline.SetSetting("timelineFrameRate", str(25))

    def create_new_timeline(self, timeline_name: str, width: int, height: int) -> bool:
        """
        Create new timeline in the _Timeline bin (the last folder under root folder).
        Check timeline duplication.

        Parameters
        ----------
        timeline_name
            The name of the timeline that will be created.
        width
            The width of the timeline that will be created.
        height
            The height of the timeline that will be created.

        Returns
        -------
        bool
        """
        self.media_pool.SetCurrentFolder(
            self.root_folder.GetSubFolderList()[-1]
        )  # SetCurrentFolder to _Timeline bin to build the timeline there

        if self.project.GetTimelineCount() == 0:
            self.create_and_change_timeline(timeline_name, width, height)
            return True

        existing_timeline_resolution = []
        for existing_timeline in self.get_all_timeline():
            existing_timeline_resolution.append(
                f"{existing_timeline.GetSetting('timelineResolutionWidth')}"
                f"x{existing_timeline.GetSetting('timelineResolutionHeight')}"
            )
        if f"{str(width)}x{str(height)}" not in existing_timeline_resolution:
            return self.create_and_change_timeline(timeline_name, width, height)
        else:
            current_timeline = self.project.GetCurrentTimeline()
            new_name = f"{current_timeline.GetName()}_{str(width)}x{str(height)}"
            return current_timeline.SetName(new_name)

    def append_to_timeline(self) -> None:
        """Append to timeline"""
        all_timeline_name = [timeline.GetName() for timeline in self.get_all_timeline()]
        for subfolder in self.root_folder.GetSubFolderList():
            for clip in subfolder.GetClipList():
                if (
                    clip.GetClipProperty("type") == "Video"
                    or clip.GetClipProperty("type") == "Video + Audio"
                ):
                    clip_width = clip.GetClipProperty("Resolution").split("x")[0]
                    clip_height = clip.GetClipProperty("Resolution").split("x")[1]
                    for name in all_timeline_name:
                        if f"{clip_width}x{clip_height}" in name:
                            self.project.SetCurrentTimeline(
                                self.get_timeline_by_name(name)
                            )
                            self.media_pool.AppendToTimeline(clip)

    def add_render_job(self):
        """
        Select a render preset, set the render path, add to render queue.

        Notes
        -----
        - DaVinci Resolve Render Preset path
            - Windows: ``%USERNAME%\\AppData\\Roaming\\Blackmagic Design\\DaVinci Resolve\\Support\\Resolve Disk Database\\Resolve Projects\\Settings``
            - macOS: ``/Users/{user_name}/Library/Application Support/Blackmagic Design/DaVinci Resolve/Resolve Disk Database/Resolve Projects/Settings``
        """
        # Load H.265 preset.
        for preset in self.project.GetRenderPresetList():
            if re.search(r".*(Proxy).*(H\.265).*", preset):
                self.project.LoadRenderPreset(preset)
                log.info("Successfully loaded H.265 render preset")
                break
            else:
                continue

        # If there is no valid preset, it will not pass the following checks.
        # The following operations will not be performed.
        if any(
            re.search(r".*(Proxy).*(H\.265).*", preset)
            for preset in self.project.GetRenderPresetList()
        ):
            # Add all timelines to the render queue
            for timeline in self.get_all_timeline():
                self.project.SetCurrentTimeline(timeline)
                try:
                    os.mkdir(f"{self.proxy_parent_path}/{timeline.GetName()}")
                except FileExistsError:
                    pass
                rendering_setting = {
                    "TargetDir": f"{self.proxy_parent_path}/{timeline.GetName()}",
                    "ColorSpaceTag": "Same as Project",
                    "GammaTag": "Same as Project",
                }
                self.project.SetRenderSettings(rendering_setting)
                self.project.AddRenderJob()
        else:
            log.debug("No valid render preset, program is terminated.")

    def set_project_color_management(self):
        """
        Set the project color management to DaVinci YRGB and timeline color
        space to Rec.709 Gamma 2.4.

        Notes
        -----
            `SetSetting()` will fail as long as the Output Color Space is
        changed in the first place, not "Same as Timeline". This is
        acceptable, because the default Output Color Space for newly created
        projects is "Same as Timeline". In this case, `SetSetting()` to "Same as
        Timeline" will succeed, even if this operation is not necessary. If the
        project's default Output Color Space is not "Same as Timeline",
        there needs to be a mechanism to handle this.  # TODO
        """
        if self.project.SetSetting("colorScienceMode", "davinciYRGB"):
            timeline_color_space = self.project.GetSetting("colorSpaceTimeline")
            output_colorspace = self.project.GetSetting("colorSpaceOutput")
            log.info("Set Project Color Management to 'DaVinci YRGB'")
            log.info(f"Timeline Color Space is '{timeline_color_space}'")
            log.info(f"Output Color Space is '{output_colorspace}'")
            log.info("----------------")

        if self.project.SetSetting("colorSpaceTimeline", "Rec.709 Gamma 2.4"):
            timeline_color_space = self.project.GetSetting("colorSpaceTimeline")
            output_colorspace = self.project.GetSetting("colorSpaceOutput")
            log.info("Set Timeline Color Space to 'Rec.709 Gamma 2.4'")
            log.info(f"Timeline Color Space is '{timeline_color_space}'")
            log.info(f"Output Color Space is '{output_colorspace}'")
            log.info("----------------")

        if self.project.SetSetting("colorSpaceOutput", "Same as Timeline"):
            log.info("Set Output Color Space to 'Same as Timeline'")
        else:
            log.debug("Failed to set Output Color Space to 'Same as Timeline'")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="dailies is a commandline tool to automatic import clips, "
        "create timelines, add to render queue using the predefined preset."
    )
    parser.add_argument(
        "input", help="Input path of source media.", action="store", type=str
    )
    parser.add_argument(
        "output",
        help="Output path of proxy rendering.",
        action="store",
        type=str,
    )

    return parser


def main():
    parser = create_parser()

    # Show help messages if no arguments are provided.
    if len(sys.argv) == 1:
        parser.print_help()

    media_parent_path = parser.parse_args().input

    # Ensure that the output path exists.
    if not os.path.exists(parser.parse_args().output):
        log.debug(
            f"{parser.parse_args().output} does not exist, program is terminated."
        )
        parser.print_help()
        sys.exit()
    else:
        proxy_parent_path = parser.parse_args().output

    # Initialize the proxy object.
    p = Proxy(media_parent_path, proxy_parent_path)

    p.set_project_color_management()

    # Create bin in the media pool.
    media_fullpath_list = p.media_storage.GetSubFolderList(media_parent_path)
    p.create_bin(get_subfolders_name(media_fullpath_list))

    # Import clips to the corresponding bin in media pool.
    p.import_clip()

    # Create new timeline based on the resolution of all the clips in the
    # media pool.
    for res in p.get_resolution():
        if "x" not in res:
            continue
        # If any number in the resolution (such as "1920x1080") is less than or
        # equal to 1080, then the resolution of the newly created timeline will
        # not be divided by 2. It will still be created at the original
        # resolution.
        if int(res.split("x")[1]) <= 1080 or int(res.split("x")[0]) <= 1080:
            timeline_width: int = int(res.split("x")[0])
            timeline_height: int = int(res.split("x")[1])
            p.create_new_timeline(res, timeline_width, timeline_height)
        else:
            timeline_width: int = int(int(res.split("x")[0]) / 2)
            timeline_height: int = int(int(res.split("x")[1]) / 2)
            p.create_new_timeline(res, timeline_width, timeline_height)

    # Import footage to timeline
    p.append_to_timeline()

    # Apply H.265 render preset to all timelines and add them to the render
    # queue sequentially.
    p.add_render_job()

    # Pause the program prior to initiating the rendering process. Confirm with the user
    # whether the Burn-in has been incorporated and whether the other configurations
    # are accurate. Subsequently, commence the rendering.
    render_input = input(
        "The program is paused, please add burn-in manually, then enter 'y' to "
        "start rendering. Enter 'n' to exit the program. Y/n?"
    ).lower()  # Store the user input in a variable and make it lower case

    # If user input is 'y' or if user pressed enter without typing anything,
    # start rendering.
    if render_input == "y" or render_input == "":
        p.project.StartRendering(isInteractiveMode=True)


if __name__ == "__main__":
    main()
