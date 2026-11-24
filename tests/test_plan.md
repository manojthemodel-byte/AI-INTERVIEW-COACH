# Milestone 2: Comprehensive Application Test Plan

**Project:** AI Mock Interview Coach  
**Target Model:** `gemini-3.5-flash-lite`  
**Application File:** `app.py`  
**Document Status:** In Progress (Manual & Automated Verification)  

---

## 1. Objectives & Testing Methodology

This test plan provides a standardized verification suite to evaluate the AI Mock Interview Coach across functional, edge, and invalid operational scenarios.

### Scope of Testing:
- **Functional Validation:** Verification of question generation, answer evaluation, rubric scoring (0.0 to 10.0), multidimensional feedback (Relevance, Technical Accuracy, Clarity, Completeness), strengths/weaknesses extraction, actionable suggestions, and context-aware follow-up question synthesis.
- **Session State Persistence:** Ensuring question text, candidate answer, and evaluation feedback persist across Streamlit reruns.
- **Client & Prompt Guardrails:** Verification of empty answer validation, off-topic detection guardrails (0.0–2.0 cap), and resilience against nonsensical or unusually long inputs.

### Test Type Legend:
- **Normal:** Standard candidate responses spanning different roles, difficulties, interview types, verbosity levels, and degrees of technical accuracy.
- **Edge:** Boundary conditions including empty inputs, single-word or terse responses, and topic mismatches.
- **Invalid / Unusual:** Non-standard inputs including keyboard mash / gibberish and very high word-count answers testing token limits.

> [!IMPORTANT]
> **Scoring Integrity Disclaimer:**  
> In accordance with scientific testing standards, **no actual AI scores or feedback have been invented** for unexecuted test cases. Only genuine, verified application observations and user-verified manual test executions (TC-01 through TC-10) contain recorded scores. At least 10 distinct manual test inputs are now fully recorded, including 3 distinct edge cases (TC-02, TC-03, TC-04). Remaining test cases (TC-11 and TC-12) remain marked as **`[Pending Live Execution]`**.

---

## 2. Master Test Cases Specification

---

### Test Case: TC-01 (Normal — Detailed & Relevant System Architecture)
- **Test ID:** `TC-01`
- **Type:** Normal
- **Job Role:** Software Engineer
- **Difficulty:** Hard
- **Interview Type:** Technical
- **Interview Question:**  
  *"Design a distributed rate limiter that can handle 100,000 requests per second across multiple regions. How would you handle race conditions and synchronization?"*
- **Candidate Answer:**  
  *"To design a distributed rate limiter for 100k RPS, I would use the Token Bucket algorithm backed by Redis as a centralized in-memory datastore. We maintain rate limits per user or API key, storing the current token count and timestamp of the last request. To prevent race conditions and concurrency conflicts, we use atomic operations in Redis so token inspection and decrement occur safely. If a client exceeds their limit, the service rejects the request with an HTTP 429 Too Many Requests response code."*
- **Expected Application Behavior:**
  - Application accepts input and generates structured evaluation via `gemini-3.5-flash-lite`.
  - Evaluates answer in the **Strong** performance bracket (7.5 – 8.9 / 10).
  - Praises Token Bucket algorithm, Redis in-memory storage, atomic concurrency control, per-user/API-key limits, and HTTP 429 status code.
  - Notes absence of detailed multi-region synchronization strategies or exact atomic implementation mechanics as areas for improvement.
  - Generates a relevant follow-up question probing cross-region synchronization or latency handling.
- **Prior Genuine Observation:**
  - **Status:** **VERIFIED IN APPLICATION TEST**
  - **Actual Observed Score:** `8.5 / 10.0`
  - **Observation Logged:** Recorded in `docs/prompt_iteration_log.md` (Observed Application Test 2).
  - **Verified Date:** 2026-11-22

---

### Test Case: TC-02 (Edge — Irrelevant / Off-Topic Answer)
- **Test ID:** `TC-02`
- **Type:** Edge
- **Job Role:** Software Engineer
- **Difficulty:** Hard
- **Interview Type:** Technical
- **Interview Question:**  
  *"Design a distributed rate limiter that can handle 100,000 requests per second across multiple regions. How would you handle race conditions and synchronization?"*
- **Candidate Answer:**  
  *"A hash map is a data structure that implements an associative array abstract data type, a structure that can map keys to values. A hash map uses a hash function to compute an index, also called a hash code, into an array of buckets or slots, from which the desired value can be found. Collisions can be solved by chaining using linked lists or open addressing."*
- **Expected Application Behavior:**
  - Strict off-topic guardrail triggers.
  - Score capped between `0.0` and `2.0 / 10.0` despite technically sound and articulate prose about hash maps.
  - Relevance assessment clearly flags that the answer does not address distributed rate limiting.
  - Weaknesses highlight complete topic mismatch.
  - Follow-up question redirects candidate back to the original rate limiter problem.
- **Prior Genuine Observation:**
  - **Status:** **VERIFIED IN APPLICATION TEST**
  - **Actual Observed Score:** `1.0 / 10.0`
  - **Observation Logged:** Recorded in `docs/prompt_iteration_log.md` (Observed Application Test 1).
  - **Verified Date:** 2026-11-22

---

### Test Case: TC-03 (Edge — Empty Answer Submission)
- **Test ID:** `TC-03`
- **Type:** Edge
- **Job Role:** Software Engineer
- **Difficulty:** Medium
- **Interview Type:** Technical
- **Interview Question:**  
  *"Explain how a hash map works internally and how hash collisions are resolved."*
- **Candidate Answer:**  
  `""` *(Empty text area or whitespace only)*
- **Expected Application Behavior:**
  - The application displays an empty-answer warning (`⚠️ Please enter your answer before requesting an evaluation.`) and blocks evaluation.
  - No score is generated.
  - Interview question, dropdown configuration, and UI state remain completely intact.
- **Manual Test Execution Record:**
  - **Status:** **PASS**
  - **Actual Score:** `N/A (Client-side validation)`
  - **Actual Observation:**
    - Empty answer was submitted.
    - Application displayed: *"Please enter your answer before requesting an evaluation."*
    - Evaluation was blocked and the warning appeared.
    - No actual score was generated.
  - **Evidence:** Screenshot of the warning banner, TC-03.
  - **Verified Date:** 2026-11-22

---

### Test Case: TC-04 (Edge — Extremely Short / Terse Answer)
- **Test ID:** `TC-04`
- **Type:** Edge
- **Job Role:** Data Analyst
- **Difficulty:** Easy
- **Interview Type:** Technical
- **Interview Question:**  
  *"What is the difference between the WHERE clause and the HAVING clause in SQL?"*
- **Candidate Answer:**  
  *"HAVING filters groups, WHERE filters rows."*
- **Expected Application Behavior:**
  - Evaluation identifies that the core concept is directionally accurate but severely lacks explanation, syntax context, or examples.
  - Categorized under Below Expectations or Fair (`3.5 - 5.5 / 10.0`).
  - Completeness assessment notes absence of aggregation examples (e.g., `GROUP BY`, `COUNT`, `SUM`).
  - Suggestions recommend providing full SQL query examples.
  - Follow-up question asks for an example query illustrating both clauses.
- **Manual Test Execution Record:**
  - **Status:** **PASS**
  - **Expected Range:** `3.5 – 5.5`
  - **Actual Score:** `5.0 / 10.0`
  - **Actual Behavior:** Correctly identified the core SQL distinction but deducted marks for missing explanation, execution order, and practical examples.
  - **Evidence:** User-provided screenshot of the 5.0/10 evaluation dashboard.
  - **Verified Date:** 2026-11-22

---

### Test Case: TC-05 (Normal — Concise & Highly Accurate Technical Answer)
- **Test ID:** `TC-05`
- **Type:** Normal
- **Job Role:** Data Scientist
- **Difficulty:** Easy
- **Interview Type:** Technical
- **Interview Question:**  
  *"Explain what overfitting means in machine learning and how you can prevent it."*
- **Candidate Answer:**  
  *"Overfitting occurs when a machine learning model fits too closely to the training data, capturing random noise rather than underlying patterns, which causes poor generalization on unseen test data. Common techniques to prevent overfitting include: using cross-validation to tune hyperparameters, applying L1/L2 regularization penalties, pruning decision trees, using dropout in neural networks, and augmenting or collecting more training data."*
- **Expected Application Behavior:**
  - High score in the Strong or Outstanding bracket (`8.0 - 9.5 / 10.0`).
  - Relevance and Technical Accuracy scored high; commends clear definition and enumeration of 5 distinct prevention techniques across model paradigms.
  - Clarity praised for crisp, professional terminology.
  - Follow-up question probes deeper into one of the mentioned techniques (e.g., mathematical difference between L1 and L2 regularization).
- **Manual Test Execution Record:**
  - **Status:** **PASS**
  - **Expected Range:** `8.0 – 9.5`
  - **Actual Score:** `8.5 / 10.0`
  - **Actual Behavior:** Answer successfully covered the definition of overfitting, poor generalization on unseen data, and 5 prevention techniques (cross-validation, L1/L2 regularization, decision tree pruning, dropout, and more training data).
  - **Evidence:** User-reported manual execution result.
  - **Verified Date:** 2026-11-22

---

### Test Case: TC-06 (Normal — Partially Correct / Flawed A/B Testing Answer)
- **Test ID:** `TC-06`
- **Type:** Normal
- **Job Role:** Data Scientist
- **Difficulty:** Medium
- **Interview Type:** Technical
- **Interview Question:**  
  *"How would you design an A/B test to evaluate a new recommendation algorithm for an e-commerce platform, specifically addressing how you would determine the required sample size, handle potential novelty effects, and decide whether to stop the experiment early if the initial results look overwhelmingly positive?"*
- **Candidate Answer:**  
  *"I would divide users into two groups and show the new recommendation algorithm to one group and the old algorithm to the other. I would compare click-through rates to decide which algorithm is better. I would use around 100 users in each group because that should be enough. Novelty effects are not a major concern because users will eventually get used to the new system. If the initial results show a big improvement, I would stop the experiment early and launch the new algorithm."*
- **Expected Application Behavior:**
  - Evaluator recognizes response touches on sample size, novelty effects, and early stopping, but identifies severe statistical flaws and lack of depth.
  - Scores answer in the Below Expectations / Flawed bracket (`3.0 – 5.0 / 10.0`).
  - Penalizes unjustified arbitrary sample size (100 users) and absence of power, significance, MDE, and variance calculations.
  - Penalizes dismissal of novelty effects and flags the peeking problem / inflated Type I error risks of naive early stopping.
- **Manual Test Execution Record:**
  - **Status:** **PASS** *(Application correctly evaluated the flawed response, penalizing statistical misconceptions and providing rigorous feedback)*
  - **Expected Range:** `3.0 – 5.0`
  - **Actual Score:** `3.0 / 10.0`
  - **Actual Feedback:** The answer addressed sample size, novelty effects and early stopping, but the sample size assumption was statistically unjustified. It failed to discuss statistical power, significance levels, baseline conversion rate, minimum detectable effect, and variance. Early stopping based on positive initial results risks the peeking problem and inflated Type I error. The response was easy to follow but lacked depth.
  - **Evidence:** User-provided screenshot of the A/B testing evaluation dashboard.
  - **Verified Date:** 2026-11-22

---

### Test Case: TC-07 (Normal — Severely Flawed Imbalanced Classification Answer)
- **Test ID:** `TC-07`
- **Type:** Normal
- **Job Role:** Data Scientist
- **Difficulty:** Medium
- **Interview Type:** Technical
- **Interview Question:**  
  *"In a customer churn prediction problem where only 2% of customers actually churn (extreme class imbalance), what evaluation metrics would you prioritize and what techniques would you use to handle the data imbalance?"*
- **Candidate Answer:**  
  *"I would use accuracy as the main evaluation metric because it tells us how many predictions are correct. Since 98% of customers do not churn, even a model predicting that nobody will churn can achieve 98% accuracy, which is quite good. I would use only accuracy to compare models. To handle imbalance, I would simply duplicate the churn records until both classes are equal. I would not need to check precision or recall because accuracy is enough."*
- **Expected Application Behavior:**
  - Evaluator detects fundamental statistical flaws and misleading reliance on accuracy for an extreme (2%) imbalanced classification dataset.
  - Scores answer in the Inadequate / Severely Flawed tier (`1.0 – 2.5 / 10.0`).
  - Flags that predicting no churn yields trivial 98% accuracy without operational utility.
  - Penalizes naive duplicate oversampling without considering overfitting or cross-validation leak.
  - Criticizes explicit omission of precision, recall, F1, PR-AUC, ROC-AUC, SMOTE, and cost-sensitive learning.
- **Manual Test Execution Record:**
  - **Status:** **PASS** *(Application correctly caught the severe statistical fallacies, penalizing reliance on accuracy and naive duplication with an appropriately low 1.5/10 score)*
  - **Expected Range:** `1.0 – 2.5`
  - **Actual Score:** `1.5 / 10.0`
  - **Actual Feedback:** The evaluator identified misleading accuracy on a 2% imbalanced dataset, naive oversampling without considering overfitting or validation, and omissions including precision, recall, F1-score, ROC-AUC, PR-AUC, cost-sensitive learning, and SMOTE.
  - **Evidence:** User-provided screenshot of the churn evaluation dashboard.
  - **Verified Date:** 2026-11-22

---

### Test Case: TC-08 (Normal — Flawed Lock-Free Queue Concurrency Answer)
- **Test ID:** `TC-08`
- **Type:** Normal
- **Job Role:** Software Engineer
- **Difficulty:** Hard
- **Interview Type:** Technical
- **Interview Question:**  
  *"Design and implement a thread-safe, lock-free bounded queue in your language of choice, and explain how its memory ordering guarantees prevent race conditions and data corruption under high concurrency."*
- **Candidate Answer:**  
  The candidate proposed a shared array with front/rear variables, artificial delays between thread operations, a mutex while incorrectly claiming it is lock-free, relaxed memory ordering, and a simple queue-size check.
- **Expected Application Behavior:**
  - Evaluator identifies critical technical contradictions (using a mutex while asserting the design is lock-free).
  - Penalizes reliance on thread sleep/delays for synchronization and inadequate relaxed memory ordering.
  - Scores answer in the Inadequate / Severely Flawed bracket (`1.0 – 2.5 / 10.0`).
- **Manual Test Execution Record:**
  - **Status:** **PASS** *(Application correctly penalized contradictory lock-free claims and invalid concurrency mechanisms with a low 1.5/10 score)*
  - **Expected Range:** `1.0 – 2.5`
  - **Actual Score:** `1.5 / 10.0`
  - **Actual Feedback:** Evaluator identified contradictory use of a mutex in a supposedly lock-free design, reliance on thread delays, and inadequate relaxed memory ordering guarantees.
  - **Evidence:** User-provided screenshot of the evaluation dashboard.
  - **Verified Date:** 2026-11-22

---

### Test Case: TC-09 (Normal — Flawed DAU Drop Investigation Answer)
- **Test ID:** `TC-09`
- **Type:** Normal
- **Job Role:** Data Analyst
- **Difficulty:** Medium
- **Interview Type:** Technical
- **Interview Question:**  
  *"Imagine you are analyzing user engagement data for an e-commerce platform, and you notice a sudden, sharp drop in daily active users (DAU) over the past week. Walk me through your step-by-step analytical approach to investigate this drop, including how you would differentiate between a potential data pipeline error, a tracking implementation bug, and an actual behavioral shift in user retention."*
- **Candidate Answer:**  
  The candidate immediately blamed declining user interest, checked only the dashboard's weekly totals, suggested a marketing campaign, ignored pipeline and tracking investigations, and proposed waiting another week.
- **Expected Application Behavior:**
  - Evaluator identifies critical analytical shortcomings: premature assumption of behavioral decline without investigation.
  - Penalizes reliance solely on high-level dashboard totals, failure to verify data pipelines or tracking telemetry, and proposing passive waiting.
  - Scores answer in the Inadequate / Severely Flawed bracket (`1.0 – 2.5 / 10.0`).
- **Manual Test Execution Record:**
  - **Status:** **PASS** *(Application correctly penalized the superficial analysis, omitted pipeline checks, and unjustified assumptions with a low 1.5/10 score)*
  - **Expected Range:** `1.0 – 2.5`
  - **Actual Score:** `1.5 / 10.0`
  - **Actual Feedback:** Evaluator scored the response 1.5/10, penalizing the premature assumption of declining user interest, reliance solely on weekly totals, neglect of pipeline and tracking verifications, and proposing to wait rather than investigating.
  - **Evidence:** User-provided screenshot of the evaluation dashboard.
  - **Verified Date:** 2026-11-22

---

### Test Case: TC-10 (Normal — Strong & Scalable URL Shortener System Design)
- **Test ID:** `TC-10`
- **Type:** Normal
- **Job Role:** Software Engineer
- **Difficulty:** Hard
- **Interview Type:** Technical
- **Interview Question:**  
  *"How would you design a scalable, highly available URL shortening service (like TinyURL or Bitly) that handles high read and write throughput while ensuring low latency?"*
- **Candidate Answer:**  
  Comprehensive system design answer covering:
  - Horizontally scalable stateless application servers behind global and regional load balancers.
  - Distributed Snowflake IDs and Base62 encoding (avoiding hash collision retries).
  - Distributed NoSQL datastore (Cassandra / DynamoDB) partitioned by short key for horizontal scalability and fast key-value lookups.
  - Multi-tier caching with Redis cluster and CDN / edge caching for redirect acceleration.
  - Cache strategies: Cache-aside pattern, appropriate TTLs, request coalescing (mitigating cache stampedes / thundering herds), and negative caching for invalid keys.
  - High availability & resilience: Hot-key mitigation, autoscaling, token-bucket rate limiting, and graceful load shedding.
  - Asynchronous analytics telemetry: Decoupled message queues (e.g., Kafka) and continuous health monitoring.
  - Fault tolerance & disaster recovery: Multi-region replication, data partitioning, automated backups, and cross-region disaster recovery failover.
- **Expected Application Behavior:**
  - Evaluator scores in the top tier (`9.0 – 10.0 / 10.0`) for architectural depth, completeness, and scalability awareness.
  - Commends distributed ID generation, database selection and partitioning, caching hierarchy and stampede mitigation, rate limiting, and asynchronous analytics decoupling.
  - Evaluates high technical accuracy, logical structure, and clarity.
- **Manual Test Execution Record:**
  - **Status:** **PASS** *(Evaluator scored the comprehensive system design 9.2/10, confirming high-tier evaluation performance)*
  - **Expected Range:** `9.0 – 10.0`
  - **Actual Score:** `9.2 / 10.0`
  - **Actual Feedback:** Evaluator awarded 9.2/10 as a strong-answer diagnostic, recognizing comprehensive coverage across load balancing, Base62/Snowflake ID generation, NoSQL storage, multi-tier caching, resilience mechanisms, and asynchronous analytics pipelines.
  - **Evidence:** User-reported from evaluation dashboard (strong-answer diagnostic).
  - **Verified Date:** 2026-11-22

---

### Test Case: TC-11 (Invalid / Unusual — Nonsensical Keyboard Mash / Gibberish)
- **Test ID:** `TC-11`
- **Type:** Invalid
- **Job Role:** Data Analyst
- **Difficulty:** Easy
- **Interview Type:** Technical
- **Interview Question:**  
  *"What is the difference between an inner join and a left outer join in SQL?"*
- **Candidate Answer:**  
  *"asdfjkl; qwertyuiop 12345 zxcvbnm!@#$%^&*()_+ lorem ipsum dolor sit amet blablabla foo bar bazzzzzz"*
- **Expected Application Behavior:**
  - Application does not crash or throw unhandled exceptions.
  - Evaluator identifies input as nonsensical / non-responsive text.
  - Strict guardrail triggers: score strictly capped between `0.0` and `2.0 / 10.0`.
  - Relevance assessment notes input does not contain meaningful SQL concepts.
  - Weaknesses state no substantive response was provided.
  - Follow-up question asks candidate to restate the definition of SQL joins.
- **Execution Status:** `[Pending Live Execution]`
  - Actual AI Score: `[Pending execution]`
  - Actual Feedback: `[Pending execution]`

---

### Test Case: TC-12 (Edge — Reluctant / 'I Don't Know' Answer with Speculation)
- **Test ID:** `TC-12`
- **Type:** Edge
- **Job Role:** Software Engineer
- **Difficulty:** Medium
- **Interview Type:** Technical
- **Interview Question:**  
  *"Explain the difference between TCP and UDP and give an example of when you would use each."*
- **Candidate Answer:**  
  *"To be completely honest, I don't know the exact protocol details, but I think TCP is used for regular web pages and UDP is something used for gaming or live streaming where speed matters more than losing a packet."*
- **Expected Application Behavior:**
  - Identifies honesty and notes the high-level intuition about web browsing vs gaming is correct.
  - Scores in Below Expectations bracket (`3.0 - 4.5 / 10.0`) due to lack of technical depth.
  - Weaknesses highlight missing technical mechanisms: 3-way handshake, connection-oriented vs connectionless, reliability guarantees, flow control, congestion control, and packet ordering.
  - Follow-up question asks candidate to explain what happens when a packet is dropped in TCP versus UDP.
- **Execution Status:** `[Pending Live Execution]`
  - Actual AI Score: `[Pending execution]`
  - Actual Feedback: `[Pending execution]`

---

## 3. Test Coverage Matrix

| Category | Test Case IDs | Roles Covered | Difficulty Levels | Interview Types |
| :--- | :--- | :--- | :--- | :--- |
| **Normal: Relevant & Detailed** | `TC-01`, `TC-07`, `TC-08`, `TC-09`, `TC-10` | Software Eng, Data Analyst, Data Scientist | Medium, Hard | Technical, HR, Mixed |
| **Normal: Concise Answers** | `TC-05` | Data Scientist | Easy | Technical |
| **Normal: Partially Correct** | `TC-06` | Data Scientist | Medium | Technical |
| **Edge: Empty Answer** | `TC-03` | Software Engineer | Medium | Technical |
| **Edge: Extremely Short** | `TC-04`, `TC-12` | Data Analyst, Software Eng | Easy, Medium | Technical |
| **Edge: Irrelevant / Off-Topic** | `TC-02` | Software Engineer | Hard | Technical |
| **Invalid / Unusual: Nonsensical** | `TC-11` | Data Analyst | Easy | Technical |

---

## 4. Manual Execution Guide for Streamlit

Follow these steps to manually execute and record results for any test case in the running application:

### Step 1: Launch Application
In your terminal, activate your virtual environment and start Streamlit:
```powershell
.\.venv\Scripts\streamlit run app.py
```

### Step 2: Configure Interview Settings
Match the test case configuration in the UI dropdowns:
- **Target Job Role:** Select `Software Engineer`, `Data Analyst`, or `Data Scientist`.
- **Difficulty:** Select `Easy`, `Medium`, or `Hard`.
- **Interview Type:** Select `Technical`, `HR`, or `Mixed`.

### Step 3: Set Question
- Click **Generate Interview Question** to generate a live question, OR test against the specific predefined prompt in the test case.

### Step 4: Submit Candidate Answer
- Paste the exact text from the **Candidate Answer** field of the test case into the **"Type your answer:"** text area.
- For `TC-03` (Empty Answer), leave the text area completely blank.

### Step 5: Trigger Evaluation & Record Output
- Click **"🎯 Evaluate My Answer"**.
- Confirm that the response renders:
  1. **Overall Score:** (e.g., `8.5 / 10.0`)
  2. **Core Criteria Breakdown:** Relevance, Technical Accuracy, Clarity, Completeness
  3. **Key Strengths**
  4. **Areas for Improvement**
  5. **Actionable Suggestions**
  6. **Follow-Up Question**
- Record the actual score and feedback in your execution log.

---

## 5. Execution Summary Table (To Record Live Test Results)

| Test ID | Role | Difficulty | Type | Status | Expected Score Range | Actual Score | Verified Date |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Software Engineer | Hard | Normal | **Observed** | 7.5 – 8.9 | **8.5 / 10** | 2026-11-22 |
| **TC-02** | Software Engineer | Hard | Edge | **Observed** | 0.0 – 2.0 | **1.0 / 10** | 2026-11-22 |
| **TC-03** | Software Engineer | Medium | Edge | **PASS** | N/A (Client warning) | N/A (Client-side validation) | 2026-11-22 |
| **TC-04** | Data Analyst | Easy | Edge | **PASS** | 3.5 – 5.5 | **5.0 / 10** | 2026-11-22 |
| **TC-05** | Data Scientist | Easy | Normal | **PASS** | 8.0 – 9.5 | **8.5 / 10** | 2026-11-22 |
| **TC-06** | Data Scientist | Medium | Normal | **PASS** | 3.0 – 5.0 | **3.0 / 10** | 2026-11-22 |
| **TC-07** | Data Scientist | Medium | Normal | **PASS** | 1.0 – 2.5 | **1.5 / 10** | 2026-11-22 |
| **TC-08** | Software Engineer | Hard | Normal | **PASS** | 1.0 – 2.5 | **1.5 / 10** | 2026-11-22 |
| **TC-09** | Data Analyst | Medium | Normal | **PASS** | 1.0 – 2.5 | **1.5 / 10** | 2026-11-22 |
| **TC-10** | Software Engineer | Hard | Normal | **PASS** | 9.0 – 10.0 | **9.2 / 10** | 2026-11-22 |
| **TC-11** | Data Analyst | Easy | Invalid | Ready | 0.0 – 2.0 | `[Pending]` | — |
| **TC-12** | Software Engineer | Medium | Edge | Ready | 3.0 – 4.5 | `[Pending]` | — |
