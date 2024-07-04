import argparse
import time

from dftt_timecode import DfttTimecode
from dri import Resolve


def convert_smpte_to_frames(timecode, fps):
    timecode_obj = DfttTimecode(timecode, "auto", fps, drop_frame=False, strict=True)
    return timecode_obj.timecode_output("frame")


def get_blue_markers(timeline, start_frames):
    markers = timeline.GetMarkers()
    blue_markers = {
        frame + int(start_frames): info
        for frame, info in markers.items()
        if info["color"] == "Blue"
    }
    return blue_markers


def get_clip_name_at_frame(timeline, frame):
    clips = timeline.GetItemListInTrack("Video", 1)
    for clip in clips:
        if clip.GetStart() <= frame <= clip.GetEnd():
            return clip.GetName()
    return "unknown_clip"


def add_render_jobs(project, timeline, blue_markers, target_dir, render_preset):
    # Clear the render queue before adding new render jobs
    project.DeleteAllRenderJobs()

    job_ids = []
    for frame in blue_markers:
        clip_name = get_clip_name_at_frame(timeline, frame)

        # TODO: move this check upstream, otherwise the render preset doesn't load on, but the timeline params are modified.
        if not project.LoadRenderPreset(render_preset):
            raise ValueError(
                f"Failed to load render preset: {render_preset}. Is this render preset exist?"
            )
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
        job_id = project.AddRenderJob()
        job_ids.append(job_id)
    return job_ids


def main(target_dir, render_preset):
    resolve = Resolve.resolve_init()
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    current_timeline = project.GetCurrentTimeline()

    start_frames = current_timeline.GetStartFrame()
    blue_markers = get_blue_markers(current_timeline, start_frames)

    # Remember current timeline settings
    original_settings = {
        "colorScienceMode": current_timeline.GetSetting("colorScienceMode"),
        "colorAcesODT": current_timeline.GetSetting("colorAcesODT"),
        "colorAcesGamutCompressType": current_timeline.GetSetting(
            "colorAcesGamutCompressType"
        ),
        "colorSpaceOutput": current_timeline.GetSetting("colorSpaceOutput"),
        "colorSpaceOutputGamutLimit": current_timeline.GetSetting(
            "colorSpaceOutputGamutLimit"
        ),
        "colorSpaceTimeline": current_timeline.GetSetting("colorSpaceTimeline"),
        "inputDRT": current_timeline.GetSetting("inputDRT"),
        "outputDRT": current_timeline.GetSetting("outputDRT"),
        "useCATransform": current_timeline.GetSetting("useCATransform"),
    }

    # Check if current timeline is color managed by ACES
    if original_settings["colorScienceMode"] != "acescct":
        current_timeline.SetSetting("colorScienceMode", "acescct")

    # Set additional settings for ACES
    current_timeline.SetSetting("colorAcesODT", "No Output Transform")
    current_timeline.SetSetting("colorAcesGamutCompressType", "None")

    job_ids = add_render_jobs(
        project, current_timeline, blue_markers, target_dir, render_preset
    )

    if job_ids:
        project.StartRendering(job_ids)
        while any(
            project.GetRenderJobStatus(job_id)["JobStatus"] == "Rendering"
            for job_id in job_ids
        ):
            time.sleep(1)  # Wait for rendering to complete

    for key, value in original_settings.items():
        if current_timeline.SetSetting(key, value):
            print(f'Restored "{key}" to "{value}".')
        else:
            print(f'Failed to restore "{key}".')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render frames as EXR from blue markers in DaVinci Resolve."
    )
    parser.add_argument("target_dir", help="The target directory for rendered files.")
    parser.add_argument(
        "render_preset", help="The name of the EXR render preset to use."
    )
    args = parser.parse_args()

    main(args.target_dir, args.render_preset)
