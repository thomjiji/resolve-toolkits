from dri import Resolve

resolve = Resolve.resolve_init()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()
current_timeline = project.GetCurrentTimeline()

items_to_be_deleted = []
for clip in media_pool.GetCurrentFolder().GetClipList():
    if (
        clip.GetClipProperty("Type") != "Video + Audio"
        and clip.GetClipProperty("Type") != "Video"
    ):
        items_to_be_deleted.append(clip)

if __name__ == "__main__":
    media_pool.DeleteClips(items_to_be_deleted)
