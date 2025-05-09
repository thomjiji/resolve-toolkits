import argparse
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Union

# --- Module-level Constants ---
# Default directories and file names
DEFAULT_UNGRADED_DIR: str = "ungraded"
DEFAULT_GRADED_DIR: str = "graded"
DEFAULT_OUTPUT_PDF: str = "comparison_simplified.pdf"

# Input image extensions to look for (case-insensitive JPG/JPEG only)
INPUT_IMAGE_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg")

# Temporary file settings (always lossless to preserve color info)
# Temporary files will be created directly in the Current Working Directory (CWD).
TEMP_FILE_PREFIX: str = (
    "__temp_comparison_page_"  # A distinctive prefix for temporary files
)
TEMP_IMAGE_FORMAT: str = "TIFF"  # TIFF is a lossless format for intermediates
TEMP_IMAGE_EXTENSION: str = "tif"  # File extension for temporary images


# --- Logging Configuration ---
def setup_logging(log_level: str = "INFO") -> None:
    """
    Configures the logging module for the script.

    Parameters
    ----------
    log_level : str, optional
        The desired logging level (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
        Defaults to "INFO".
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.info(f"Logging level set to {log_level.upper()}")


# --- Utility Functions ---
def check_magick() -> bool:
    """
    Checks if the 'magick' command is available in the system's PATH.

    Returns
    -------
    bool
        True if 'magick' is found and executable, False otherwise.

    Raises
    ------
    SystemExit
        If 'magick' is not found, the script exits.
    """
    try:
        logging.debug("Checking for 'magick' command availability...")
        # Use a simple command to check if magick is callable
        subprocess.run(
            ["magick", "-version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logging.debug("'magick' command found.")
        return True
    except FileNotFoundError:
        logging.error(
            "Error: 'magick' command not found. "
            "Please ensure ImageMagick is installed and added to your system's PATH."
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logging.error(
            f"Error checking 'magick' version: Command exited with code {e.returncode}. "
            f"Stdout: {e.stdout.decode().strip()} | Stderr: {e.stderr.decode().strip()}"
        )
        sys.exit(1)
    except Exception as e:
        logging.exception(f"An unexpected error occurred while checking 'magick': {e}")
        sys.exit(1)


# --- Main Logic ---
def process_images_to_pdf(
    ungraded_dir: Path,
    graded_dir: Path,
    output_pdf: Path,
) -> None:
    """
    Processes image pairs from two directories (assumed JPG/JPEG), combines them side-by-side
    using 'magick' command, and then creates a multi-page PDF.
    Temporary files are created directly in the Current Working Directory (CWD)
    using a specific prefix and lossless format to preserve color information.

    Parameters
    ----------
    ungraded_dir : Path
        Path to the directory containing ungraded (original) JPG/JPEG images.
    graded_dir : Path
        Path to the directory containing graded (color-corrected) JPG/JPEG images.
    output_pdf : Path
        Path for the output PDF file.

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        If essential directories are not found, or if ImageMagick operations fail.
    """
    logging.info("Starting image comparison PDF generation.")

    # 1. Validate input directories
    if not ungraded_dir.is_dir():
        logging.error(f"Error: Ungraded images directory not found: '{ungraded_dir}'")
        sys.exit(1)
    if not graded_dir.is_dir():
        logging.error(f"Error: Graded images directory not found: '{graded_dir}'")
        sys.exit(1)

    # 2. Get and sort filenames (filtering specifically for JPG/JPEG)
    try:
        # Get all files in the ungraded directory, filter by JPG/JPEG extension (case-insensitive),
        # and sort them naturally.
        filenames: List[str] = sorted(
            [
                f
                for f in os.listdir(ungraded_dir)
                if Path(f).suffix.lower() in INPUT_IMAGE_EXTENSIONS
            ]
        )

        if not filenames:
            logging.warning(
                f"No JPG/JPEG image files found in '{ungraded_dir}'. "
                "Ensure your images are in JPG/JPEG format. No PDF will be generated."
            )
            return
    except OSError as e:
        logging.exception(f"Error reading files from directory '{ungraded_dir}': {e}")
        sys.exit(1)

    combined_image_paths: List[Path] = []
    logging.info(
        f"Found {len(filenames)} JPG/JPEG files in '{ungraded_dir}'. Processing image pairs..."
    )

    # Get the current working directory for temporary files
    cwd: Path = Path.cwd()

    # 3. Process each image pair
    for i, filename in enumerate(filenames):
        ungraded_path: Path = ungraded_dir / filename
        graded_path: Path = graded_dir / filename

        # Check for existence of both files
        if not ungraded_path.is_file():
            logging.warning(f"Skipping: Ungraded file not found: '{ungraded_path}'")
            continue
        if not graded_path.is_file():
            # Note: We check the graded file with the *same* filename.
            logging.warning(
                f"Skipping: Graded file not found corresponding to '{ungraded_path.name}': '{graded_path}'."
            )
            continue

        logging.info(f"Processing pair {i + 1}/{len(filenames)}: '{filename}'")

        # Define temporary combined image path in CWD with a distinctive prefix
        base_filename_no_ext: str = ungraded_path.stem
        temp_combined_filename: str = (
            f"{TEMP_FILE_PREFIX}{i:04d}_{base_filename_no_ext}.{TEMP_IMAGE_EXTENSION}"
        )
        temp_combined_path: Path = cwd / temp_combined_filename

        # Build 'magick' command for horizontal append
        # Using +append: Images are stacked horizontally. If heights differ, ImageMagick pads.
        # This approach aims to preserve original pixel data as much as possible by
        # avoiding resizing or resampling which could alter color information.
        magick_append_command: List[str] = [
            "magick",
            str(ungraded_path),  # Convert Path to string for subprocess
            str(graded_path),  # Convert Path to string for subprocess
            "+append",  # Horizontal append
            str(temp_combined_path),  # Output path (lossless TIFF)
        ]

        try:
            logging.debug(
                f"Executing append command: {' '.join(magick_append_command)}"
            )
            process: subprocess.CompletedProcess = subprocess.run(
                magick_append_command, check=True, capture_output=True, text=True
            )
            logging.debug(f"Magick append stdout: {process.stdout.strip()}")
            logging.debug(f"Magick append stderr: {process.stderr.strip()}")
            combined_image_paths.append(temp_combined_path)
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Error: Failed to append images for '{filename}'. "
                f"Magick command exited with code {e.returncode}. "
                f"Stdout: {e.stdout.strip()} | Stderr: {e.stderr.strip()}"
            )
            # If appending fails for one pair, log the error and continue with the next pair.
            continue
        except FileNotFoundError:
            # This case should ideally be caught by check_magick() early on,
            # but included here as a safeguard.
            logging.error(
                f"Error: 'magick' command not found during append for '{filename}'. Exiting."
            )
            sys.exit(1)
        except Exception as e:
            logging.exception(
                f"An unexpected error occurred during image append for '{filename}': {e}"
            )
            # Log the exception and continue with the next pair.
            continue

    # 4. Combine all temporary images into a PDF
    logging.info(
        f"All image pairs processed ({len(combined_image_paths)} pairs). "
        f"Generating final PDF: '{output_pdf}'..."
    )

    if not combined_image_paths:
        logging.warning(
            "No combined images were successfully created. No PDF will be generated."
        )
        return

    # Build 'magick' command for PDF creation
    # Images are listed as input, and ImageMagick creates a multi-page PDF.
    magick_pdf_command: List[str] = [
        "magick",
        *[str(p) for p in combined_image_paths],  # Convert Path objects to strings
        str(output_pdf),  # Output PDF path
    ]

    pdf_generation_successful: bool = False
    try:
        logging.debug(
            f"Executing PDF generation command: {' '.join(magick_pdf_command)}"
        )
        process: subprocess.CompletedProcess = subprocess.run(
            magick_pdf_command, check=True, capture_output=True, text=True
        )
        logging.info(f"PDF '{output_pdf}' successfully generated.")
        logging.debug(f"Magick PDF stdout: {process.stdout.strip()}")
        logging.debug(f"Magick PDF stderr: {process.stderr.strip()}")
        pdf_generation_successful = True
    except subprocess.CalledProcessError as e:
        logging.error(
            f"Error: Failed to generate PDF '{output_pdf}'. "
            f"Magick command exited with code {e.returncode}. "
            f"Stdout: {e.stdout.strip()} | Stderr: {e.stderr.strip()}"
        )
    except FileNotFoundError:
        # This case should ideally be caught by check_magick() early on.
        logging.error(
            f"Error: 'magick' command not found during PDF generation. Exiting."
        )
        sys.exit(1)
    except Exception as e:
        logging.exception(f"An unexpected error occurred during PDF generation: {e}")
    finally:
        # 5. Clean up temporary files from CWD
        if (
            combined_image_paths
        ):  # Only attempt cleanup if files were intended to be generated
            if pdf_generation_successful:
                logging.info("Cleaning up temporary files from CWD...")
                for temp_file_path in combined_image_paths:
                    try:
                        # Only delete files that actually exist and match the expected pattern
                        if (
                            temp_file_path.is_file()
                            and temp_file_path.name.startswith(TEMP_FILE_PREFIX)
                            and temp_file_path.suffix.lower()
                            == f".{TEMP_IMAGE_EXTENSION}".lower()
                        ):
                            temp_file_path.unlink()  # Delete the file
                            logging.debug(f"Deleted temporary file: {temp_file_path}")
                        elif temp_file_path.is_file():
                            # Log if a file in the list exists but doesn't match the pattern (shouldn't happen with this logic)
                            logging.warning(
                                f"Temporary file '{temp_file_path}' found but doesn't match cleanup pattern. Skipping deletion."
                            )
                        else:
                            # Log if a file in the list wasn't found (might happen if a previous step failed)
                            logging.debug(
                                f"Temporary file '{temp_file_path}' not found for deletion."
                            )
                    except OSError as e:
                        logging.error(
                            f"Error deleting temporary file '{temp_file_path}': {e}"
                        )
                logging.info("Temporary files cleaned.")
            else:
                # If PDF generation failed, temporary files are intentionally left for debugging.
                logging.warning(
                    f"PDF generation failed. Temporary files retained in '{cwd}' for debugging."
                )


# --- Argument Parsing ---
def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments for the script.

    Returns
    -------
    argparse.Namespace
        An object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Generate a side-by-side PDF comparison of ungraded and graded JPG images "
        "using ImageMagick, preserving original color information. "
        "Temporary files are created in the current working directory (CWD)."
    )
    parser.add_argument(
        "--ungraded-dir",
        type=Path,
        default=DEFAULT_UNGRADED_DIR,
        help=f"Path to the directory containing ungraded (original) JPG/JPEG images. "
        f"Defaults to '{DEFAULT_UNGRADED_DIR}'.",
    )
    parser.add_argument(
        "--graded-dir",
        type=Path,
        default=DEFAULT_GRADED_DIR,
        help=f"Path to the directory containing graded (color-corrected) JPG/JPEG images. "
        f"Defaults to '{DEFAULT_GRADED_DIR}'.",
    )
    parser.add_argument(
        "--output-pdf",
        type=Path,
        default=DEFAULT_OUTPUT_PDF,
        help=f"Path for the output PDF file. Defaults to '{DEFAULT_OUTPUT_PDF}'.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level. Defaults to INFO.",
    )

    args = parser.parse_args()
    return args


# --- Main Execution Block ---
def main() -> None:
    """
    Main function to parse arguments, set up logging, and execute the image processing logic.
    """
    args = parse_arguments()
    setup_logging(args.log_level)

    logging.info("Script started.")
    check_magick()  # Check magick availability early

    try:
        process_images_to_pdf(
            ungraded_dir=args.ungraded_dir,
            graded_dir=args.graded_dir,
            output_pdf=args.output_pdf,
        )
        logging.info("Script finished successfully.")
    except SystemExit as e:
        # SystemExit is raised intentionally for controlled exits due to errors
        logging.error(f"Script exited due to an error: {e.code}")
        sys.exit(e.code)
    except Exception as e:
        # Catch any other unexpected exceptions
        logging.exception(f"An unhandled error occurred during script execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
