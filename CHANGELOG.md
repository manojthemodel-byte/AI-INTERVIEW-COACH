# Changelog

All notable changes to the **AI Mock Interview Coach** project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Milestone 3 Development] - 2026-11-27

### Added
- **AI Interviewer Personalities & Pressure Mode (Feature 2):**
  - **3 Distinct Interviewer Personalities ("Choose Your Interviewer"):**
    - *Friendly Mentor (🌱):* Encouraging, supportive, and patient. Frames questions around real-world application and growth mindset, offering constructive feedback and gentle, guiding follow-ups.
    - *Strict Technical Interviewer (⚖️):* Professional, rigorous, and demanding. Rejects hand-waving or superficial answers, requires deep architectural/mathematical justification, and asks challenging follow-up probes.
    - *FAANG-Style Interviewer (🚀):* Big-tech caliber. Focuses on large-scale distributed systems, algorithmic complexity (Big-O time/space), throughput/latency bottlenecks, high concurrency, and engineering trade-offs under extreme scale.
    - *Objective Scoring Independence:* Personalities dynamically influence question synthesis, tone, and follow-up probes, while maintaining strict adherence to the standardized 10-point scoring scale and objective rubric criteria.
  - **Interview Pressure Mode:**
    - Optional countdown timer simulating high-stakes live interview pressure.
    - Configurable timer durations: `60 seconds (High Pressure)`, `120 seconds (Standard, default)`, and `180 seconds (Extended)`.
    - Live countdown timer rendered via Streamlit fragment (`@st.fragment(run_every=1)`), enabling smooth, second-by-second countdown without interrupting candidate typing in `st.text_area`.
    - Expiry safety mechanisms:
      - Automatically disables answer text area upon timer expiry (`disabled=True`).
      - Displays prominent "⏰ Time's Up!" alert.
      - Never silently discards candidate answers.
      - Enables candidates to review and submit their answer for evaluation.
      - Zero automated penalty deductions for time expiration; evaluated strictly on technical merit.
      - Zero duplicate Gemini API calls or session corruption on expiry.
      - Timer automatically resets cleanly upon moving to the next question, regenerating, or practicing follow-ups.
  - **Expanded Automated Unit Test Suite:**
    - Expanded test suite from 25 to 31 tests (all 31 passing in ~1.3s):
      - `test_personality_selection_and_configurations`: Validates configurations, properties, and fallback logic for all 3 personalities.
      - `test_question_prompt_personality_adaptation`: Verifies dynamic tone and style adaptation for questions across all 3 personas.
      - `test_evaluation_prompt_personality_followup_adaptation`: Verifies personality-adapted evaluation directives and follow-up guidance without rubric alterations.
      - `test_pressure_mode_timer_configuration`: Validates pressure mode state initialization and MM:SS display formatting.
      - `test_pressure_mode_timer_expiry_and_remaining`: Verifies remaining time arithmetic and boundary expiry detection.
      - `test_pressure_mode_turn_recording_and_no_penalty`: Verifies turn recording with personality/pressure metadata and answer preservation.

### Fixed
- **Streamlit Answer Widget State Decoupling:**
  - Resolved `st.session_state['candidate_answer'] cannot be modified after the widget with that key is instantiated` runtime error.
  - Decoupled the text area widget key (`candidate_answer_widget_{id}`) from `st.session_state.candidate_answer` using versioned key IDs (`reset_candidate_answer_state()`).
  - Ensured that advancing to the next question, clearing answers, regenerating questions, and resetting sessions cleanly instantiates a fresh, empty text area widget without attempting to mutate an already-rendered widget's key in session state.

### Added
- **Smart Answer Correction & Teaching Feedback (Feature 1):**
  - Enhanced evaluation engine to provide structured pedagogical feedback on incorrect and incomplete answers without requiring a second Gemini API call:
    - **4-Tier Answer Classification:** Categorizes candidate responses into `Correct`, `Partially Correct`, `Incorrect`, or `Off-topic` with distinct visual badges.
    - **Correct Concepts Extraction:** Identifies and highlights valid technical statements made by the candidate without penalizing for synonymous wording.
    - **Mistakes & Misconceptions Analysis:** Isolates flawed technical assertions and pairs each with an educational explanation of *why* it is wrong.
    - **Missing Concepts Identification:** Identifies omitted trade-offs, architecture components, or practical edge cases.
    - **Technically Correct Explanation:** Generates an accurate, educational explanation clarifying core principles and resolving misconceptions.
    - **Expandable Ideal Answer:** Adds an interactive `💡 View Ideal Answer` drawer rendering an exemplary, interview-ready response calibrated to the selected role and difficulty.
  - Expanded `AnswerEvaluation` Pydantic schema with backward-compatible defaults for all smart correction fields (`classification`, `correct_concepts`, `incorrect_statements`, `mistake_explanations`, `missing_concepts`, `correct_explanation`, `ideal_answer`).
  - Updated production evaluation prompts in `prompts/final/prompt.txt` and `prompts/v3/prompt.txt` with rigorous teaching instructions, anti-hallucination rules, and strict off-topic guardrails.
  - Integrated Smart Correction review inside the Final Performance Dashboard's turn-by-turn question review drawers.
- **Final Performance Dashboard:**
  - Added comprehensive post-interview analytics dashboard rendered exclusively upon session completion (`should_display_dashboard()`):
    - **Session Performance Metrics:** Displays total completed questions, average score (out of 10.0), overall performance rating (calibrated 5-tier rubric: Outstanding, Strong, Fair, Below Expectations, Inadequate), and score spread.
    - **Performance Highlights:** Highlights highest-scoring and lowest-scoring questions with question text and score badges.
    - **Question Score Trajectory:** Interactive score visualization across all 15 questions powered by Streamlit native charting (`st.bar_chart`).
    - **Individual Question Analysis Table:** Structured breakdown displaying Question #, Interview Question text, Score, Relevance, Technical Accuracy, Clarity, and Completeness.
    - **Qualitative Feedback Synthesis:** Deterministic aggregation of recurring strengths (with observation frequency), common weaknesses, and prioritized actionable suggestions directly from session history with zero hallucinations.
    - **Turn-by-Turn Expandable Review:** Dedicated expanders allowing candidates to inspect each question, submitted answer, rubric criteria breakdown, and original follow-up probes.
    - **Fresh Start Session Action:** One-click restart button cleanly resetting session state, answer history, and question cache.
  - Added pure offline analytics helpers in `app.py`:
    - `calculate_performance_rating()`: Maps scores to 5-tier calibrated performance tiers.
    - `calculate_session_metrics()`: Computes total, average, highest, lowest, rating, and scores safely.
    - `get_question_analysis_table()`: Formats criteria rows for tabular visualization.
    - `aggregate_feedback()`: Extracts and counts recurring strengths, weaknesses, and unique suggestions.
    - `should_display_dashboard()`: Restricts dashboard rendering to completed sessions.
- **Complete Multi-Question Interview Session Mode:**
  - Added dual practice mode selector in Streamlit sidebar:
    - *Single Question Practice:* Preserves 100% of Milestone 2 standalone practice functionality.
    - *Complete Interview Session (15 Questions):* Structured full-session mock interview pacing candidates through 15 sequentially adapted questions.
  - Added session state management tracking `current_index`, `total_questions`, `completed`, and recorded interview `history`/`turns`.
  - Added dynamic session progress bar with progress ratio calculation and display labels (e.g., `Question 3 of 15`).
  - Added visual interview stage banner indicating current difficulty and focus:
    - *Stage 1 (Questions 1–4):* Foundational Concepts & Core Principles.
    - *Stage 2 (Questions 5–11):* Technical Implementation & Architecture.
    - *Stage 3 (Questions 12–15):* Advanced Scenarios, Debugging & High-Stakes Decisions.
  - Implemented strict progression validation (`can_advance_session()`):
    - Intercepts blank or whitespace-only answers.
    - Prevents skipping to the next question without evaluating the current answer first.
  - Added dedicated "Next Question (X of 15) ➡️" workflow and "🏁 Complete Interview Session" finalization.
  - Added interview session completion celebration card displaying summary metrics upon finishing Question 15.
- **Decoupled Question Generation Prompt:**
  - Created standalone prompt template file `prompts/question/prompt.txt`.
  - Added safe prompt loader function `get_question_prompt()` in `app.py` that loads and formats the question prompt dynamically with embedded fallback resilience.
- **Interview Stage Awareness (Paced Generation):**
  - Added stage-aware question synthesis via `get_interview_stage()` supporting progression for full 15-question interviews.
  - Adapted `generate_interview_question()` to accept optional `question_number` while retaining existing anti-repetition instructions and `gemini-3.5-flash-lite` integration.
- **Automated Verification:**
  - Expanded automated unit test suite in `tests/test_evaluation.py` from 5 to 25 tests (all 25 passing):
    - `test_smart_answer_correction_schema_fields_and_defaults`: Verifies AnswerEvaluation schema includes smart correction fields with safe defaults.
    - `test_smart_answer_correction_correct_classification`: Verifies Smart Answer Correction for a Correct candidate answer.
    - `test_smart_answer_correction_partially_correct_classification`: Verifies Smart Answer Correction for a Partially Correct candidate answer.
    - `test_smart_answer_correction_incorrect_classification`: Verifies Smart Answer Correction for an Incorrect candidate answer and mistake explanations.
    - `test_smart_answer_correction_off_topic_classification`: Verifies Smart Answer Correction strictly enforces Off-topic classification and score cap.
    - `test_regression_candidate_answer_widget_state_decoupling`: Verifies answer widget state reset and key versioning preventing Streamlit mutation errors.
    - `test_dashboard_average_score_and_extrema_calculation`: Verifies average score, highest, lowest, and rating calculation.
    - `test_dashboard_performance_rating_brackets`: Verifies 5-tier calibrated performance rubric mapping.
    - `test_dashboard_question_wise_analytics_table`: Verifies question analysis table formatting and criteria extraction.
    - `test_dashboard_aggregated_feedback_strengths_and_weaknesses`: Verifies frequency-based recurring strengths/weaknesses and suggestion aggregation.
    - `test_dashboard_completion_only_visibility`: Verifies dashboard renders only when session is completed.
    - `test_dashboard_safe_handling_of_missing_or_malformed_data`: Verifies resilience against None, string scores, bad schemas, and empty collections.
    - `test_session_initialization`: Verifies clean 15-question default state and custom question limits.
    - `test_session_progress_calculation`: Verifies start, middle, end, and edge case progress ratios and labels.
    - `test_prevention_of_skipping_unanswered_or_unevaluated_questions`: Verifies defense against blank answers or unevaluated advances.
    - `test_session_turn_recording_and_storage`: Verifies accurate turn persistence and idempotency.
    - `test_session_advancement_and_completion_condition`: Verifies index incrementation and session completion condition.
    - `test_question_prompt_file_exists_and_valid`: Verifies question template file.
    - `test_interview_stage_selection_rules`: Verifies 3-stage question pacing logic.
    - `test_get_question_prompt_formatting_and_adaptation`: Verifies dynamic prompt synthesis.
    - 5 Milestone 2 baseline tests (eval prompt, prompt differentiation, sample cases, TC-01, TC-02).
- **Repository Synchronization:**
  - Synchronized `code/app.py` with root `app.py`.

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
