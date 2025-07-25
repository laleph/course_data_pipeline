import json
from KreativEU import KEUCourse

def generate_schema():
    """Generates the JSON schema for the KEUCourse model and saves it to a file."""
    schema = KEUCourse.model_json_schema()
    with open("course_catalogue_schema.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print("Successfully generated course_catalogue_schema.json")

if __name__ == "__main__":
    generate_schema()
