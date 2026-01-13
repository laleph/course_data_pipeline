"""KreativEU (KEU) Course Data Model

This module defines Pydantic models and enums for representing KreativEU course data.
It provides structured data models for:
- Course metadata (KEUCourse)
- Educational program details (StudyProgramme, University)
- Course delivery modes (Modus)
- Term scheduling information
- JSON schema for validation and documentation

The module includes:
- Enum classes for standardized values (e.g., Language, Modus, StudyProgramme)
- Pydantic models for course entries and related entities
- Automatic JSON schema generation for the KEUCourse model

Used in conjunction with the HIS2KEU_mapping module for data transformation
between HIS and KreativEU formats.
"""

import json
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, NonNegativeFloat, PositiveInt
from pydantic.config import ConfigDict

# Enums remain largely the same, but Pydantic can work with them directly.
# For string enums, it's common to inherit from str for better FastAPI/JSON schema generation.

# Alternative: json to pydantic model
# https://docs.pydantic.dev/latest/integrations/datamodel_code_generator/#installation


class Language(str, Enum):
    """The language of instruction."""

    Bulgarian = "Bulgarian"
    Czech = "Czech"
    Dutch = "Dutch"
    English = "English"
    German = "German"
    Italian = "Italian"
    Other = "Other"
    Polish = "Polish"
    Portuguese = "Portuguese"
    Romanian = "Romanian"
    Slovakian = "Slovakian"
    Swedish = "Swedish"
    Turkish = "Turkish"


class Modus(str, Enum):
    """The mode of delivery, e.g., Online, In-person, Hybrid."""

    Hybrid = "Hybrid"
    Inperson = "In-person"
    Online = "Online"


class StudyProgramme(str, Enum):
    """The study programme the course belongs to, e.g., Bachelor, Master, PhD and Lifelong Learning."""

    Bachelor = "Bachelor"
    Master = "Master"
    LifelongLearning = "Lifelong Learning"  # This is a placeholder for LLL, micro-credentials, etc.
    PhD = "PhD"


class CourseCycle(str, Enum):
    """The cycle of the course, e.g., Block or Weekly course, etc."""

    Block = "Block"
    Flexible = "Flexible"
    Weekly = "Weekly"
    SingleEvent = "Single Event"
    BiWeekly = "Bi-Weekly"
    Monthly = "Monthly"
    Quarterly = "Quarterly"
    # from here on not really necessary if each semester is separate
    Annual = "Annual"
    BiAnnual = "Bi-Annual"


class Semester(str, Enum):
    """The semester in which the course is offered, e.g., Autumn/Winter.
    Autumn/Winter is the time from Autumn to Spring
    Spring/Summer is the time from Spring to Autumn.
    """

    Spring_Summer = "Spring/Summer"
    Autumn_Winter = "Autumn/Winter"


class Appointment(BaseModel):
    """An appointment for a course."""

    # TODO this needs changing, e.g. format of schedule, or derived from dates?
    # datatime.date .datetime .time .timedelta
    courseCycle: Optional[CourseCycle] = Field(
        default=None,
        alias="courseCycle",
        description="The cycle of the course's appointment, e.g., Block course, Weekly course.",
    )
    # TODO correct? derive weekday from start, end and courseCycle, so that it needs to be datetime
    start: Optional[datetime] = Field(
        default=None, alias="start", description="The start of the appointment."
    )
    end: Optional[datetime] = Field(
        default=None, alias="end", description="The end of the appointment."
    )

    startDate: Optional[datetime] = Field(
        default=None,
        alias="startDate",
        description="The start date of the appointment.",
    )
    endDate: Optional[datetime] = Field(
        default=None, alias="endDate", description="The end date of the appointment."
    )


class Term(BaseModel):
    """General term information for a course."""

    # frequency_of_the_course: Optional[FrequencyOfTheCourse] = Field(default=None, alias="frequencyOfTheCourse", description="How often the course is offered (e.g., Every semester, Every year).")
    registrationEnd: Optional[datetime] = Field(
        default=None,
        alias="registrationEnd",
        description="The end date for course registration.",
    )
    registrationStart: Optional[datetime] = Field(
        default=None,
        alias="registrationStart",
        description="The start date for course registration.",
    )
    semester: Optional[Semester] = Field(
        default=None,
        description="The semester in which the course is offered, e.g., Autumn/Winter",
    )
    appointments: Optional[List[Appointment]] = Field(
        default=None,
        description="A list of appointments for the course.",
    )


class TypeOfCourse(str, Enum):
    """The type of course, e.g., Lecture, Seminar, BIP, COIL, etc.."""

    BIP = "BIP"
    COIL = "COIL"
    Excursion = "Excursion"
    Hackathon = "Hackathon"
    Internship = "Internship"
    Lecture = "Lecture"
    MOOC = "MOOC"
    Practical = "Practical"
    Project = "Project"
    Seminar = "Seminar"
    SummerSchool = "Summer School"
    Other = "Other"  # TODO remove?


class University(str, Enum):
    """Name of the university offering the course."""

    ATU = "Adana Alparslan Türkeş Science and Technology University"
    BUas = "Breda University of Applied Sciences"
    TAE = "D. A. Tsenov Academy of Economics"
    OUTech = "Opole University of Technology"
    IPT = "Polytechnic University of Tomar"
    SH = "Södertörn University"
    UNICAM = "University of Camerino"
    UG = "University of Greifswald"
    USB = "University of South Bohemia in České Budějovice"
    TUT = "University of Trnava"
    VUT = "Valahia University of Târgoviște"


class KEUCourse(BaseModel):
    """Schema for a university course catalogue entry."""

    # assessment: str = Field(
    #     description="Description of how the course will be assessed (e.g., Exam, Project, Presentation)."
    # )
    assignedContact: str = Field(
        description="Name of contact person for course-related inquiries or course instructor."
    )
    courseContent: str = Field(
        description="Detailed description of the course's content, prerequisites, assessment, etc."
    )
    courseName: str = Field(description="The official name of the course.")
    departmentOrFieldOfStudy: str = Field(
        description="Department, faculty or field of study the course belongs to (e.g., Physics)."
    )
    ectsCredits: Optional[NonNegativeFloat] = Field(
        default=None,
        ge=0,
        description="The number of ECTS credits awarded for completing the course.",
    )
    # faculty: str = Field(
    #     # TODO necessary? faculties and institutes vary among partners, e.g.,
    #     # Institute or Faculty of Physics, etc.
    #     description="The faculty or institute offering the course (e.g., Faculty of Science)."
    # )
    learningOutcomes: Optional[str] = Field(
        default=None,
        description="What students will be able to do after completing the course.",
    )
    linkToLocalWebsiteOrCatalogue: List[HttpUrl] = Field(
        description="A link to the course's page on the university's website or course catalogue."
    )
    localCourseCode: str = Field(
        description="The course code used within the local university's system."
    )
    modus: Modus = Field(description="The mode of delivery, e.g., Online, In-person, Hybrid.")
    LMS: Optional[List[HttpUrl]] = Field(
        description="Link to the local course page on the L(earning) M(anagement) S(ystem), e.g., Moodle.",
        default=None,
    )
    studentsWorkload: Optional[float] = Field(
        default=None,
        ge=1,
        description="Estimate of the expected student workload per week in hours,e.g., 5 (hours).",
    )
    studyProgramme: List[StudyProgramme] = Field(
        description="The study programme the course belongs to, e.g., Bachelor, Master, PhD and Lifelong Learning."
    )
    typeOfCourse: List[TypeOfCourse] = Field(
        description="The type of course, e.g., Lecture, Seminar, BIP, etc. Multiple values allowed."
    )
    university: List[University] = Field(
        description="Name of the university offering the course (including abbreviation). Multiple values allowed for Joint Courses."
    )
    email: Optional[List[EmailStr]] = Field(
        default=None, description="The email address for course-related inquiries."
    )
    keywords: Optional[List[str]] = Field(
        default=None, description="Keywords related to the course."
    )
    kreativeuMicroCredentials: Optional[NonNegativeFloat] = Field(
        default=None,
        description="Number of KreativeU micro-credentials associated with the course.",
    )
    language: Language = Field(description="The language of instruction.")
    languageLevel: Optional[str] = Field(
        default=None, description="The required language level (e.g., B2, C1)."
    )
    literatureAndCourseMaterials: Optional[str] = Field(
        default=None,
        description="A list of required and recommended reading materials.",
    )
    maxParticipants: Optional[int] = Field(
        default=None,
        ge=1,
        description="The maximum number of students allowed in the course.",
    )
    minParticipants: Optional[int] = Field(
        default=1,
        ge=1,
        description="The minimum number of students required for the course to run.",
    )
    # prerequisites: Optional[str] = Field(
    #     default=None, description="Any required prior knowledge or courses."
    # )
    term: Optional[Term] = Field(default=None)
    KEUCourse: Optional[bool] = Field(default=None, description="Is the course a KreativEU course?")

    model_config = ConfigDict(
        use_enum_values=True,  # To serialize enums to their values
        validate_by_name=True,  # To allow populating by alias, if you use aliases
        str_strip_whitespace=True,  # Good practice for string fields
        validate_assignment=True,  # Re-validate on assignment
        title="KreativEU Course",
    )


single_course_schema = (
    KEUCourse.model_json_schema()
)  # generate JSON-compatible schema from pydantic model

# added mappings for abbreviation <-> full university name
single_course_schema["uni2abbreviation"] = {e.value: e.name for e in University}
single_course_schema["abbreviation2uni"] = {e.name: e.value for e in University}

# Save the JSON schema to a file.
with open("course_catalogue_schema.json", "w", encoding="utf-8") as f:
    json.dump(single_course_schema, f, ensure_ascii=False, indent=2)


class SemesterInfo(BaseModel):
    """Semester information for the catalogue."""

    semester: List[Semester] = Field(
        description="The semester in which the course is offered. See Semester definition."
    )
    year: List[PositiveInt] = Field(
        description="Year in which the course is offered. Only use a single year information, e.g., 2026 instead of 2025/26",
        ge=2025,  # birth year of KreativEU
        lt=2100,  # far in the future
    )


class Contact(BaseModel):
    """Contact information for the catalogue."""

    name: List[str] = Field(description="Name(s) of the contact person(s).")
    email: List[EmailStr] = Field(description="Email address(es) of the contact person(s).")


class CatalogueMetadata(BaseModel):
    """Metadata about the catalogue."""

    # TODO python semver + pydantic
    version: str = Field(description="Version of the catalogue.")
    dateOfGeneration: datetime = Field(description="Date when the catalogue was generated.")
    contact: Contact = Field(description="Contact information for the catalogue.")
    semester: SemesterInfo = Field(
        description="Semester information. Only use a single year information, e.g., 2026 instead of 2025/26"
    )


# Define a model for the entire course catalogue
class CourseCatalogue(BaseModel):
    """Schema for a complete KreativEU course catalogue."""

    metadata: CatalogueMetadata = Field(
        description="Metadata about the catalogue, such as version, generation date and contact."
    )
    courses: List[KEUCourse] = Field(description="List of KreativEU courses in the catalogue.")

    model_config = ConfigDict(
        use_enum_values=True,
        validate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        title="KreativEU Course Catalogue",
    )


# Generate JSON schema for the entire catalogue
catalogue_schema = CourseCatalogue.model_json_schema()

# Save the JSON schema for the catalogue to a separate file.
with open("course_catalogue_full_schema.json", "w", encoding="utf-8") as f:
    json.dump(catalogue_schema, f, ensure_ascii=False, indent=2)

