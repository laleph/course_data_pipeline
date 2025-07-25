#!/bin/bash
# This script runs the entire (UG) pipeline to map HIS courses to KEU courses.

# Run the PHP script to fetch and process English courses from UG HIS (not included in KEU)
# php src/english_courses.php  # UG only

# generates the JSON schema file
uv run src/KreativEU.py

# Run the Python script to map HIS courses to intermediate JSON (intermediate_JSON.json)
# xml tooling is worse than json tooling.
# This is an intermediate step. It is also used for minor data fixes and debugging purposes.
# Initial data can be found in the 'test_SOAP_for_KEU_demo.xml' file within the data_pipeline folder.
# https://politecnicotomar.sharepoint.com/:f:/r/teams/WP2KreativEUAlliance/Documentos%20Partilhados/11_D2.1_Course_Catalogue/20250417_Prototype_Course_Catalogue?csf=1&web=1&e=0X6cCZ
uv run src/xml2json.py --xml-file test_SOAP_for_KEU_demo.xml

# This is the Mapping step, which maps the intermediate JSON to KEU courses.
uv run src/HIS2KEU_mapping.py
