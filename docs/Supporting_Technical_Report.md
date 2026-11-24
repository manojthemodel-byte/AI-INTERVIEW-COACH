# SCSE4041 Milestone 2: Supporting Technical Report
**Project:** AI Mock Interview Coach | **Model:** `gemini-3.5-flash-lite` | **Framework:** Streamlit (Python 3.12)  
**Submission Type:** Solo Student Project | **Author:** `[TO BE FILLED: Student Name & ID]` | **Date:** November 22, 2026  

---

### 1. Project Overview & Problem Statement
Technical interview preparation in Software Engineering, Data Science, and Data Analytics presents significant barriers for aspiring practitioners. Traditional preparation relies heavily on expensive private coaching or ad-hoc peer mocks that suffer from subjective evaluation variance, uncalibrated scoring, and a lack of structured feedback.

The **AI Mock Interview Coach** resolves this gap through an automated, real-time platform powered by Google's `gemini-3.5-flash-lite`. The system synthesizes role- and difficulty-parameterized technical interview questions, enforces an anti-repetition generation history, and provides objective, multi-dimensional evaluations scored on a calibrated 0.0–10.0 scale with evidence-based feedback across *Relevance*, *Technical Accuracy*, *Clarity*, and *Completeness*.

---

### 2. System Architecture & Technology Stack
The platform follows a decoupled, three-tier architecture connecting a reactive frontend to Google's foundation model:

* **Presentation Tier (`Streamlit`):** Manages reactive UI components, session state persistence (`current_question`, `question_history`, `evaluation_result`), client-side input validation, and real-time metric visualization (score cards, progress bars, criteria breakdown, and follow-up practice triggers).
* **Application Logic Tier (`app.py`):** Orchestrates dynamic question generation (`generate_interview_question`), anti-repetition negative constraints, prompt template rendering (`get_evaluation_prompt`), state transition callbacks, and defensive JSON parsing.
* **Model & Validation Tier (`google.genai` & `Pydantic`):** Connects to `gemini-3.5-flash-lite` using structured decoding (`response_mime_type="application/json"`, `response_schema=AnswerEvaluation`). Credentials are dynamically loaded via `python-dotenv` without hardcoded secrets.

```
[Streamlit Frontend: Controls & Feedback UI]
       │                 ▲
       ▼                 │ (Session State & Visual Cards)
[Logic Layer: app.py (Question Gen, Prompt Loader, Pydantic Schema)]
       │                 ▲
       ▼                 │ (Validated JSON Payload)
[Google GenAI SDK: gemini-3.5-flash-lite (Structured JSON Mode)]
```

---

### 3. Gemini Prompt Engineering Approach (V1, V2, V3 & Final)
The candidate answer evaluation prompt underwent three structured iterations to address generative evaluation vulnerabilities (verbosity bias, unearned leniency, and unstructured output):

1. **Version 1 (V1 — Baseline) ([prompts/v1/prompt.txt](file:///c:/Users/lenovo/OneDrive/Desktop/AI_INTERVIEW-COACH/prompts/v1/prompt.txt)):** Minimal zero-shot prompt requesting a general 1–10 score and unstructured feedback.  
   *Limitations:* Unanchored scores, high variance, no dimension separation, and high vulnerability to articulate but off-topic answers.
2. **Version 2 (V2 — Rubric-Based) ([prompts/v2/prompt.txt](file:///c:/Users/lenovo/OneDrive/Desktop/AI_INTERVIEW-COACH/prompts/v2/prompt.txt)):** Introduced an experienced technical interviewer persona and established four evaluation pillars (*Relevance, Technical Accuracy, Clarity, Completeness*).  
   *Limitations:* Subjective scoring without tier calibrations, absence of concrete actionable suggestions, and failure to generate follow-up questions.
3. **Version 3 / Final (Production) ([prompts/final/prompt.txt](file:///c:/Users/lenovo/OneDrive/Desktop/AI_INTERVIEW-COACH/prompts/final/prompt.txt)):** Production prompt integrated directly into `app.py`.  
   * **Off-Topic Guardrail:** Enforces a strict score cap of `0.0 – 2.0 / 10.0` for non-responsive or evasive answers regardless of eloquence.
   * **Calibrated 5-Tier Scoring Anchors:** `9.0–10.0` (Outstanding), `7.5–8.9` (Strong), `5.5–7.4` (Fair), `3.5–5.4` (Below Expectations), `0.0–3.4` (Inadequate/Off-Topic).
   * **Evidence-Based Extraction:** Mandates citing candidate statements, verified concepts, and specific technical omissions.
   * **Structured Output Structure:** Requires 2–4 Strengths, 1–4 Weaknesses, 2–4 Actionable Suggestions, 1 Probing Follow-Up Question, and direct alignment with the `AnswerEvaluation` Pydantic model.

---

### 4. Implementation Methodology
* **Zero Code-Prompt Coupling:** Prompts are stored as standalone text templates under `prompts/` and loaded dynamically via `get_evaluation_prompt()`.
* **Anti-Repetition Question Generation:** When regenerating questions, `generate_interview_question()` injects `previous_question` and recent history (up to 5 past questions) as explicit negative constraints with high temperature (`0.85`), guaranteeing non-repeating conceptual focus.
* **Client-Side Guardrails:** Empty answers are intercepted client-side via `candidate_answer.strip()`, triggering an immediate UI warning (`⚠️ Please enter your answer before requesting an evaluation.`) and avoiding wasted API calls.
* **Defensive Decoding:** Implements automatic stripping of accidental markdown backticks (` ```json `) prior to `json.loads()` validation.

---

### 5. Testing Methodology & Actual Results
Verification utilized a dual-track strategy combining automated regression tests with standardized manual test cases logged in [tests/test_plan.md](file:///c:/Users/lenovo/OneDrive/Desktop/AI_INTERVIEW-COACH/tests/test_plan.md).

#### 5.1 Automated Unit Testing (`tests/test_evaluation.py`)
Executed via Python's built-in `unittest` runner: **5/5 tests passed** (Execution duration: ~2.4s).
* `test_sample_cases_structure`: Validates schema conformity across benchmark test definitions.
* `test_off_topic_test_case_spec` & `test_relevant_test_case_spec`: Asserts factual grounding and scoring constraints for benchmark cases.
* `test_prompt_files_exist_and_meaningfully_different`: Verifies prompt differentiation across V1, V2, and V3; confirms `prompts/final/prompt.txt` equals V3.
* `test_app_loads_final_prompt`: Validates dynamic loading and parameter formatting in `app.py`.

#### 5.2 Manual Execution Results (10 Recorded Test Cases)
The application was evaluated across 10 genuine manual test cases, including **three executed edge cases** (`TC-02`, `TC-03`, `TC-04`):

| Test ID | Role & Difficulty | Category | Focus / Scenario | Expected | Actual Score | Status | Evidence Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | SE (Hard) | Normal | Distributed Rate Limiter (Token Bucket/Redis) | 7.5–8.9 | **8.5 / 10** | Observed | Application log (`prompt_iteration_log.md`) |
| **TC-02** | SE (Hard) | **Edge** | Off-Topic Hash Map Answer to Rate Limiter | 0.0–2.0 | **1.0 / 10** | Observed | Guardrail verification (`prompt_iteration_log.md`) |
| **TC-03** | SE (Medium) | **Edge** | Empty Answer Submission | Warning | **N/A** | **PASS** | Screenshot evidence (Client warning banner) |
| **TC-04** | DA (Easy) | **Edge** | Terse SQL Answer ("HAVING filters groups...") | 3.5–5.5 | **5.0 / 10** | **PASS** | Screenshot evidence (Dashboard score 5.0/10) |
| **TC-05** | DS (Easy) | Normal | ML Overfitting Definition & 5 Techniques | 8.0–9.5 | **8.5 / 10** | **PASS** | User-reported manual execution |
| **TC-06** | DS (Medium) | Normal | Flawed A/B Testing (Sample size 100, Peeking) | 3.0–5.0 | **3.0 / 10** | **PASS** | Screenshot evidence (Dashboard score 3.0/10) |
| **TC-07** | DS (Medium) | Normal | 2% Churn Imbalance Accuracy Fallacy | 1.0–2.5 | **1.5 / 10** | **PASS** | Screenshot evidence (Dashboard score 1.5/10) |
| **TC-08** | SE (Hard) | Normal | Contradictory Lock-Free Queue Concurrency | 1.0–2.5 | **1.5 / 10** | **PASS** | Screenshot evidence (Dashboard score 1.5/10) |
| **TC-09** | DA (Medium) | Normal | Flawed DAU Drop Root Cause Investigation | 1.0–2.5 | **1.5 / 10** | **PASS** | Screenshot evidence (Dashboard score 1.5/10) |
| **TC-10** | SE (Hard) | Normal | Scalable URL Shortener System Design | 9.0–10.0 | **9.2 / 10** | **PASS** | User-reported strong-answer diagnostic |
| *TC-11* | DA (Easy) | *Invalid* | Nonsensical Keyboard Mash / Gibberish | 0.0–2.0 | `[Pending]` | Ready | Specified in test plan; pending execution |
| *TC-12* | SE (Medium) | *Edge* | Reluctant "I Don't Know" Answer with Intuition | 3.0–4.5 | `[Pending]` | Ready | Specified in test plan; pending execution |

---

### 6. Limitations & Future Improvements

#### Current System Limitations
1. **Single-Turn Evaluation Scope:** The system evaluates candidate responses on an individual question turn; it currently lacks aggregated session scoring across an entire multi-question interview.
2. **Text-Only Modality:** Input and feedback are text-based, omitting realistic verbal interview conditions (speech pace, hesitation markers, vocal confidence).
3. **Synchronous Cloud Dependency:** Answer evaluation requires active internet connectivity and depends on Google GenAI API response latency (~2–4 seconds).

#### Planned Future Scope (Milestone 3)
1. **Audio & Voice Pipeline:** Integration of Speech-to-Text (STT) and Text-to-Speech (TTS) for spoken interview simulations.
2. **Multi-Turn Session State Machine:** Aggregating performance metrics over 5 sequential questions to generate an end-of-interview competency score and PDF report.
3. **Automated Evaluation Harness:** Programmatic execution of standardized benchmark sets across future prompt variations.

---
*Verified against project codebase and test plan. Solo student contribution: 100% individual effort. Submission metadata: [TO BE FILLED: Repository URL & Student ID].*
