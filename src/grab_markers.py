import argparse
import logging

from dri import Resolve

resolve = Resolve.resolve_init()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()
current_timeline = project.GetCurrentTimeline()

# Define the list of valid colors (capitalized)
VALID_COLORS = [
    "All",
    "Blue",
    "Cyan",
    "Green",
    "Yellow",
    "Red",
    "Pink",
    "Purple",
    "Fuchsia",
    "Rose",
    "Lavender",
    "Sky",
    "Mint",
    "Lemon",
    "Sand",
    "Cocoa",
    "Cream",
]
# Create a mapping from lowercase color name to capitalized color name
VALID_COLORS_MAP = {c.lower(): c for c in VALID_COLORS}


def capitalized_color(color_str: str) -> str:
    """
    Argparse type function to validate and capitalize color input.
    Allows case-insensitive input but returns the canonical capitalized form.
    """
    lower_color = color_str.lower()
    if lower_color in VALID_COLORS_MAP:
        return VALID_COLORS_MAP[lower_color]  # Return the capitalized version
    raise argparse.ArgumentTypeError(
        f"invalid color value: '{color_str}'. Choose from: {', '.join(VALID_COLORS)}"
    )


def main(selected_color: str):
    # get start frame of crurent timeline
    start_frame = current_timeline.GetStartFrame()
    logging.info(f"Timeline start frame: {start_frame}")

    # get all markers
    markers = current_timeline.GetMarkers()
    logging.debug(f"Found markers: {markers}")

    # iterate through markers, filter by the specified color, calculate the actual frame
    # position, and grab a still
    processed_markers = 0
    for timecode, marker_data in markers.items():
        if selected_color == "All" or marker_data["color"] == selected_color:
            # calculate the actual "Record Frame" in the DaVinci Resolve UI
            record_frame = timecode + start_frame
            logging.info(
                f"Setting timecode to {record_frame} for '{marker_data['color']}' marker "
                f"'{marker_data['name']}'"
            )

            # set timecode and grab still
            current_timeline.SetCurrentTimecode(str(record_frame))
            still = current_timeline.GrabStill()

            if still:
                logging.info(
                    f"Grabbed still for '{marker_data['color']}' marker "
                    f"'{marker_data['name']}' at timecode {record_frame}"
                )
                processed_markers += 1
            else:
                logging.warning(
                    f"Failed to grab still for '{marker_data['color']}' marker "
                    f"'{marker_data['name']}' at timecode {record_frame}"
                )
    logging.info(f"Finished processing. Grabbed {processed_markers} stills.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Grab stills for markers of a specific color from the current timeline."
    )
    parser.add_argument(
        "--color",
        type=capitalized_color,
        default="Blue",
        help=(
            "Specify the color of the markers to grab (case-insensitive). "
            f"Use 'All' to grab all markers. Choices: {', '.join(VALID_COLORS)}"
        ),
    )
    args = parser.parse_args()

    selected_color = args.color

    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    main(selected_color)
