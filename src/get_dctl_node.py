import argparse
from tabulate import tabulate
from dri.resolve import Resolve


def check_clips_for_dctl():
    resolve = Resolve.resolve_init()
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    media_storage = resolve.GetMediaStorage()
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    current_timeline = project.GetCurrentTimeline()

    clips_data = []

    # Iterate through each clip in the video track 1
    for i, timeline_item in enumerate(current_timeline.GetItemListInTrack("video", 1)):
        node_graph = timeline_item.GetNodeGraph()
        num_of_nodes = node_graph.GetNumNodes()

        # Check each node for the presence of the "DCTL" tool
        for node_index in range(1, num_of_nodes + 1):
            tools_in_node = node_graph.GetToolsInNode(node_index)

            if tools_in_node is None:
                continue

            # Check if "OFX: DCTL" tool is in the current node
            for tool in tools_in_node:
                if "OFX: DCTL" in tool:
                    clips_data.append([i + 1, timeline_item.GetName(), node_index])

    if clips_data:
        print(
            f'The following clips in timeline "{current_timeline.GetName()}" have DCTL tool used:\n\n'
            f'{tabulate(clips_data, headers=["Clip Number", "Clip Name", "Node Index"], tablefmt="simple")}'
        )
    else:
        print("No clips with DCTL tool found in the specified nodes.")


def main():
    parser = argparse.ArgumentParser(
        description="Script to check clips in track 2 of current timeline for DCTL tool usage."
    )
    args = parser.parse_args()
    check_clips_for_dctl()


if __name__ == "__main__":
    main()
