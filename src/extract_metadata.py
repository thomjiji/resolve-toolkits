import argparse
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from pymediainfo import MediaInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Configuration for metadata fields to extract
METADATA_CONFIG = {
    "WhiteBalance_FirstFrame": {
        "track_type": "Other",
        "attribute": "whitebalance_firstframe",
        "description": "First frame white balance value",
    },
    "ExposureIndexofPhotoMeter_FirstFrame": {
        "track_type": "Other",
        "attribute": "exposureindexofphotometer_firstframe",
        "description": "First frame exposure index value",
    },
    # Add new metadata fields here following the same structure
    # Example:
    # "NewField": {
    #     "track_type": "Other",
    #     "attribute": "new_field_attribute",
    #     "description": "Description of the new field"
    # }
}


def get_metadata_value(track, attribute: str) -> Optional[str]:
    """Safely get metadata value from track if it exists.

    Parameters
    ----------
    track : MediaInfo track object
        The track to extract metadata from
    attribute : str
        The attribute name to get

    Returns
    -------
    Optional[str]
        The attribute value if it exists, None otherwise
    """
    if hasattr(track, attribute):
        return getattr(track, attribute)
    return None


def extract_metadata(file_path: str) -> Dict[str, str]:
    """Extract metadata from an MP4 file.

    Parameters
    ----------
    file_path : str
        Path to the MP4 file.

    Returns
    -------
    Dict[str, str]
        Dictionary containing extracted metadata with keys defined in METADATA_CONFIG
    """
    media_info = MediaInfo.parse(file_path)

    # Initialize metadata dictionary with default values
    metadata = {
        "Filename": Path(file_path).name,
        "ProcessingTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Add empty values for all configured metadata fields
    for field in METADATA_CONFIG:
        metadata[field] = ""

    # Extract metadata from tracks
    for track in media_info.tracks:
        for field, config in METADATA_CONFIG.items():
            if track.track_type == config["track_type"]:
                value = get_metadata_value(track, config["attribute"])
                if value is not None:
                    metadata[field] = value

    return metadata


def process_clip_directory(clip_dir: str) -> None:
    """Process all MP4 files in a directory and save metadata to a CSV file.

    Scans the specified directory for files ending with '.MP4', extracts
    metadata from each file using `extract_metadata`, and writes the
    collected metadata to a timestamped CSV file in the current working
    directory.

    Parameters
    ----------
    clip_dir : str
        Path to the directory containing the MP4 files.
    """
    clip_path = Path(clip_dir)

    if not clip_path.exists():
        logger.error(f"Directory {clip_dir} does not exist")
        return

    # Initialize list to store all metadata
    all_metadata = []

    # Process only MP4 files in the directory
    for file_path in clip_path.glob("*.MP4"):
        logger.info(f"Processing file: {file_path.name}")
        try:
            metadata = extract_metadata(str(file_path))
            all_metadata.append(metadata)
            logger.debug(f"Successfully extracted metadata from {file_path.name}")
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {str(e)}")

    # Save to CSV
    if all_metadata:
        output_file = f"metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        fieldnames = all_metadata[0].keys()

        try:
            with open(output_file, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_metadata)

            logger.info(f"Successfully saved metadata to {output_file}")
            logger.info(f"Processed {len(all_metadata)} files")
        except Exception as e:
            logger.error(f"Error saving CSV file: {str(e)}")
    else:
        logger.warning("No MP4 files were found or no metadata was extracted.")


def main() -> None:
    """Parse command-line arguments and initiate metadata extraction."""
    parser = argparse.ArgumentParser(description="Extract metadata from MP4 files.")
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to the directory containing MP4 files",
    )
    parser.add_argument(
        "--output", "-o", type=str, help="Custom output CSV filename (optional)"
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )

    args = parser.parse_args()

    # Set logging level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)

    process_clip_directory(args.input_path)


if __name__ == "__main__":
    main()
