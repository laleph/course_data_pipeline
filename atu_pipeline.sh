#!/bin/bash
# ATU Course Data Pipeline
# This script runs the complete ATU pipeline to convert KEU_All_EN_Course.xml to KEU format.

echo "🚀 ATU Course Data Pipeline Started"
echo "=================================="

# Check if input file exists
XML_INPUT="KEU_All_EN_Course.xml"
if [ ! -f "$XML_INPUT" ]; then
    echo "❌ Error: Input file $XML_INPUT not found!"
    echo "Please ensure the ATU XML file is in the current directory."
    exit 1
fi

echo "📁 Input file: $XML_INPUT"
echo ""

# Step 1: Generate KEU schema (shared with other universities)
echo "📋 Step 1: Generating KEU schema..."
uv run src/KreativEU.py
if [ $? -eq 0 ]; then
    echo "✅ Schema generated successfully"
else
    echo "❌ Schema generation failed"
    exit 1
fi
echo ""

# Step 2: Convert ATU XML to intermediate JSON
echo "🔄 Step 2: Converting ATU XML to intermediate JSON..."
uv run src/ATU_xml2json.py --xml-file "$XML_INPUT" --json-output atu_intermediate.json
if [ $? -eq 0 ]; then
    echo "✅ XML to JSON conversion completed"
else
    echo "❌ XML to JSON conversion failed"
    exit 1
fi
echo ""

# Step 3: Map ATU intermediate JSON to KEU format
echo "🎯 Step 3: Mapping ATU courses to KEU format..."
uv run src/ATU2KEU_mapping.py --json-input atu_intermediate.json --json-output ATU_keu_courses.json
if [ $? -eq 0 ]; then
    echo "✅ ATU to KEU mapping completed"
else
    echo "❌ ATU to KEU mapping failed"
    exit 1
fi
echo ""

# Step 4: Validate output
echo "🔍 Step 4: Validating output files..."

if [ -f "atu_intermediate.json" ]; then
    INTERMEDIATE_SIZE=$(wc -c < atu_intermediate.json)
    echo "  ✅ Intermediate JSON: atu_intermediate.json ($(numfmt --to=iec $INTERMEDIATE_SIZE))"
else
    echo "  ❌ Intermediate JSON not found"
    exit 1
fi

if [ -f "ATU_keu_courses.json" ]; then
    FINAL_SIZE=$(wc -c < ATU_keu_courses.json)
    echo "  ✅ Final KEU JSON: ATU_keu_courses.json ($(numfmt --to=iec $FINAL_SIZE))"
else
    echo "  ❌ Final KEU JSON not found"
    exit 1
fi

if [ -f "course_catalogue_schema.json" ]; then
    echo "  ✅ Schema: course_catalogue_schema.json"
else
    echo "  ❌ Schema file not found"
    exit 1
fi

echo ""

# Step 5: Quick statistics
echo "📊 Step 5: Pipeline statistics..."
if command -v jq >/dev/null 2>&1; then
    # Use jq if available for better JSON parsing
    COURSE_COUNT=$(jq '. | length' ATU_keu_courses.json 2>/dev/null)
    if [ $? -eq 0 ] && [ "$COURSE_COUNT" != "null" ]; then
        echo "  📚 Total courses processed: $COURSE_COUNT"
    fi
    
    INTERMEDIATE_COUNT=$(jq '.ATU.courses | length' atu_intermediate.json 2>/dev/null)
    if [ $? -eq 0 ] && [ "$INTERMEDIATE_COUNT" != "null" ]; then
        echo "  🔄 Intermediate courses: $INTERMEDIATE_COUNT"
    fi
else
    # Fallback without jq
    echo "  📚 Course files generated successfully"
    echo "  💡 Install 'jq' for detailed statistics"
fi

echo ""
echo "🎉 ATU Pipeline completed successfully!"
echo "✅ Output files:"
echo "   • ATU_keu_courses.json (Final KEU format)"
echo "   • atu_intermediate.json (Intermediate format)"
echo "   • course_catalogue_schema.json (Schema)"
echo ""
echo "📋 Next steps:"
echo "   • Validate schema compliance with your validation tools"
echo "   • Review output files for data quality"
echo "   • Integrate with KreativEU platform"
echo ""
echo "🏫 University: Adana Alparslan Türkeş Science and Technology University"
echo "🌍 Language: English"
echo "📅 Generated: $(date)"
