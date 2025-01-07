from dri import Resolve

resolve = Resolve.resolve_init()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()
current_timeline = project.GetCurrentTimeline()

# print(project.GetUniqueId())

for project_name in project_manager.GetProjectListInCurrentFolder():
    project = project_manager.LoadProject(project_name)
    project_id = project.GetUniqueId()
    print(f"Project '{project_name}' ID: {project_id}")
    project_manager.CloseProject(project)
