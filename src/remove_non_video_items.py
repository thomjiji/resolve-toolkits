from dri import Resolve


def delete_non_video_clips(folder):
    items_to_be_deleted = []

    # Check clips in the current folder
    for clip in folder.GetClipList():
        if clip.GetClipProperty("Type") not in ("Video + Audio", "Video"):
            items_to_be_deleted.append(clip)

    # Delete the identified clips
    if items_to_be_deleted:
        media_pool.DeleteClips(items_to_be_deleted)

    # Recursively process subfolders
    for subfolder in folder.GetSubFolderList():
        delete_non_video_clips(subfolder)


if __name__ == "__main__":
    resolve = Resolve.resolve_init()
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()

    delete_non_video_clips(root_folder)
