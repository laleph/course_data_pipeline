#!/usr/bin/env python3
"""
ATU to KEU Course Mapping Module
Maps ATU intermediate JSON format to KreativEU (KEU) Course format
Compatible with the course_data_pipeline architecture
"""

import argparse
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pydantic import HttpUrl

from KreativEU import (
    KEUCourse,
    Language,
    Modus,
    Semester,
    StudyProgramme,
    Term,
    TypeOfCourse,
    University,
)

def custom_json_encoder(obj):
    """Custom JSON encoder to handle pydantic HttpUrl and datetime objects."""
    if isinstance(obj, HttpUrl):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return json.JSONEncoder().default(obj)

def map_atu_to_keu(atu_course: Dict[str, Any]) -> KEUCourse:
    """
    Maps an ATU course dictionary to a KreativEU KEUCourse object.
    
    Args:
        atu_course: Dictionary containing ATU course data
        
    Returns:
        KEUCourse object with mapped data
    """
    
    # --- Basic course information ---
    course_name = atu_course.get('courseName', 'N/A')
    local_course_code = atu_course.get('localCourseCode', 'N/A')
    
    # --- Content and academic information ---
    course_content = atu_course.get('courseContent', 'Course content to be provided.')
    learning_outcomes = atu_course.get('learningOutcomes', 'Learning outcomes to be defined.')
    department = atu_course.get('departmentOrFieldOfStudy', 'N/A (Department)')
    
    # --- Assessment and contact ---
    assessment = atu_course.get('assessment', 'Assessment method to be determined.')
    assigned_contact = atu_course.get('assignedContact', 'Bölüm Öğretim Üyesi')
    
    # --- Link generation ---
    link_url = atu_course.get('linkToLocalWebsiteOrCatalogue')
    if not link_url:
        # Generate default ATU course link
        link_url = f"https://obs.atu.edu.tr/oibs/bologna/progCourseDetails.aspx?curCourse={local_course_code}&lang=en"
    
    # Ensure it's a list of HttpUrl objects
    try:
        course_links = [HttpUrl(link_url)]
    except Exception:
        course_links = [HttpUrl(f"https://obs.atu.edu.tr/oibs/bologna/progCourseDetails.aspx?curCourse={local_course_code}&lang=en")]
    
    # --- Numeric fields ---
    ects_credits = atu_course.get('ectsCredits')
    students_workload = atu_course.get('studentsWorkload')
    
    # --- Optional fields ---
    literature = atu_course.get('literatureAndCourseMaterials')
    
    # --- ATU-specific mappings ---
    university_list = [University.AdanaAlparslanTürkeşScienceandTechnologyUniversity]
    language = Language.English
    modus = Modus.Inperson  # Default for ATU
    study_programme = [StudyProgramme.Bachelor]  # Default, could be enhanced
    type_of_course = TypeOfCourse.Lecture  # Default, could be enhanced
    
    # --- Term information (basic structure) ---
    term_data = None
    if atu_course.get('schedule'):
        term_data = Term(
            semester=Semester.Autumn_Winter,  # Default, could be enhanced
            appointments=[]  # Could be enhanced with schedule parsing
        )
    
    # --- Construct KEUCourse object ---
    keu_course_data = {
        "courseName": course_name,
        "localCourseCode": local_course_code,
        "courseContent": course_content,
        "departmentOrFieldOfStudy": department,
        "learningOutcomes": learning_outcomes,
        "assignedContact": assigned_contact,
        "linkToLocalWebsiteOrCatalogue": course_links,
        "modus": modus,
        "studyProgramme": study_programme,
        "typeOfCourse": type_of_course,
        "university": university_list,
        "language": language,
        
        # Optional fields
        "ectsCredits": ects_credits,
        "studentsWorkload": students_workload,
        "literatureAndCourseMaterials": literature,
        "term": term_data,
        
        # Additional optional fields with defaults
        "email": None,
        "keywords": None,
        "kreativeuMicroCredentials": None,
        "languageLevel": None,
        "maxParticipants": None,
        "minParticipants": 1,
        "moodle": None,
    }
    
    return KEUCourse(**keu_course_data)

def enhance_study_programme(atu_course: Dict[str, Any]) -> List[StudyProgramme]:
    """
    Enhanced study programme detection based on course code or content
    
    Args:
        atu_course: ATU course dictionary
        
    Returns:
        List of appropriate StudyProgramme enums
    """
    course_code = atu_course.get('localCourseCode', '').upper()
    course_name = atu_course.get('courseName', '').lower()
    content = atu_course.get('courseContent', '').lower()
    
    # Basic heuristics for programme detection
    if any(keyword in course_name for keyword in ['master', 'graduate', 'advanced']):
        return [StudyProgramme.Master]
    elif any(keyword in course_name for keyword in ['phd', 'doctoral', 'dissertation']):
        return [StudyProgramme.PhD]
    elif any(keyword in content for keyword in ['master', 'graduate']):
        return [StudyProgramme.Master]
    else:
        return [StudyProgramme.Bachelor]  # Default

def enhance_type_of_course(atu_course: Dict[str, Any]) -> TypeOfCourse:
    """
    Enhanced course type detection based on course information
    
    Args:
        atu_course: ATU course dictionary
        
    Returns:
        Appropriate TypeOfCourse enum
    """
    course_name = atu_course.get('courseName', '').lower()
    content = atu_course.get('courseContent', '').lower()
    schedule = atu_course.get('schedule', '').lower()
    
    # Detection heuristics
    if any(keyword in course_name for keyword in ['lab', 'laboratory', 'practical']):
        return TypeOfCourse.Practical
    elif any(keyword in course_name for keyword in ['seminar', 'workshop']):
        return TypeOfCourse.Seminar
    elif any(keyword in course_name for keyword in ['project', 'thesis', 'capstone']):
        return TypeOfCourse.Project
    elif any(keyword in content for keyword in ['laboratory', 'lab work', 'experiment']):
        return TypeOfCourse.Practical
    elif any(keyword in schedule for keyword in ['lab', 'practical']):
        return TypeOfCourse.Practical
    else:
        return TypeOfCourse.Lecture  # Default

def process_atu_intermediate_json(json_file_path: str) -> List[KEUCourse]:
    """
    Process ATU intermediate JSON file and convert to KEUCourse objects
    
    Args:
        json_file_path: Path to the ATU intermediate JSON file
        
    Returns:
        List of KEUCourse objects
    """
    
    print(f"📂 Loading ATU intermediate data from {json_file_path}")
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File {json_file_path} not found!")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {json_file_path}: {e}")
        return []
    
    # Extract courses from ATU intermediate format
    atu_courses = data.get('ATU', {}).get('courses', [])
    
    if not atu_courses:
        print("❌ No courses found in ATU intermediate data!")
        return []
    
    print(f"📚 Found {len(atu_courses)} ATU courses to process")
    
    keu_courses = []
    successful_mappings = 0
    
    for i, atu_course in enumerate(atu_courses):
        try:
            # Enhanced mapping with type and programme detection
            enhanced_course = atu_course.copy()
            enhanced_course['enhanced_study_programme'] = enhance_study_programme(atu_course)
            enhanced_course['enhanced_type_of_course'] = enhance_type_of_course(atu_course)
            
            # Map to KEUCourse
            keu_course = map_atu_to_keu(enhanced_course)
            
            # Apply enhancements
            keu_course.studyProgramme = enhanced_course['enhanced_study_programme']
            keu_course.typeOfCourse = enhanced_course['enhanced_type_of_course']
            
            keu_courses.append(keu_course)
            successful_mappings += 1
            
            if (i + 1) % 500 == 0:
                print(f"  ✅ Processed {i + 1}/{len(atu_courses)} courses...")
                
        except Exception as e:
            print(f"  ❌ Error mapping course {i} ({atu_course.get('localCourseCode', 'N/A')}): {e}")
            continue
    
    print(f"✅ Successfully mapped {successful_mappings}/{len(atu_courses)} courses")
    
    return keu_courses

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description="Map ATU intermediate JSON to KEU format for KreativEU pipeline."
    )
    parser.add_argument(
        "--json-input",
        type=str,
        help="Path to the ATU intermediate JSON input file (default: atu_intermediate.json)",
        default="atu_intermediate.json",
    )
    parser.add_argument(
        "--json-output",
        type=str,
        help="Path to the KEU JSON output file (default: ATU_keu_courses.json)",
        default="ATU_keu_courses.json",
    )
    
    args = parser.parse_args()
    
    print(f"🚀 ATU to KEU Mapping Started")
    print(f"{'='*50}")
    
    # Process intermediate JSON
    keu_courses = process_atu_intermediate_json(args.json_input)
    
    if not keu_courses:
        print("❌ No courses to save!")
        return False
    
    # Save KEU courses to JSON
    try:
        print(f"💾 Saving {len(keu_courses)} KEU courses to {args.json_output}...")
        
        with open(args.json_output, 'w', encoding='utf-8') as f:
            json.dump(
                [course.model_dump() for course in keu_courses],
                f,
                indent=2,
                ensure_ascii=False,
                default=custom_json_encoder
            )
        
        print(f"✅ Successfully saved KEU courses to {args.json_output}")
        
        # Statistics
        print(f"\\n📊 MAPPING SUMMARY")
        print(f"{'='*40}")
        print(f"📚 Total KEU courses: {len(keu_courses)}")
        print(f"🏫 University: ATU")
        print(f"🌍 Language: English")
        print(f"📁 Output: {args.json_output}")
        
        # Study programme distribution
        programme_counts = {}
        type_counts = {}
        
        for course in keu_courses:
            # Study programmes
            for prog in course.studyProgramme:
                prog_value = prog.value if hasattr(prog, 'value') else str(prog)
                programme_counts[prog_value] = programme_counts.get(prog_value, 0) + 1
            
            # Course types
            type_value = course.typeOfCourse.value if hasattr(course.typeOfCourse, 'value') else str(course.typeOfCourse)
            type_counts[type_value] = type_counts.get(type_value, 0) + 1
        
        if programme_counts:
            print(f"\\n📈 STUDY PROGRAMMES:")
            for prog, count in programme_counts.items():
                print(f"  • {prog}: {count} courses")
        
        if type_counts:
            print(f"\\n🎯 COURSE TYPES:")
            for course_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {course_type}: {count} courses")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving KEU courses: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\\n🎉 ATU to KEU mapping completed successfully!")
    else:
        print(f"\\n❌ ATU to KEU mapping failed!")
