"""
When importing PowerGrade from another Resolve instance, the label of stills will be
appended a "_1", this script is used to remove it all for every single powergrade
imported.
"""

from dri import Resolve

resolve = Resolve.resolve_init()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()
current_timeline = project.GetCurrentTimeline()

galley = project.GetGallery()
current_gallery_still_ablum = galley.GetCurrentStillAlbum()

for gallery_still_album in galley.GetGalleryStillAlbums():
    for still in gallery_still_album.GetStills():
        label = gallery_still_album.GetLabel(still)
        print(label)
        if label.endswith("_1"):
            gallery_still_album.SetLabel(still, label[:-2])
