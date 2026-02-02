# Pediatric IR - Q&A XML Curation

## Overview

This project has successfully curated comprehensive Q&A datasets for pediatric interventional radiology procedures using the **Society of Interventional Radiology (SIR)** standard parent education questions.

## What Was Generated

### Output Location
```
KB/qna_xml/
├── procedures_master_qna.xml          # Master file with all procedures
├── ablation_qna.xml                    # Individual Q&A for Ablation
├── biopsy_qna.xml                      # Individual Q&A for Biopsy
├── drainage_qna.xml                    # Individual Q&A for Drainage
├── gastrojejunostomy_qna.xml           # Individual Q&A for Gastrojejunostomy
├── gastrostomy_qna.xml                 # Individual Q&A for Gastrostomy
├── sclerotherapy_qna.xml               # Individual Q&A for Sclerotherapy
└── venous_access_ports_qna.xml         # Individual Q&A for Venous Access Ports
```

## SIR Standard Questions

Each procedure includes comprehensive answers to these 10 standard questions:

1. **Why is the treatment being recommended for my child?**
   - Category: Indication
   - Source: "Why perform it?" section

2. **What are the benefits and potential risks of the treatment?**
   - Category: Risks & Benefits
   - Source: Combined from "Why perform it?" and "What are the risks?" sections

3. **Are there alternative options?**
   - Category: Alternatives
   - Source: "How it works?" or definition sections

4. **How will the treatment be performed?**
   - Category: Procedure Method
   - Source: "How does the procedure work?" section

5. **Will my child require sedation or anesthesia? Will a pediatric anesthesia specialist be provided?**
   - Category: Anesthesia
   - Source: "How it works?" section (if mentioned)

6. **What special preparations will we need to make to ensure my child is ready for the treatment?**
   - Category: Preparation
   - Source: General guidance provided

7. **May they eat or drink prior to the procedure? If not, for how long must they abstain from food and drink?**
   - Category: Fasting
   - Source: General guidance provided

8. **Will my child need to stay in a hospital? If so, for how long?**
   - Category: Hospitalization
   - Source: General guidance provided

9. **Will there be any restrictions on my child's activities? If so, when can my child return to normal activity?**
   - Category: Recovery & Activity
   - Source: General guidance provided

10. **What follow up will be required after the treatment?**
    - Category: Follow-up
    - Source: General guidance provided

## XML Structure

Each Q&A pair contains:

```xml
<procedure name="Ablation">
  <qna_set>
    <qna id="q1">
      <question>Why is the treatment being recommended for my child?</question>
      <answer>The goal of tumour ablation is to destroy the tumour without using surgery...</answer>
      <metadata>
        <question_category>indication</question_category>
        <from_section>why_perform</from_section>
      </metadata>
    </qna>
    <!-- More Q&A pairs... -->
  </qna_set>
</procedure>
```

### XML Elements

- **`<procedure>`**: Root element for each procedure (contains `name` attribute)
- **`<qna_set>`**: Container for all Q&A pairs for a procedure
- **`<qna>`**: Individual question-answer pair (contains `id` attribute, e.g., `q1`, `q2`, etc.)
- **`<question>`**: The SIR standard question
- **`<answer>`**: Generated answer based on procedure knowledge
- **`<metadata>`**: Contains categorization info
  - `<question_category>`: Type of question (indication, risks_benefits, alternatives, etc.)
  - `<from_section>`: Which procedure section provided the source content

## Master File Structure

The `procedures_master_qna.xml` file aggregates all procedures:

```xml
<?xml version="1.0" ?>
<procedures total="7">
  <procedure name="Ablation">
    <!-- Q&A pairs -->
  </procedure>
  <procedure name="Biopsy">
    <!-- Q&A pairs -->
  </procedure>
  <!-- 5 more procedures... -->
</procedures>
```

## Procedures Included

The following 7 pediatric IR procedures have been curated:

| Procedure | Q&A Pairs | Key Indications |
|-----------|-----------|-----------------|
| **Ablation** | 10 | Tumor destruction via thermal/non-thermal techniques |
| **Biopsy** | 10 | Tissue sampling for diagnosis |
| **Drainage** | 10 | Fluid collection management |
| **Gastrojejunostomy** | 10 | GI access for nutrition/medication |
| **Gastrostomy** | 10 | Direct gastric access |
| **Sclerotherapy** | 10 | Vascular/variceal treatment |
| **Venous Access Ports** | 10 | Central line placement for medication/nutrition |

**Total: 70 Q&A pairs across 7 procedures**

## Question Categories

All questions are categorized for easy retrieval:

- `indication` - Why the procedure is recommended
- `risks_benefits` - Benefits and risks
- `alternatives` - Alternative treatment options
- `procedure_method` - How the procedure is performed
- `anesthesia` - Sedation and anesthesia requirements
- `preparation` - Pre-procedure preparation
- `fasting` - Fasting and dietary restrictions
- `hospitalization` - Hospital stay requirements
- `recovery_activity` - Activity restrictions and recovery
- `follow_up` - Post-procedure follow-up

## How to Use

### 1. Query Individual Procedure
Access procedure-specific Q&A by file:
```python
import xml.etree.ElementTree as ET

tree = ET.parse('KB/qna_xml/ablation_qna.xml')
root = tree.getroot()
for qna in root.findall('.//qna'):
    question = qna.find('question').text
    answer = qna.find('answer').text
    print(f"Q: {question}\nA: {answer}\n")
```

### 2. Query Master File by Procedure
```python
tree = ET.parse('KB/qna_xml/procedures_master_qna.xml')
root = tree.getroot()

# Get all ablation Q&As
ablation = root.find("procedure[@name='Ablation']")
for qna in ablation.findall('.//qna'):
    question = qna.find('question').text
    answer = qna.find('answer').text
```

### 3. Filter by Question Category
```python
tree = ET.parse('KB/qna_xml/procedures_master_qna.xml')
root = tree.getroot()

# Find all risk/benefits questions
for qna in root.findall(".//qna[metadata/question_category='risks_benefits']"):
    procedure = qna.getparent().getparent()
    print(f"{procedure.get('name')}: {qna.find('question').text}")
```

## Integration Points

The curated Q&A data can be integrated with:

1. **RAG Pipeline** - As a knowledge source for retrieval
2. **LLM Fine-tuning** - For training domain-specific models
3. **API Endpoints** - For serving Q&A pairs to frontend
4. **Search Indexes** - For semantic search capabilities
5. **Evaluation Datasets** - For testing retrieval accuracy

## Script Location

The curation script is located at:
```
scripts/create_qna_xml.py
```

### Usage
```bash
# Default (uses KB/CIRSE ped procedure info → KB/qna_xml)
python scripts/create_qna_xml.py

# Custom source and output directories
python scripts/create_qna_xml.py <source_dir> <output_dir>
```

## Quality Notes

- ✅ All 10 SIR standard questions included for each procedure
- ✅ Answers extracted from source procedure documents
- ✅ Metadata includes question categories for easy filtering
- ✅ XML validation and pretty-printing for readability
- ⚠️ Some generic answers provided for questions without explicit source content
- ⚠️ Manual review recommended for questions 6-10 (preparation, fasting, hospitalization, recovery, follow-up)

## Next Steps

1. **Review & Manual Curation** - Review answers for accuracy and completeness
2. **Enrich Answers** - Add procedure-specific details for preparation/fasting/recovery
3. **Add Procedure Variations** - Include age-specific variations if applicable
4. **Create JSON Alternative** - Generate JSON format for API consumption
5. **Integrate with RAG** - Link Q&A pairs to procedure documents
6. **Create Interactive Schema** - Build frontend to consume and display Q&A

## Troubleshooting

### Issue: Some answers are too generic
**Solution:** Manually review and update the answers in the XML files, particularly for questions 6-10.

### Issue: Missing answers for specific procedures
**Solution:** Check if the source procedure document contains the relevant information. Update source if needed, then re-run the script.

### Issue: XML parsing errors
**Solution:** Ensure all XML files are well-formed by validating with an XML validator.

## References

- **SIR Standards**: Society of Interventional Radiology Patient Education Guidelines
- **Source Documents**: CIRSE Pediatric Procedure Information (KB/CIRSE ped procedure info)
- **Output Format**: XML 1.0 UTF-8 encoded

---

**Generated**: October 22, 2025
**Total Procedures**: 7
**Total Q&A Pairs**: 70
**SIR Questions**: 10 per procedure

