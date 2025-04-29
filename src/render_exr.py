import argparse
import logging
import time
from typing import Dict, List

from dftt_timecode import DfttTimecode
from dri import Resolve
from resolve_utils import initialize_resolve

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def convert_smpte_to_frames(timecode: str, fps: float) -> int:
    """Convert SMPTE timecode to frame number.

    Parameters
    ----------
    timecode : str
        SMPTE timecode string (e.g., "01:00:00:00")
    fps : float
        Frames per second of the timeline

    Returns
    -------
    int
        Frame number corresponding to the timecode
    """
    timecode_obj = DfttTimecode(timecode, "auto", fps, drop_frame=False, strict=True)
    return timecode_obj.timecode_output("frame")


def get_blue_markers(timeline, start_frames: int) -> Dict[int, Dict]:
    """Get all blue markers from the timeline.

    Parameters
    ----------
    timeline : object
        DaVinci Resolve timeline object
    start_frames : int
        Start frame of the timeline

    Returns
    -------
    Dict[int, Dict]
        Dictionary of blue markers with frame numbers as keys
    """
    markers = timeline.GetMarkers()
    blue_markers = {
        frame + int(start_frames): info
        for frame, info in markers.items()
        if info["color"] == "Blue"
    }
    return blue_markers


def get_clip_name_at_frame(timeline, frame: int) -> str:
    """Get the name of the clip at a specific frame.

    Parameters
    ----------
    timeline : object
        DaVinci Resolve timeline object
    frame : int
        Frame number to check

    Returns
    -------
    str
        Name of the clip at the specified frame, or "unknown_clip" if not found
    """
    clips = timeline.GetItemListInTrack("Video", 1)
    for clip in clips:
        if clip.GetStart() <= frame <= clip.GetEnd():
            return clip.GetName()
    return "unknown_clip"


def add_render_jobs(
    project,
    timeline,
    blue_markers: Dict[int, Dict],
    target_dir: str,
    render_preset: str,
) -> List[str]:
    """Add render jobs for each blue marker.

    Parameters
    ----------
    project : object
        DaVinci Resolve project object
    timeline : object
        DaVinci Resolve timeline object
    blue_markers : Dict[int, Dict]
        Dictionary of blue markers with frame numbers as keys
    target_dir : str
        Target directory for rendered files
    render_preset : str
        Name of the render preset to use

    Returns
    -------
    List[str]
        List of job IDs for the added render jobs

    Raises
    ------
    ValueError
        If the render preset cannot be loaded
    """
    # Clear the render queue before adding new render jobs
    project.DeleteAllRenderJobs()
    logger.info("Cleared existing render queue")

    job_ids = []
    for frame in blue_markers:
        clip_name = get_clip_name_at_frame(timeline, frame)
        logger.debug(f"Processing frame {frame}, clip: {clip_name}")

        # Load render preset
        if not project.LoadRenderPreset(render_preset):
            error_msg = f"Failed to load render preset: {render_preset}. Does this render preset exist?"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Configure render settings
        project.SetRenderSettings(
            {
                "TargetDir": target_dir,
                "CustomName": f"{clip_name}_",
                "FormatWidth": int(timeline.GetSetting("timelineResolutionWidth")),
                "FormatHeight": int(timeline.GetSetting("timelineResolutionHeight")),
                "MarkIn": frame,
                "MarkOut": frame,
            }
        )

        # Add render job
        job_id = project.AddRenderJob()
        job_ids.append(job_id)
        logger.info(f"Added render job for frame {frame}, clip: {clip_name}")

    logger.info(f"Added {len(job_ids)} render jobs")
    return job_ids


def get_timeline_settings(timeline) -> Dict[str, str]:
    """Get current timeline settings.

    Parameters
    ----------
    timeline : object
        DaVinci Resolve timeline object

    Returns
    -------
    Dict[str, str]
        Dictionary of timeline settings
    """
    return {
        "useCustomSettings": timeline.GetSetting("useCustomSettings"),
        "colorScienceMode": timeline.GetSetting("colorScienceMode"),
        "colorAcesODT": timeline.GetSetting("colorAcesODT"),
        "colorAcesGamutCompressType": timeline.GetSetting("colorAcesGamutCompressType"),
        "colorSpaceOutput": timeline.GetSetting("colorSpaceOutput"),
        "colorSpaceOutputGamutLimit": timeline.GetSetting("colorSpaceOutputGamutLimit"),
        "colorSpaceTimeline": timeline.GetSetting("colorSpaceTimeline"),
        "inputDRT": timeline.GetSetting("inputDRT"),
        "outputDRT": timeline.GetSetting("outputDRT"),
        "useCATransform": timeline.GetSetting("useCATransform"),
    }


def configure_timeline_for_exr(
    project, timeline, original_settings: Dict[str, str]
) -> None:
    """Configure timeline settings for EXR rendering.

    Parameters
    ----------
    project : object
        DaVinci Resolve project object
    timeline : object
        DaVinci Resolve timeline object
    original_settings : Dict[str, str]
        Original timeline settings to reference

    Returns
    -------
    None
    """
    # Check if current timeline is under project level color management
    if original_settings["useCustomSettings"] == "0":
        logger.info("Timeline is using project settings, switching to custom settings")
        project_res_width = project.GetSetting("timelineResolutionWidth")
        project_res_height = project.GetSetting("timelineResolutionHeight")
        project_fps = project.GetSetting("timelineFrameRate")
        timeline.SetSetting("useCustomSettings", "1")
        timeline.SetSetting("timelineResolutionWidth", project_res_width)
        timeline.SetSetting("timelineResolutionHeight", project_res_height)
        timeline.SetSetting("timelineFrameRate", project_fps)

    # Configure ACES color management
    if original_settings["colorScienceMode"] != "acescct":
        logger.info("Setting color science mode to ACES CCT")
        timeline.SetSetting("colorScienceMode", "acescct")

    # Set additional settings for ACES
    logger.info("Configuring ACES settings for EXR output")
    timeline.SetSetting("colorAcesODT", "No Output Transform")
    timeline.SetSetting("colorAcesGamutCompressType", "None")


def wait_for_rendering(project, job_ids: List[str]) -> None:
    """Wait for rendering to complete.

    Parameters
    ----------
    project : object
        DaVinci Resolve project object
    job_ids : List[str]
        List of job IDs to monitor

    Returns
    -------
    None
    """
    logger.info("Starting rendering process")
    project.StartRendering(job_ids)

    # Monitor rendering progress
    while any(
        project.GetRenderJobStatus(job_id)["JobStatus"] == "Rendering"
        for job_id in job_ids
    ):
        time.sleep(1)  # Wait for rendering to complete

    logger.info("Rendering completed")


def restore_timeline_settings(timeline, original_settings: Dict[str, str]) -> None:
    """Restore original timeline settings.

    Parameters
    ----------
    timeline : object
        DaVinci Resolve timeline object
    original_settings : Dict[str, str]
        Original timeline settings to restore

    Returns
    -------
    None
    """
    logger.info("Restoring original timeline settings")

    # If timeline was using project settings, simply toggle back
    if original_settings["useCustomSettings"] == "0":
        timeline.SetSetting("useCustomSettings", "0")
        logger.info("Restored timeline to use project settings")
        return

    # Otherwise restore each setting individually
    for key, value in original_settings.items():
        if timeline.SetSetting(key, value):
            logger.debug(f'Restored "{key}" to "{value}"')
        else:
            logger.warning(f'Failed to restore "{key}"')


def main(target_dir: str, render_preset: str) -> None:
    """Render EXR frames from blue markers in the current timeline.

    Parameters
    ----------
    target_dir : str
        Target directory for rendered files
    render_preset : str
        Name of the render preset to use

    Returns
    -------
    None
    """
    # Initialize Resolve API
    _, _, project, current_timeline = initialize_resolve(
        need_current_timeline=True
    )

    logger.info(f"Processing timeline: {current_timeline.GetName()}")
    logger.info(f"Target directory: {target_dir}")
    logger.info(f"Render preset: {render_preset}")

    # Get blue markers
    start_frames = current_timeline.GetStartFrame()
    blue_markers = get_blue_markers(current_timeline, start_frames)
    logger.info(f"Found {len(blue_markers)} blue markers")

    if not blue_markers:
        logger.warning("No blue markers found in timeline. Nothing to render.")
        return

    # Save original settings to restore later
    original_settings = get_timeline_settings(current_timeline)

    try:
        # Configure timeline for EXR rendering
        configure_timeline_for_exr(project, current_timeline, original_settings)

        # Add render jobs
        job_ids = add_render_jobs(
            project, current_timeline, blue_markers, target_dir, render_preset
        )

        # Start rendering if jobs were added
        if job_ids:
            wait_for_rendering(project, job_ids)
        else:
            logger.warning("No render jobs were created")

    finally:
        # Always restore original settings, even if an error occurred
        restore_timeline_settings(current_timeline, original_settings)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render frames as EXR from blue markers in DaVinci Resolve."
    )
    parser.add_argument("target_dir", help="The target directory for rendered exrs.")
    parser.add_argument(
        "render_preset", help="The name of the EXR render preset to use."
    )
    args = parser.parse_args()

    main(args.target_dir, args.render_preset)