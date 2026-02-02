# MedGemma Curation - Quick Start (5 minutes)

## TL;DR - Just Run It

```bash
# 1. Start Ollama (in a separate terminal)
ollama serve

# 2. In another terminal, run the curation
python scripts/curate_with_medgemma.py

# Done! Check KB/qna_xml for generated XML files
```

## Prerequisites Checklist

- [ ] Ollama installed ([download here](https://ollama.ai))
- [ ] MedGemma model pulled: `ollama pull alibayram/medgemma`
- [ ] Python dependencies: Already in your `requirements.txt`
- [ ] `.env` file configured (or using defaults)

## Step 1: Verify MedGemma is Installed

```bash
ollama list
```

You should see:
```
NAME                    ID              SIZE    MODIFIED
alibayram/medgemma      ...             13GB    ...
```

If not, pull it:
```bash
ollama pull alibayram/medgemma
```

## Step 2: Start Ollama

```bash
# Windows
ollama serve

# Or just launch the Ollama app from Windows menu
```

Wait until you see: `Listening on 127.0.0.1:11434`

## Step 3: Run the Curation

**Option A: Using defaults (recommended for first time)**

```bash
python scripts/curate_with_medgemma.py
```

This processes:
- **Input:** `KB/md/` (your markdown files)
- **Output:** `KB/qna_xml/` (new Q&A XML files)

**Option B: Specify custom directories**

```bash
python scripts/curate_with_medgemma.py KB/md KB/qna_xml_custom
```

**Option C: Use OpenAI instead (faster, costs $)**

```bash
python scripts/curate_with_medgemma.py KB/md KB/qna_xml --use-openai
```

## What's Happening?

```
🏁 Starting...
├─ 📂 Found markdown files (HKSIR + SickKids)
├─ 🧠 Processing each procedure...
│  ├─ Q1: Why is treatment recommended? ✓
│  ├─ Q2: Benefits and risks? ✓
│  ├─ Q3: Are there alternatives? ✓
│  ├─ Q4: How is it performed? ✓
│  ├─ Q5: Sedation/anesthesia? ✓
│  ├─ Q6: Preparations? ✓
│  ├─ Q7: Food/drink restrictions? ✓
│  ├─ Q8: Hospital stay? ✓
│  ├─ Q9: Activity restrictions? ✓
│  └─ Q10: Follow-up care? ✓
└─ 💾 Saving XML files...
✅ Done!
```

**Expected time:** 5-30 minutes depending on your GPU

## View the Results

The script creates:

### Individual Procedure Files
```
KB/qna_xml/
├─ angioplasty_and_stent_qna_medgemma.xml
├─ biopsy_qna_medgemma.xml
├─ drainage_qna_medgemma.xml
└─ ...
```

### Master File
```
KB/qna_xml/procedures_master_qna_medgemma.xml
```

Open any XML file to see the generated Q&A pairs:

```xml
<procedure name="Angioplasty And Stent" curation_method="medgemma">
  <qna_set>
    <qna id="q1">
      <question>Why is the treatment being recommended for my child?</question>
      <answer>Angioplasty and stenting is recommended when blood vessels are narrowed or blocked. 
      In children, this might be due to...</answer>
      <metadata>
        <question_category>indication</question_category>
        <curation_model>alibayram/medgemma</curation_model>
      </metadata>
    </qna>
    <!-- More Q&A pairs... -->
  </qna_set>
</procedure>
```

## Next: Integrate with RAG

Once you have XML files, add them to your knowledge base:

```bash
python scripts/ingest_qna_to_rag.py KB/qna_xml
```

Then test:

```bash
python test_chat.py
```

## Troubleshooting (30 seconds)

| Problem | Solution |
|---------|----------|
| "Connection refused" | Run `ollama serve` first |
| Takes forever | This is normal! MedGemma is thorough. Or use `--use-openai` |
| Empty answers | Check markdown files have content |
| Script crashes | Check `.env` file exists and is readable |

## Performance Expectations

| Setup | Time per Procedure | 50 Procedures |
|-------|-------------------|--------------|
| MedGemma (GPU) | 5-10 sec | 5-15 min |
| MedGemma (CPU) | 20-60 sec | 15-50 min |
| OpenAI | 2-5 sec | 2-5 min |

## Cost

- **MedGemma:** Free (local, no API calls)
- **OpenAI:** ~$0.01-0.05 per procedure

## The 10 Questions Generated

✅ Why is treatment recommended for my child?
✅ What are benefits and potential risks?
✅ Are there alternative options?
✅ How will treatment be performed?
✅ Will my child need sedation/anesthesia?
✅ What preparations are needed?
✅ May they eat/drink before procedure?
✅ Will hospital stay be needed?
✅ Are there activity restrictions?
✅ What follow-up is required?

---

## Still Running?

Grab a ☕ - MedGemma is working hard to generate high-quality, medically accurate answers!

For details, see `MEDGEMMA_CURATION_GUIDE.md`

