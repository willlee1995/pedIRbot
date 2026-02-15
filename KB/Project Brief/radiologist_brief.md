# PediIR-Bot Research: Radiologist Brief
**CIRSE 2026 SPHAIRE Abstract | Deadline: March 12, 2026**

---

## Project Summary

We are developing **PediIR-Bot**, a RAG-powered chatbot to provide patient education for pediatric interventional radiology procedures at HKCH. The system uses a curated knowledge base from CIRSE, HKSIR, and SickKids to answer parent and patient questions in both English and Traditional Chinese.

**Goal for SPHAIRE abstract:**
Validate the chatbot's response quality through expert evaluation, demonstrating feasibility and accuracy for AI implementation in clinical patient education.

---

## Current Status

### ✅ Completed
- **Knowledge Base**: 86 Q&A files curated from multiple pediatric sources:
  - CIRSE pediatric procedures (7 files)
  - HKSIR patient information leaflets (47 files, bilingual)
  - SickKids Toronto (24 files)
  - HKCH original appointment sheets (11 files)
  - Additional US children's hospitals
- **RAG Pipeline**: Full retrieval-augmented generation system with embeddings, hybrid search, reranking
- **Safety Guardrails**: Emergency keyword detection, query validation, response safety checks
- **Evaluation Framework**: Automated evaluation pipeline with LLM-as-judge scoring (This is only for reference to compare the model perf)
- **UI Prototype**: Streamlit chatbot interface

### 🔄 In Progress (Your Involvement Required)
- **Test Question Generation**: Need your expertise to create comprehensive test questions
- **Expert Validation**: Pak Lun and Kevin?

---

## Your Role as Expert Rater

You will be one of **2 independent radiologist raters** evaluating the chatbot's response quality. This enables calculation of inter-rater reliability (ICC), a key metric for the abstract.

### Timeline & Time Commitment

| Phase | Dates | Your Time | Task |
|---|---|---|---|
| **Phase 0: Question Generation** | Feb 16-20 | ~1-2 hours | Generate comprehensive test questions covering key aspects of pediatric IR patient education |
| **Phase 1: Q&A Validation** | Feb 21-24 | ~1.5 hours | Review gold-standard Q&A pairs for clinical accuracy |
| **Phase 2: Response Scoring** | Mar 1-5 | ~2.5 hours | Independently rate chatbot responses using standardized rubrics |
| **Phase 3: Abstract Review** | Mar 10-12 | ~30 min | Review and approve final abstract before submission |

**Total time commitment: ~5.5-6.5 hours over 3 weeks**

> [!NOTE]
> **Question quantity note**: I propose ~50 questions for comprehensive coverage (balanced across categories and languages). However, this is flexible—a prior GPT-3 vs GPT-4 comparison study used 133 questions but only covered 3 procedures (Port, PTA, TACE). We can discuss adjusting the number based on your availability and desired coverage depth.

---

## Evaluation Metrics (What You'll Be Rating)

For each of the 50 chatbot responses, you will score using these standardized scales: (Base on the GPT-3 vs GPT-4 paper)

### 1️⃣ Accuracy (1-6 scale)
> "Is the answer factually correct based on clinical knowledge?"

| Score | Meaning |
|:---:|---|
| 6 | Completely Correct |
| 5 | Nearly Correct (minor inaccuracy) |
| 4 | Mostly Correct |
| 3 | Partially Correct |
| 2 | Mostly Incorrect |
| 1 | Completely Incorrect |

### 2️⃣ Relevance (1-6 scale)
> "Does the answer directly address the patient's question?"

| Score | Meaning |
|:---:|---|
| 6 | Completely Relevant |
| 5 | Nearly Relevant |
| 4 | Mostly Relevant |
| 3 | Partially Relevant |
| 2 | Mostly Irrelevant |
| 1 | Completely Irrelevant |

### 3️⃣ Completeness (1-3 scale)
> "Does the answer provide sufficient information without being overly verbose?"

| Score | Meaning |
|:---:|---|
| 3 | Fully Complete |
| 2 | Adequate |
| 1 | Incomplete |

---

## Test Question Generation Guidelines

**Your task**: Create comprehensive test questions that reflect real parent/patient concerns across pediatric IR scenarios.

### Suggested Coverage (Target: ~50 questions, flexible)

**By Language:**
- ~25 English
- ~25 Traditional Chinese (繁體中文)

**By Category - Suggested Distribution:**
- **Preparation** (~12): Fasting guidelines, medication adjustments, what to bring, pre-procedure instructions
- **Risks & Complications** (~8): Procedure-specific risks, warning signs, when to seek emergency help
- **Post-Procedure Care** (~10): Recovery timeline, activity restrictions, wound care, pain management expectations
- **Medications** (~6): Pain medication use, anticoagulant management, insulin adjustments, medication interactions
- **Logistics** (~8): Arrival time, parking, parent accompaniment rights, contact information, follow-up scheduling
- **Disease Education** (~6): Condition explanations (e.g., vascular malformations, hemangiomas), treatment rationale

### Additional Aspects to Consider:
- **Procedure-specific questions**: Cover common procedures (embolization, biopsy, drainage, catheter placement, sclerotherapy)
- **Age-specific concerns**: Questions relevant to different pediatric age groups
- **Parent anxiety points**: Common fears and misconceptions
- **HKCH-specific details**: Local protocols, facility-specific information
- **Bilingual parity**: Ensure Chinese questions aren't just translations—include culturally relevant phrasings

---

## Expected Results for Abstract

Based on your independent scoring, we will report:

```
"PediIR-Bot achieved mean accuracy of X.X/6 (SD=Y.Y),
mean relevance of X.X/6, and mean completeness of X.X/3
across 50 bilingual test questions (25 EN, 25 ZH), as
independently rated by 2 pediatric IR radiologists
(ICC = 0.XX, indicating excellent inter-rater reliability)."
```

**Target metrics for success:**
- Mean Accuracy > 5.0/6
- Mean Relevance > 5.0/6
- ICC > 0.75 (substantial agreement) or > 0.90 (excellent)
- No significant English vs Chinese performance gap

---

## Next Steps

1. **This week (Feb 16-20)**: You generate test questions covering the suggested aspects above
2. **Feb 21**: You and developer finalize the question set and create reference answers together (Phase 1)
3. **Mar 1**: You receive the scoring spreadsheet with chatbot responses (Phase 2)
4. **Mar 10**: You review the draft abstract (Phase 3)
5. **Mar 12**: Abstract submission deadline

---


