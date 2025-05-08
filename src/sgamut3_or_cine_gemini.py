"""
traverse_and_parse_xml.py

This script traverses a given directory and its subdirectories to find all XML files
with the uppercase '.XML' extension. It extracts specific information from these
XML files by looking for <Item> tags whose 'name' attribute contains specific
keywords (e.g., 'Gamma', 'ColorPrimaries'). It then writes the extracted information
(File Path, Item Name, Item Value) to a CSV file.

The script uses argparse for command-line arguments, pathlib for directory traversal,
xml.etree.ElementTree for XML parsing, csv for writing results, and includes
detailed logging output.

Example Usage:
    python traverse_and_parse_xml.py /path/to/your/directory
"""

import argparse
import csv  # Import the csv module
import logging
import pathlib
import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional  # Import types for type hints

# --- Logging Setup ---
# Configure the logger
# level=logging.INFO means logging messages of INFO, WARNING, ERROR, CRITICAL levels
# format defines the format of log messages: timestamp - log level name - message content
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Constants ---
CSV_OUTPUT_FILENAME: str = "xml_extraction_results.csv"
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
        if no relevant items are found or if an error occurs.

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

        # Use findall to find all matching Item elements
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
                    extracted_data_for_file.append(
                        {
                            "File Path": str(
                                file_path.resolve()
                            ),  # Store absolute path
                            "Item Name": item_name,
                            "Item Value": item_value,
                        }
                    )
                    # Optionally log finding it
                    logging.info(
                        f"  Found relevant item: name='{item_name}', value='{item_value}'"
                    )
                else:
                    logging.warning(
                        f"  Found relevant item '{item_name}' but it has no 'value' attribute in file '{file_path.name}'."
                    )

        if found_items_count == 0:
            logging.warning(
                f"  Found no items matching keywords {target_name_keywords} in file '{file_path.name}'."
            )

    except FileNotFoundError:
        logging.error(f"Error: File not found: {file_path}")
        return []  # Return empty list on error
    except ET.ParseError as e:
        logging.error(f"Error: Failed to parse XML file '{file_path}': {e}")
        return []  # Return empty list on error
    except Exception as e:
        logging.error(
            f"An unexpected error occurred while processing '{file_path}': {e}",
            exc_info=True,
        )  # exc_info=True prints traceback
        return []  # Return empty list on error

    return extracted_data_for_file


# --- Main Execution Block ---
def main() -> None:
    """
    Main function to parse command-line arguments, initiate directory traversal,
    and write extracted data to a CSV file.

    Configures the command-line parser, gets the user-specified directory path.
    Checks if the path is a valid directory, then recursively finds and processes
    all .XML files within it. Collects results and writes them to a CSV file.
    Logs status and errors during execution.

    Parameters
    ----------
    None
        This function parses command-line arguments directly and takes no parameters.

    Returns
    -------
    None
        This function controls the script execution flow, writes results to CSV,
        and exits the program on errors.

    Raises
    ------
    SystemExit
        If the provided path is not a valid directory, or if an unrecoverable error
        occurs during directory traversal or CSV writing, the script will exit
        with a non-zero status code.
    """
    # Create a command-line argument parser using argparse
    parser = argparse.ArgumentParser(
        description="Traverse all uppercase .XML files in a given directory, extract specific item values, and write to CSV."
    )

    # Add a required positional argument 'directory'
    parser.add_argument(
        "directory", type=str, help="The path to the directory to traverse."
    )

    # Parse the command-line arguments
    args: argparse.Namespace = parser.parse_args()
    base_directory_path_str: str = args.directory

    # Create a Path object using pathlib
    base_directory: pathlib.Path = pathlib.Path(base_directory_path_str)

    # Check if the provided path is a valid directory
    if not base_directory.is_dir():
        logging.error(
            f"Error: '{base_directory_path_str}' is not a valid directory. Please provide a correct directory path."
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

    # --- Write results to CSV ---
    if all_extracted_data:
        logging.info(f"Extracted {len(all_extracted_data)} relevant data entries.")
        logging.info(f"Writing results to {CSV_OUTPUT_FILENAME}")
        try:
            # Open the CSV file in write mode ('w')
            # newline='' is important to prevent extra blank rows
            # encoding='utf-8' ensures proper handling of various characters
            with open(
                CSV_OUTPUT_FILENAME, "w", newline="", encoding="utf-8"
            ) as csvfile:
                # Create a DictWriter object
                writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDNAMES)

                # Write the header row
                writer.writeheader()

                # Write the data rows
                writer.writerows(all_extracted_data)

            # Log success message
            logging.info(
                f"Successfully wrote {len(all_extracted_data)} entries to {CSV_OUTPUT_FILENAME}"
            )

        except IOError as e:
            logging.error(f"Error writing to CSV file {CSV_OUTPUT_FILENAME}: {e}")
            sys.exit(1)  # Exit on CSV writing error
        except Exception as e:
            logging.error(
                f"An unexpected error occurred while writing CSV: {e}", exc_info=True
            )
            sys.exit(1)  # Exit on unexpected CSV writing error
    else:
        logging.warning(
            "No relevant data extracted from any files. No CSV file will be created or will be empty."
        )

    logging.info("Script execution complete.")


# Execute the main() function when the script is run directly
if __name__ == "__main__":
    main()
