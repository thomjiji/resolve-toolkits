"""
traverse_and_parse_xml.py

This script traverses a given directory and its subdirectories to find all XML files
with the uppercase '.XML' extension. It extracts specific information from these
XML files by looking for <Item> tags whose 'name' attribute contains specific
keywords (e.g., 'Gamma', 'ColorPrimaries').

Based on command-line arguments, the script can optionally write the extracted
information (File Path, Item Name, Item Value) to a dated CSV file.

The script uses argparse for command-line arguments, pathlib for directory traversal,
xml.etree.ElementTree for XML parsing, csv for writing results, and includes
detailed logging output.

Example Usage (logging only):
    python traverse_and_parse_xml.py /path/to/your/directory

Example Usage (logging and outputting CSV):
    python traverse_and_parse_xml.py /path/to/your/directory --output my_extraction_results
    # This will create a file like my_extraction_results_YYYY-MM-DD.csv
"""

import argparse
import csv  # Import the csv module
import logging
import pathlib
import sys
import xml.etree.ElementTree as ET
from datetime import date  # Import date for including it in the filename
from typing import Dict, List, Optional  # Import types for type hints

# --- Constants ---
# Field names for the CSV file
CSV_FIELDNAMES: List[str] = [
    "file full path (filename)",
    "color primaries",
    "transfer function",
]


# --- XML Processing Function ---
def process_xml_file(file_path: pathlib.Path) -> Optional[Dict[str, str]]:
    """
    Processes a single XML file, searching for color primaries and transfer function,
    and returns a dictionary with the file path, color primaries, and transfer function.

    Returns None if neither value is found or if an error occurs.
    """
    logging.info(f"Processing file: {file_path}")

    namespace_uri: str = "urn:schemas-professionalDisc:nonRealTimeMeta:ver.2.20"
    namespaces: Dict[str, str] = {"ns": namespace_uri}

    color_primaries: Optional[str] = None
    transfer_function: Optional[str] = None

    try:
        tree: ET.ElementTree = ET.parse(file_path)
        root: ET.Element = tree.getroot()

        for item_element in root.findall(".//ns:Item", namespaces):
            item_name: Optional[str] = item_element.get("name")
            item_value: Optional[str] = item_element.get("value")
            if item_name and item_value:
                if "ColorPrimaries" in item_name and color_primaries is None:
                    color_primaries = item_value
                    logging.info(f"  Found color primaries: {item_value}")
                elif "Gamma" in item_name and transfer_function is None:
                    transfer_function = item_value
                    logging.info(f"  Found transfer function: {item_value}")
            if color_primaries and transfer_function:
                break  # Stop early if both found

        if color_primaries is None and transfer_function is None:
            logging.warning(
                f"  No color primaries or transfer function found in file '{file_path.name}'."
            )
            return None

        return {
            "file full path (filename)": str(file_path.resolve()),
            "color primaries": color_primaries or "",
            "transfer function": transfer_function or "",
        }

    except FileNotFoundError:
        logging.error(f"Error: File not found: {file_path}")
        return None
    except ET.ParseError as e:
        logging.error(f"Error: Failed to parse XML file '{file_path}': {e}")
        return None
    except Exception as e:
        logging.error(
            f"An unexpected error occurred while processing '{file_path}': {e}",
            exc_info=True,
        )
        return None


# --- Main Execution Function ---
def main(args: argparse.Namespace) -> None:
    """
    Main function to control script execution, including directory traversal
    and optional CSV writing.

    Retrieves the directory path and output filename base from the parsed
    command-line arguments. Checks directory validity, recursively finds and
    processes .XML files. Collects extracted data and, if an output filename
    base was provided, writes the data to a dated CSV file. Logs status
    and errors throughout execution.

    Parameters
    ----------
    args : argparse.Namespace
        The namespace object containing parsed command-line arguments.

    Returns
    -------
    None
        This function controls the script's flow and exits using sys.exit() on errors.

    Raises
    ------
    SystemExit
        If the provided directory path is invalid, or if a critical error occurs
        during directory traversal or CSV file writing, the script will exit
        with a non-zero status code.
    """
    base_directory: pathlib.Path = pathlib.Path(args.directory)

    # Check if the provided path is a valid directory
    if not base_directory.is_dir():
        logging.error(
            f"Error: '{args.directory}' is not a valid directory. Please provide a correct directory path."
        )
        sys.exit(1)  # Non-zero exit code typically indicates script failure

    logging.info(f"Starting traversal of directory: {base_directory}")

    all_extracted_data: List[Dict[str, str]] = []  # List to collect data from all files
    xml_files_count: int = 0

    try:
        # Use the glob method to find all .XML files (uppercase) recursively
        # '**/*.XML' means find all files ending with '.XML' ('*.XML') in the current directory
        # and any subdirectory ('**').
        # The type of xml_file_path is pathlib.Path
        for xml_file_path in base_directory.glob("**/*.XML"):
            # Although *.XML in glob usually ensures this, we double-check it's actually a file
            if xml_file_path.is_file():
                xml_files_count += 1
                # Process the file and extend the list of all results
                file_result = process_xml_file(xml_file_path)
                if file_result:
                    all_extracted_data.append(file_result)

        if xml_files_count == 0:
            logging.warning(
                f"No uppercase .XML files found in directory '{base_directory}' and its subdirectories."
            )

    except Exception as e:
        logging.error(
            f"An error occurred during directory traversal of '{base_directory}': {e}",
            exc_info=True,
        )  # Print traceback
        # Do NOT exit immediately here, we might still write partial results

    # --- Write results to CSV (if output filename base is provided) ---
    if args.output:
        if all_extracted_data:
            logging.info(f"Extracted {len(all_extracted_data)} relevant data entries.")

            # Get today's date and format it
            today: date = date.today()
            date_str: str = today.strftime("%Y-%m-%d")

            # Construct the full CSV filename with the user-provided base and the date
            csv_filename: str = f"{args.output}_{date_str}.csv"

            logging.info(f"Writing results to {csv_filename}")
            try:
                # Open the CSV file in write mode ('w')
                # newline='' is important to prevent extra blank rows
                # encoding='utf-8' ensures proper handling of various characters
                with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
                    # Create a DictWriter object using the predefined field names
                    writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDNAMES)

                    # Write the header row
                    writer.writeheader()

                    # Write the data rows
                    writer.writerows(all_extracted_data)

                # Log success message
                logging.info(
                    f"Successfully wrote {len(all_extracted_data)} entries to {csv_filename}"
                )

            except IOError as e:
                logging.error(f"Error writing to CSV file {csv_filename}: {e}")
                sys.exit(1)  # Exit on CSV writing error
            except Exception as e:
                logging.error(
                    f"An unexpected error occurred while writing CSV: {e}",
                    exc_info=True,
                )
                sys.exit(1)  # Exit on unexpected CSV writing error
        else:
            # This case happens if --output was given but no data was extracted from any file
            logging.warning(
                "No relevant data extracted from any files. No CSV file will be created."
            )
    else:
        # This case happens if --output was NOT given
        logging.info("CSV output not requested. Results were logged above.")

    logging.info("Script execution complete.")


# --- Main Execution Block ---
# When the script is run directly, execute the following
if __name__ == "__main__":
    # --- Argument Parsing ---
    # Moved argparse setup outside of main function as requested
    parser = argparse.ArgumentParser(
        description="Traverse all uppercase .XML files in a given directory, extract specific item values, and optionally write to a dated CSV file."
    )

    # Add the required positional argument for the directory
    parser.add_argument(
        "directory", type=str, help="The path to the directory to traverse."
    )

    # Add the optional argument for the output CSV base name
    parser.add_argument(
        "--output",
        type=str,
        help='Base name for the output CSV file (e.g., "results"). If provided, results will be written to a file named <base_name>_YYYY-MM-DD.csv. If not provided, no CSV will be generated.',
    )

    # Parse the command-line arguments
    args: argparse.Namespace = parser.parse_args()

    # --- Logging Setup ---
    # Configure logging here before calling main
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # --- Call main function with parsed arguments ---
    main(args)
