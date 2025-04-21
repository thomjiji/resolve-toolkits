import unittest
import tempfile
import shutil
from pathlib import Path

from extract_metadata import extract_metadata, process_clip_directory


class TestMetadataExtraction(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.test_mp4 = Path(self.test_dir) / "test.MP4"

        # Create a dummy MP4 file with some metadata
        with open(self.test_mp4, "w") as f:
            f.write("Dummy MP4 content")  # This is just for testing file existence

        # Mock MediaInfo.parse to return test data
        self.original_parse = None
        try:
            from pymediainfo import MediaInfo

            self.original_parse = MediaInfo.parse
            MediaInfo.parse = self.mock_parse
        except ImportError:
            pass

    def tearDown(self):
        """Clean up test environment."""
        # Restore original MediaInfo.parse
        if self.original_parse:
            from pymediainfo import MediaInfo

            MediaInfo.parse = self.original_parse

        # Remove temporary directory
        shutil.rmtree(self.test_dir)

    def mock_parse(self, file_path):
        """Mock MediaInfo.parse to return test data."""

        class MockTrack:
            def __init__(self):
                self.track_type = "Other"
                self.whitebalance_firstframe = "6500K"
                self.exposureindexofphotometer_firstframe = "800"

        class MockMediaInfo:
            def __init__(self):
                self.tracks = [MockTrack()]

        return MockMediaInfo()

    def test_extract_metadata(self):
        """Test metadata extraction from a single file."""
        metadata = extract_metadata(str(self.test_mp4))

        self.assertEqual(metadata["Filename"], "test.MP4")
        self.assertEqual(metadata["WhiteBalance_FirstFrame"], "6500K")
        self.assertEqual(metadata["ExposureIndexofPhotoMeter_FirstFrame"], "800")
        self.assertIn("ProcessingTime", metadata)

    def test_process_clip_directory(self):
        """Test processing a directory of MP4 files."""
        # Create output directory
        output_dir = Path(self.test_dir) / "output"
        output_dir.mkdir()

        # Process the directory
        process_clip_directory(str(self.test_dir))

        # Check if CSV file was created
        csv_files = list(Path(self.test_dir).glob("metadata_*.csv"))
        self.assertTrue(len(csv_files) > 0, "No CSV file was created")

    def test_nonexistent_directory(self):
        """Test handling of nonexistent directory."""
        with self.assertLogs(level="ERROR") as log:
            process_clip_directory("/nonexistent/path")
            self.assertIn("Directory /nonexistent/path does not exist", log.output[0])

    def test_no_mp4_files(self):
        """Test handling of directory with no MP4 files."""
        # Create a directory with no MP4 files
        empty_dir = Path(self.test_dir) / "empty"
        empty_dir.mkdir()

        with self.assertLogs(level="WARNING") as log:
            process_clip_directory(str(empty_dir))
            self.assertIn(
                "No MP4 files were found or no metadata was extracted", log.output[0]
            )


if __name__ == "__main__":
    unittest.main()