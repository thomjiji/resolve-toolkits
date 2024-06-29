import argparse
from dri import Resolve
from dftt_timecode import DfttTimecode


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

        project.LoadRenderPreset(render_preset)
        project.SetRenderSettings(
            {
                "TargetDir": target_dir,
                "CustomName": f"{clip_name}_",
                "FormatWidth": timeline.GetSetting("timelineResolutionWidth"),
                "FormatHeight": timeline.GetSetting("timelineResolutionHeight"),
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
    # fps = float(
    #     current_timeline.GetSetting("timelineFrameRate").get("timelineFrameRate")
    # )
    timeline_fps_setting = current_timeline.GetSetting("timelineFrameRate")
    if isinstance(timeline_fps_setting, float):
        fps = timeline_fps_setting
    else:
        raise TypeError(
            f"Unexpected type for timelineFrameRate: {type(timeline_fps_setting)}"
        )

    start_timecode = current_timeline.GetStartTimecode()
    start_frames = convert_smpte_to_frames(start_timecode, fps)
    blue_markers = get_blue_markers(current_timeline, start_frames)

    job_ids = add_render_jobs(
        project, current_timeline, blue_markers, target_dir, render_preset
    )

    if job_ids:
        project.StartRendering(job_ids)


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
