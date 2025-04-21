import argparse
import logging

from dri import Resolve

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

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


def initialize_resolve() -> tuple:
    """Initialize DaVinci Resolve API and get common objects.

    Returns
    -------
    tuple
        Tuple containing (resolve, project_manager, project, media_storage, 
        media_pool, root_folder, current_timeline)
    """
    resolve = Resolve.resolve_init()
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    media_storage = resolve.GetMediaStorage()
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    current_timeline = project.GetCurrentTimeline()

    logger.info(f"Initialized Resolve with project: {project.GetName()}")
    logger.info(f"Current timeline: {current_timeline.GetName()}")

    return (
        resolve, 
        project_manager, 
        project, 
        media_storage, 
        media_pool, 
        root_folder, 
        current_timeline
    )


def capitalized_color(color_str: str) -> str:
    """Validate and capitalize color input.

    Parameters
    ----------
    color_str : str
        Input color string (case-insensitive)

    Returns
    -------
    str
        Capitalized color name from VALID_COLORS

    Raises
    ------
    argparse.ArgumentTypeError
        If the input color is not in VALID_COLORS
    """
    lower_color = color_str.lower()
    if lower_color in VALID_COLORS_MAP:
        return VALID_COLORS_MAP[lower_color]  # Return the capitalized version
    raise argparse.ArgumentTypeError(
        f"invalid color value: '{color_str}'. Choose from: {', '.join(VALID_COLORS)}"
    )


def main(selected_color: str) -> None:
    """Process timeline markers of specified color and grab stills.

    Parameters
    ----------
    selected_color : str
        Color of markers to process (or 'All' for all markers)

    Returns
    -------
    None
    """
    # Initialize Resolve API
    _, _, _, _, _, _, current_timeline = initialize_resolve()

    # Get start frame of current timeline
    start_frame = current_timeline.GetStartFrame()
    logger.info(f"Timeline start frame: {start_frame}")

    # Get all markers
    markers = current_timeline.GetMarkers()
    logger.debug(f"Found markers: {markers}")

    if not markers:
        logger.warning("No markers found in the timeline")
        return

    # Iterate through markers, filter by the specified color, calculate the actual frame
    # position, and grab a still
    processed_markers = 0
    for timecode, marker_data in markers.items():
        if selected_color == "All" or marker_data["color"] == selected_color:
            # Calculate the actual "Record Frame" in the DaVinci Resolve UI
            record_frame = timecode + start_frame
            logger.info(
                f"Setting timecode to {record_frame} for '{marker_data['color']}' marker "
                f"'{marker_data['name']}'"
            )

            # Set timecode and grab still
            current_timeline.SetCurrentTimecode(str(record_frame))
            still = current_timeline.GrabStill()

            if still:
                logger.info(
                    f"Grabbed still for '{marker_data['color']}' marker "
                    f"'{marker_data['name']}' at timecode {record_frame}"
                )
                processed_markers += 1
            else:
                logger.warning(
                    f"Failed to grab still for '{marker_data['color']}' marker "
                    f"'{marker_data['name']}' at timecode {record_frame}"
                )

    logger.info(f"Finished processing. Grabbed {processed_markers} stills.")


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
    parser.add_argument(
        "--debug", "-d", 
        action="store_true", 
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Set logging level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)

    logger.info(f"Starting grab_markers with color: {args.color}")
    main(args.color)