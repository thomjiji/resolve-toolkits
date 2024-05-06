"""
XML Tag Extractor

This script extracts values from an XML file for a specific tag and saves them to a CSV file.

Usage:
    python xml_tag_extractor.py input.xml output.csv tag_name

Arguments:
    input.xml (str): Path to the input XML file.
    output.csv (str): Path to the output CSV file.
    tag_name (str): Tag to extract values from in the XML file.

Example:
    python xml_tag_extractor.py /path/to/input.xml /path/to/output.csv pathurl
"""

import argparse
import xml.etree.ElementTree as ET
import csv
from urllib.parse import unquote


def parse_xml_to_csv(xml_file, output_csv, tag):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Tag", "Path"])

        for elem in root.iter(tag):
            tag_name = elem.tag
            path = unquote(elem.text) if elem.text else ""
            writer.writerow([tag_name, path])


def main():
    parser = argparse.ArgumentParser(description="Convert XML file to CSV")
    parser.add_argument("xml_file", help="Path to the input XML file")
    parser.add_argument("output_csv", help="Path to the output CSV file")
    parser.add_argument("tag", help="Tag to search for in the XML file")

    args = parser.parse_args()
    parse_xml_to_csv(args.xml_file, args.output_csv, args.tag)


if __name__ == "__main__":
    main()
