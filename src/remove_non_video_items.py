from dri import Resolve


def delete_non_video_clips(folder):
    items_to_be_deleted = []

    for clip in folder.GetClipList():
        if clip.GetClipProperty("Type") not in ("Video + Audio", "Video"):
            items_to_be_deleted.append(clip)

    if items_to_be_deleted:
        print(f"Deleting clips in {folder.GetName()}")
        media_pool.DeleteClips(items_to_be_deleted)

    for subfolder in folder.GetSubFolderList():
        delete_non_video_clips(subfolder)


def delete_empty_subfolders(folder):
    subfolders = folder.GetSubFolderList()

    for subfolder in subfolders:
        delete_empty_subfolders(subfolder)

    if not folder.GetSubFolderList() and not folder.GetClipList():
        print(f"Deleting folder {folder.GetName()}")
        media_pool.DeleteFolders([folder])


if __name__ == "__main__":
    resolve = Resolve.resolve_init()
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()

    delete_non_video_clips(root_folder)
    delete_empty_subfolders(root_folder)
