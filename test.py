from python_get_resolve import GetResolve

resolve = GetResolve()

project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
sub_folder_List = media_storage.GetSubFolderList("/Volumes/DIT-2T#7/白举纲MV记录0808")

media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()
media_pool.AddSubFolder(root_folder, "GH5#1")
media_pool.AddSubFolder(root_folder, "GH5#2")

for count, sub_folder in enumerate(root_folder.GetSubFolderList()):
    media_pool.SetCurrentFolder(sub_folder)
    media_storage.AddItemListToMediaPool(sub_folder_List[count])