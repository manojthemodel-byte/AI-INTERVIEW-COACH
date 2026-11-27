# 🎯 AI Mock Interview Coach

An interactive, generative AI mock interview platform designed to help aspiring technical professionals prepare for high-stakes interviews across **Software Engineering**, **Data Science**, and **Data Analytics**.

Powered by Google's `gemini-3.5-flash-lite` and built with [Streamlit](https://streamlit.io/), the application dynamically generates role-calibrated technical questions, prevents question repetition, and delivers objective, multi-dimensional evaluation with rubric scoring (0.0 to 10.0), defensive off-topic guardrails, and contextual follow-up probing.

---

## 🚀 Key Features

* **AI Interviewer Personalities ("Choose Your Interviewer"):** Customize your mock interview experience across three calibrated interviewer personas:
  * 🌱 **Friendly Mentor:** Encouraging, supportive, and patient. Frames questions around real-world application and growth mindset, providing constructive feedback and gentle follow-up guidance.
  * ⚖️ **Strict Technical Interviewer:** Professional, rigorous, and demanding. Challenges vague answers, requires deep architectural/mathematical justification, rejects hand-waving, and asks probing follow-ups.
  * 🚀 **FAANG-Style Interviewer:** Big-tech engineering caliber. Focuses on system scalability, algorithmic optimization (Big-O time/space), throughput/latency trade-offs, high-concurrency bottlenecks, and failure edge cases.
  * ⚖️ **Objective Scoring Standards:** Personality influences tone, phrasing, and follow-up depth without altering the standardized 10-point scoring scale or rubric fairness.
* **Interview Pressure Mode:** Practice under real-world time constraints:
  * ⏱️ **Configurable Countdown Timer:** Choose between `60 seconds (High Pressure)`, `120 seconds (Standard, default)`, or `180 seconds (Extended)`.
  * ⏳ **Visual Countdown Bar:** Smooth, live timer powered by Streamlit fragments without disrupting active typing.
  * 🔒 **Safe Time-Expiry Handling:** Automatically disables edits when time expires without discarding candidate answers or penalizing scores. Candidates review and submit their answer normally.
* **Smart Answer Correction & Teaching Feedback:** Provides structured pedagogical feedback when candidate answers are incorrect or incomplete:
  * 🏷️ **4-Tier Answer Classification:** Categorizes answers into `Correct`, `Partially Correct`, `Incorrect`, or `Off-topic` with color-coded assessment badges.
  * 🟢 **Correct Concepts Extraction:** Isolates and credits factually sound statements without penalizing for synonymous wording.
  * 🔴 **Mistakes & Misconceptions Analysis:** Highlights technical errors paired with explanations clarifying *why* each claim is wrong.
  * 🔸 **Missing Concepts:** Pinpoints key components, edge cases, and trade-offs omitted from a complete answer.
  * 📖 **Educational Explanations:** Delivers concise, technically accurate explanations resolving misconceptions.
  * 💡 **Expandable Ideal Answer:** Interactive drawer (`💡 View Ideal Answer`) demonstrating an exemplary, interview-ready response.
* **Final Performance Dashboard:** Comprehensive post-interview analytics rendered upon session completion:
  * 📊 **Summary Metrics:** Total questions completed, average score (0.0 to 10.0), 5-tier calibrated rating, and score spread.
  * 🎯 **Performance Highlights:** Highlights highest-scoring and lowest-scoring questions with questions and score badges.
  * 📈 **Trajectory Visualization:** Visual question score trajectory across all 15 questions.
  * 📋 **Individual Question Table:** Tabular breakdown detailing Question #, Interview Question text, Score, Relevance, Technical Accuracy, Clarity, and Completeness.
  * 🔍 **Qualitative Feedback Synthesis:** Deterministic aggregation of recurring strengths, common weaknesses, and key actionable suggestions without generative hallucinations.
  * 🔎 **Expandable Question Review:** Inspect submitted answers and full rubric criteria breakdown for every turn.
  * 🔄 **Fresh Session Reset:** One-click clean restart wiping previous session state without cross-session contamination.
* **Complete 15-Question Interview Sessions:** Conduct structured, full-length mock interviews pacing candidates through 15 sequentially adapted questions across three pedagogical stages (Foundational, Implementation & Architecture, Advanced Scenarios) with progress tracking, stage badges, and session turn history.
* **Dual Practice Modes:** Choose between lightweight **Single Question Practice** (quick topic drills) and **Complete Interview Session** (15-question end-to-end evaluation).
* **Role & Level Customization:** Configure interview practice for Software Engineer, Data Analyst, or Data Scientist across Easy, Medium, and Hard difficulties in Technical, HR, or Mixed formats.
* **Dynamic Question Synthesis:** Powered by `gemini-3.5-flash-lite` with decoupled prompt templating (`prompts/question/prompt.txt`), interview stage awareness, and an anti-repetition memory system that tracks recent questions.
* **One-Click Question Regeneration:** Regenerate a distinct question for the same role and difficulty without resetting preferences.
* **Calibrated 5-Tier Rubric Scoring:** Evaluates answers on a standardized 0.0 to 10.0 scale with clearly defined scoring anchors (Outstanding, Strong, Fair, Below Expectations, Inadequate).
* **Multi-Dimensional Criteria Breakdown:** Analyzes candidate responses across four core pillars:
  * 🎯 **Relevance:** Did the response address the specific prompt directly?
  * ⚙️ **Technical Accuracy:** Are definitions, algorithms, and concepts factually sound?
  * 💡 **Clarity & Structure:** Is communication articulate, structured, and professional?
  * 📦 **Completeness & Depth:** Were key trade-offs, edge cases, and nuances addressed?
* **Defensive Off-Topic Guardrails:** Automatically caps scores at `0.0 – 2.0 / 10.0` for evasive or completely off-topic answers, preventing generative leniency toward articulate fluff.
* **Client-Side Input Validation & Anti-Skipping:** Intercepts empty or whitespace-only answers before invoking the API, preserving tokens, and enforces answer evaluation before candidates can advance to the next session question.
* **Evidence-Based Feedback:** Generates 2–4 concrete strengths, 1–4 technical weaknesses, and 2–4 actionable improvement suggestions with direct references to candidate text.
* **Probing Follow-Up Workflow:** Synthesizes a contextual follow-up question based on the candidate's answer with a single-click button to practice the follow-up immediately.

---

## 📂 Repository Structure

```text
AI_INTERVIEW-COACH/
├── .env.example                      # Template for environment variables (API key)
├── .gitignore                        # Git exclusion rules (.env, .venv, __pycache__)
├── app.py                            # MAIN APPLICATION ENTRY POINT (Streamlit)
├── CHANGELOG.md                      # Milestone 2 dated progress and release notes
├── README.md                         # Project documentation and setup guide
├── code/
│   └── app.py                        # Reference source code copy for repository modularity
├── docs/
│   ├── M2_Report.md                  # Milestone 2 Comprehensive Report (SCSE4041 format)
│   ├── Supporting_Technical_Report.md# Milestone 2 Supporting Technical Report (1-2 pages)
│   └── prompt_iteration_log.md       # Prompt engineering iteration log (V1, V2, V3)
├── prompts/
│   ├── final/
│   │   └── prompt.txt                # Production evaluation prompt template (V3)
│   ├── question/
│   │   └── prompt.txt                # Decoupled stage-aware question generation prompt
│   ├── v1/
│   │   └── prompt.txt                # Baseline unstructured evaluation prompt
│   ├── v2/
│   │   └── prompt.txt                # Multi-criteria rubric evaluation prompt
│   └── v3/
│       └── prompt.txt                # Guardrailed & calibrated evaluation prompt
├── test-data/
│   └── test_cases.json               # Master structured test cases dataset (TC-01 to TC-12)
└── tests/
    ├── sample_test_cases.json        # Benchmark test cases for automated unit tests
    ├── test_evaluation.py            # Automated unittest test suite (5 passing tests)
    └── test_plan.md                  # Comprehensive manual test plan & execution records
```

> [!IMPORTANT]
> **Application Entry Point:**  
> The active, runnable application entry point is **`app.py` located in the root directory** (`./app.py`). It dynamically loads prompt templates from `prompts/final/prompt.txt`. A reference copy is also provided in `code/app.py` for repository modularity.

---

## 🛠️ Technology Stack

* **Language:** Python 3.12 (compatible with 3.10+)
* **Frontend Framework:** Streamlit
* **Foundation Model:** Google `gemini-3.5-flash-lite`
* **API SDK:** Google GenAI SDK (`google-genai`)
* **Schema Validation:** Pydantic (`BaseModel`, `Field`)
* **Configuration:** `python-dotenv`
* **Test Runner:** Python built-in `unittest` (compatible with `pytest`)

---

## ⚙️ Installation & Setup

### 1. Prerequisites
* Python 3.10, 3.11, or 3.12 installed on your machine.
* A Google Gemini API key (obtainable from [Google AI Studio](https://aistudio.google.com/)).

### 2. Clone Repository & Setup Virtual Environment
```powershell
# Navigate to the workspace directory
cd AI_INTERVIEW-COACH

# Create a Python virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On macOS / Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```powershell
pip install streamlit google-genai pydantic python-dotenv
```

### 4. Configure Environment Secrets
Create a `.env` file in the root directory (you can copy `.env.example`):
```powershell
cp .env.example .env
```
Open `.env` and insert your actual Gemini API key:
```text
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
> [!WARNING]
> Never commit your `.env` file or expose your API key. The `.gitignore` file is configured to exclude all `.env` files automatically.

---

## 🏃 Running the Application

Launch the Streamlit interactive application from the root directory:
```powershell
streamlit run app.py
```
The application will launch automatically in your default browser at `http://localhost:8501`.

### How to Practice an Interview:
1. **Choose Mode:** Select either **Single Question Practice** or **Complete Interview Session (15 Questions)** in the sidebar.
2. **Configure:** Select your target job role (`Software Engineer`, `Data Analyst`, or `Data Scientist`), difficulty, and interview type.
3. **Session Progression (Complete Session Mode):**
   - Click **"🚀 Start 15-Question Interview Session"** to initialize your paced mock interview.
   - Question 1 loads automatically aligned with **Stage 1: Foundational Concepts**.
   - Input your answer and click **"🎯 Evaluate My Answer"**.
   - Review your calibrated score, four-dimension breakdown, strengths, weaknesses, and actionable feedback.
   - Click **"Next Question ➡️"** to advance through Stage 2 (Implementation & Architecture) and Stage 3 (Advanced Scenarios).
   - Anti-skipping protection guarantees you cannot advance without evaluating an answer.
   - Upon completing Question 15, view your final session completion summary!
4. **Standalone Drills (Single Question Mode):**
   - Click **"Generate Interview Question"** (or **"🔄 Regenerate"**) to practice individual questions on demand.
   - Click **"👉 Practice This Follow-up Question"** to drill deeper on the interviewer's targeted follow-up.

---

## 🧪 Running Automated Tests

Run the automated unit test suite using Python's built-in `unittest` runner:
```powershell
python -m unittest tests/test_evaluation.py -v
```

### Test Suite Results:
```text
test_app_loads_final_prompt (tests.test_evaluation.TestInterviewCoachEvaluation.test_app_loads_final_prompt) ... ok
test_dashboard_aggregated_feedback_strengths_and_weaknesses (tests.test_evaluation.TestInterviewCoachEvaluation.test_dashboard_aggregated_feedback_strengths_and_weaknesses) ... ok
test_dashboard_average_score_and_extrema_calculation (tests.test_evaluation.TestInterviewCoachEvaluation.test_dashboard_average_score_and_extrema_calculation) ... ok
test_dashboard_completion_only_visibility (tests.test_evaluation.TestInterviewCoachEvaluation.test_dashboard_completion_only_visibility) ... ok
test_dashboard_performance_rating_brackets (tests.test_evaluation.TestInterviewCoachEvaluation.test_dashboard_performance_rating_brackets) ... ok
test_dashboard_question_wise_analytics_table (tests.test_evaluation.TestInterviewCoachEvaluation.test_dashboard_question_wise_analytics_table) ... ok
test_dashboard_safe_handling_of_missing_or_malformed_data (tests.test_evaluation.TestInterviewCoachEvaluation.test_dashboard_safe_handling_of_missing_or_malformed_data) ... ok
test_evaluation_prompt_personality_followup_adaptation (tests.test_evaluation.TestInterviewCoachEvaluation.test_evaluation_prompt_personality_followup_adaptation) ... ok
test_get_question_prompt_formatting_and_adaptation (tests.test_evaluation.TestInterviewCoachEvaluation.test_get_question_prompt_formatting_and_adaptation) ... ok
test_interview_stage_selection_rules (tests.test_evaluation.TestInterviewCoachEvaluation.test_interview_stage_selection_rules) ... ok
test_off_topic_test_case_spec (tests.test_evaluation.TestInterviewCoachEvaluation.test_off_topic_test_case_spec) ... ok
test_personality_selection_and_configurations (tests.test_evaluation.TestInterviewCoachEvaluation.test_personality_selection_and_configurations) ... ok
test_pressure_mode_timer_configuration (tests.test_evaluation.TestInterviewCoachEvaluation.test_pressure_mode_timer_configuration) ... ok
test_pressure_mode_timer_expiry_and_remaining (tests.test_evaluation.TestInterviewCoachEvaluation.test_pressure_mode_timer_expiry_and_remaining) ... ok
test_pressure_mode_turn_recording_and_no_penalty (tests.test_evaluation.TestInterviewCoachEvaluation.test_pressure_mode_turn_recording_and_no_penalty) ... ok
test_prevention_of_skipping_unanswered_or_unevaluated_questions (tests.test_evaluation.TestInterviewCoachEvaluation.test_prevention_of_skipping_unanswered_or_unevaluated_questions) ... ok
test_prompt_files_exist_and_meaningfully_different (tests.test_evaluation.TestInterviewCoachEvaluation.test_prompt_files_exist_and_meaningfully_different) ... ok
test_question_prompt_file_exists_and_valid (tests.test_evaluation.TestInterviewCoachEvaluation.test_question_prompt_file_exists_and_valid) ... ok
test_question_prompt_personality_adaptation (tests.test_evaluation.TestInterviewCoachEvaluation.test_question_prompt_personality_adaptation) ... ok
test_regression_candidate_answer_widget_state_decoupling (tests.test_evaluation.TestInterviewCoachEvaluation.test_regression_candidate_answer_widget_state_decoupling) ... ok
test_relevant_test_case_spec (tests.test_evaluation.TestInterviewCoachEvaluation.test_relevant_test_case_spec) ... ok
test_sample_cases_structure (tests.test_evaluation.TestInterviewCoachEvaluation.test_sample_cases_structure) ... ok
test_session_advancement_and_completion_condition (tests.test_evaluation.TestInterviewCoachEvaluation.test_session_advancement_and_completion_condition) ... ok
test_session_initialization (tests.test_evaluation.TestInterviewCoachEvaluation.test_session_initialization) ... ok
test_session_progress_calculation (tests.test_evaluation.TestInterviewCoachEvaluation.test_session_progress_calculation) ... ok
test_session_turn_recording_and_storage (tests.test_evaluation.TestInterviewCoachEvaluation.test_session_turn_recording_and_storage) ... ok
test_smart_answer_correction_correct_classification (tests.test_evaluation.TestInterviewCoachEvaluation.test_smart_answer_correction_correct_classification) ... ok
test_smart_answer_correction_incorrect_classification (tests.test_evaluation.TestInterviewCoachEvaluation.test_smart_answer_correction_incorrect_classification) ... ok
test_smart_answer_correction_off_topic_classification (tests.test_evaluation.TestInterviewCoachEvaluation.test_smart_answer_correction_off_topic_classification) ... ok
test_smart_answer_correction_partially_correct_classification (tests.test_evaluation.TestInterviewCoachEvaluation.test_smart_answer_correction_partially_correct_classification) ... ok
test_smart_answer_correction_schema_fields_and_defaults (tests.test_evaluation.TestInterviewCoachEvaluation.test_smart_answer_correction_schema_fields_and_defaults) ... ok

----------------------------------------------------------------------
Ran 31 tests in 1.3s

OK (31/31 passing)
```

---

## 📊 Verification Summary

* **Automated Unit Tests:** **31/31 tests passed** validating interviewer personality selection, personality-adapted question synthesis, personality-aware follow-up probes, pressure mode countdown timer arithmetic and boundary expiry, answer text preservation under pressure mode, prompt differentiation, smart answer correction & 4-tier classification (Correct, Partially Correct, Incorrect, Off-topic), post-interview performance dashboard analytics (metric calculations, rating brackets, question analysis table, feedback aggregation, completion-only visibility, malformed data safety), answer widget state decoupling regression prevention, interview session state management, question stage selection rules, decoupled question prompt templating, schema validation, dynamic template loading, and test specifications.
* **Manual Live Executions:** **10 distinct recorded test cases** (`TC-01` to `TC-10`) in [tests/test_plan.md](file:///c:/Users/lenovo/OneDrive/Desktop/AI_INTERVIEW-COACH/tests/test_plan.md):
  * `TC-01`: SE Hard Technical — Distributed Rate Limiter (`8.5 / 10.0`, Observed)
  * `TC-02`: SE Hard Technical — Off-Topic Hash Map (`1.0 / 10.0`, Observed, **Edge Case 1**)
  * `TC-03`: SE Medium Technical — Empty Input (`PASS`, Client Warning, **Edge Case 2**)
  * `TC-04`: DA Easy Technical — Terse SQL (`5.0 / 10.0`, **Edge Case 3**)
  * `TC-05`: DS Easy Technical — ML Overfitting (`8.5 / 10.0`)
  * `TC-06`: DS Medium Technical — Flawed A/B Testing (`3.0 / 10.0`)
  * `TC-07`: DS Medium Technical — Extreme Class Imbalance Fallacy (`1.5 / 10.0`)
  * `TC-08`: SE Hard Technical — Lock-Free Queue Contradiction (`1.5 / 10.0`)
  * `TC-09`: DA Medium Technical — Flawed DAU Drop Root Cause (`1.5 / 10.0`)
  * `TC-10`: SE Hard Technical — Scalable URL Shortener Design (`9.2 / 10.0`)
  * *Pending Cases:* `TC-11` (Invalid Gibberish) and `TC-12` (Reluctant Speculation) are formally specified as pending future execution.
* **Prompt Engineering Iterations:** Detailed in [docs/prompt_iteration_log.md](file:///c:/Users/lenovo/OneDrive/Desktop/AI_INTERVIEW-COACH/docs/prompt_iteration_log.md) covering V1, V2, and V3.
* **Comprehensive Submission Report:** Full SCSE4041 report available at [docs/M2_Report.md](file:///c:/Users/lenovo/OneDrive/Desktop/AI_INTERVIEW-COACH/docs/M2_Report.md).
* **Supporting Technical Report:** 1–2 page executive summary available at [docs/Supporting_Technical_Report.md](file:///c:/Users/lenovo/OneDrive/Desktop/AI_INTERVIEW-COACH/docs/Supporting_Technical_Report.md).

---

## 👤 Project Information

* **Course:** SCSE4041 — Machine Learning & Generative AI Systems
* **Milestone:** Milestone 2 (Prompt Engineering, Evaluation Engine & System Verification)
* **Project Type:** Solo Student Project
* **Author / Student:** `[TO BE FILLED: Student Full Name & Student ID]`
* **Repository URL:** `[TO BE FILLED: GitHub Repository URL]`
