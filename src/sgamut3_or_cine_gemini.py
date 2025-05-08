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
import logging
import pathlib
import xml.etree.ElementTree as ET
import sys
import csv  # Import the csv module
from typing import List, Dict, Optional  # Import types for type hints
from datetime import date  # Import date for including it in the filename

# --- Constants ---
# Field names for the CSV file
CSV_FIELDNAMES: List[str] = ["File Path", "Item Name", "Item Value"]


# --- XML Processing Function ---
def process_xml_file(file_path: pathlib.Path) -> List[Dict[str, str]]:
    """
    Processes a single XML file, searching for Item tags whose name contains specific keywords,
    and returns the extracted data.

    Traverses the XML tree, looking for all <Item> tags within the default namespace.
    If an Item's 'name' attribute contains any of the specified keywords, its actual
    'name' and 'value' attributes are extracted.

    Parameters
    ----------
    file_path : pathlib.Path
        A pathlib.Path object representing the path to the XML file to process.

    Returns
    -------
    List[Dict[str, str]]
        A list of dictionaries. Each dictionary represents a found item and contains
        keys 'File Path', 'Item Name', and 'Item Value'. Returns an empty list
        if no relevant items are found or if an error occurs during processing
        of *this specific file*.

    Raises
    ------
    FileNotFoundError
        If the provided file path does not exist. This exception is caught and logged
        within the function.
    xml.etree.ElementTree.ParseError
        If the file content is not well-formed XML. This exception is caught and logged
        within the function.
    Exception
        Any other unexpected error occurring during file processing. This exception is
        caught and logged within the function.
    """
    logging.info(f"Processing file: {file_path}")

    # Define the default namespace URI for the XML
    namespace_uri: str = "urn:schemas-professionalDisc:nonRealTimeMeta:ver.2.20"
    # Define a prefix for the namespace; ElementTree needs this mapping for find/findall
    namespaces: Dict[str, str] = {"ns": namespace_uri}

    # Define the list of keywords to search for within the 'name' attribute of Item tags
    target_name_keywords: List[str] = ["Gamma", "ColorPrimaries"]

    extracted_data_for_file: List[Dict[str, str]] = []

    try:
        # Use ElementTree to parse the XML file
        tree: ET.ElementTree = ET.parse(file_path)
        root: ET.Element = tree.getroot()

        # Use findall to find all matching Item elements anywhere in the document
        # .//ns:Item searches for all (recursively) 'Item' tags within the 'ns'
        # namespace (mapped above to the namespace_uri) anywhere below the current element (root).
        found_items_count: int = 0
        # The type of item_element is ET.Element
        for item_element in root.findall(".//ns:Item", namespaces):
            # get() method returns None if the attribute does not exist
            item_name: Optional[str] = item_element.get("name")
            item_value: Optional[str] = item_element.get("value")

            # Check if the Item has a name attribute and if that name contains any of our keywords
            if item_name and any(
                keyword in item_name for keyword in target_name_keywords
            ):
                found_items_count += 1
                # If it matches and has a value attribute, add it to our list
                if item_value is not None:
                    # Store absolute path for clarity in CSV
                    extracted_data_for_file.append(
                        {
                            "File Path": str(file_path.resolve()),
                            "Item Name": item_name,
                            "Item Value": item_value,
                        }
                    )
                    # Optionally log finding it for immediate feedback
                    logging.info(
                        f"  Found relevant item: name='{item_name}', value='{item_value}'"
                    )
                else:
                    logging.warning(
                        f"  Found relevant item '{item_name}' but it has no 'value' attribute in file '{file_path.name}'."
                    )

        # Log a warning if no relevant items were found in this specific file
        if found_items_count == 0:
            logging.warning(
                f"  Found no items matching keywords {target_name_keywords} in file '{file_path.name}'."
            )

    except FileNotFoundError:
        logging.error(f"Error: File not found: {file_path}")
        # Return empty list on error processing this file
        return []
    except ET.ParseError as e:
        logging.error(f"Error: Failed to parse XML file '{file_path}': {e}")
        # Return empty list on error processing this file
        return []
    except Exception as e:
        logging.error(
            f"An unexpected error occurred while processing '{file_path}': {e}",
            exc_info=True,
        )  # exc_info=True prints traceback
        # Return empty list on error processing this file
        return []

    return extracted_data_for_file


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
                file_results = process_xml_file(xml_file_path)
                all_extracted_data.extend(file_results)

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
