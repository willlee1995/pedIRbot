# Continuing Q&A Curation from Document 21

## What Was Changed

The script has been updated to **skip the first 20 documents** and process from **document 21 to the end**.

---

## Current Range

- **Processed**: Documents 1-20 ✅
- **Next**: Documents 21 onwards 🚀

---

## How to Run

Simply run the script as normal:

```bash
python scripts/curate_with_medgemma.py
```

The script will:
1. Find all markdown files
2. Skip documents 1-20 (already processed)
3. Start processing from document 21
4. Continue until the last document

---

## What You'll See

```
================================================================================
Processing source: HKSIR (138 files)
================================================================================

Processing documents 21 to 138 (118 files)

Processing: EN21 Percutaneous abscess drainage eng 2010.md
  Procedure: Percutaneous Abscess Drainage
  Sections: overview, procedure, indication, risks, benefits
  ✅ Generated 10 Q&A pairs

Processing: EN22 FNA & biopsy adrenal eng 2010.md
...
```

---

## Expected Output

| Source | Total Files | Processed in Phase 1 | Processing Now (Phase 2) |
|--------|-------------|----------------------|--------------------------|
| HKSIR | 138+ | 1-20 | 21+ |
| SickKids | 224+ | 1-20 | 21+ |

---

## Resume Configuration

To easily switch between phases, you can modify `start_idx`:

### Phase 1 (Documents 1-20):
```python
start_idx = 0
end_idx = 20
```

### Phase 2 (Documents 21+):
```python
start_idx = 20
end_idx = None  # ← Currently set here
```

### Process All (No limit):
```python
start_idx = 0
end_idx = None
```

---

## Monitoring Progress

```
✅ Generated 10 Q&A pairs      (document 21)
✅ Generated 10 Q&A pairs      (document 22)
✅ Generated 10 Q&A pairs      (document 23)
...
```

Each procedure should take ~2-5 seconds with OpenRouter.

---

## Expected Time

For 118 remaining documents:
- **At 2-5 sec/doc**: 3-10 minutes
- **Total (1-20 + 21+)**: 13-30 minutes for full curation

---

## When Complete

The script will save:
- Individual XML files for each procedure
- Master XML file: `procedures_master_qna_medgemma.xml`

All in: `KB/qna_xml/`

---

## Next Steps

```bash
# After curation completes, ingest into RAG:
python scripts/ingest_qna_to_rag.py KB/qna_xml

# Test it:
python test_chat.py

# Deploy API:
python scripts/start_api.py
```

---

## Current Status

✅ Phase 1 Complete (Docs 1-20)
🚀 Phase 2 Ready (Docs 21+)

Run the script now to continue! 🎉

