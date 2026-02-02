# High-Quality Q&A Curation with MedGemma

## Overview

This guide explains how to use the `curate_with_medgemma.py` script to automatically generate high-quality Q&A pairs for pediatric interventional radiology (IR) procedures using **MedGemma**, a specialized medical LLM.

**Key Features:**
- 🏥 Generates answers to 10 SIR standard pediatric IR questions
- 🧠 Uses MedGemma (or OpenAI GPT-4) for medical accuracy
- 📄 Processes markdown documents from HKSIR, SickKids, and other sources
- 📊 Outputs structured XML for RAG integration
- 🔄 Intelligent context matching for each question

## Prerequisites

### 1. **MedGemma Model (Recommended)**

For the best medical accuracy with privacy, use MedGemma via Ollama:

```bash
# Install Ollama if you haven't already
# Windows: Download from https://ollama.ai
# Linux/Mac: curl -fsSL https://ollama.ai/install.sh | sh

# Pull the MedGemma model
ollama pull alibayram/medgemma

# Verify installation
ollama list
```

### 2. **Alternative: OpenAI API**

If you prefer cloud-based generation:

```bash
# Set environment variable
export OPENAI_API_KEY=sk-your-key-here
```

### 3. **Python Dependencies**

All required packages should already be installed:
```bash
# From requirements.txt
pip install -r requirements.txt
```

## Configuration

### Using MedGemma (Local, Recommended)

Update your `.env` file:

```env
# .env
LLM_PROVIDER=ollama
OLLAMA_CHAT_MODEL=alibayram/medgemma
OLLAMA_API_BASE=http://localhost:11434

EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

Then ensure Ollama is running:

```bash
# In a separate terminal
ollama serve
```

### Using OpenAI

Update your `.env` file:

```env
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_CHAT_MODEL=gpt-4o
```

## The 10 SIR Standard Questions

The script generates answers to these pediatric IR questions:

1. **Why is the treatment being recommended for my child?**
   - Category: Indication
   - Uses: indication + overview sections

2. **What are the benefits and potential risks of the treatment?**
   - Category: Risks & Benefits
   - Uses: benefits + risks sections

3. **Are there alternative options?**
   - Category: Alternatives
   - Uses: indication + procedure sections

4. **How will the treatment be performed?**
   - Category: Procedure Method
   - Uses: procedure section

5. **Will my child require sedation or anesthesia? Will a pediatric anesthesia specialist be provided?**
   - Category: Anesthesia
   - Uses: procedure + preparation sections

6. **What special preparations will we need to make to ensure my child is ready for the treatment?**
   - Category: Preparation
   - Uses: preparation + procedure sections

7. **May they eat or drink prior to the procedure? If not, for how long must they abstain from food and drink?**
   - Category: Fasting
   - Uses: preparation section

8. **Will my child need to stay in a hospital? If so, for how long?**
   - Category: Hospitalization
   - Uses: followup + procedure sections

9. **Will there be any restrictions on my child's activities? If so, when can my child return to normal activity?**
   - Category: Recovery & Activity
   - Uses: followup section

10. **What follow up will be required after the treatment?**
    - Category: Follow-up
    - Uses: followup section

## Usage

### Basic Usage

```bash
# Using default directories (KB/md → KB/qna_xml)
python scripts/curate_with_medgemma.py

# With custom input/output directories
python scripts/curate_with_medgemma.py KB/md KB/qna_xml_medgemma

# Using OpenAI instead of MedGemma
python scripts/curate_with_medgemma.py KB/md KB/qna_xml --use-openai
```

### Running on Specific Procedures

To process only certain procedures, you can modify the script's line:

```python
for md_file in source_files[:10]:  # Limit to first 10 per source
```

Change `10` to your desired number or `None` for all files.

## Process Flow

```
┌─────────────────────────────────┐
│  Markdown Files (KB/md/)        │
│  ├─ HKSIR/EN01-EN46             │
│  └─ SickKids/ (224 files)       │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Extract Procedure Name         │
│  e.g., "EN01 Angioplasty..."    │
│  →  "Angioplasty and Stent"     │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Extract Key Sections           │
│  - Overview                     │
│  - Procedure                    │
│  - Indication                   │
│  - Risks                        │
│  - Preparation                  │
│  - Follow-up                    │
└──────────────┬──────────────────┘
               │
               ▼
     ┌─────────┴──────────┐
     │                    │
     ▼                    ▼
┌────────────────┐  ┌──────────────┐
│ For Each of    │  │  Build       │
│ 10 Questions   │  │  Contextual  │
└────────┬───────┘  │  Prompts     │
         │          └──────────────┘
         │                │
         └────────────────┤
                          ▼
                 ┌─────────────────────┐
                 │  Call MedGemma      │
                 │  (or OpenAI)        │
                 │  Generate Answer    │
                 └────────────┬────────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
                 Success             Fallback
                    │                    │
                    │                Use source
                    │                text excerpt
                    │                    │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │  Create Q&A Pair     │
                    │  - Question          │
                    │  - Answer            │
                    │  - Metadata          │
                    │  - Categorization    │
                    └────────────┬─────────┘
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │  Save Individual XML │
                    │  (per procedure)     │
                    └────────────┬─────────┘
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │  Create Master XML   │
                    │  (all procedures)    │
                    └──────────────────────┘
```

## Output Structure

### Individual Procedure File

`procedures_angioplasty_and_stent_qna_medgemma.xml`:

```xml
<?xml version="1.0" ?>
<procedure name="Angioplasty And Stent" curation_method="medgemma">
  <qna_set>
    <qna id="q1">
      <question>Why is the treatment being recommended for my child?</question>
      <answer>Angioplasty and stenting is recommended when there is narrowing or blockage in blood vessels. In children, this may be due to various conditions affecting blood flow to vital organs...</answer>
      <metadata>
        <question_category>indication</question_category>
        <curation_model>alibayram/medgemma</curation_model>
        <confidence>high</confidence>
      </metadata>
    </qna>
    <!-- More Q&A pairs... -->
  </qna_set>
</procedure>
```

### Master File

`procedures_master_qna_medgemma.xml` combines all procedures:

```xml
<?xml version="1.0" ?>
<procedures total="20" curation_method="medgemma">
  <procedure name="Angioplasty And Stent" curation_method="medgemma">
    <!-- Q&A pairs -->
  </procedure>
  <procedure name="Biopsy" curation_method="medgemma">
    <!-- Q&A pairs -->
  </procedure>
  <!-- More procedures... -->
</procedures>
```

## Integrating with RAG

### Option 1: Direct Integration

Use the existing ingestion script to add MedGemma-curated Q&A to your vector store:

```bash
python scripts/ingest_qna_to_rag.py KB/qna_xml --reset
```

### Option 2: Compare with Original Q&A

To compare MedGemma-curated vs. template-based Q&A:

```bash
# Generate with MedGemma
python scripts/curate_with_medgemma.py KB/md KB/qna_xml_medgemma

# Keep original template-based Q&A in KB/qna_xml

# Ingest original first
python scripts/ingest_qna_to_rag.py KB/qna_xml

# Later, ingest MedGemma (optional separate collection)
# Modify ingest script to use different collection name
```

## Customization

### Modify the Questions

Edit `SIR_QUESTIONS` list in `curate_with_medgemma.py`:

```python
SIR_QUESTIONS = [
    "Your custom question 1?",
    "Your custom question 2?",
    # ...
]
```

### Adjust Section Extraction

The script automatically categorizes markdown headers. To add custom section types:

```python
def extract_key_sections(self, content: str) -> Dict[str, str]:
    # Add new patterns
    if any(word in header_title for word in ['your', 'custom', 'pattern']):
        sections['custom_section'] = header_content
```

### Fine-Tune MedGemma Prompt

Edit `_create_medgemma_prompt()` method:

```python
def _create_medgemma_prompt(self, question: str, procedure_name: str, context: str) -> str:
    return f"""Your custom system prompt here...
    
PROCEDURE: {procedure_name}
CONTEXT: {context}
QUESTION: {question}
ANSWER:"""
```

### Adjust Temperature and Token Limits

Control response quality and length:

```python
# In generate_answer_with_medgemma()
response = self.llm_provider.generate(
    prompt=prompt,
    temperature=0.1,        # Lower = more factual, higher = more creative
    max_tokens=300          # Adjust response length
)
```

## Troubleshooting

### Issue: "Connection refused" from Ollama

**Solution:** Ensure Ollama is running:

```bash
# Start Ollama service
ollama serve

# Or check if model is loaded
ollama list
ollama run alibayram/medgemma "test"
```

### Issue: Very Long Processing Time

**Solution:** MedGemma generates high-quality answers, which takes time. For faster results:

1. Reduce the number of files processed (modify `source_files[:10]`)
2. Use OpenAI instead: `--use-openai`
3. Run on GPU for faster inference

### Issue: Empty or Generic Answers

**Solution:** 

1. Check markdown content has sufficient detail
2. Verify section extraction is working (check logs)
3. Fallback answers are used if extraction fails (this is normal)
4. Consider using OpenAI for better answer generation

### Issue: XML Parse Errors

**Solution:** The script handles this automatically, but if you see errors:

1. Check markdown file encoding (should be UTF-8)
2. Verify no special characters breaking XML
3. Check output directory has write permissions

## Performance Tips

### Speed Optimization

```bash
# Limit files per source (in script)
for md_file in source_files[:5]:  # Process only 5 per source

# Or use OpenAI for faster generation (parallel possible)
python scripts/curate_with_medgemma.py KB/md KB/qna_xml --use-openai
```

### Quality Optimization

```python
# Lower temperature for more factual answers
temperature=0.1  # More focused, less creative

# Longer context for better understanding
context_size = 3000  # chars (up from 2000)

# More retries on failure
attempt > 3  # Increase from 3
```

## Cost Estimation

### Using MedGemma (Local)

- **Cost:** FREE (one-time download)
- **Speed:** 5-15 seconds per procedure (GPU-dependent)
- **Total time for 50 procedures:** ~5-15 minutes

### Using OpenAI

- **Cost:** ~$0.01-0.05 per procedure (varies by model)
- **Speed:** 2-5 seconds per procedure
- **Total cost for 50 procedures:** ~$0.50-2.50

## Quality Assurance

### Review Generated Q&A

```bash
# Export to JSON for review
python scripts/export_qna_for_review.py KB/qna_xml_medgemma

# Review in Excel or spreadsheet
# Check for accuracy, clarity, pediatric appropriateness

# Mark for correction as needed
```

### Manual Validation

The curated Q&A is suitable for RAG, but for production deployment:

1. **Clinical Review:** Have pediatric IR team review
2. **Accuracy Check:** Verify answers match source documents
3. **Parent Perspective:** Test with parent focus groups
4. **Compare Versions:** A/B test MedGemma vs. template-based

## Next Steps

After curation:

1. **Validate:** Review generated XML files
2. **Integrate:** Use `ingest_qna_to_rag.py` to add to vector store
3. **Test:** Use `test_chat.py` to query against curated data
4. **Evaluate:** Run `run_evaluation.py` to measure quality
5. **Deploy:** Integrate into RAG pipeline for production

## Example: Full Workflow

```bash
# 1. Make sure Ollama is running
ollama serve &

# 2. Generate MedGemma-curated Q&A
python scripts/curate_with_medgemma.py KB/md KB/qna_xml_medgemma

# 3. Ingest into RAG
python scripts/ingest_qna_to_rag.py KB/qna_xml_medgemma

# 4. Test the system
python test_chat.py

# 5. Run evaluation
python scripts/run_evaluation.py test_data/sample_questions.json
```

## References

- **MedGemma:** [alibayram/medgemma](https://ollama.ai/library/alibayram/medgemma)
- **SIR Standards:** Society of Interventional Radiology parent education materials
- **RAG Integration:** See `QNA_RAG_INTEGRATION.md`
- **Troubleshooting:** See `docs/` directory for detailed guides

## Support

For issues or questions:

1. Check the logs (they're verbose and informative)
2. Review the troubleshooting section above
3. Consult project documentation in `docs/`
4. Check GitHub issues if using version control

