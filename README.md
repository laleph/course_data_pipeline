# course data pipeline

This is an exemplary pipeline that returns all courses taught in English from an XML format and transforms them into JSON.

---

## 🧰 Dependencies

Installed via `pyproject.toml` using `uv`:

- `defusedxml` (safely parse XML)
- `pydantic` (data validation and serialization)
- `xmltodict` (XML-to-JSON conversion)
- Other utilities: `bleach`, `markdownify`

---

## 🚀 Usage

1. **Install dependencies**
   Ensure Python environment is installed. Run:

   ```bash
   uv sync
   ```

2. **Run the pipeline**
   Execute the shell script:

   ```bash
   ./whole_pipeline.sh
   ```

   This:
   - Fetches XML data (from `test_SOAP_for_KEU_demo.xml`) if it exists (see the note in `whole_pipeline.sh` to receive the XML file).
   - Converts XML to an intermediate JSON file (`intermediate.json`).
   - Maps data to KreativEU format.

3. **Output**
   Intermediate and final JSON files are generated in the working directory.

---

## 📌 Notes

- Review `whole_pipeline.sh` for step-by-step execution details.
- Check `src/KreativEU.py` for course data definition and JSON schema output.
- The `xml2json.py` script handles duplicate entries, sanitizes the XML data and converts it to JSON format.
- The `HIS2KEU_mapping.py` script maps courses to KEU courses.
