"""HIS2KEU Course Mapping

This module provides utilities to transform data from HISCourse to the KreativEU (KEU) Course format.
It includes functions for:
- Date/time parsing from HIS-specific formats
- Type mapping between HIS and KEUCourse enums
- Custom JSON serialization for pydantic HttpUrl objects
- Data transformation and validation

The module relies on:
- `pydantic` for data validation and model handling
- `HISCourse` and `KEUCourse` data models from respective modules

Usage:
- Run as a script to process a JSON file and output KEUCourse data
- Import functions like `map_his_to_keu` for programmatic data transformation
"""

import argparse
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, TypeVar, Union

from pydantic import HttpUrl

from HISCourse import CourseCycle as HISCourseCycle
from HISCourse import (
    HISCourse,
    RootResponse,
    Termin,
)
from HISCourse import Typ as HISCourseTyp
from KreativEU import CourseCycle as KEUCourseCycle
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

T = TypeVar("T")  # Define T as a TypeVar


def custom_json_encoder(o):
    """Custom JSON encoder to handle pydantic HttpUrl and datetime objects."""
    if isinstance(o, HttpUrl):
        return str(o)
    elif isinstance(o, datetime):
        return o.isoformat()
    return json.JSONEncoder().default(o)


def get_first_item(data_obj: Optional[Union[List[T], T]]) -> Optional[T]:
    """Helper function to get the first item if data is a list,
    or data itself if it's a single item."""
    if isinstance(data_obj, list):
        return data_obj[0] if data_obj else None
    return data_obj


TYPE_OF_COURSE_MAPPING: Dict[HISCourseTyp, TypeOfCourse] = {
    HISCourseTyp.Practical: TypeOfCourse.Practical,
    HISCourseTyp.Archive_Seminar: TypeOfCourse.Seminar,
    HISCourseTyp.Colloquium: TypeOfCourse.Lecture,
    HISCourseTyp.Seminar: TypeOfCourse.Seminar,
    HISCourseTyp.Introductory_Seminar: TypeOfCourse.Seminar,
    HISCourseTyp.Seminar_Lecture: TypeOfCourse.Lecture,  # Prioritizing Lecture
    HISCourseTyp.Excursion: TypeOfCourse.Excursion,
    HISCourseTyp.Course: TypeOfCourse.Lecture,  # General term, mapping to Lecture
    HISCourseTyp.Foundation_Course: TypeOfCourse.Lecture,
    HISCourseTyp.Block_Seminar: TypeOfCourse.Seminar,
    HISCourseTyp.Test: TypeOfCourse.Other,  # Assessment, not a course type
    HISCourseTyp.Lecture: TypeOfCourse.Lecture,
    HISCourseTyp.Advanced_Seminar: TypeOfCourse.Seminar,
    HISCourseTyp.Examination: TypeOfCourse.Other,  # Assessment
    HISCourseTyp.Artistic_Training: TypeOfCourse.Practical,
    HISCourseTyp.Practice: TypeOfCourse.Practical,
    HISCourseTyp.Seminar_Practical: TypeOfCourse.Seminar,  # Prioritizing Seminar
    HISCourseTyp.Lecture_Practical_Course: TypeOfCourse.Practical,  # Prioritizing Lecture
    HISCourseTyp.Practical_Course: TypeOfCourse.Practical,
}

COURSE_CYCLE_MAP = {
    HISCourseCycle.Block: KEUCourseCycle.Block,
    HISCourseCycle.Block_Sa: KEUCourseCycle.Block,
    HISCourseCycle.Singular: KEUCourseCycle.SingleEvent,
    HISCourseCycle.a14day: KEUCourseCycle.BiWeekly,
    HISCourseCycle.n_V: KEUCourseCycle.Flexible,
    HISCourseCycle.Monthly: KEUCourseCycle.Monthly,
    HISCourseCycle.Block_SaSo: KEUCourseCycle.Block,
    HISCourseCycle.BlockSaSo: KEUCourseCycle.Block,
    HISCourseCycle.Weekly: KEUCourseCycle.Weekly,
}

# TODO necessary? derive weekday from iso format?
DAY_MAP_HIS_TO_VERBOSE = {
    "Mo": "Mondays",
    "Di": "Tuesdays",
    "Mi": "Wednesdays",
    "Do": "Thursdays",
    "Fr": "Fridays",
    "Sa": "Saturdays",
    "So": "Sundays",
}


def parse_his_datetime(
    date_str: Optional[str], time_str: Optional[str] = None
) -> Optional[datetime]:
    """Parses date and optional time strings from HIS format to datetime objects (ISO 8601) in UTC."""
    if not date_str:
        return None
    try:
        if time_str:
            # Parse date and time in DD.MM.YYYY HH:MM format
            return datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M").astimezone(
                tz=timezone.utc
            )

        # Parse date only
        return datetime.strptime(date_str, "%d.%m.%Y").astimezone(
            tz=timezone.utc
        )  # Date only, time defaults to 00:00:00
    except ValueError:
        # warning if parsing fails
        # print(f"Warning: Could not parse date '{date_str}' with time '{time_str}'")
        return None


def map_his_to_keu(
    his_course: HISCourse,
    university: University,
    default_language: Language = Language.English,
    # default_ects: int = 5,
    default_modus: Modus = Modus.Inperson,
) -> KEUCourse:
    """Maps a HISCourse object to a KreativEU KEUCourse object."""

    # --- Basic Info ---
    course_name = his_course.titel
    local_course_code = his_course.id

    # --- Contact Person ---
    his_lehrperson = get_first_item(his_course.lehrperson)  # TODO only first contact? correct
    assigned_contact_parts = []
    if his_lehrperson:
        if his_lehrperson.Vorname:
            assigned_contact_parts.append(his_lehrperson.Vorname)
        if his_lehrperson.Nachname:
            assigned_contact_parts.append(his_lehrperson.Nachname)
    assigned_contact = " ".join(assigned_contact_parts) if assigned_contact_parts else "N/A (Staff)"

    # # --- Faculty & Department ---
    # his_einrichtung = get_first_item(his_course.einrichtung)
    # faculty = (
    #     his_einrichtung.Einrichtung
    #     if his_einrichtung and his_einrichtung.Einrichtung
    #     else "Unknown Faculty"
    # )

    his_einrichtung = get_first_item(his_course.einrichtung)
    his_studiengang_item = get_first_item(his_course.studiengang)
    department_or_field_of_study = (
        his_studiengang_item.Studiengang
        if his_studiengang_item and his_studiengang_item.Studiengang
        # f"Department: {his_einrichtung.Einrichtung}"
        else (
            f"{his_einrichtung.Einrichtung}"
            if his_einrichtung and his_einrichtung.Einrichtung
            else "N/A (Department)"
        )
    )

    # --- Study Programme ---
    # Default include all
    study_programme_val = [
        StudyProgramme.Bachelor,
        StudyProgramme.Master,
        StudyProgramme.PhD,
    ]
    if his_studiengang_item and his_studiengang_item.Studiengang:
        sg_lower = his_studiengang_item.Studiengang.lower()
        if "bachelor" in sg_lower:
            study_programme_val = [StudyProgramme.Bachelor]
        elif "master" in sg_lower:
            study_programme_val = [StudyProgramme.Master]
        elif "phd" in sg_lower or "doktor" in sg_lower:
            study_programme_val = [StudyProgramme.PhD]

    # --- Type of Course ---
    type_of_course_val = TYPE_OF_COURSE_MAPPING.get(his_course.typ, TypeOfCourse.Other)

    # --- Term Information ---
    kreativeu_term_data = {}
    all_his_termine: List[Termin] = []
    if his_course.termin:
        if isinstance(his_course.termin, list):
            all_his_termine = his_course.termin
        else:
            all_his_termine = [his_course.termin]

    if all_his_termine:
        appointments = []

        for t in all_his_termine:
            s_dt = parse_his_datetime(t.startdat, t.start)
            e_dt = parse_his_datetime(t.enddat, t.end)

            appointment = {}

            appointment["courseCycle"] = COURSE_CYCLE_MAP[t.type]
            # time of the appointment as datetime in order to derive weekdays in UTC
            appointment["start"] = s_dt
            appointment["end"] = e_dt
            # dates for the start and end of the series, e.g., for weekly this usually means the first and last day of the lecture series
            # in UTC, so that the CC app can use it for scheduling
            appointment["startDate"] = s_dt
            appointment["endDate"] = e_dt

            appointments.append(appointment)

        kreativeu_term_data["appointments"] = appointments

    # Semester
    if his_course.semid:
        sem_lower = his_course.semid.lower()
        if "wise" in sem_lower or "winter" in sem_lower:
            kreativeu_term_data["semester"] = Semester.Autumn_Winter
        elif "sose" in sem_lower or "summer" in sem_lower:
            kreativeu_term_data["semester"] = Semester.Spring_Summer

    kreativeu_term_instance = Term(**kreativeu_term_data) if kreativeu_term_data else None

    def combine_course_content():
        """Combine the content with additional sections found in HIS."""
        if his_course.lerninhalt is None:
            primary_content = ""
        else:
            primary_content = his_course.lerninhalt

        additional_sections = []

        if his_course.nachweis:
            additional_sections.append(f"\n## **Assessment**\n{his_course.nachweis}")

        if his_course.kommentar:
            additional_sections.append(f"\n## **Comments**\n{his_course.kommentar}")

        if his_course.bemerkung:
            # This field might be redundant as Bemerkung and Kommentar are similar in meaning.
            additional_sections.append(f"\n## **Remarks**\n{his_course.bemerkung}")

        if his_course.zugang:
            additional_sections.append(f"\n## **Access Requirements**\n{his_course.zugang}")

        return f"{primary_content}\n\n" + "\n\n".join(additional_sections)

    def handle_email():
        """Email got to complicated. Here is the separate logic."""
        termin_list = (
            his_course.termin
            if isinstance(his_course.termin, list)
            else [his_course.termin] if his_course.termin is not None else []
        )
        email_list = [
            person.EMail
            for termin in termin_list
            if termin.person is not None  # Skip if termin.person is None
            for person in (termin.person if isinstance(termin.person, list) else [termin.person])
            if person is not None
            and person.EMail is not None  # Skip None persons and missing emails
        ]
        return email_list

    def handle_moodle_url():
        # Handle both single and list of URLs
        moodle_url = (
            [HttpUrl(url) for url in his_course.moodle]
            if isinstance(his_course.moodle, list)
            else ([HttpUrl(his_course.moodle)] if his_course.moodle else [])
        )
        return moodle_url

    def handle_moodle_and_catalogue_url():
        # Handle both single and list of URLs
        moodle_url = handle_moodle_url()
        if moodle_url:
            return moodle_url
        else:
            # if empty default to HIS link
            return [
                HttpUrl(
                    "https://his.uni-greifswald.de/qisserver/rds?state=change&type=5&moduleParameter=veranstaltungSearch&nextdir=change&next=search.vm&subdir=veranstaltung&_form=display&function=search&clean=y&category=veranstaltung.search&navigationPosition=lectures%2Csearch&breadcrumb=searchLectures&topitem=lectures&subitem=search&noDBAction=y&init=y"
                )
            ]

    # --- Construct KEUCourse ---
    # TODO only add compulsory items and leave voluntary elements if empty
    keu_course_data = {
        "assignedContact": assigned_contact,
        "courseContent": combine_course_content()
        or his_course.kommentar
        or "Detailed course content to be provided.",
        "courseName": course_name,
        "departmentOrFieldOfStudy": department_or_field_of_study,
        "ectsCredits": None,
        # "faculty": faculty,
        "learningOutcomes": his_course.zielgruppe,
        # or "Specific learning outcomes to be defined.",  # zielgruppe might be better for outcomes
        "linkToLocalWebsiteOrCatalogue": handle_moodle_and_catalogue_url(),  # TODO add detailed link to Catalogue
        "localCourseCode": local_course_code,
        "modus": default_modus,  # TODO check again if there is a corresponding HIS data element
        "studentsWorkload": (
            his_course.sws if his_course.sws is not None else None
        ),  # SWS means weekly hours
        "studyProgramme": study_programme_val,
        "typeOfCourse": [type_of_course_val],
        # Uni passed as a parameter, UG only within list
        "university": [university],  # TODO check whether many universities possible in HIS?!
        "language": default_language,  # Passed as parameter
        # Optional fields from HISCourse
        "literatureAndCourseMaterials": his_course.literatur,
        "maxParticipants": (
            his_course.maxTeilnehmer
            if his_course.maxTeilnehmer is not None and his_course.maxTeilnehmer > 0
            else None
        ),  # Ensure positive
        "minParticipants": 1,  # Default from KEUCourse model, HIS doesn't provide this
        "term": kreativeu_term_instance,
        # Other optional fields in KEUCourse not directly from HISCourse
        "email": handle_email(),
        # TODO generate keywords from content, etc. with AI
        "keywords": None,
        # not yet existing at UG
        "kreativeuMicroCredentials": None,
        # first English only, for future (non-)English courses
        "languageLevel": None,
        "LMS": handle_moodle_url(),
    }

    # Pydantic handles optional fields defaulting to None if not provided.
    # So, filtering None is mostly for clarity.
    # filtered_keu_course_data = {k: v for k, v in keu_course_data.items() if v is not None}

    return KEUCourse(**keu_course_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Map a JSON file with course catalogue data to the KEU format."
    )
    parser.add_argument(
        "--json-input",
        type=str,
        help="Path to the JSON data input file (default: intermediate.json)",
        default="intermediate.json",
    )
    parser.add_argument(
        "--json-output",
        type=str,
        help="Path to the KEU JSON data output file (default: UG_keu_courses.json)",
        default="UG_keu_courses.json",
    )
    args = parser.parse_args()
    JSON_FILE_PATH = args.json_input
    JSON_OUTPUT_FILE_PATH = args.json_output

    keu_courses = []
    try:
        # Load the JSON data from the file
        with open(JSON_FILE_PATH, encoding="utf-8") as f:
            data = json.load(f)

        # Parse the data using the RootResponse model
        root_response = RootResponse.model_validate(data)

        his_courses_list = root_response.KreativEU.veranstaltung

        if not his_courses_list:
            print(f"No courses found in {JSON_FILE_PATH}")

        print(f"Found {len(his_courses_list)} HIS courses. Mapping to KEUCourse format...\n")
        i = 1
        for course_instance in his_courses_list:
            print(f"--- Processing HIS Course {i}: {course_instance.titel} ({course_instance.id})")
            try:
                # Map to KEUCourse
                # Ensure University.UniversityofGreifswald is a valid enum member in KreativEU.py
                # or use a different university as appropriate.
                mapped_course = map_his_to_keu(
                    course_instance,
                    university=University.UG,
                    default_language=Language.English,
                    # default_ects=5,
                    default_modus=Modus.Inperson,
                )

                # remove tests from the KEU courses list
                if mapped_course.typeOfCourse == TypeOfCourse.Other:
                    continue
                else:
                    keu_courses.append(mapped_course)
                    i += 1
                    print("Mapped KEUCourse:")
                    print(mapped_course.model_dump_json(indent=2))
                    print("-" * 40 + "\n")

            except Exception as e:
                print(f"An error occurred during mapping course '{course_instance.titel}': {e}")
                print("HISCourse data:", course_instance.model_dump_json(indent=2))
                print("-" * 40 + "\n")

    except FileNotFoundError:
        print(f"Error: The file {JSON_FILE_PATH} was not found. Please create it with xml2json.py.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {JSON_FILE_PATH}. Please ensure it's valid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # Save the mapped KEUCourses to a JSON file.
    with open(JSON_OUTPUT_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(
            [course.model_dump() for course in keu_courses],
            f,
            indent=2,
            default=custom_json_encoder,  # necessary since JSON does not know urls?!
        )
