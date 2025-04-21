import argparse

from dri import Resolve
from tabulate import tabulate


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

        # Keep track of DCTL nodes for each clip
        dctl_nodes = []

        # Check each node for the presence of the "DCTL" tool
        for node_index in range(1, num_of_nodes + 1):
            tools_in_node = node_graph.GetToolsInNode(node_index)
            if tools_in_node is None:
                continue
            # Check if "OFX: DCTL" tool is in the current node
            if any("OFX: DCTL" in tool for tool in tools_in_node):
                node_label = node_graph.GetNodeLabel(node_index)
                dctl_nodes.append((node_index, node_label))

        # Sort the DCTL nodes by node index
        dctl_nodes.sort()

        # Add the clip data with sorted DCTL nodes
        if dctl_nodes:
            node_indices = [node_index for node_index, _ in dctl_nodes]
            node_labels = [node_label for _, node_label in dctl_nodes]
            clips_data.append(
                [i + 1, timeline_item.GetName(), node_indices, node_labels]
            )

    if clips_data:
        print(
            f'The following clips in timeline "{current_timeline.GetName()}" have DCTL tool used:\n\n'
            f'{tabulate(clips_data, headers=["Clip Number", "Clip Name", "Node Index", "Node Label"], tablefmt="simple")}'
        )
    else:
        print(
            f'No clips with DCTL tool found in timeline "{current_timeline.GetName()}".'
        )


def main():
    parser = argparse.ArgumentParser(
        description="Script to check clips in track 1 of current timeline for DCTL tool usage."
    )
    args = parser.parse_args()
    check_clips_for_dctl()


if __name__ == "__main__":
    main()
