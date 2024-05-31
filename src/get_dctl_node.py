from pprint import pprint

from dri.resolve import Resolve

resolve = Resolve.resolve_init()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()
current_timeline = project.GetCurrentTimeline()

# Iterate through each clip in the video track 1
for i, timeline_item in enumerate(current_timeline.GetItemListInTrack("video", 1)):
    node_graph = timeline_item.GetNodeGraph()
    num_of_nodes = node_graph.GetNumNodes()

    # Check each node for the presence of the "DCTL" tool
    for node_index in range(1, num_of_nodes + 1):
        tools_in_node: list[str] = node_graph.GetToolsInNode(node_index)

        # Check if tools_in_node is None
        if tools_in_node is None:
            # print(f"Node {node_index} in clip {i+1} has no tools.")
            continue

        # # Use len() to count the number of items in tools_in_node
        # tool_count = len(tools_in_node)

        # print(f"Number of tools in node {node_index}: {tool_count}")

        # Check if "OFX: DCTL" tool is in the current node
        for tool in tools_in_node:
            if "OFX: DCTL" in tool:
                pprint(f"Clip {i+1} has DCTL tool used in node {node_index}")
