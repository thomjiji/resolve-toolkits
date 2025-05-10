import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# --- Module-level Constants ---
# Default directories and file names
DEFAULT_UNGRADED_DIR: str = "ungraded"
DEFAULT_GRADED_DIR: str = "graded"
DEFAULT_OUTPUT_PDF: str = "comparison_with_labels_lowqual_temps.pdf"

# Input image extensions to look for (case-insensitive JPG/JPEG only)
INPUT_IMAGE_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg")

# Temporary file settings (will now use lossy compression for smaller files)
# Temporary files will be created in a unique subdirectory within the system's temporary directory.
TEMP_DIR_PREFIX: str = "image_comparison_temp_"  # Prefix for the temporary subdirectory
TEMP_RAW_COMBINED_PREFIX: str = (
    "raw_combined_"  # Prefix for intermediate combined files
)
TEMP_FINAL_PAGE_PREFIX: str = (
    "final_page_"  # Prefix for final temporary files (with text)
)
# NOTE: Using JPEG for temporary format for quality reduction at append stage.
# This introduces lossy compression earlier, potentially altering color information.
TEMP_IMAGE_FORMAT: str = "JPEG"
TEMP_IMAGE_EXTENSION: str = "jpg"

# Text Annotation Settings
DEFAULT_UNGRADED_LABEL: str = "Ungraded"
DEFAULT_GRADED_LABEL: str = "Graded"
TEXT_FONT: str = "Noto Sans"  # Font to use for text labels
TEXT_POINTSIZE: int = 100  # Font size
TEXT_FILL_COLOR: str = "white"  # Text color (e.g., "white", "black", "#RRGGBB")
TEXT_OFFSET_X: int = 20  # X offset from the corner (pixels)
TEXT_OFFSET_Y: int = 20  # Y offset from the corner (pixels)

# Output Quality Setting (Applied during temporary file creation)
# This quality setting will now affect the temporary files directly,
# using lossy compression (JPEG).
IMAGE_QUALITY: int = (
    80  # Output image quality (0-100). Lower means smaller file size and more loss.
)


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
    ungraded_label: str,
    graded_label: str,
) -> None:
    """
    Processes image pairs from two directories (assumed JPG/JPEG), combines them side-by-side,
    adds text labels using 'magick' command, and then creates a multi-page PDF.
    Temporary files are created in a unique subdirectory within the system's temporary directory
    using specific prefixes and lossy format (JPEG) with controlled quality.
    This approach reduces temporary file size but may alter original color information.

    Parameters
    ----------
    ungraded_dir : Path
        Path to the directory containing ungraded (original) JPG/JPEG images.
    graded_dir : Path
        Path to the directory containing graded (color-corrected) JPG/JPEG images.
    output_pdf : Path
        Path for the output PDF file.
    ungraded_label : str
        Text label to add to the top-left of the ungraded image in the pair.
    graded_label : str
        Text label to add to the top-right of the graded image in the pair.

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        If essential directories are not found, or if ImageMagick operations fail.
    """
    logging.info(
        "Starting image comparison PDF generation with text labels and early quality reduction."
    )
    logging.warning(
        f"NOTE: Applying image quality {IMAGE_QUALITY} during temporary file creation ({TEMP_IMAGE_FORMAT}). "
        "This uses lossy compression and may alter original color information compared to source files. "
        "For strict color fidelity review, consider using a lossless temporary format."
    )

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
        filenames: list[str] = sorted(
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

    # 3. Create a temporary directory within the system temp location
    # Use process ID to make the directory name more unique
    temp_dir: Path = Path(tempfile.gettempdir()) / f"{TEMP_DIR_PREFIX}{os.getpid()}"
    logging.info(f"Creating temporary directory: '{temp_dir}'")
    try:
        # exist_ok=False will raise FileExistsError if the directory already exists,
        # which helps prevent accidental cleanup of unrelated directories.
        temp_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        # If it exists, it might be from a previous failed run. Try to clean it up first.
        logging.warning(
            f"Temporary directory '{temp_dir}' already exists. Attempting to clean it up."
        )
        try:
            shutil.rmtree(temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=False)
            logging.info(f"Cleaned up and recreated temporary directory: '{temp_dir}'")
        except Exception as e:
            logging.exception(
                f"Error cleaning up or recreating temporary directory '{temp_dir}': {e}"
            )
            sys.exit(1)
    except OSError as e:
        logging.exception(f"Error creating temporary directory '{temp_dir}': {e}")
        sys.exit(1)

    final_page_paths: list[Path] = []
    logging.info(
        f"Found {len(filenames)} JPG/JPEG files in '{ungraded_dir}'. Processing image pairs..."
    )

    # 4. Process each image pair: Combine and Add Text
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

        # --- Stage 1: Combine Images Horizontally (with quality reduction) ---
        base_filename_no_ext: str = ungraded_path.stem
        # Temporary file will be JPEG with quality applied, inside the temporary directory
        temp_raw_combined_filename: str = f"{TEMP_RAW_COMBINED_PREFIX}{i:04d}_{base_filename_no_ext}.{TEMP_IMAGE_EXTENSION}"
        temp_raw_combined_path: Path = temp_dir / temp_raw_combined_filename

        # Build 'magick' command for horizontal append
        # Added -quality here to affect the temporary file size and compression.
        magick_append_command: list[str] = [
            "magick",
            str(ungraded_path),  # Convert Path to string for subprocess
            str(graded_path),  # Convert Path to string for subprocess
            "+append",  # Horizontal append
            "-quality",
            str(IMAGE_QUALITY),  # Apply quality here
            str(temp_raw_combined_path),  # Output path (lossy JPEG)
        ]

        try:
            logging.debug(
                f"Executing append command: {' '.join(magick_append_command)}"
            )
            process_append: subprocess.CompletedProcess = subprocess.run(
                magick_append_command, check=True, capture_output=True, text=True
            )
            logging.debug(f"Magick append stdout: {process_append.stdout.strip()}")
            logging.debug(f"Magick append stderr: {process_append.stderr.strip()}")

        except subprocess.CalledProcessError as e:
            logging.error(
                f"Error: Failed to append images for '{filename}'. "
                f"Magick command exited with code {e.returncode}. "
                f"Stdout: {e.stdout.strip()} | Stderr: {e.stderr.strip()}"
            )
            # If appending fails, skip adding text and processing this pair further.
            continue
        except FileNotFoundError:
            logging.error(
                f"Error: 'magick' command not found during append for '{filename}'. Exiting."
            )
            # Clean up the temporary directory before exiting
            shutil.rmtree(temp_dir, ignore_errors=True)
            sys.exit(1)
        except Exception as e:
            logging.exception(
                f"An unexpected error occurred during image append for '{filename}': {e}"
            )
            continue

        # --- Stage 2: Add Text Annotations to the Combined Image ---
        # This step reads the lossy JPEG and saves it as another lossy JPEG (or TIFF,
        # but keeping it JPEG maintains the smaller file size).
        temp_final_page_filename: str = f"{TEMP_FINAL_PAGE_PREFIX}{i:04d}_{base_filename_no_ext}.{TEMP_IMAGE_EXTENSION}"
        temp_final_page_path: Path = (
            temp_dir / temp_final_page_filename
        )  # Save in temp_dir

        # Build 'magick' command to add text
        # Read the raw combined (lossy JPEG) image, add annotations, and save.
        # We re-apply quality here to ensure the output is also a JPEG with the desired quality,
        # although the primary loss happened in the append step.
        magick_annotate_command: list[str] = [
            "magick",
            str(temp_raw_combined_path),  # Input: the raw combined image (lossy JPEG)
            "-font",
            TEXT_FONT,
            "-pointsize",
            str(TEXT_POINTSIZE),
            "-fill",
            TEXT_FILL_COLOR,
            "-gravity",
            "northwest",
            "-annotate",
            f"+{TEXT_OFFSET_X}+{TEXT_OFFSET_Y}",
            ungraded_label,
            "-gravity",
            "northeast",
            "-annotate",
            f"+{TEXT_OFFSET_X}+{TEXT_OFFSET_Y}",
            graded_label,
            "-quality",
            str(IMAGE_QUALITY),  # Re-apply quality for the output temporary file
            str(
                temp_final_page_path
            ),  # Output: the final temporary image for this page (lossy JPEG)
        ]

        try:
            logging.debug(
                f"Executing annotate command: {' '.join(magick_annotate_command)}"
            )
            process_annotate: subprocess.CompletedProcess = subprocess.run(
                magick_annotate_command, check=True, capture_output=True, text=True
            )
            logging.debug(f"Magick annotate stdout: {process_annotate.stdout.strip()}")
            logging.debug(f"Magick annotate stderr: {process_annotate.stderr.strip()}")
            final_page_paths.append(temp_final_page_path)

        except subprocess.CalledProcessError as e:
            logging.error(
                f"Error: Failed to add text annotations to combined image for '{filename}'. "
                f"Magick command exited with code {e.returncode}. "
                f"Stdout: {e.stdout.strip()} | Stderr: {e.stderr.strip()}"
            )
            # If annotation fails, remove the raw combined file and skip this pair.
            if temp_raw_combined_path.is_file():
                try:
                    temp_raw_combined_path.unlink()
                    logging.debug(
                        f"Cleaned up raw combined file after annotation failure: {temp_raw_combined_path}"
                    )
                except OSError as cleanup_e:
                    logging.error(
                        f"Error cleaning up raw combined file '{temp_raw_combined_path}': {cleanup_e}"
                    )
            continue  # Continue to next pair
        except FileNotFoundError:
            logging.error(
                f"Error: 'magick' command not found during annotation for '{filename}'. Exiting."
            )
            # Clean up the temporary directory before exiting
            shutil.rmtree(temp_dir, ignore_errors=True)
            sys.exit(1)
        except Exception as e:
            logging.exception(
                f"An unexpected error occurred during image annotation for '{filename}': {e}"
            )
            # Log the exception and continue with the next pair.
            if temp_raw_combined_path.is_file():
                try:
                    temp_raw_combined_path.unlink()
                    logging.debug(
                        f"Cleaned up raw combined file after annotation failure: {temp_raw_combined_path}"
                    )
                except OSError as cleanup_e:
                    logging.error(
                        f"Error cleaning up raw combined file '{temp_raw_combined_path}': {cleanup_e}"
                    )
            continue

        # --- Clean up the intermediate raw combined file ---
        # This file is no longer needed after annotation
        if temp_raw_combined_path.is_file():
            try:
                temp_raw_combined_path.unlink()
                logging.debug(
                    f"Cleaned up intermediate raw combined file: {temp_raw_combined_path}"
                )
            except OSError as e:
                logging.error(
                    f"Error cleaning up intermediate raw combined file '{temp_raw_combined_path}': {e}"
                )

    # 5. Combine all final temporary images into a PDF
    # The quality is already set in the temporary JPEG files.
    # We still include -quality here, but its effect might be less pronounced
    # than when applied to lossless inputs. It controls the final PDF compression.
    logging.info(
        f"All image pairs processed ({len(final_page_paths)} pairs). "
        f"Generating final PDF: '{output_pdf}' with quality {IMAGE_QUALITY} (based on temporary files)..."
    )

    if not final_page_paths:
        logging.warning(
            "No final combined images with labels were successfully created. No PDF will be generated."
        )
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        return

    # Build 'magick' command for PDF creation
    # Images are listed as input, and ImageMagick creates a multi-page PDF.
    # -quality here affects the final PDF compression, reading from the temporary JPEGs.
    magick_pdf_command: list[str] = [
        "magick",
        *[str(p) for p in final_page_paths],  # Convert Path objects to strings
        "-quality",
        str(IMAGE_QUALITY),  # Set PDF output quality (reads from lossy temps)
        str(output_pdf),  # Output PDF path
    ]

    # Initialize pdf_generation_successful before the try block
    pdf_generation_successful: bool = False
    try:
        logging.debug(
            f"Executing PDF generation command: {' '.join(magick_pdf_command)}"
        )
        process_pdf: subprocess.CompletedProcess = subprocess.run(
            magick_pdf_command, check=True, capture_output=True, text=True
        )
        logging.info(f"PDF '{output_pdf}' successfully generated.")
        logging.debug(f"Magick PDF stdout: {process_pdf.stdout.strip()}")
        logging.debug(f"Magick PDF stderr: {process_pdf.stderr.strip()}")
        pdf_generation_successful = (
            True  # Set to True only on successful PDF generation
        )
    except subprocess.CalledProcessError as e:
        logging.error(
            f"Error: Failed to generate PDF '{output_pdf}'. "
            f"Magick command exited with code {e.returncode}. "
            f"Stdout: {e.stdout.strip()} | Stderr: {e.stderr.strip()}"
        )
        # pdf_generation_successful remains False
    except FileNotFoundError:
        # This case should ideally be caught by check_magick() early on.
        logging.error(
            "Error: 'magick' command not found during PDF generation. Exiting."
        )
        # Clean up the temporary directory before exiting
        shutil.rmtree(temp_dir, ignore_errors=True)
        sys.exit(1)
    except Exception as e:
        logging.exception(f"An unexpected error occurred during PDF generation: {e}")
        # pdf_generation_successful remains False
    finally:
        # 6. Clean up the temporary directory
        # Now, we check pdf_generation_successful to decide whether to clean up.
        if pdf_generation_successful:
            logging.info(f"Cleaning up temporary directory: '{temp_dir}'...")
            try:
                shutil.rmtree(temp_dir)
                logging.info("Temporary directory cleaned.")
            except OSError as e:
                logging.error(
                    f"Error cleaning up temporary directory '{temp_dir}': {e}"
                )
        else:
            # If PDF generation failed, temporary files are intentionally left for debugging.
            logging.warning(
                f"PDF generation failed. Temporary directory retained: '{temp_dir}' for debugging."
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
    # Declare global IMAGE_QUALITY before its first use in this function
    global IMAGE_QUALITY

    parser = argparse.ArgumentParser(
        description="Generate a side-by-side PDF comparison of ungraded and graded JPG images "
        "with text labels, using ImageMagick. Applies quality reduction during temporary "
        "file creation to reduce their size, which may alter original color information. "
        "Temporary files are created in a unique subdirectory within the system's temporary directory."
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
        "--ungraded-label",
        type=str,
        default=DEFAULT_UNGRADED_LABEL,
        help=f"Text label for the ungraded images (top-left). Defaults to '{DEFAULT_UNGRADED_LABEL}'.",
    )
    parser.add_argument(
        "--graded-label",
        type=str,
        default=DEFAULT_GRADED_LABEL,
        help=f"Text label for the graded images (top-right). Defaults to '{DEFAULT_GRADED_LABEL}'.",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=IMAGE_QUALITY,  # Use the module-level default
        choices=range(0, 101),  # Quality is usually 0-100
        metavar="[0-100]",
        help=f"Output image quality (0-100) applied during temporary file creation (using JPEG). "
        f"Lower quality reduces file size but increases loss. Defaults to {IMAGE_QUALITY}. "
        "Note: This affects temporary files and may alter original color information.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level. Defaults to INFO.",
    )

    args = parser.parse_args()

    # Update the module-level IMAGE_QUALITY based on parsed arguments
    # This is done AFTER parsing, so the default value is correctly used if not provided
    IMAGE_QUALITY = args.quality

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

    # Log the labels being used
    logging.info(
        f"Using labels: Ungraded='{args.ungraded_label}', Graded='{args.graded_label}'"
    )
    # IMPORTANT: Ensure the 'Noto Sans' font is available to ImageMagick on your system.
    # You might need to install it system-wide or configure ImageMagick's font paths.
    logging.info(
        f"Using font '{TEXT_FONT}' for text labels. Ensure this font is available to ImageMagick."
    )

    try:
        process_images_to_pdf(
            ungraded_dir=args.ungraded_dir,
            graded_dir=args.graded_dir,
            output_pdf=args.output_pdf,
            ungraded_label=args.ungraded_label,
            graded_label=args.graded_label,
        )
        logging.info("Script finished successfully.")
    except SystemExit as e:
        # SystemExit is raised intentionally for controlled exits due to errors
        # The cleanup logic in process_images_to_pdf's finally block handles temp dir cleanup
        # based on the pdf_generation_successful flag.
        logging.error(f"Script exited due to an error: {e.code}")
        sys.exit(e.code)
    except Exception as e:
        # Catch any other unexpected exceptions
        logging.exception(f"An unhandled error occurred during script execution: {e}")
        # In case of an unhandled exception outside process_images_to_pdf,
        # the temp dir might not have been cleaned. A basic cleanup attempt here.
        # This is a fallback; the finally block in process_images_to_pdf is the primary handler.
        try:
            temp_dir = Path(tempfile.gettempdir()) / f"{TEMP_DIR_PREFIX}{os.getpid()}"
            if temp_dir.exists():
                logging.warning(
                    f"Attempting fallback cleanup of temporary directory: '{temp_dir}'"
                )
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as cleanup_e:
            logging.error(f"Fallback cleanup failed: {cleanup_e}")

        sys.exit(1)


if __name__ == "__main__":
    main()
