#!/usr/bin/env python3
"""
ATU XML to JSON Converter for KreativEU Pipeline
Specifically designed for KEU_All_EN_Course.xml file from ATU
Converts table-based XML structure to intermediate JSON format
"""

import argparse
import json
import re
import time
from typing import Dict, List, Optional, Any
from collections import defaultdict

def extract_atu_courses_from_xml(xml_file: str) -> List[Dict[str, Any]]:
    """
    Extract course data from ATU XML file using regex-based table parsing
    
    Args:
        xml_file: Path to the KEU_All_EN_Course.xml file
        
    Returns:
        List of course dictionaries in intermediate format
    """
    print(f"📁 Reading ATU XML file: {xml_file}")
    start_time = time.time()
    
    try:
        with open(xml_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: XML file {xml_file} not found!")
        return []
    except Exception as e:
        print(f"❌ Error reading XML file: {e}")
        return []
    
    read_time = time.time() - start_time
    print(f"⏱️ File read in {read_time:.2f} seconds")
    print(f"📊 File size: {len(content):,} characters")
    
    # Find all table elements using regex
    print(f"🔍 Extracting table data...")
    table_pattern = r'<table[^>]*>(.*?)</table>'
    tables = re.findall(table_pattern, content, re.DOTALL | re.IGNORECASE)
    print(f"📋 Found {len(tables)} tables")
    
    courses = []
    processed_codes = set()  # To avoid duplicates
    
    print(f"🔄 Processing tables...")
    for i, table_content in enumerate(tables):
        if (i + 1) % 5000 == 0:
            print(f"  ✅ Processed {i + 1}/{len(tables)} tables...")
        
        try:
            course = extract_course_from_table(table_content)
            if course and course.get('localCourseCode'):
                # Check for duplicates
                course_code = course['localCourseCode']
                if course_code not in processed_codes:
                    courses.append(course)
                    processed_codes.add(course_code)
        except Exception as e:
            continue  # Skip problematic tables
    
    print(f"✅ Extraction completed!")
    print(f"📚 Total unique courses extracted: {len(courses)}")
    
    return courses

def extract_course_from_table(table_content: str) -> Optional[Dict[str, Any]]:
    """
    Extract course information from a single table element
    
    Args:
        table_content: HTML table content as string
        
    Returns:
        Dictionary with course information or None if extraction fails
    """
    
    # Define field patterns for ATU courses
    patterns = {
        'courseName': r'<td[^>]*>\s*([A-Za-z][^<]{3,}?)\s*</td>',
        'localCourseCode': r'<td[^>]*>\s*([A-Z]{2,4}[-_]?\s*\d{2,4}[A-Z]?)\s*</td>',
        'departmentOrFieldOfStudy': r'<td[^>]*>\s*([A-Za-z].*?(?:Engineering|Management|Science|Administration|Architecture|Studies|Design|Arts|Law|Medicine|Nursing|Economics|Finance|Technology|Tourism|Education|Literature|Philosophy|Psychology|Sociology|Mathematics|Physics|Chemistry|Biology|Computer|Information|Industrial|Civil|Mechanical|Electrical|Chemical|Food|Materials|Aerospace|Bioengineering|Mining)[^<]*)\s*</td>',
        'courseContent': r'<td[^>]*>\s*([A-Za-z][^<]{20,}?[.!?])\s*</td>',
        'learningOutcomes': r'<td[^>]*>\s*((?:To |Upon |After |Students |The student)[^<]{20,}?[.!?])\s*</td>',
        'assessment': r'<td[^>]*>\s*((?:Exam|Assessment|Project|Presentation|Assignment|Quiz|Test|Midterm|Final|Portfolio|Homework|Lab|Report|Thesis|Paper|Essay|Oral|Written|Practical|Continuous|Coursework|Grading|Evaluation)[^<]*?)\s*</td>',
        'assignedContact': r'<td[^>]*>\s*((?:Prof|Dr|Asst|Assoc|Lecturer|Instructor|Faculty|Department|Staff|Member|Teacher)[^<]*?)\s*</td>',
        'linkToLocalWebsiteOrCatalogue': r'<td[^>]*>\s*(https?://[^\s<]+)\s*</td>',
        'ectsCredits': r'<td[^>]*>\s*(\d+(?:\.\d+)?)\s*</td>',
        'studentsWorkload': r'<td[^>]*>\s*(\d+)\s*(?:hours?|saat|hour|h)?\s*</td>',
        'literatureAndCourseMaterials': r'<td[^>]*>\s*([A-Za-z][^<]{10,}?(?:book|Book|edition|Edition|Author|author|publisher|Publisher|ISBN|isbn|literature|Literature|material|Material|reference|Reference|text|Text|manual|Manual|guide|Guide)[^<]*?)\s*</td>',
        'schedule': r'<td[^>]*>\s*(\d+\s*hours?.*?(?:Theory|Practice|Lab|Laboratory|Lecture|Tutorial)[^<]*?)\s*</td>'
    }
    
    course = {}
    
    # Extract each field
    for field, pattern in patterns.items():
        matches = re.findall(pattern, table_content, re.IGNORECASE | re.DOTALL)
        if matches:
            # Take the most relevant match
            value = matches[0].strip()
            if value and len(value) > 1:  # Avoid single characters
                if field in ['ectsCredits', 'studentsWorkload']:
                    try:
                        course[field] = int(float(value))
                    except (ValueError, TypeError):
                        course[field] = None
                else:
                    # Clean up the value
                    value = re.sub(r'\s+', ' ', value)  # Normalize whitespace
                    value = value.strip()
                    course[field] = value
    
    # Set ATU-specific defaults
    course['university'] = "Adana Alparslan Türkeş Science and Technology University"
    course['language'] = "English"
    course['modus'] = "In-person"
    course['studyProgramme'] = "Bachelor"
    course['typeOfCourse'] = "Lecture"
    
    # Only return if we have essential fields
    if course.get('courseName') and course.get('localCourseCode'):
        return course
    
    return None

def convert_to_intermediate_format(courses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convert extracted courses to intermediate JSON format compatible with pipeline
    
    Args:
        courses: List of course dictionaries
        
    Returns:
        Dictionary in intermediate format for pipeline processing
    """
    
    # Create structure similar to UG's intermediate format
    intermediate_data = {
        "ATU": {
            "courses": courses,
            "metadata": {
                "university": "Adana Alparslan Türkeş Science and Technology University",
                "totalCourses": len(courses),
                "language": "English",
                "extractionDate": time.strftime("%Y-%m-%d %H:%M:%S"),
                "dataSource": "KEU_All_EN_Course.xml"
            }
        }
    }
    
    return intermediate_data

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description="Convert ATU XML course data to intermediate JSON format for KreativEU pipeline."
    )
    parser.add_argument(
        "--xml-file",
        type=str,
        help="Path to the ATU XML data input file (default: KEU_All_EN_Course.xml)",
        default="KEU_All_EN_Course.xml",
    )
    parser.add_argument(
        "--json-output",
        type=str,
        help="Path to the intermediate JSON data output file (default: atu_intermediate.json)",
        default="atu_intermediate.json",
    )
    
    args = parser.parse_args()
    
    print(f"🚀 ATU XML to JSON Converter Started")
    print(f"{'='*60}")
    
    # Extract courses from XML
    courses = extract_atu_courses_from_xml(args.xml_file)
    
    if not courses:
        print("❌ No courses found in the XML file!")
        return False
    
    # Convert to intermediate format
    print(f"🔄 Converting to intermediate format...")
    intermediate_data = convert_to_intermediate_format(courses)
    
    # Save intermediate JSON
    try:
        print(f"💾 Saving intermediate data to {args.json_output}...")
        with open(args.json_output, 'w', encoding='utf-8') as f:
            json.dump(intermediate_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully saved {len(courses)} courses to {args.json_output}")
        
        # Quick statistics
        print(f"\\n📊 EXTRACTION SUMMARY")
        print(f"{'='*40}")
        print(f"📚 Total courses: {len(courses)}")
        print(f"🏫 University: ATU")
        print(f"🌍 Language: English")
        print(f"📁 Output: {args.json_output}")
        
        # Department distribution
        dept_counts = defaultdict(int)
        for course in courses:
            dept = course.get('departmentOrFieldOfStudy', 'Unknown')
            dept_counts[dept] += 1
        
        if dept_counts:
            print(f"\\n🏢 TOP 5 DEPARTMENTS:")
            for dept, count in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  • {dept}: {count} courses")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving intermediate JSON: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\\n🎉 ATU XML conversion completed successfully!")
    else:
        print(f"\\n❌ ATU XML conversion failed!")
