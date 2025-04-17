import argparse
import csv
import logging
from datetime import datetime
from pathlib import Path

from pymediainfo import MediaInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def extract_metadata(file_path: str) -> dict:
    """Extract metadata from an MP4 file.

    Parameters
    ----------
    file_path : str
        Path to the MP4 file.

    Returns
    -------
    dict
        Dictionary containing extracted metadata with the following keys:
        - Filename: Name of the file.
        - WhiteBalance_FirstFrame: First frame white balance value.
        - ExposureIndexofPhotoMeter_FirstFrame: First frame exposure index value.
        - ProcessingTime: Timestamp when metadata was processed.
    """
    media_info = MediaInfo.parse(file_path)

    # Initialize metadata dictionary
    metadata = {
        "Filename": Path(file_path).name,
        "WhiteBalance_FirstFrame": "",
        "ExposureIndexofPhotoMeter_FirstFrame": "",
        "ProcessingTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Extract specific metadata fields from video tracks
    for track in media_info.tracks:
        if track.track_type == "Other":
            # Get WhiteBalance_FirstFrame
            if hasattr(track, "whitebalance_firstframe"):
                metadata["WhiteBalance_FirstFrame"] = track.whitebalance_firstframe

            # Get ExposureIndexofPhotoMeter_FirstFrame
            if hasattr(track, "exposureindexofphotometer_firstframe"):
                metadata["ExposureIndexofPhotoMeter_FirstFrame"] = (
                    track.exposureindexofphotometer_firstframe
                )

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
        "input_path", type=str, help="Path to the directory containing MP4 files"
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
