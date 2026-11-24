# Milestone 2: Prompt Engineering Iteration Log

**Project:** AI Mock Interview Coach  
**Model:** `gemini-3.5-flash-lite`  
**Task:** Candidate Answer Evaluation Module Design & Prompt Iteration  

---

## 1. Executive Summary

This document details the architectural evolution of the candidate answer evaluation prompts for the AI Mock Interview Coach. To establish a rigorous, objective, and constructive feedback loop for job seekers, we designed three distinct prompt versions (V1, V2, and V3) moving from a naive baseline to a calibrated, evidence-based, rubric-driven evaluation system.

The final selected prompt (V3), integrated into `app.py` and saved under `prompts/final/prompt.txt`, enforces strict off-topic detection guardrails, calibrated 5-tier scoring, and structured JSON output matching the application's Pydantic schema.

---

## 2. Prompt Versions & Design Evolution

### Version 1 (V1) — Baseline Unstructured Evaluation
- **Location:** `prompts/v1/prompt.txt`
- **Core Intent:** Provide a minimal working baseline prompt to obtain a basic score and narrative feedback.
- **Prompt Structure:**
  - Generic persona: *"You are an interviewer evaluating a job candidate."*
  - Context passed: `{role}`, `{difficulty}`, `{interview_type}`, `{question}`, `{candidate_answer}`.
  - Vague instruction: *"Give a score from 1 to 10 and provide feedback on their answer."*
- **Design Limitations:**
  - **No Evaluation Criteria:** Lacks dimension-specific rubrics; does not separate technical correctness from communication fluency.
  - **Uncalibrated Scoring:** The model's definition of "7/10" vs "4/10" is unconstrained and subject to high variance.
  - **No Guardrails:** Susceptible to "hallucinated generosity"—giving high marks to articulate, fluent prose even if factually deficient or evasive.
  - **No Structured Output:** Produces freeform text that cannot be reliably parsed into UI components.

---

### Version 2 (V2) — Multi-Criteria Rubric-Based Evaluation
- **Location:** `prompts/v2/prompt.txt`
- **Design Changes from V1:**
  - **Pillars of Assessment:** Introduced four distinct evaluation dimensions:
    1. *Relevance* (Does the candidate answer the specific prompt?)
    2. *Technical Accuracy* (Is terminology and domain knowledge factually sound?)
    3. *Clarity* (Is structure and communication articulate?)
    4. *Completeness* (Are depth and key trade-offs covered?)
  - **More Detailed Persona:** Upgraded to an experienced technical interviewer for the specific job role.
  - **Categorized Sections:** Requested feedback split across the four categories alongside an overall score.
- **Design Limitations:**
  - **Lacks Anchor Calibrations:** Scores out of 10 remain subjective without explicit tier definitions.
  - **Vulnerability to Fluent Off-Topic Answers:** Without explicit penalty rules, the model may give points under "Clarity" and "Technical Accuracy" for a technically correct response to the *wrong* question.
  - **Missing Actionable Guidance:** Generates critique without concrete, step-by-step improvement suggestions.
  - **No Conversational Continuity:** Does not generate follow-up interview questions to probe deeper.

---

### Version 3 (V3) — Calibrated, Guardrailed, Evidence-Based Evaluation (Selected Final)
- **Location:** `prompts/v3/prompt.txt` & `prompts/final/prompt.txt`
- **Design Changes from V2:**
  - **Explicit Off-Topic Guardrail:** Explicit rule stipulating that non-responsive, evasive, or completely off-topic answers (such as answering a distributed rate limiting question with a hash map definition) must receive a maximum score between 0.0 and 2.0 regardless of how grammatically articulate the answer is.
  - **Calibrated 5-Tier Scoring Anchor Scale:**
    - `9.0 - 10.0`: Outstanding / Senior-ready (comprehensive, technically rigorous, handles trade-offs).
    - `7.5 - 8.9`: Strong (solid foundation, minor omissions or depth gaps).
    - `5.5 - 7.4`: Fair / Average (partially correct, misses core concepts or edge cases).
    - `3.5 - 5.4`: Below Expectations (shallow, notable technical inaccuracies or confusion).
    - `0.0 - 3.4`: Inadequate / Off-Topic (irrelevant or fundamentally incorrect).
  - **Evidence-Based Feedback:** Explicit instruction to cite specific claims, correct statements, and omissions from the candidate's actual text.
  - **Categorized Actionable Output:**
    - 2–4 Key Strengths (what the candidate did well).
    - 1–4 Areas for Improvement / Weaknesses (specific gaps).
    - 2–4 Actionable Suggestions (concrete recommendations to improve).
  - **Interviewer Follow-Up Question Generation:** Generates exactly one relevant follow-up question to probe conceptual boundaries or unaddressed trade-offs.
  - **Strict Structured JSON Schema:** Configured with `google.genai.types.GenerateContentConfig(response_mime_type="application/json", response_schema=AnswerEvaluation)` to guarantee 100% reliable UI rendering in Streamlit.

---

## 3. Comparison of Prompt Design Features

| Feature Dimension | V1 (Baseline) | V2 (Rubric-Based) | V3 / Final (Production) |
| :--- | :--- | :--- | :--- |
| **Interviewer Persona** | Generic ("Interviewer") | Experienced technical interviewer | Expert hiring manager calibrated to role and seniority |
| **Evaluation Dimensions** | None (General feedback) | 4 Criteria (Relevance, Accuracy, Clarity, Completeness) | 4 Criteria with explicit assessment questions per dimension |
| **Scoring Anchor Rubric** | None (1–10 arbitrary) | None (Overall score only) | 5-tier calibrated anchor scale with decimal precision |
| **Off-Topic Detection** | ❌ None | ❌ Weak / implicit | ✅ Strict rule cap (0.0 – 2.0 max) |
| **Evidence-Based Feedback** | ❌ None | ⚠️ General summary | ✅ Explicitly cites candidate's statements and omissions |
| **Actionable Suggestions** | ❌ General text | ⚠️ High-level notes | ✅ 2–4 concrete, actionable improvement recommendations |
| **Follow-Up Generation** | ❌ None | ❌ None | ✅ 1 context-aware follow-up question |
| **Output Format** | Unstructured free text | Semi-structured text headers | Strict JSON Schema via Pydantic model |

---

## 4. Preliminary Observations & Observed Application Tests

> [!NOTE]
> **Status Disclaimer:** The following observations represent preliminary application-level test runs executed on the live system using `gemini-3.5-flash-lite` with the application's evaluation module. These tests were conducted to verify real-world behavior and scoring calibration on contrasting candidate responses. They are **not** presented as a completed, side-by-side empirical benchmark of all three prompt versions (V1, V2, and V3) across a statistical test set.

### Observed Application Test 1: Off-Topic Answer
- **Target Role:** Software Engineer
- **Difficulty:** Hard
- **Interview Type:** Technical
- **Question:**  
  *"Design a distributed rate limiter that can handle 100,000 requests per second across multiple regions. How would you handle race conditions and synchronization?"*
- **Candidate Answer Submitted:**  
  *"A hash map is a data structure that implements an associative array abstract data type, a structure that can map keys to values. A hash map uses a hash function to compute an index, also called a hash code, into an array of buckets or slots, from which the desired value can be found. Collisions can be solved by chaining using linked lists or open addressing."*
- **Observed Result:**
  - **Assigned Score:** `1.0 / 10.0`
  - **Relevance:** Correctly identified that the answer was completely off-topic and failed to address distributed rate limiting.
  - **Technical Accuracy:** Noted that while the hash map definition was technically accurate in isolation, it was completely irrelevant to the system design question.
  - **Strengths:** Noted accurate definition of hash maps and collision resolution techniques.
  - **Weaknesses:** Highlighted total failure to answer the distributed rate limiter question.
  - **Follow-up Question:** Re-focused the candidate back to distributed rate limiting.
- **Key Takeaway:** The evaluation guardrail successfully prevented the model from giving an unearned high score based on the candidate's fluent and correct prose about an unrelated topic.

---

### Observed Application Test 2: Relevant Architecture Answer
- **Target Role:** Software Engineer
- **Difficulty:** Hard
- **Interview Type:** Technical
- **Question:**  
  *"Design a distributed rate limiter that can handle 100,000 requests per second across multiple regions. How would you handle race conditions and synchronization?"*
- **Candidate Answer Submitted:**  
  *"To design a distributed rate limiter for 100k RPS, I would use the Token Bucket algorithm backed by Redis as a centralized in-memory datastore. We maintain rate limits per user or API key, storing the current token count and timestamp of the last request. To prevent race conditions and concurrency conflicts, we use atomic operations in Redis so token inspection and decrement occur safely. If a client exceeds their limit, the service rejects the request with an HTTP 429 Too Many Requests response code."*
- **Observed Result:**
  - **Assigned Score:** `8.5 / 10.0`
  - **Relevance:** Recognized direct, comprehensive alignment with rate limiting and race condition prevention.
  - **Technical Accuracy:** Commended the use of the Token Bucket algorithm, centralized Redis, atomic operations for concurrency, per-user/API-key boundaries, and returning HTTP 429.
  - **Completeness & Identified Gaps:** The evaluation noted that while the core design was sound, the candidate did not explicitly address how to synchronize state across multiple geographic regions or the specific implementation details of the atomic operations (such as Redis Lua scripts), which prevented the answer from reaching the 9.0+ range.
  - **Follow-up Question:** Asked how to handle synchronization and latency trade-offs across multiple data center regions.
- **Key Takeaway:** The evaluation engine accurately calibrated the response at 8.5/10 ("Strong"): it credited the solid core components (Token Bucket, Redis, atomic operations, per-user limits, HTTP 429) while appropriately noting the absence of multi-region synchronization details.

---

## 5. Next Steps for Milestone 2

1. **Systematic Multi-Prompt Benchmark:** Run automated evaluation runs comparing V1, V2, and V3 side-by-side across a standardized dataset of candidate answers (ranging from empty/partial to off-topic, junior, and senior levels).
2. **Scoring Consistency Metrics:** Measure score variance and rubric adherence across repeated calls to verify prompt determinism.
3. **Candidate Experience Refinement:** Continue enhancing the UI feedback display based on candidate performance metrics.
