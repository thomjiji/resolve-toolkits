"""
traverse_and_parse_xml.py

This script traverses a given directory and its subdirectories to find all XML files.
It extracts specific information from these XML files by looking for <Item> tags
whose 'name' attribute contains specific keywords (e.g., 'Gamma', 'ColorPrimaries').
It then prints the 'value' attribute of these found items.

The script uses argparse for command-line arguments, pathlib for directory traversal,
xml.etree.ElementTree for XML parsing, and includes detailed logging output.

Example Usage:
    python traverse_and_parse_xml.py /path/to/your/directory
"""

import argparse
import logging
import pathlib
import xml.etree.ElementTree as ET
import sys
from typing import List, Dict, Optional  # Import types for type hints

# --- Logging Setup ---
# Configure the logger
# level=logging.INFO means logging messages of INFO, WARNING, ERROR, CRITICAL levels
# format defines the format of log messages: timestamp - log level name - message content
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# --- XML Processing Function ---
def process_xml_file(file_path: pathlib.Path) -> None:
    """
    Processes a single XML file, searching for Item tags whose name contains specific keywords.

    Traverses the XML tree, looking for all <Item> tags within the default namespace.
    If an Item's 'name' attribute contains any of the specified keywords, its actual
    'name' and 'value' attributes are logged.

    Parameters
    ----------
    file_path : pathlib.Path
        A pathlib.Path object representing the path to the XML file to process.

    Returns
    -------
    None
        The function logs findings and errors but does not return a value.

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

    try:
        # Use ElementTree to parse the XML file
        tree: ET.ElementTree = ET.parse(file_path)
        root: ET.Element = tree.getroot()

        # Use findall to find all matching Item elements
        # .//ns:Item searches for all (recursively) 'Item' tags within the 'ns'
        # namespace (mapped above to the namespace_uri) anywhere below the current element (root).
        # We don't pre-filter by name here, we'll check the name attribute in the loop.
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
                # If it matches and has a value attribute, log it
                if item_value is not None:
                    logging.info(
                        f"  Found relevant item in file '{file_path.name}': name='{item_name}', value='{item_value}'"
                    )
                    found_items_count += 1
                else:
                    logging.warning(
                        f"  Found relevant item '{item_name}' in file '{file_path.name}' but it has no 'value' attribute."
                    )

        if found_items_count == 0:
            logging.warning(
                f"  Found no items matching keywords {target_name_keywords} in file '{file_path.name}'."
            )

    except FileNotFoundError:
        logging.error(f"Error: File not found: {file_path}")
    except ET.ParseError as e:
        logging.error(f"Error: Failed to parse XML file '{file_path}': {e}")
    except Exception as e:
        logging.error(
            f"An unexpected error occurred while processing '{file_path}': {e}",
            exc_info=True,
        )  # exc_info=True prints traceback


# --- Main Execution Block ---
def main() -> None:
    """
    Main function to parse command-line arguments and initiate directory traversal.

    Configures the command-line parser, gets the directory path specified by the user.
    Checks if the path is a valid directory, then recursively finds and processes
    all XML files within it using the `process_xml_file` function. Logs status
    and errors during traversal and processing.

    Parameters
    ----------
    None
        This function parses command-line arguments directly and takes no parameters.

    Returns
    -------
    None
        This function controls the script execution flow, outputs results via logging,
        and exits the program on errors.

    Raises
    ------
    SystemExit
        If the provided path is not a valid directory, or if an unrecoverable error
        occurs during directory traversal or file processing, the script will exit
        with a non-zero status code.
    """
    # Create a command-line argument parser using argparse
    parser = argparse.ArgumentParser(
        description="Traverse all XML files in a given directory and extract values for items whose name contains specific keywords (e.g., Gamma, ColorPrimaries)."
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

    xml_files_count: int = 0
    try:
        # Use the glob method to find all .xml files recursively in the directory and its subdirectories
        # '**/*.xml' means find all files ending with '.xml' ('*.xml') in the current directory
        # and any subdirectory ('**').
        # The type of xml_file_path is pathlib.Path
        for xml_file_path in base_directory.glob("**/*.xml"):
            # Although *.xml in glob usually ensures this, we double-check it's actually a file
            if xml_file_path.is_file():
                xml_files_count += 1
                process_xml_file(xml_file_path)

        if xml_files_count == 0:
            logging.warning(
                f"No XML files found in directory '{base_directory}' and its subdirectories."
            )

    except Exception as e:
        logging.error(
            f"An error occurred during directory traversal of '{base_directory}': {e}",
            exc_info=True,
        )  # Print traceback
        sys.exit(1)  # Error during traversal also considered a failure

    logging.info("Directory traversal complete.")


# Execute the main() function when the script is run directly
if __name__ == "__main__":
    main()
