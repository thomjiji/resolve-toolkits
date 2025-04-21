import sys

from pymediainfo import MediaInfo


def print_all_metadata(file_path):
    """
    Print all available metadata from a media file.
    """
    media_info = MediaInfo.parse(file_path)

    print(f"\nProcessing file: {file_path}")
    print("=" * 50)

    for track in media_info.tracks:
        print(f"\nTrack Type: {track.track_type}")
        print("-" * 30)

        # Print all available attributes
        for attr in dir(track):
            if not attr.startswith("_"):  # Skip private attributes
                try:
                    value = getattr(track, attr)
                    if value:  # Only print non-empty values
                        print(f"{attr}: {value}")
                except:
                    pass


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_metadata.py <path_to_mp4_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    print_all_metadata(file_path)
