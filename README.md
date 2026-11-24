# 🎯 AI Mock Interview Coach

An interactive, generative AI mock interview platform designed to help aspiring technical professionals prepare for high-stakes interviews across **Software Engineering**, **Data Science**, and **Data Analytics**.

Powered by Google's `gemini-3.5-flash-lite` and built with [Streamlit](https://streamlit.io/), the application dynamically generates role-calibrated technical questions, prevents question repetition, and delivers objective, multi-dimensional evaluation with rubric scoring (0.0 to 10.0), defensive off-topic guardrails, and contextual follow-up probing.

---

## 🚀 Key Features

* **Role & Level Customization:** Configure interview practice for Software Engineer, Data Analyst, or Data Scientist across Easy, Medium, and Hard difficulties in Technical, HR, or Mixed formats.
* **Dynamic Question Synthesis:** Powered by `gemini-3.5-flash-lite` with an anti-repetition memory system that tracks recent questions and guarantees fresh questions on regeneration.
* **One-Click Question Regeneration:** Regenerate a distinct question for the same role and difficulty without resetting preferences.
* **Calibrated 5-Tier Rubric Scoring:** Evaluates answers on a standardized 0.0 to 10.0 scale with clearly defined scoring anchors (Outstanding, Strong, Fair, Below Expectations, Inadequate).
* **Multi-Dimensional Criteria Breakdown:** Analyzes candidate responses across four core pillars:
  * 🎯 **Relevance:** Did the response address the specific prompt directly?
  * ⚙️ **Technical Accuracy:** Are definitions, algorithms, and concepts factually sound?
  * 💡 **Clarity & Structure:** Is communication articulate, structured, and professional?
  * 📦 **Completeness & Depth:** Were key trade-offs, edge cases, and nuances addressed?
* **Defensive Off-Topic Guardrails:** Automatically caps scores at `0.0 – 2.0 / 10.0` for evasive or completely off-topic answers, preventing generative leniency toward articulate fluff.
* **Client-Side Input Validation:** Intercepts empty or whitespace-only answers before invoking the API, preserving user tokens and session state.
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
1. **Configure:** Select your target job role (`Software Engineer`, `Data Analyst`, or `Data Scientist`), difficulty, and interview type.
2. **Generate Question:** Click **"Generate Interview Question"**. Click **"🔄 Regenerate"** at any time to receive a fresh question.
3. **Submit Answer:** Type your structured answer into the text area.
4. **Evaluate:** Click **"🎯 Evaluate My Answer"** to view your overall score, criteria breakdown, strengths, areas for improvement, actionable suggestions, and a follow-up question.
5. **Probe Deeper:** Click **"👉 Practice This Follow-up Question"** to load the interviewer's follow-up directly into the question card.

---

## 🧪 Running Automated Tests

Run the automated unit test suite using Python's built-in `unittest` runner:
```powershell
python -m unittest tests/test_evaluation.py -v
```

### Test Suite Results:
```text
test_app_loads_final_prompt (tests.test_evaluation.TestInterviewCoachEvaluation.test_app_loads_final_prompt) ... ok
test_off_topic_test_case_spec (tests.test_evaluation.TestInterviewCoachEvaluation.test_off_topic_test_case_spec) ... ok
test_prompt_files_exist_and_meaningfully_different (tests.test_evaluation.TestInterviewCoachEvaluation.test_prompt_files_exist_and_meaningfully_different) ... ok
test_relevant_test_case_spec (tests.test_evaluation.TestInterviewCoachEvaluation.test_relevant_test_case_spec) ... ok
test_sample_cases_structure (tests.test_evaluation.TestInterviewCoachEvaluation.test_sample_cases_structure) ... ok

----------------------------------------------------------------------
Ran 5 tests in 2.4s

OK (5/5 passing)
```

---

## 📊 Milestone 2 Verification Summary

* **Automated Unit Tests:** **5/5 tests passed** validating prompt differentiation, schema validation, dynamic template loading, and test specifications.
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
