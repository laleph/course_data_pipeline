import argparse
import json
import re
from typing import List

import bleach
import xmltodict
from markdownify import markdownify

from HISCourse import HISCourse


def remove_duplicate_entries(kreativeu_data_dict):
    """Remove duplicate entries from the SOAP response and update the XML dictionary"""
    # get courses data from xml_dict
    courses_list = kreativeu_data_dict.get("KreativEU", {}).get("veranstaltung", [])

    # remove duplicate entries
    # TODO check with Daniel to remove this from the original xml
    for course in courses_list:
        if isinstance(course.get("kommentar"), list):
            course["kommentar"] = course["kommentar"][0]
        if isinstance(course.get("literatur"), list):
            course["literatur"] = course["literatur"][0]
        if isinstance(course.get("moodle"), list):
            course["moodle"] = course["moodle"][0]

    # Update the original xml_dict with modified courses_data
    if "KreativEU" in kreativeu_data_dict:
        kreativeu_data_dict["KreativEU"]["veranstaltung"] = courses_list
    else:
        print("Error: 'KreativEU' key not found in XML dictionary.")
        return None
    return kreativeu_data_dict


def remove_tests(kreativeu_data_dict):
    """Remove Test and Examination entries from the SOAP response and update the XML dictionary"""
    # get courses data from xml_dict
    courses_list = kreativeu_data_dict.get("KreativEU", {}).get("veranstaltung", [])

    for course in courses_list:
        if course.get("typ") == "Test":
            courses_list.remove(course)
        elif course.get("typ") == "Examination":
            courses_list.remove(course)
        else:
            continue

    # Update the original xml_dict with modified courses_data
    if "KreativEU" in kreativeu_data_dict:
        kreativeu_data_dict["KreativEU"]["veranstaltung"] = courses_list
    else:
        print("Error: 'KreativEU' key not found, remove 'Test' and 'Examination' entries failed.")
        return None
    return kreativeu_data_dict


def sanitize_and_convert(value):
    """convert (and sanitize) HTML values to Markdown"""
    if isinstance(value, str):
        # Sanitize HTML using bleach
        sanitized_html = bleach.clean(
            value,
            tags=["b", "i", "u", "a", "p", "strong", "em", "ul", "ol", "li"],
            attributes={"a": ["href", "title"], "p": [], "strong": [], "em": []},
            protocols=["http", "https"],
        )

        # Convert sanitized HTML to Markdown
        markdown_value = markdownify(sanitized_html)

        # Replace <u> tags with **bold**
        markdown_value = re.sub(
            r"<span style=\"text-decoration: underline;\">(.*?)</span>",
            r"<u>\1</u>",
            markdown_value,
        )

        # Convert HTML headers to Markdown headers using regex
        markdown_value = re.sub(
            r"<h([1-6])>(.*?)<\/h\1>",
            lambda m: "#" * int(m.group(1)) + " " + m.group(2),
            markdown_value,
        )

        return markdown_value
    return value


def recursive_conversion(keu_dict):
    """apply HTML to markdown conversion to all string values in xml_dict recursively"""
    if isinstance(keu_dict, dict):
        return {k: (recursive_conversion(v) if k != "moodle" else v) for k, v in keu_dict.items()}
    elif isinstance(keu_dict, list):
        return [recursive_conversion(i) for i in keu_dict]
    else:
        return sanitize_and_convert(keu_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process an XML file.")
    parser.add_argument(
        "--xml-file",
        type=str,
        help="Path to the XML data input file (default: SOAP_response.xml)",
        default="SOAP_response.xml",
    )
    parser.add_argument(
        "--json-output",
        type=str,
        help="Path to the intermiediate JSON data output file (default: intermediate.json)",
        default="intermediate.json",
    )
    args = parser.parse_args()
    XML_FILE_PATH = args.xml_file
    JSON_FILE_PATH = args.json_output

    # read the SOAP xml response from a file
    with open(XML_FILE_PATH, encoding="utf-8") as f:
        soap_response = f.read()

    # convert SOAP (XML) to dictionary using xmltodict
    xml_dict = xmltodict.parse(soap_response)

    # Remove tests from the dictionary
    xml_dict = remove_tests(xml_dict)
    if xml_dict is not None:
        # Remove duplicate entries from the dictionary
        xml_dict = remove_duplicate_entries(xml_dict)
        if xml_dict is not None:  # Check again in case of error
            # html to markdown for all strings in the dictionary
            xml_dict = recursive_conversion(xml_dict)

            # write the JSON response to a file
            json.dump(xml_dict, open(JSON_FILE_PATH, "w", encoding="utf-8"), indent=2)
        else:
            print("Failed to remove duplicate entries.")

    # Check SOAP data according to HISCourse definition
    courses_data = xml_dict.get("KreativEU", {}).get("veranstaltung", [])
    his_courses: List[HISCourse] = [HISCourse(**course) for course in courses_data]

    # Output course and lecturer to console for debugging purposes
    for hcourse in his_courses:
        print(f"Course Title: {hcourse.titel}, Type: {hcourse.typ}")
        if hcourse.lehrperson:
            if isinstance(hcourse.lehrperson, list):
                for lp in hcourse.lehrperson:
                    print(f"  Lecturer: {lp.Vorname} {lp.Nachname}")
            else:  # Single lecturer
                print(f"  Lecturer: {hcourse.lehrperson.Vorname} {hcourse.lehrperson.Nachname}")
