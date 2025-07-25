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
    courses_list = kreativeu_data_dict.get("KreativEU", {}).get("veranstaltung", [])

    # Create a new list to store courses with duplicates removed
    cleaned_courses = []
    for course in courses_list:
        # Create a copy to avoid modifying the original course object in the list
        cleaned_course = course.copy()
        if isinstance(cleaned_course.get("kommentar"), list):
            cleaned_course["kommentar"] = cleaned_course["kommentar"][0]
        if isinstance(cleaned_course.get("literatur"), list):
            cleaned_course["literatur"] = cleaned_course["literatur"][0]
        if isinstance(cleaned_course.get("moodle"), list):
            cleaned_course["moodle"] = cleaned_course["moodle"][0]
        cleaned_courses.append(cleaned_course)

    # Update the original xml_dict with the new list of courses
    if "KreativEU" in kreativeu_data_dict:
        kreativeu_data_dict["KreativEU"]["veranstaltung"] = cleaned_courses
    else:
        print("Error: 'KreativEU' key not found in XML dictionary.")
        return None
    return kreativeu_data_dict


def remove_tests(kreativeu_data_dict):
    """Remove Test and Examination entries from the SOAP response and update the XML dictionary"""
    courses_list = kreativeu_data_dict.get("KreativEU", {}).get("veranstaltung", [])

    # Use a list comprehension to create a new list excluding specified course types
    filtered_courses = [
        course for course in courses_list
        if course.get("typ") not in ["Test", "Examination"]
    ]

    # Update the original xml_dict with the filtered list
    if "KreativEU" in kreativeu_data_dict:
        kreativeu_data_dict["KreativEU"]["veranstaltung"] = filtered_courses
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


def main():
    """Main function to process the XML file."""
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
        help="Path to the intermediate JSON data output file (default: intermediate.json)",
        default="intermediate.json",
    )
    args = parser.parse_args()
    xml_file_path = args.xml_file
    json_file_path = args.json_output

    try:
        with open(xml_file_path, encoding="utf-8") as f:
            soap_response = f.read()

        xml_dict = xmltodict.parse(soap_response)

        # Process the data
        xml_dict = remove_tests(xml_dict)
        if xml_dict:
            xml_dict = remove_duplicate_entries(xml_dict)
        if xml_dict:
            xml_dict = recursive_conversion(xml_dict)

            # Write the JSON response to a file
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(xml_dict, f, indent=2)
            print(f"Successfully converted {xml_file_path} to {json_file_path}")

            # Validate data and print debug info
            courses_data = xml_dict.get("KreativEU", {}).get("veranstaltung", [])
            his_courses: List[HISCourse] = [HISCourse(**course) for course in courses_data]
            for hcourse in his_courses:
                print(f"Course Title: {hcourse.titel}, Type: {hcourse.typ}")
                if hcourse.lehrperson:
                    if isinstance(hcourse.lehrperson, list):
                        for lp in hcourse.lehrperson:
                            print(f"  Lecturer: {lp.Vorname} {lp.Nachname}")
                    else:
                        print(f"  Lecturer: {hcourse.lehrperson.Vorname} {hcourse.lehrperson.Nachname}")
        else:
            print("Failed to process XML data.")

    except FileNotFoundError:
        print(f"Error: The file {xml_file_path} was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
