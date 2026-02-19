# **A Comprehensive Implementation and Research Plan for a RAG-Powered Chatbot for Pediatric Interventional Radiology Patient Education at HKCH**

## **I. Constructing a Clinically-Grounded, Pediatric-Focused Knowledge Base**

The foundational element of any Retrieval-Augmented Generation (RAG) system intended for clinical use is the integrity, accuracy, and relevance of its knowledge base. Unlike general-purpose chatbots that draw from the vast and unvetted expanse of the internet, a medical chatbot's reliability is entirely contingent upon the quality of the curated data it retrieves. The potential for Large Language Models (LLMs) to generate factually incorrect but plausible-sounding information, a phenomenon known as "hallucination," poses an unacceptable risk in a healthcare context.1 The RAG architecture is the primary technical safeguard against this risk, as it constrains the LLM to generate responses based solely on a trusted, pre-approved corpus of information.1 Therefore, the development of this knowledge base is the most critical phase of the project, requiring a meticulous, multi-stage process of data sourcing, clinical localization, pediatric adaptation, and expert-led validation.

### **1.1 Phase 1: Foundational Data Sourcing and Curation**

The initial objective is to assemble a comprehensive library of authoritative, evidence-based information on a wide range of Interventional Radiology (IR) procedures. This process will leverage publicly available patient education materials from leading international and local radiological societies to ensure the foundational content reflects current best practices.
The methodology for this phase involves a systematic collection and cataloging of all relevant patient information leaflets, brochures, and web content from three primary sources:

1. **Cardiovascular and Interventional Radiological Society of Europe (CIRSE):** CIRSE provides a wealth of patient-facing documents covering numerous procedures relevant to this project, including embolization, angioplasty, stenting, ablation, and various drainage techniques.2 These materials are designed to inform patients about the purpose of a procedure, expected benefits, preparations, risks, and post-procedure follow-up plans.3
2. **Hong Kong Society of Interventional Radiology (HKSIR):** Resources from HKSIR are of paramount strategic importance due to their direct applicability to the local clinical context of Hong Kong Children's Hospital (HKCH).5 Crucially, HKSIR provides a comprehensive set of patient information leaflets in English, Traditional Chinese, and Simplified Chinese, which will be invaluable for building a truly bilingual chatbot capable of serving the local patient population.6
3. **Society of Interventional Radiology (SIR):** As a leading American organization, SIR offers extensive resources covering a broad spectrum of IR, including specialized topics in interventional oncology, pain management, and specific sections on pediatric IR.7 These materials will help ensure the knowledge base is comprehensive and covers the full scope of modern IR practice.

All collected source materials, which are predominantly in PDF format, will undergo an initial processing step. They will be converted into a standardized Markdown format using optical character recognition (OCR) and parsing tools. Each resulting Markdown document will be meticulously tagged with metadata, including its source organization (e.g., CIRSE), publication or review date, original language, and the specific procedure it describes. This structured metadata will be essential for content management, future updates, and ensuring traceability of all information within the system.

### **1.2 Phase 2: Localization with HKCH-Specific Protocols**

While international society guidelines provide an excellent foundation for clinical knowledge, they are inherently generic. To be genuinely useful to a patient and their family preparing for a procedure at a specific institution, the information must be localized with site-specific logistical and procedural details. A patient's journey involves not just understanding the medical aspects of a procedure but also navigating the practical realities of the hospital environment.
This phase will involve close collaboration with the clinical and administrative staff of the HKCH Radiology department, including nurses, technologists, and patient coordinators. The objective is to gather and document the precise protocols and logistical information that patients need to know. The process will be guided by reviewing the types of practical information provided by other leading medical centers.9 The data collection will focus on several key areas:

- **Pre-procedure Logistics:** Documenting HKCH-specific fasting instructions (e.g., "Stop all food and milk at midnight, clear fluids are allowed until 6 a.m."), protocols for managing medications (e.g., specific instructions for stopping anticoagulants like Coumadin or Plavix, and diabetes medications like metformin), and the exact process for appointment confirmation calls from hospital staff.9
- **Day of Procedure Information:** Detailing the correct hospital entrance and building to use, the specific location of the radiology reception desk, the required arrival time relative to the procedure time, and a checklist of what to bring (e.g., identity documents, insurance information) and what to leave at home (e.g., jewelry, valuables).9
- **Post-procedure and Follow-up Care:** Capturing HKCH's standard discharge instructions, providing the correct after-hours contact numbers for the on-call IR fellow or specialist nurse for urgent concerns, and explaining the process for scheduling follow-up appointments.9

This localized information will be structured into separate Markdown documents and integrated with the foundational clinical content, ensuring that the chatbot can answer practical questions like "What time should I stop my child from drinking water?" with an answer that is not just medically correct in general, but specifically correct for a patient at HKCH.

### **1.3 Phase 3: The Critical Pediatric Adaptation Process**

A systematic review of the patient information materials from the target societies reveals a critical gap: the content is almost exclusively written for and targeted at adult patients.3 The language is often clinical, the tone is impersonal, and the explanations assume a level of health literacy and emotional context that is inappropriate for children and their guardians. Directly using this adult-centric content would result in a chatbot that is, at best, unhelpful and, at worst, confusing and anxiety-inducing for its intended users. Therefore, this project's success is contingent upon a dedicated, expert-led phase of content transformation.
This phase requires a multidisciplinary team comprising pediatric IR clinicians, child life specialists, and medical writers with experience in pediatric communication. The methodology will be as follows:

- **Readability and Complexity Analysis:** All curated and localized texts will be analyzed using standard readability scoring systems (e.g., Flesch-Kincaid Grade Level, Gunning fog index). The baseline complexity will be established, with a target of achieving a 6th-8th grade reading level for parent-facing materials and an even simpler, more direct style for child-facing content.
- **Content Simplification and Rephrasing:** Complex medical terminology will be systematically identified and replaced with simpler language and age-appropriate analogies. For example, "percutaneous transhepatic cholangiography" might be explained as "a special X-ray test where the doctor uses a tiny tube to look at the bile ducts inside the liver to see why they might be blocked."
- **Tone and Empathy Adjustment:** The clinical, detached tone of the source documents will be revised to be empathetic, reassuring, and supportive. The content will be rewritten to directly address common fears and anxieties experienced by both children ("Will it hurt?") and parents ("What are the biggest risks?"). This aligns with the qualitative findings from the NeuroBot study, where users highlighted the importance of an empathetic tone in patient-facing communication.1
- **Age-Banding of Content:** Recognizing that a 5-year-old and a 15-year-old have vastly different cognitive and emotional needs, key explanations will be developed in multiple versions tailored to specific age bands (e.g., 5-8 years, 9-12 years, 13-17 years). The younger-age content will rely more on simple analogies and focus on sensory experiences, while the teen-focused content can be more detailed and address concerns about autonomy and long-term outcomes.

This adaptation process transforms the knowledge base from a simple collection of facts into a clinically effective communication tool, designed to meet the unique needs of the pediatric patient population at HKCH.

### **1.4 Phase 4: Advanced Data Augmentation using Medical LLMs**

A raw knowledge base, even one that has been expertly curated, is not in an optimal format for a conversational RAG system. The system needs to be trained to recognize a wide variety of questions and map them to the correct informational passages. This phase leverages advanced LLMs to transform the curated Markdown documents into a robust, conversational dataset of question-answer (Q\&A) pairs, a methodology successfully employed in the development of the NeuroBot chatbot.1
The process will be executed in three steps:

1. **Q\&A Pair Generation:** A state-of-the-art LLM, such as GPT-4o or Gemini 1.5 Pro, will be used to process the pediatric-adapted content. The model will be prompted to "act as a curious parent or a child" and generate a comprehensive list of clinically relevant questions that could be answered by each paragraph or section of the source text. For each question, the model will also be instructed to extract or synthesize a detailed answer directly from the provided text. This step effectively converts the entire declarative knowledge base into a conversational, interrogative format.
2. **Paraphrasing and Question Variation Generation:** To ensure the chatbot is robust to the myriad ways users might phrase a query, the LLM will be used for data augmentation. For each canonical Q\&A pair generated in the previous step, the model will be prompted to create 5 to 10 semantically equivalent variations of the question. For example, for the question "How long does my child need to fast before the procedure?", variations might include "What are the rules for eating and drinking?", "Can she have a sip of water in the morning?", and "When should he have his last meal?". This step is crucial for the retriever's ability to find the correct context regardless of the user's specific wording.
3. **Mandatory Manual Verification:** This is the most critical quality control step in the entire data preparation pipeline. Following the rigorous protocol of the NeuroBot study, every single LLM-generated Q\&A pair and its variations will be exported into a structured format (e.g., a spreadsheet) and undergo a manual review by the HKCH pediatric IR clinical team (nurses and radiologists).1 The clinicians will verify the accuracy of each answer against the source text and the clinical appropriateness of each question. Any pairs that are inaccurate, ambiguous, or clinically irrelevant will be either corrected or discarded. This human-in-the-loop validation is a non-negotiable safeguard to ensure 100% clinical accuracy of the data that will ultimately power the chatbot.



## **II. Architecting a Dual-Path Agentic RAG Pipeline**

A dual-path RAG pipeline solves the limitations of traditional vector-only search by running two retrieval strategies in parallel—semantic search and metadata filtering. These paths merge into a refined candidate set, which is then handed off to an intelligent agent for deeper reading and reasoning.

### **2.1 Phase 1: Ingestion & Indexing (Data Layout)**

Before you can query your data, it needs to be processed into structured, searchable formats.

- **Document Ingestion:** Raw files (PDFs, HTML, DOCX) are converted into a normalized Markdown format. This raw text and parsed text are stored in a central documents table.
- **Smart Chunking:** Instead of splitting text by arbitrary token counts, the Markdown is chunked semantically (by headings, paragraphs, or bullet blocks). These are saved in a chunks table with positional metadata (e.g., page number, section).
- **Embedding Computation:** An embedding model (like Gemini Embeddings) processes each chunk. The resulting vectors are stored in an embeddings table linked to their parent chunk IDs.
- **Metadata Extraction:** An LLM scans the documents to extract structured, schema-driven fields (e.g., procedure_type, age_group, doc_type). This is stored in a structured store, such as DuckDB, enabling hard filtering later.

### **2.2 Phase 2: Dual-Path Retrieval (Query Time)**

When a user asks a question, the system fans the query out into two distinct, parallel paths.

#### **Path 1: Semantic Search (The "Fuzzy" Concept Matcher)**
- **Embed Query:** The user's prompt is embedded using the same model from the ingestion phase.
- **Vector Search:** The system runs a similarity search over the embeddings table to fetch the top N chunks (e.g., 50–200) that are conceptually similar to the query.
- **Result:** A candidate list of top-ranked chunks and their parent documents.

#### **Path 2: Metadata Filtering (The "Hard" Constraint Matcher)**
- **Interpret Query:** An LLM translates the natural language question into structured SQL/metadata constraints (e.g., “Which leaflets mention fasting for children under 5?” becomes `doc_type = 'patient_leaflet' AND age_group = 'under_5'`).
- **Filter Store:** These constraints run against the structured metadata tables (e.g., in DuckDB) to isolate exact document matches.
- **Result:** A candidate list of documents matching the hard parameters.

#### **Merging the Paths**
- **Deduplicate & Union:** The system combines the document IDs from both Path 1 and Path 2 into a single set.
- **Score & Prioritize:** Documents are ranked using a combined score (e.g., maximum semantic chunk similarity + a bonus for metadata matches).
- **Size Control:** The list is aggressively trimmed to a manageable maximum (e.g., 20–50 documents) to save time and token costs for the next phase.

### **2.3 Phase 3: Agentic File Exploration (The Brains)**

Instead of just dumping the retrieved text into an LLM context window, an agent iteratively explores the refined candidate set.

- **Parallel Shallow Scan:** The agent uses tools to quickly read summaries, headings, or abstracts across the candidate documents to build a mental map of what is relevant.
- **Targeted Deep Dive:** For the most promising files, the agent issues specific tool calls to read full sections, search for exact terms inside a document, or extract structured data (like specific risks or instructions).
- **Backtracking & Cross-Referencing:** If the initial deep dive lacks context, the agent can backtrack to deprioritized documents or follow cross-references (e.g., opening a linked procedure annex from a general guide).
- **Answer Synthesis:** Once sufficient evidence is gathered, the agent drafts a final response, summarizing the findings and providing precise pointers/citations to the supporting document sections.

## **III. A Multi-faceted Evaluation Framework for Large Language Model Selection**

The user query specifies a desire to test a diverse range of LLMs, from proprietary cloud-based models to locally hosted and Chinese open-source options. This necessitates a structured, multi-criteria evaluation framework to move beyond anecdotal performance and make a data-driven decision. The selection of the optimal LLM is not merely a matter of choosing the one with the highest accuracy score; it involves a complex trade-off between response quality, language proficiency, speed, cost, and, most importantly, data privacy and security—a paramount concern in any hospital environment.

### **3.1 Defining the Candidate Models: A Strategic Overview**

The evaluation will encompass models from three distinct strategic categories, each representing a different set of trade-offs for deployment within HKCH.

1. **Proprietary Cloud APIs (High Performance, High Cost, Privacy Considerations):** These models represent the current state-of-the-art in terms of general reasoning, language understanding, and generation quality.
   - Gemini-2.5 Pro/Flash (Google): Google's flagship models, noted for their strong multilingual capabilities and large context windows, which can be advantageous for RAG.
   - GPT-5-mini (or latest equivalent, e.g., GPT-4o from OpenAI): The successors to the models that served as the high-performing benchmark in the NeuroBot study, which found the Assistants API (GPT-based) to significantly outperform other models.1
2. **Local Open-Source Models (Maximum Privacy, Variable Performance/High Upfront Cost):** This approach involves hosting an open-source model on dedicated hardware within the HKCH's own IT infrastructure, managed via a framework like Ollama. This offers the highest possible level of data privacy and security, as no patient query or data ever leaves the hospital's network.
   - Candidates could include high-performing general models like Llama3-70B or Mixtral-8x7B, or more specialized, medically fine-tuned models such as MediTron-70B. The trade-off is the requirement for significant computational resources (high-end GPUs) and in-house technical expertise for maintenance and optimization.
3. **Open-Source Models via Managed API (Balanced Cost/Performance):** This hybrid approach uses a service like Open Router to access a variety of leading open-source models through a unified API. This simplifies testing and avoids the need for local hardware management while often providing a more cost-effective solution than the proprietary APIs.
   - **Chinese Language Models:** This category is critical for evaluating performance on Traditional Chinese queries. Candidates include DeepSeek-V2, GLM-4, and Qwen2-72B. It is particularly important to rigorously test the latest Qwen models, as the NeuroBot study found a previous version of Qwen to be a significant underperformer compared to its peers.1

### **3.2 Protocol for Head-to-Head Benchmarking**

To quantitatively and qualitatively compare the performance of the candidate models, a rigorous benchmarking protocol will be implemented, directly adapting the successful internal validation methodology from the NeuroBot study.1

- **Test Dataset:** A representative set of 100 challenging questions will be carefully sampled from the augmented knowledge base created in Section I. This set will be balanced, comprising 50 questions in English and 50 in Traditional Chinese, and will cover all major information categories (preparation, risks, post-op care, etc.).
- **Response Generation:** For each of the 100 questions, a response will be generated from every candidate LLM using the identical RAG pipeline (i.e., the same retriever and prompt template). This ensures that any variation in response quality is attributable solely to the generative model itself.
- **Blinded Expert Evaluation:** The generated responses will be collated and anonymized; evaluators will not be told which model produced which response. This blinded dataset will be presented to a panel of 5-8 clinical experts from the HKCH pediatric IR team (nurses and radiologists).
- **Evaluation Metrics:** The expert panel will rate each response using the same validated Likert scales employed in the NeuroBot research 1:
  - **Accuracy:** A 6-point scale measuring factual correctness against the source material (1 \= Completely Incorrect, 6 \= Completely Correct).
  - **Relevance:** A 6-point scale measuring how well the response addresses the specific user query (1 \= Completely Irrelevant, 6 \= Completely Relevant).
  - **Completeness:** A 3-point scale measuring whether the response provides all the necessary information without being deficient or overly verbose (1 \= Incomplete, 2 \= Adequate, 3 \= Fully Complete). The 3-point scale for completeness was found to have higher inter-rater agreement in the NeuroBot study for procedural content.1
- **Qualitative Feedback:** In addition to the quantitative scores, evaluators will be asked to provide free-text comments on the qualitative aspects of each response, such as its tone, clarity, simplicity, and perceived empathy.

### **3.3 Technical and Operational Performance Analysis**

A model that generates perfect answers but takes 30 seconds to do so or violates data privacy policies is not viable for clinical deployment. Therefore, parallel to the quality benchmarking, a technical and operational analysis will be conducted.

- **Latency:** The average end-to-end response time (in seconds) will be measured for each model across the 100-question test set. A target of \< 5 seconds is desirable for a positive user experience.
- **Cost:** For all API-based models, the cost per 1,000 queries will be calculated based on the provider's pricing for input and output tokens. For the locally hosted model, an estimated Total Cost of Ownership (TCO) will be calculated, factoring in the initial hardware investment, power consumption, and ongoing maintenance.
- **Data Privacy & Governance:** A qualitative assessment will be performed. For cloud API providers, their terms of service, data usage policies, and options for data residency and business associate agreements (BAAs) under frameworks like HIPAA will be reviewed. The local model will, by default, receive the highest rating for data privacy.

The results of this comprehensive evaluation will be synthesized into a decision matrix, providing a clear, holistic view of the trade-offs and enabling an evidence-based selection of the single best LLM for the PediIR-Bot.

| Table III.1: LLM Candidate Comparison Matrix |                                |                                    |                                      |                                   |     |     |     |     |     |
| :------------------------------------------- | :----------------------------- | :--------------------------------- | :----------------------------------- | :-------------------------------- | :-- | :-- | :-- | :-- | :-- |
| **Metric**                                   | **Model A (e.g., GPT-5-mini)** | **Model B (e.g., Gemini-2.5 Pro)** | **Model C (e.g., medgemma3 from Google)** | **Model D (e.g., Qwen3-1T Max API)** |     |     |     |     |     |
| **Deployment Type**                          | Cloud API                      | Cloud API                          | Local (Ollama)                       | Cloud API (Open Router)           |     |     |     |     |     |
| **Provider**                                 | OpenAI                         | Google                             | HKCH                                 | Alibaba Cloud                     |     |     |     |     |     |
| **Avg. Accuracy Score (1-6)**                |                                |                                    |                                      |                                   |     |     |     |     |     |
| **Avg. Relevance Score (1-6)**               |                                |                                    |                                      |                                   |     |     |     |     |     |
| **Avg. Completeness Score (1-3)**            |                                |                                    |                                      |                                   |     |     |     |     |     |
| **Chinese Language Performance**             |                                |                                    |                                      |                                   |     |     |     |     |     |
| **Avg. Latency (s)**                         |                                |                                    |                                      |                                   |     |     |     |     |     |
| **Est. Cost / 1M Tokens**                    |                                |                                    |                                      |                                   |     |     |     |     |     |
| **Data Privacy Rating**                      | Medium                         | Medium                             | High                                 | Medium                            |     |     |     |     |     |

## **IV. Prototyping the User Interface for Clinical Testing and Feedback**

The user interface (UI) is the sole point of interaction between the patient and the complex AI system. Its design is therefore critical to the project's success. A poorly designed interface can undermine the utility of even the most accurate chatbot, creating frustration, mistrust, or confusion. The prototype will be developed using a rapid application development framework like Streamlit or Gradio, allowing for iterative design and quick incorporation of feedback from clinical evaluators. The design will be guided by principles of simplicity, accessibility, trust, and safety.

### **4.1 Design Principles for a Patient-Facing Medical Chatbot**

The UI design will prioritize the user's cognitive and emotional state. Patients and parents interacting with the chatbot are likely to be experiencing stress and anxiety related to an upcoming medical procedure. Therefore, the interface must minimize cognitive load and build trust.1

- **Simplicity and Clarity:** The UI will feature a clean, uncluttered layout with a large, highly readable font. The interaction model will be a simple, familiar chat window. There will be no complex menus or unnecessary visual elements.
- **Accessibility:** The design will be fully responsive, ensuring a seamless experience on both mobile devices (the likely primary access point for many parents) and desktop computers. It will adhere to the Web Content Accessibility Guidelines (WCAG) to be usable by individuals with disabilities.
- **Trust and Transparency:** The interface will clearly and consistently identify the chatbot as an AI assistant. The bot will be given a name (e.g., "PediIR-Bot") and an avatar, but it will never masquerade as a human. A brief introductory message will explain its purpose and limitations.
- **Safety and Reassurance:** The design will incorporate prominent visual cues for safety information, including clear disclaimers and an easily accessible pathway to contact a human clinician.

### **4.2 Implementation with Streamlit or Gradio**

Both Streamlit and Gradio are Python-based frameworks that enable the rapid development of interactive web applications for machine learning models. The choice between them will depend on the development team's familiarity, but both are well-suited for creating the necessary prototype for the validation phases.
The core functionality of the prototype will include:

- A main chat window where the conversation history is displayed.
- A text input box for the user to type their questions.
- A "Send" button and support for submitting a query by pressing the Enter key.
- A "Start New Chat" button to clear the conversation history and begin fresh.
- An initial welcome message that includes the necessary legal and medical disclaimers.
- A simple feedback mechanism for each response, such as "thumbs up" and "thumbs down" icons. Clicking these icons will log the user's satisfaction level, providing valuable data for continuous improvement during the trial phases.

### **4.3 Incorporating Essential Safeguard Features**

Beyond the core chat functionality, the UI will be engineered with several critical safeguards to handle potential risks and edge cases. These features are designed to ensure that the chatbot always acts as a safe and responsible tool within the clinical ecosystem.

- **Emergency Keyword Detection and Canned Responses:** The system will include a pre-processing step that scans all user input for a predefined list of keywords related to medical emergencies (e.g., "severe bleeding," "can't breathe," "chest pain," "allergic reaction"). If any of these keywords are detected, the RAG pipeline will be bypassed entirely. Instead, a pre-programmed, non-LLM-generated "canned response" will be immediately displayed, such as: "This sounds like it could be an emergency. Please do not rely on this chatbot. Call 999 or go to the nearest Accident & Emergency department immediately."
- **Human Escalation Pathway:** A clearly visible and persistently available button or link labeled "Talk to a Nurse" will be integrated into the UI. Clicking this will not initiate a live chat with a nurse but will provide the user with the direct phone number for the HKCH IR nurse coordinator and their hours of availability, offering a clear and immediate off-ramp from the AI system to a human expert.
- **Anonymized Session Logging:** All conversations will be logged for quality assurance and system improvement purposes. These logs will be fully anonymized, with any potential personally identifiable information (PII) stripped out before storage. The logs will be reviewed regularly by the project team to identify common questions, topics where the chatbot is underperforming, and potential new areas of knowledge to add to the database.

## **V. A Rigorous, Mixed-Methods Validation Protocol**

The development of a patient-facing AI tool necessitates a validation process that is as rigorous and evidence-based as the development of a new medical device or therapeutic. To ensure the final chatbot—"PediIR-Bot"—is clinically valid, reliable, safe, and genuinely useful, this project will adopt the comprehensive, multi-phase, mixed-methods evaluation framework successfully employed in the peer-reviewed NeuroBot study.1 This framework integrates quantitative performance metrics with qualitative insights from domain experts to provide a holistic assessment of the system's fitness for purpose.

### **5.1 Phase 1: Internal Validation \- A Two-Stage Model Selection**

The first phase of validation serves a dual purpose: to empirically select the single best-performing LLM from the candidates evaluated in Section III and to iteratively refine the knowledge base by identifying and correcting its weaknesses.
The methodology will proceed in two rounds, directly mirroring the NeuroBot protocol 1:

- **Round 1: Initial Comparison:** The top 3-4 LLM candidates (as determined by the benchmarking in Section 3.2) will be subjected to a larger-scale evaluation. An internal team of 8 evaluators, comprising project-affiliated pediatric IR nurses and junior doctors/trainees, will assess the models' performance on a comprehensive set of 300 bilingual questions (150 English, 150 Traditional Chinese). Using the established Likert scales for Accuracy, Relevance, and Completeness, the model with the demonstrably poorest performance will be identified and eliminated from further consideration.
- **Knowledge Base Refinement:** During Round 1, evaluators will document every instance of an incorrect, incomplete, or ambiguous answer. These "failure cases" provide an invaluable roadmap for improving the knowledge base. The project team will analyze these failures, identify the gaps or errors in the source data, and update the knowledge base with corrected or new Q\&A pairs to address these specific shortcomings.
- **Round 2: Final Head-to-Head:** After the knowledge base has been refined, the remaining top two LLM candidates will be re-evaluated on the same 300-question set. This second round serves to assess the impact of the knowledge base improvements and to determine the final, single best-performing model under optimized conditions. The model that achieves the highest composite scores in this round will be officially selected as the generative engine for the "PediIR-Bot."

### **5.2 Phase 2: External Validation \- Assessing Clinical Fitness-for-Purpose**

Once the optimal model and refined knowledge base are integrated into the final PediIR-Bot prototype, the system must be validated by independent domain experts who have had no involvement in its development. This external validation phase is crucial for establishing the chatbot's objective clinical credibility and mitigating any potential confirmation bias from the internal development team.1

- **Participants:** A panel of 10 senior domain experts will be recruited. This panel will consist of experienced pediatric interventional radiologists and senior pediatric IR nurses from HKCH and, if possible, other local or international institutions to ensure a diverse and unbiased perspective.
- **Test Dataset:** A purposive sample of 50 high-stakes questions will be selected for this validation. The selection will focus on questions that were identified as challenging during the internal validation phase or that relate to topics with high clinical risk, such as potential complications, medication side effects, and situations requiring urgent medical attention.
- **Evaluation Protocol:** The external experts will interact with the PediIR-Bot and rate its generated responses using the identical, standardized rubrics for Accuracy (1-6), Relevance (1-6), and Completeness (1-3) that were used in the internal validation.
- **Statistical Analysis:** To ensure the reliability of the evaluation itself, the consistency of the experts' ratings will be measured using the Intraclass Correlation Coefficient (ICC). As demonstrated in the NeuroBot study, achieving a high ICC value (e.g., \> 0.8) indicates excellent agreement among the raters, validating that the evaluation metrics are being interpreted and applied consistently.1 The mean scores across all three metrics will be calculated to provide a final quantitative assessment of the chatbot's performance.

### **5.3 Phase 3: Qualitative Assessment \- Focus Groups on Usability and Integration**

A chatbot can be perfectly accurate but still fail if it is not perceived as useful, trustworthy, or easy to integrate into clinical workflows by frontline staff. This qualitative phase aims to move beyond quantitative scores to understand the nuanced perspectives of clinicians on the PediIR-Bot's practical utility and potential impact.
The methodology will again be adapted from the NeuroBot study 1:

- **Participants:** A cohort of 15-20 frontline clinicians from HKCH—including nurses, radiologists, and trainees who regularly interact with pediatric IR patients and their families—will be recruited to participate in focus groups.
- **Procedure:** Participants will be given access to the PediIR-Bot prototype for a one-week period and encouraged to interact with it freely, testing it with questions they commonly receive from patients. Following this hands-on period, they will participate in 30-40 minute semi-structured focus group interviews, facilitated by a qualitative researcher.
- **Thematic Analysis:** The interviews will be audio-recorded, transcribed verbatim, and analyzed using an inductive thematic analysis approach. The analysis will seek to identify key themes related to the clinicians' perceptions. The themes identified in the NeuroBot study provide an excellent framework for the interview guide and analysis 1:
  - **Chatbot as a Patient Resource:** Perceived utility for providing quick, reliable, and accessible information.
  - **Impact on Clinical Outcomes:** Potential to enhance patient education, reduce anxiety, and improve treatment compliance.
  - **Role in Communication:** Views on the chatbot as a tool to supplement, not replace, patient-clinician dialogue.
  - **Usability and Features:** Feedback on the user interface, ease of use, and suggestions for additional features.
  - **Concerns and Barriers:** Identification of concerns related to accuracy, liability, patient acceptance, and the practical challenges of integrating the tool into existing clinical workflows.

The rich qualitative data from this phase will provide critical context to the quantitative results and offer actionable recommendations for the final iteration of the chatbot before its clinical deployment.

| Table V.1: Multi-Phase Validation Protocol Summary |                                                                         |                                                |                                 |                                                     |                                                       |
| :------------------------------------------------- | :---------------------------------------------------------------------- | :--------------------------------------------- | :------------------------------ | :-------------------------------------------------- | :---------------------------------------------------- |
| **Phase**                                          | **Objective**                                                           | **Participants (N & Role)**                    | **Test Data**                   | **Evaluation Metrics**                              | **Statistical Method**                                |
| **Internal Validation (Round 1\)**                 | Select top 2-3 LLM candidates; identify knowledge base gaps.            | 8 (Project Nurses, Junior Doctors)             | 300 bilingual questions         | Accuracy (1-6), Relevance (1-6), Completeness (1-3) | ANOVA                                                 |
| **Internal Validation (Round 2\)**                 | Select the single best-performing LLM with a refined knowledge base.    | 8 (Project Nurses, Junior Doctors)             | 300 bilingual questions         | Accuracy (1-6), Relevance (1-6), Completeness (1-3) | Paired t-test                                         |
| **External Validation**                            | Assess the clinical fitness-for-purpose of the final chatbot prototype. | 10 (Senior Pediatric IR Radiologists & Nurses) | 50 high-stakes questions        | Accuracy (1-6), Relevance (1-6), Completeness (1-3) | Mean Scores, Intraclass Correlation Coefficient (ICC) |
| **Qualitative Assessment**                         | Understand perceived benefits, concerns, and integration challenges.    | 15-20 (Frontline HKCH Clinicians)              | Free interaction with prototype | N/A                                                 | Thematic Analysis (NVivo), Cohen's Kappa              |

## **VI. Implementation Roadmap and Ethical Considerations for Clinical Deployment**

The successful development and validation of the PediIR-Bot is a significant milestone, but it is not the final step. The transition from a research prototype to a live, reliable clinical service requires a carefully planned implementation roadmap, a robust governance structure for ongoing maintenance, and a thorough consideration of the profound ethical and medicolegal challenges inherent in deploying patient-facing AI in a pediatric setting.

### **6.1 Staged Rollout Plan**

To manage risk and ensure a smooth integration into clinical practice, a staged rollout plan is proposed:

- **Stage 1: Internal Pilot (Months 1-3 Post-Validation):** The fully validated PediIR-Bot will be deployed on the HKCH intranet, accessible only to clinical staff within the radiology and pediatric departments. This controlled environment will allow staff to use the tool in their daily work (e.g., to quickly find answers for patients), providing real-world feedback and identifying any remaining usability issues or knowledge gaps before any patient interaction occurs.
- **Stage 2: Limited Patient Beta Trial (Months 4-6):** Following a successful internal pilot, the chatbot will be offered to a small, select group of 20-30 patient families who are scheduled for non-urgent IR procedures. These families will be formally recruited into a usability study, provide informed consent, and understand that they are interacting with a new tool. Their usage will be closely monitored, and they will be interviewed about their experience.
- **Stage 3: Full Clinical Deployment (Month 7+):** Once the chatbot has been proven to be stable, safe, and effective in the limited beta trial, it will be made available to all pediatric IR patients at HKCH. Access can be provided via QR codes on appointment letters, links on the official HKCH patient portal, or on tablets available in the clinic waiting area.

### **6.2 Governance and Maintenance Protocol**

An AI tool in medicine is not a one-time product launch; it is an ongoing clinical service that requires continuous governance and maintenance to remain safe and effective.

- **Clinical Content Governance:** A clinical lead (e.g., a designated senior IR nurse) will be formally assigned responsibility for the chatbot's knowledge base. This individual will lead a review of all content on a semi-annual basis to ensure it remains aligned with the latest clinical guidelines and HKCH protocols. This addresses the critical need, identified in the NeuroBot discussion, to have a system in place for keeping the information up-to-date in a rapidly evolving medical field.1
- **Technical Performance Monitoring:** An automated dashboard will be created to track key operational metrics in real-time, including query volume, average response latency, user feedback scores (thumbs up/down), and the frequency of "I don't know" responses. A designated technical team member will review these metrics weekly.
- **Error Reporting and Correction Loop:** A clear, simple process will be established for both users and staff to report any perceived errors. When an error is confirmed by the clinical lead, a formal correction protocol will be triggered: the incorrect information is immediately deactivated in the knowledge base, the correct information is sourced and verified, and the updated knowledge base is deployed within a predefined service-level agreement (e.g., within 48 business hours).

### **6.3 Navigating Ethical and Medicolegal Challenges**

Deploying an LLM-powered chatbot in a pediatric hospital setting requires proactive management of significant ethical and legal considerations.

- **Data Privacy and Security:** The choice of LLM has profound privacy implications. If a cloud-based model (e.g., from OpenAI or Google) is used in the final deployment, a formal Data Processing Agreement (DPA) and Business Associate Agreement (BAA) must be in place to ensure compliance with data protection regulations. All queries must be processed to strip any potential PII. However, the most robust solution from a privacy perspective would be the deployment of a high-performing, locally hosted open-source model via Ollama, which would ensure that no patient data ever leaves the secure HKCH network. This will be a primary consideration in the final model selection.
- **Liability and Accountability:** The risk of a patient acting on incorrect information from the chatbot is a major concern. To mitigate this, the chatbot's interface will feature prominent and persistent disclaimers clarifying that it is an educational tool and not a substitute for professional medical advice, a key recommendation from the NeuroBot study and other literature on medical AI ethics.1 A clear line of accountability for the chatbot's performance and content will be formally established within the HKCH Radiology department's clinical governance structure.
- **Managing Patient and Staff Expectations:** A critical challenge is preventing over-reliance on the chatbot or misunderstanding its capabilities. To address this, clear communication materials will be developed for both patients and staff. These materials will educate users on what the chatbot is designed to do (answer common, non-urgent questions about procedures) and what it is not designed to do (provide diagnoses, offer emergency advice, or replace conversations with their clinical team). This proactive management of expectations is essential for fostering appropriate use and addressing the concerns about public acceptability and overconfidence in AI that were raised by experts in the NeuroBot study.1

## **VII. Conclusions**

This report outlines a comprehensive, evidence-based plan for the implementation and research of a RAG-powered chatbot for pediatric interventional radiology patient education at Hong Kong Children's Hospital. The proposed "PediIR-Bot" project is both technically feasible and clinically valuable, with the potential to significantly enhance patient and family preparedness, alleviate anxiety, and improve the overall care experience.
The plan's methodology is deeply informed by the successful development and validation of the "NeuroBot" chatbot, adopting its rigorous, mixed-methods approach to ensure the final product is not only accurate but also clinically relevant and trusted by frontline staff.1 The project's success, however, does not hinge on novel AI breakthroughs. Instead, it depends on meticulous execution in three critical domains:

1. **Clinically-Led Content Curation:** The single most important factor will be the creation of a high-quality, pediatric-adapted knowledge base. The recognition that existing source materials are not fit-for-purpose for a pediatric audience and the dedication of a specific phase to content transformation by a multidisciplinary team is a cornerstone of this plan.
2. **Rigorous, Multi-faceted Validation:** The multi-phase validation protocol, integrating quantitative expert ratings with qualitative focus group insights, provides a robust framework for ensuring the chatbot is safe, reliable, and genuinely useful before it is ever exposed to a patient.
3. **Robust Governance and Ethical Safeguards:** The plan extends beyond development to address the long-term operational realities of deploying AI in a hospital. The detailed governance, maintenance, and ethical protocols are essential for managing risk and ensuring the chatbot remains a trusted and effective service over time.

By systematically addressing each of these areas, the PediIR-Bot project is well-positioned to serve as a pioneering example of how LLM-driven applications can be responsibly and effectively integrated into patient-centered care, ultimately improving the quality of medical education and patient support in a specialized and sensitive clinical setting. The subsequent steps will involve securing institutional review board approval for the validation protocol and assembling the requisite multidisciplinary team to begin the critical work of knowledge base construction.

#### **Works cited**

1. jmir-2025-1-e74299.pdf
2. CIRSE Patient Information, accessed on October 21, 2025, [https://www.cirse.org/wp-content/uploads/2025/03/cirse_PIB_2025_english_stamped_print.pdf](https://www.cirse.org/wp-content/uploads/2025/03/cirse_PIB_2025_english_stamped_print.pdf)
3. Printable content – CIRSE, accessed on October 21, 2025, [https://www.cirse.org/patients/general-information/printable-content/](https://www.cirse.org/patients/general-information/printable-content/)
4. IR procedures \- CIRSE, accessed on October 21, 2025, [https://www.cirse.org/patients/general-information/ir-procedures/](https://www.cirse.org/patients/general-information/ir-procedures/)
5. Patient information \- hksir, accessed on October 21, 2025, [https://www.hksir.org.hk/Patient-information](https://www.hksir.org.hk/Patient-information)
6. Patient Information Leaflets \- hksir, accessed on October 21, 2025, [https://www.hksir.org.hk/leaflet](https://www.hksir.org.hk/leaflet)
7. For Patients | Society of Interventional Radiology, accessed on October 21, 2025, [https://www.sirweb.org/for-patients/](https://www.sirweb.org/for-patients/)
8. SIR Foundation | SIR Foundation, accessed on October 21, 2025, [https://www.sirfoundation.org/](https://www.sirfoundation.org/)
9. Instructions for Interventional Radiology Procedures | Memorial Sloan Kettering Cancer Center, accessed on October 21, 2025, [https://www.mskcc.org/cancer-care/patient-education/instructions-interventional-radiology-procedures](https://www.mskcc.org/cancer-care/patient-education/instructions-interventional-radiology-procedures)
10. What You Need to Know for Your Interventional Radiology Procedure \- Capital Health, accessed on October 21, 2025, [https://www.capitalhealth.org/medical-services/radiology-services/interventional-radiology/preparing-for-your-interventional-procedure](https://www.capitalhealth.org/medical-services/radiology-services/interventional-radiology/preparing-for-your-interventional-procedure)
11. PATIENT INFORMATION Have you been referred to Interventional Radiology? – Essential Facts, accessed on October 21, 2025, [https://www.bsir.org/media/resources/BSIR_Patient_leaflet_Have_you_been_referred_to_Interventional_Radiology_Essent_EJhUsa4.pdf](https://www.bsir.org/media/resources/BSIR_Patient_leaflet_Have_you_been_referred_to_Interventional_Radiology_Essent_EJhUsa4.pdf)
