# Changelog

All notable changes to the **AI Mock Interview Coach** project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Milestone 2] - 2026-11-22

### Added
- **Candidate Answer Evaluation Engine:**
  - Implemented real-time answer assessment powered by `gemini-3.5-flash-lite`.
  - Defined Pydantic schema `AnswerEvaluation` enforcing structured JSON responses across nine distinct fields: `score`, `relevance`, `technical_accuracy`, `clarity`, `completeness`, `strengths`, `weaknesses`, `suggestions`, and `follow_up_question`.
  - Added multi-criteria evaluation breakdown analyzing four core dimensions: Relevance, Technical Accuracy, Clarity, and Completeness.
  - Implemented calibrated 5-tier scoring scale (0.0 to 10.0) with explicit performance bracket definitions (Outstanding, Strong, Fair, Below Expectations, Inadequate).
  - Integrated defensive off-topic guardrails in the prompt enforcing a strict score cap (`0.0 – 2.0 / 10.0`) for evasive or irrelevant responses regardless of communication fluency.
  - Added dynamic synthesis of exactly one context-aware follow-up question per evaluation to probe conceptual depth and edge cases.
- **Prompt Engineering Assets & Version Control:**
  - `prompts/v1/prompt.txt`: Baseline unstructured zero-shot prompt.
  - `prompts/v2/prompt.txt`: Multi-criteria rubric prompt with experienced interviewer persona.
  - `prompts/v3/prompt.txt` & `prompts/final/prompt.txt`: Production guardrailed, calibrated, and JSON-schema-constrained prompt.
  - `docs/prompt_iteration_log.md`: Detailed engineering log documenting rationale, feature comparison matrix, and initial observations across prompt versions.
- **Interactive Question Generation & Anti-Repetition:**
  - Enhanced `generate_interview_question()` with negative constraints that pass the active question and recent question history (last 5 questions).
  - Added a dedicated "🔄 Regenerate Question" UI button allowing candidates to generate a fresh, distinct question without modifying their role, difficulty, or interview type settings.
  - Added question history state tracking (`st.session_state.question_history`) preventing duplicate concepts.
  - Added "👉 Practice This Follow-up Question" workflow allowing candidates to load the interviewer's follow-up directly into the practice area with one click.
- **Client-Side Defensive Interception & Callbacks:**
  - Implemented client-side input validation intercepting empty or whitespace-only answers, displaying `st.warning("⚠️ Please enter your answer before requesting an evaluation.")` and preventing wasted API calls.
  - Implemented callback functions `clear_answer()` and `practice_followup()` to eliminate Streamlit widget mutation conflicts.
  - Added defensive parsing to strip markdown backticks (\`\`\`json) before calling `json.loads()`.
- **Automated Testing Suite:**
  - Developed `tests/test_evaluation.py` using Python's built-in `unittest` framework (5/5 tests passing).
  - Added verification for prompt differentiation, schema conformity, template loading, and sample test case assertions.
  - Created structured benchmark dataset `tests/sample_test_cases.json` and `test-data/test_cases.json`.
- **Comprehensive Documentation:**
  - Created standardized master test plan in `tests/test_plan.md` detailing 10 executed manual test cases (`TC-01` to `TC-10`), including 3 verified edge cases, and 2 pending test specifications (`TC-11`, `TC-12`).
  - Authored Milestone 2 Comprehensive Report `docs/M2_Report.md` following SCSE4041 guidelines.
  - Authored Milestone 2 Supporting Technical Report `docs/Supporting_Technical_Report.md`.
  - Added `.env.example` template for secure environment configuration.
  - Created modular `code/app.py` reference copy and `test-data/` directory.

### Changed
- Refactored `app.py` UI layout to include a distinct Question Card with role/difficulty/type metadata captions and inline regeneration.
- Encapsulated top-level Streamlit code inside `def main()` and guarded execution with `if __name__ == "__main__": main()`.
- Updated `.gitignore` to comprehensively exclude environment secrets (`.env`), virtual environments (`.venv/`), and bytecode caches.

---

## [Milestone 1] - 2026-11-22

### Added
- Initial project workspace initialization for AI Mock Interview Coach.
- Core Streamlit user interface setup in `app.py`.
- Integration of Google GenAI SDK (`google.genai`) with API authentication via `.env`.
- Target job role configuration: Software Engineer, Data Analyst, Data Scientist.
- Difficulty levels: Easy, Medium, Hard.
- Interview types: Technical, HR, Mixed.
- Basic question generation mechanism using Gemini foundation models.
