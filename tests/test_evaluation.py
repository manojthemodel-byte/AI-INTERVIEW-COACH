"""
Automated Evaluation Test Suite for AI Mock Interview Coach.
Verifies the answer evaluation module, prompt version differentiation,
schema consistency, and sample test case specifications.
Compatible with both pytest and unittest.
"""

import json
import os
import unittest
from dotenv import load_dotenv

# Load environment
load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class TestInterviewCoachEvaluation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_file = os.path.join(os.path.dirname(__file__), "sample_test_cases.json")
        with open(test_file, "r", encoding="utf-8") as f:
            cls.test_cases = json.load(f)

    def test_sample_cases_structure(self):
        """Verify sample test cases contain all required fields."""
        self.assertGreaterEqual(len(self.test_cases), 2)
        for tc in self.test_cases:
            self.assertIn("id", tc)
            self.assertIn("question", tc)
            self.assertIn("candidate_answer", tc)
            self.assertIn("observed_application_score", tc)
            self.assertIn("expected_behavior", tc)

    def test_off_topic_test_case_spec(self):
        """Verify the off-topic test case (TC-01) specification."""
        tc_offtopic = next((tc for tc in self.test_cases if tc["id"] == "TC-01"), None)
        self.assertIsNotNone(tc_offtopic)
        self.assertEqual(tc_offtopic["observed_application_score"], 1.0)
        self.assertIn("hash map", tc_offtopic["candidate_answer"].lower())
        self.assertIn("rate limiter", tc_offtopic["question"].lower())

    def test_relevant_test_case_spec(self):
        """Verify the relevant answer test case (TC-02) specification and verify factual claims."""
        tc_relevant = next((tc for tc in self.test_cases if tc["id"] == "TC-02"), None)
        self.assertIsNotNone(tc_relevant)
        self.assertEqual(tc_relevant["observed_application_score"], 8.5)
        ans = tc_relevant["candidate_answer"].lower()
        # Verify actual mentioned concepts
        self.assertIn("token bucket", ans)
        self.assertIn("redis", ans)
        self.assertIn("atomic", ans)
        self.assertIn("429", ans)
        self.assertTrue("user" in ans or "api key" in ans)
        # Verify that unsupported claims are not in the candidate answer
        self.assertNotIn("lua", ans)
        self.assertNotIn("cross-region synchronization", ans)

    def test_prompt_files_exist_and_meaningfully_different(self):
        """Verify that V1, V2, and V3 prompts exist and are genuinely different."""
        p1_path = os.path.join(BASE_DIR, "prompts", "v1", "prompt.txt")
        p2_path = os.path.join(BASE_DIR, "prompts", "v2", "prompt.txt")
        p3_path = os.path.join(BASE_DIR, "prompts", "v3", "prompt.txt")
        final_path = os.path.join(BASE_DIR, "prompts", "final", "prompt.txt")

        for p in [p1_path, p2_path, p3_path, final_path]:
            self.assertTrue(os.path.exists(p), f"Missing prompt file: {p}")

        with open(p1_path, "r", encoding="utf-8") as f:
            v1_text = f.read().strip()
        with open(p2_path, "r", encoding="utf-8") as f:
            v2_text = f.read().strip()
        with open(p3_path, "r", encoding="utf-8") as f:
            v3_text = f.read().strip()
        with open(final_path, "r", encoding="utf-8") as f:
            final_text = f.read().strip()

        # Check genuine differences
        self.assertNotEqual(v1_text, v2_text)
        self.assertNotEqual(v2_text, v3_text)
        self.assertNotEqual(v1_text, v3_text)

        # V1 is unstructured baseline
        self.assertNotIn("Relevance", v1_text)
        self.assertNotIn("Technical Accuracy", v1_text)

        # V2 adds 4-dimension rubric
        self.assertIn("Relevance", v2_text)
        self.assertIn("Technical Accuracy", v2_text)
        self.assertIn("Clarity", v2_text)
        self.assertIn("Completeness", v2_text)
        self.assertNotIn("Off-Topic / Evasive Responses", v2_text)

        # V3 adds explicit guardrails, calibrated scoring tiers, and JSON schema requirements
        self.assertIn("Off-Topic / Evasive Responses", v3_text)
        self.assertIn("9.0 - 10.0: Outstanding", v3_text)
        self.assertIn("JSON Schema", v3_text)
        self.assertIn("follow_up_question", v3_text)

        # Final prompt matches V3 production prompt
        self.assertEqual(final_text, v3_text)

    def test_app_loads_final_prompt(self):
        """Verify that app.py uses the final evaluation prompt stored in prompts/final/prompt.txt."""
        from app import get_evaluation_prompt
        final_prompt_path = os.path.join(BASE_DIR, "prompts", "final", "prompt.txt")
        with open(final_prompt_path, "r", encoding="utf-8") as f:
            expected_template = f.read()

        formatted_prompt = get_evaluation_prompt(
            role="Software Engineer",
            difficulty="Hard",
            interview_type="Technical",
            question="What is Paxos?",
            candidate_answer="Paxos is a consensus algorithm."
        )

        expected_formatted = expected_template.format(
            role="Software Engineer",
            difficulty="Hard",
            interview_type="Technical",
            question="What is Paxos?",
            candidate_answer="Paxos is a consensus algorithm."
        )

        self.assertEqual(formatted_prompt, expected_formatted)

    def test_question_prompt_file_exists_and_valid(self):
        """Verify that prompts/question/prompt.txt exists and contains expected stage instructions."""
        q_path = os.path.join(BASE_DIR, "prompts", "question", "prompt.txt")
        self.assertTrue(os.path.exists(q_path), f"Missing question prompt file: {q_path}")
        with open(q_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("{role}", content)
        self.assertIn("{difficulty}", content)
        self.assertIn("{interview_type}", content)
        self.assertIn("{stage_name}", content)
        self.assertIn("{stage_focus}", content)
        self.assertIn("Questions 1–4", content)
        self.assertIn("Questions 5–11", content)
        self.assertIn("Questions 12–15", content)

    def test_interview_stage_selection_rules(self):
        """Verify interview stage awareness across questions 1 to 15 and default mode."""
        from app import get_interview_stage

        # Default / single-question practice (None, 0, negative)
        default_name, default_focus = get_interview_stage(None)
        self.assertIn("General", default_name)
        self.assertIn("Comprehensive", default_focus)

        name_0, _ = get_interview_stage(0)
        self.assertEqual(name_0, default_name)

        # Stage 1: Questions 1 to 4 (Foundational concepts & definitions)
        for q_num in [1, 2, 3, 4]:
            stage_name, stage_focus = get_interview_stage(q_num)
            self.assertIn("Foundational", stage_name)
            self.assertIn("Stage 1 of 3", stage_name)
            self.assertIn("Foundational concepts", stage_focus)

        # Stage 2: Questions 5 to 11 (Technical implementation, algorithms & architecture)
        for q_num in [5, 8, 11]:
            stage_name, stage_focus = get_interview_stage(q_num)
            self.assertIn("Technical Implementation", stage_name)
            self.assertIn("Stage 2 of 3", stage_name)
            self.assertIn("implementation", stage_focus.lower())

        # Stage 3: Questions 12 to 15 (Advanced scenarios, debugging & decisions)
        for q_num in [12, 14, 15]:
            stage_name, stage_focus = get_interview_stage(q_num)
            self.assertIn("Advanced Scenarios", stage_name)
            self.assertIn("Stage 3 of 3", stage_name)
            self.assertIn("debugging", stage_focus.lower())

    def test_get_question_prompt_formatting_and_adaptation(self):
        """Verify get_question_prompt dynamically formats stage, role, and anti-repetition rules."""
        from app import get_question_prompt

        # Test single-question practice mode (question_number=None)
        prompt_single = get_question_prompt(
            role="Data Analyst",
            difficulty="Easy",
            interview_type="Technical",
            question_number=None
        )
        self.assertIn("Data Analyst", prompt_single)
        self.assertIn("Easy", prompt_single)
        self.assertIn("Single-Question Practice", prompt_single)
        self.assertIn("General Technical Practice", prompt_single)

        # Test paced session mode (e.g. Question 7 of 15 -> Stage 2)
        prompt_session = get_question_prompt(
            role="Software Engineer",
            difficulty="Hard",
            interview_type="Technical",
            question_number=7,
            previous_question="What is a hash table?",
            history=["What is an array?", "What is a linked list?"]
        )
        self.assertIn("Software Engineer", prompt_session)
        self.assertIn("Hard", prompt_session)
        self.assertIn("Question 7 of 15", prompt_session)
        self.assertIn("Stage 2 of 3", prompt_session)
        self.assertIn("IMPORTANT REQUIREMENT:", prompt_session)
        self.assertIn("What is a hash table?", prompt_session)
        self.assertIn("What is an array?", prompt_session)
        self.assertIn("What is a linked list?", prompt_session)

        # Ensure no raw unformatted template variables remain
        self.assertNotIn("{role}", prompt_session)
        self.assertNotIn("{difficulty}", prompt_session)
        self.assertNotIn("{interview_type}", prompt_session)
        self.assertNotIn("{stage_name}", prompt_session)

    def test_session_initialization(self):
        """Verify init_interview_session defaults to 15 questions and sets clean state."""
        from app import init_interview_session

        # Default 15 questions
        session_default = init_interview_session()
        self.assertEqual(session_default["total_questions"], 15)
        self.assertEqual(session_default["current_index"], 1)
        self.assertFalse(session_default["completed"])
        self.assertEqual(session_default["turns"], [])
        self.assertIsNone(session_default["current_question"])
        self.assertEqual(session_default["current_answer"], "")
        self.assertIsNone(session_default["current_evaluation"])

        # Custom total questions (e.g., 5 questions)
        session_custom = init_interview_session(total_questions=5)
        self.assertEqual(session_custom["total_questions"], 5)
        self.assertEqual(session_custom["current_index"], 1)
        self.assertFalse(session_custom["completed"])

    def test_session_progress_calculation(self):
        """Verify calculate_session_progress handles start, middle, end, and edge cases."""
        from app import calculate_session_progress

        # Question 1 of 15
        prog, label = calculate_session_progress(1, 15)
        self.assertAlmostEqual(prog, 1 / 15)
        self.assertEqual(label, "Question 1 of 15")

        # Question 8 of 15
        prog, label = calculate_session_progress(8, 15)
        self.assertAlmostEqual(prog, 8 / 15)
        self.assertEqual(label, "Question 8 of 15")

        # Question 15 of 15
        prog, label = calculate_session_progress(15, 15)
        self.assertAlmostEqual(prog, 1.0)
        self.assertEqual(label, "Question 15 of 15")

        # Edge cases: 0 or negative total_questions defaults safely
        prog_zero, label_zero = calculate_session_progress(1, 0)
        self.assertEqual(prog_zero, 1.0)
        self.assertEqual(label_zero, "Question 1 of 1")

    def test_prevention_of_skipping_unanswered_or_unevaluated_questions(self):
        """Verify can_advance_session strictly prevents advancing without answer and evaluation."""
        from app import can_advance_session

        dummy_eval = {"overall_score": 8.0, "strengths": ["Clear explanation"]}

        # Blank answer cases
        self.assertFalse(can_advance_session("", dummy_eval))
        self.assertFalse(can_advance_session("   \n\t  ", dummy_eval))
        self.assertFalse(can_advance_session(None, dummy_eval))

        # Missing or invalid evaluation cases
        self.assertFalse(can_advance_session("Here is my answer.", None))
        self.assertFalse(can_advance_session("Here is my answer.", "not-a-dict"))
        self.assertFalse(can_advance_session("Here is my answer.", []))

        # Both blank and no evaluation
        self.assertFalse(can_advance_session("", None))

        # Valid answer and valid evaluation
        self.assertTrue(can_advance_session("Here is a thorough technical answer.", dummy_eval))

    def test_session_turn_recording_and_storage(self):
        """Verify record_session_turn properly indexes and persists interview turns."""
        from app import init_interview_session, record_session_turn

        session = init_interview_session(total_questions=3)
        dummy_eval = {"overall_score": 7.5, "strengths": ["Good clarity"]}

        turn = record_session_turn(
            session=session,
            question="Explain CAP theorem.",
            answer="Consistency, Availability, Partition tolerance trade-offs.",
            evaluation=dummy_eval,
            role="Backend Engineer",
            difficulty="Medium",
            interview_type="System Design"
        )

        self.assertEqual(len(session["turns"]), 1)
        self.assertEqual(turn["question_number"], 1)
        self.assertEqual(turn["question"], "Explain CAP theorem.")
        self.assertEqual(turn["answer"], "Consistency, Availability, Partition tolerance trade-offs.")
        self.assertEqual(turn["evaluation"], dummy_eval)
        self.assertEqual(turn["role"], "Backend Engineer")
        self.assertEqual(turn["difficulty"], "Medium")
        self.assertEqual(turn["interview_type"], "System Design")
        self.assertEqual(session["current_evaluation"], dummy_eval)

        # Idempotent re-recording on same question replaces/updates rather than duplicating
        updated_eval = {"overall_score": 8.5, "strengths": ["Refined explanation"]}
        record_session_turn(
            session=session,
            question="Explain CAP theorem.",
            answer="Refined answer with PACELC theorem mention.",
            evaluation=updated_eval,
            role="Backend Engineer",
            difficulty="Medium",
            interview_type="System Design"
        )
        self.assertEqual(len(session["turns"]), 1)
        self.assertEqual(session["turns"][0]["evaluation"]["overall_score"], 8.5)

    def test_session_advancement_and_completion_condition(self):
        """Verify advance_session steps through questions and marks session completed at limit."""
        from app import init_interview_session, advance_session, record_session_turn

        session = init_interview_session(total_questions=2)
        dummy_eval = {"overall_score": 8.0}

        # Step 1: Record Q1 turn and advance
        record_session_turn(session, "Q1 text", "A1 text", dummy_eval, "SDE", "Easy", "Technical")
        self.assertEqual(session["current_index"], 1)
        self.assertFalse(session["completed"])

        advance_session(session)
        self.assertEqual(session["current_index"], 2)
        self.assertFalse(session["completed"])
        self.assertIsNone(session["current_question"])
        self.assertEqual(session["current_answer"], "")
        self.assertIsNone(session["current_evaluation"])

        # Step 2: Record Q2 turn and advance
        record_session_turn(session, "Q2 text", "A2 text", dummy_eval, "SDE", "Easy", "Technical")
        self.assertEqual(session["current_index"], 2)
        self.assertFalse(session["completed"])

        advance_session(session)
        # Reached total_questions (2) -> completed should now be True
        self.assertTrue(session["completed"])
        self.assertEqual(len(session["turns"]), 2)

    def test_dashboard_average_score_and_extrema_calculation(self):
        """Verify calculate_session_metrics computes average score, highest, lowest, and rating."""
        from app import calculate_session_metrics

        history = [
            {
                "question_number": 1,
                "question": "Explain quicksort vs mergesort.",
                "score": 8.0,
                "evaluation": {"score": 8.0}
            },
            {
                "question_number": 2,
                "question": "Design a distributed cache.",
                "score": 9.5,
                "evaluation": {"score": 9.5}
            },
            {
                "question_number": 3,
                "question": "What is overfitting in ML?",
                "score": 6.5,
                "evaluation": {"score": 6.5}
            }
        ]

        metrics = calculate_session_metrics(history)
        self.assertEqual(metrics["total_completed"], 3)
        # Average: (8.0 + 9.5 + 6.5) / 3 = 24.0 / 3 = 8.0
        self.assertEqual(metrics["average_score"], 8.0)
        self.assertEqual(metrics["highest_score"], 9.5)
        self.assertIsNotNone(metrics["highest_turn"])
        self.assertEqual(metrics["highest_turn"]["question_number"], 2)
        self.assertEqual(metrics["lowest_score"], 6.5)
        self.assertIsNotNone(metrics["lowest_turn"])
        self.assertEqual(metrics["lowest_turn"]["question_number"], 3)
        self.assertEqual(metrics["performance_rating"], "Strong")

    def test_dashboard_performance_rating_brackets(self):
        """Verify calculate_performance_rating conforms to the 5-tier calibrated rubric."""
        from app import calculate_performance_rating

        self.assertEqual(calculate_performance_rating(10.0), "Outstanding")
        self.assertEqual(calculate_performance_rating(9.0), "Outstanding")
        self.assertEqual(calculate_performance_rating(8.9), "Strong")
        self.assertEqual(calculate_performance_rating(7.5), "Strong")
        self.assertEqual(calculate_performance_rating(7.4), "Fair")
        self.assertEqual(calculate_performance_rating(5.0), "Fair")
        self.assertEqual(calculate_performance_rating(4.9), "Below Expectations")
        self.assertEqual(calculate_performance_rating(3.0), "Below Expectations")
        self.assertEqual(calculate_performance_rating(2.9), "Inadequate")
        self.assertEqual(calculate_performance_rating(0.0), "Inadequate")

    def test_dashboard_question_wise_analytics_table(self):
        """Verify get_question_analysis_table produces complete structured rows."""
        from app import get_question_analysis_table

        history = [
            {
                "question_number": 1,
                "question": "Explain TCP handshake.",
                "score": 8.5,
                "evaluation": {
                    "score": 8.5,
                    "relevance": "Directly addressed 3-way SYN-ACK sequence.",
                    "technical_accuracy": "Accurate sequence numbers and state transitions.",
                    "clarity": "Structured step-by-step description.",
                    "completeness": "Covered handshake and SYN floods."
                }
            }
        ]

        table = get_question_analysis_table(history)
        self.assertEqual(len(table), 1)
        row = table[0]
        self.assertEqual(row["Question #"], 1)
        self.assertEqual(row["Interview Question"], "Explain TCP handshake.")
        self.assertEqual(row["Score"], 8.5)
        self.assertEqual(row["Relevance"], "Directly addressed 3-way SYN-ACK sequence.")
        self.assertEqual(row["Technical Accuracy"], "Accurate sequence numbers and state transitions.")
        self.assertEqual(row["Clarity"], "Structured step-by-step description.")
        self.assertEqual(row["Completeness"], "Covered handshake and SYN floods.")

    def test_dashboard_aggregated_feedback_strengths_and_weaknesses(self):
        """Verify aggregate_feedback counts recurring strengths/weaknesses and gathers suggestions."""
        from app import aggregate_feedback

        history = [
            {
                "question_number": 1,
                "evaluation": {
                    "strengths": ["Clear communication", "Solid foundational theory"],
                    "weaknesses": ["Missed edge cases"],
                    "suggestions": ["Mention empty input validation"]
                }
            },
            {
                "question_number": 2,
                "evaluation": {
                    "strengths": ["Clear communication", "Excellent architecture design"],
                    "weaknesses": ["Missed edge cases", "Did not discuss costs"],
                    "suggestions": ["Analyze cloud egress pricing"]
                }
            }
        ]

        feedback = aggregate_feedback(history)
        # Recurring strength: "Clear communication" appeared twice
        self.assertTrue(any("Clear communication (Observed across 2 questions)" in s for s in feedback["recurring_strengths"]))
        # Non-recurring strength: "Solid foundational theory" appeared once
        self.assertIn("Solid foundational theory", feedback["recurring_strengths"])
        # Recurring weakness: "Missed edge cases" appeared twice
        self.assertTrue(any("Missed edge cases (Observed across 2 questions)" in w for w in feedback["common_weaknesses"]))
        # Suggestions gathered
        self.assertIn("Mention empty input validation", feedback["key_suggestions"])
        self.assertIn("Analyze cloud egress pricing", feedback["key_suggestions"])

    def test_dashboard_completion_only_visibility(self):
        """Verify should_display_dashboard returns True only when session completed is True."""
        from app import should_display_dashboard

        # Active session, incomplete
        self.assertFalse(should_display_dashboard({"completed": False, "active": True}))
        # Not completed key missing
        self.assertFalse(should_display_dashboard({"active": True}))
        # Invalid inputs
        self.assertFalse(should_display_dashboard({}))
        self.assertFalse(should_display_dashboard(None))
        self.assertFalse(should_display_dashboard("completed"))
        # Official completed session
        self.assertTrue(should_display_dashboard({"completed": True, "active": True}))

    def test_dashboard_safe_handling_of_missing_or_malformed_data(self):
        """Verify all dashboard helpers handle empty lists, None values, string numbers, and malformed fields gracefully."""
        from app import calculate_session_metrics, get_question_analysis_table, aggregate_feedback

        # Empty and None inputs
        m_empty = calculate_session_metrics([])
        self.assertEqual(m_empty["total_completed"], 0)
        self.assertEqual(m_empty["average_score"], 0.0)
        self.assertIsNone(m_empty["highest_turn"])
        self.assertIsNone(m_empty["lowest_turn"])

        m_none = calculate_session_metrics(None)
        self.assertEqual(m_none["total_completed"], 0)

        # Malformed turns: string score, score inside evaluation, missing score, non-dict turn
        malformed_history = [
            "not-a-dict",
            {"question_number": 1, "question": "Q1", "score": "7.5"},
            {"question_number": 2, "question": "Q2", "score": None, "evaluation": {"score": 8.0}},
            {"question_number": 3, "question": "Q3", "score": "invalid_number"},
            {"question_number": 4, "evaluation": "not-a-dict"}
        ]
        m_malformed = calculate_session_metrics(malformed_history)
        self.assertEqual(m_malformed["total_completed"], 4)
        # scores should be [7.5, 8.0, 0.0, 0.0] -> avg = 15.5 / 4 = 3.88
        self.assertEqual(m_malformed["scores"], [7.5, 8.0, 0.0, 0.0])
        self.assertEqual(m_malformed["average_score"], 3.88)
        self.assertEqual(m_malformed["highest_score"], 8.0)
        self.assertEqual(m_malformed["lowest_score"], 0.0)

        # Malformed table generation
        table_rows = get_question_analysis_table(malformed_history)
        self.assertEqual(len(table_rows), 4)
        self.assertEqual(table_rows[0]["Score"], 7.5)

        # Malformed feedback aggregation (None, string, empty)
        bad_feedback_history = [
            {"evaluation": None},
            {"evaluation": {"strengths": "Single string strength", "weaknesses": None, "suggestions": []}},
            {"evaluation": {"strengths": [None, "", "Valid strength"], "weaknesses": ["Valid weakness"]}}
        ]
        fb = aggregate_feedback(bad_feedback_history)
        self.assertIn("Single string strength", fb["recurring_strengths"])
        self.assertIn("Valid strength", fb["recurring_strengths"])
        self.assertIn("Valid weakness", fb["common_weaknesses"])

    def test_regression_candidate_answer_widget_state_decoupling(self):
        """Regression test: verify answer widget state reset and key versioning preventing Streamlit mutation errors."""
        from unittest.mock import patch
        import streamlit as st
        from app import reset_candidate_answer_state, clear_answer, practice_followup

        class MockSessionState(dict):
            def __getattr__(self, name):
                try:
                    return self[name]
                except KeyError:
                    raise AttributeError(name)

            def __setattr__(self, name, value):
                self[name] = value

        fake_session_state = MockSessionState({
            "candidate_answer": "Draft answer to Question 1",
            "answer_widget_id": 0,
            "evaluation_result": {"score": 8.5},
            "current_question": "Original question text",
            "question_history": []
        })

        with patch.object(st, "session_state", fake_session_state):
            # 1. Test reset_candidate_answer_state clears answer and increments widget id
            reset_candidate_answer_state()
            self.assertEqual(fake_session_state["candidate_answer"], "")
            self.assertEqual(fake_session_state["answer_widget_id"], 1)

            # The new widget key must be distinct from the old one
            old_key = "candidate_answer_widget_0"
            new_key = f"candidate_answer_widget_{fake_session_state['answer_widget_id']}"
            self.assertNotEqual(old_key, new_key)
            self.assertEqual(new_key, "candidate_answer_widget_1")

            # 2. Test clear_answer callback
            fake_session_state["candidate_answer"] = "Draft answer to be cleared"
            fake_session_state["evaluation_result"] = {"score": 5.0}
            clear_answer()
            self.assertEqual(fake_session_state["candidate_answer"], "")
            self.assertEqual(fake_session_state["answer_widget_id"], 2)
            self.assertIsNone(fake_session_state["evaluation_result"])

            # 3. Test practice_followup callback
            fake_session_state["candidate_answer"] = "Another answer"
            practice_followup("Follow-up question text")
            self.assertEqual(fake_session_state["current_question"], "Follow-up question text")
            self.assertEqual(fake_session_state["candidate_answer"], "")
            self.assertEqual(fake_session_state["answer_widget_id"], 3)
            self.assertIn("Original question text", fake_session_state["question_history"])

    def test_smart_answer_correction_schema_fields_and_defaults(self):
        """Verify AnswerEvaluation schema includes smart correction fields with safe defaults."""
        from app import AnswerEvaluation

        # Legacy payload without new smart correction fields
        legacy_data = {
            "score": 8.0,
            "relevance": "Good",
            "technical_accuracy": "Accurate",
            "clarity": "Clear",
            "completeness": "Complete",
            "strengths": ["Strong points"],
            "weaknesses": ["Minor gaps"],
            "suggestions": ["Refine terminology"],
            "follow_up_question": "How to scale?"
        }
        eval_obj = AnswerEvaluation(**legacy_data)
        self.assertEqual(eval_obj.classification, "Partially Correct")
        self.assertEqual(eval_obj.correct_concepts, [])
        self.assertEqual(eval_obj.incorrect_statements, [])
        self.assertEqual(eval_obj.missing_concepts, [])
        self.assertEqual(eval_obj.mistake_explanations, [])
        self.assertEqual(eval_obj.correct_explanation, "")
        self.assertEqual(eval_obj.ideal_answer, "")

    def test_smart_answer_correction_correct_classification(self):
        """Verify Smart Answer Correction for a Correct candidate answer."""
        from app import AnswerEvaluation

        data = {
            "score": 9.2,
            "classification": "Correct",
            "relevance": "Directly and thoroughly addresses scalable URL shortening design.",
            "technical_accuracy": "Factually sound use of Snowflake IDs, Base62 encoding, and Redis caching.",
            "clarity": "Structured and logically sequenced architecture breakdown.",
            "completeness": "Covers hashing, caching, hot keys, rate limiting, and analytics queues.",
            "correct_concepts": [
                "Snowflake ID generation avoids distributed hash collisions",
                "Base62 encoding yields compact 7-character URLs",
                "Redis cache-aside mitigates read latency for hot keys"
            ],
            "incorrect_statements": [],
            "mistake_explanations": [],
            "missing_concepts": [
                "Detailed cross-region active-active database replication topology"
            ],
            "correct_explanation": "The candidate provided a robust distributed URL shortener design using 64-bit distributed IDs, Base62 encoding, and Redis caching with appropriate TTL and request coalescing.",
            "ideal_answer": "An ideal URL shortener uses Snowflake IDs base62-encoded into 7 characters, stored in DynamoDB/Cassandra with Redis cache-aside, write-through CDN edge caching, and token-bucket rate limiting.",
            "strengths": ["Excellent distributed systems architecture", "Thoughtful hot key handling"],
            "weaknesses": ["Could expand on multi-region sync latency"],
            "suggestions": ["Mention active-active multi-datacenter replication"],
            "follow_up_question": "How would you handle cache penetration if non-existent keys are requested at scale?"
        }
        eval_obj = AnswerEvaluation(**data)
        self.assertEqual(eval_obj.classification, "Correct")
        self.assertGreaterEqual(eval_obj.score, 8.5)
        self.assertGreater(len(eval_obj.correct_concepts), 0)
        self.assertEqual(len(eval_obj.incorrect_statements), 0)
        self.assertTrue(len(eval_obj.correct_explanation) > 0)
        self.assertTrue(len(eval_obj.ideal_answer) > 0)

    def test_smart_answer_correction_partially_correct_classification(self):
        """Verify Smart Answer Correction for a Partially Correct candidate answer."""
        from app import AnswerEvaluation

        data = {
            "score": 6.5,
            "classification": "Partially Correct",
            "relevance": "Addresses the question but lacks technical depth and edge-case handling.",
            "technical_accuracy": "Core definitions are sound, but synchronization mechanisms are omitted.",
            "clarity": "Informal tone with loose structure.",
            "completeness": "Misses distributed synchronization, race conditions, and error codes.",
            "correct_concepts": [
                "Centralized Redis storage for token buckets",
                "Per-user rate limit counter structure"
            ],
            "incorrect_statements": [
                "Race conditions can simply be ignored because Redis is single-threaded"
            ],
            "mistake_explanations": [
                "Redis single-threading protects single commands, but multi-step check-then-set logic without Lua scripts or atomic transactions still causes race conditions"
            ],
            "missing_concepts": [
                "Atomic Redis Lua scripts or MULTI/EXEC transactions",
                "HTTP 429 Too Many Requests response status code"
            ],
            "correct_explanation": "While Redis executes individual commands sequentially on a single thread, non-atomic read-modify-write sequences are vulnerable to concurrent interleaving unless executed via atomic Lua scripts.",
            "ideal_answer": "Use Redis with Lua script for atomic token replenishment and decrement. Reject requests exceeding quota with HTTP 429 and Retry-After header.",
            "strengths": ["Understands basic token bucket concepts"],
            "weaknesses": ["Dangerous misconception about Redis concurrency guarantees"],
            "suggestions": ["Study atomic Lua scripts in Redis to prevent concurrency bugs"],
            "follow_up_question": "Why is a Lua script atomic in Redis compared to separate GET and DECR commands?"
        }
        eval_obj = AnswerEvaluation(**data)
        self.assertEqual(eval_obj.classification, "Partially Correct")
        self.assertTrue(5.0 <= eval_obj.score < 8.0)
        self.assertGreater(len(eval_obj.correct_concepts), 0)
        self.assertGreater(len(eval_obj.missing_concepts), 0)
        self.assertEqual(len(eval_obj.incorrect_statements), len(eval_obj.mistake_explanations))

    def test_smart_answer_correction_incorrect_classification(self):
        """Verify Smart Answer Correction for an Incorrect candidate answer."""
        from app import AnswerEvaluation

        data = {
            "score": 2.5,
            "classification": "Incorrect",
            "relevance": "Directly attempts question but arrives at fundamentally contradictory conclusions.",
            "technical_accuracy": "Incorrectly claims mutex locks achieve lock-free concurrency.",
            "clarity": "Coherent phrasing but conceptually confused.",
            "completeness": "Fails to explain real lock-free memory models, CAS operations, or memory barriers.",
            "correct_concepts": [
                "Recognizes that concurrent queues need thread-safe synchronization"
            ],
            "incorrect_statements": [
                "A lock-free queue is implemented by wrapping operations in a mutex lock so no threads block"
            ],
            "mistake_explanations": [
                "A mutex lock explicitly suspends and blocks waiting threads in the OS scheduler; lock-free algorithms by definition forbid locks and rely on atomic hardware primitives like Compare-And-Swap (CAS)"
            ],
            "missing_concepts": [
                "Compare-And-Swap (CAS) atomic hardware instructions",
                "ABA problem mitigation via tagged pointers or hazard pointers",
                "Memory order guarantees and memory barriers"
            ],
            "correct_explanation": "Lock-free programming guarantees system-wide progress without operating system mutexes by using atomic hardware primitives such as CAS (std::atomic::compare_exchange_weak). Using a mutex is the exact opposite of lock-free.",
            "ideal_answer": "A lock-free queue (e.g. Michael-Scott queue) maintains head and tail atomic pointers, advancing nodes using atomic CAS operations and handling the ABA problem with tagged pointers.",
            "strengths": ["Recognizes the importance of concurrency in queues"],
            "weaknesses": ["Confuses mutex-locked synchronization with lock-free synchronization"],
            "suggestions": ["Review the formal computer science definition of non-blocking and lock-free algorithms"],
            "follow_up_question": "How does the ABA problem occur in lock-free CAS linked lists?"
        }
        eval_obj = AnswerEvaluation(**data)
        self.assertEqual(eval_obj.classification, "Incorrect")
        self.assertLessEqual(eval_obj.score, 4.0)
        self.assertGreater(len(eval_obj.incorrect_statements), 0)
        self.assertEqual(len(eval_obj.incorrect_statements), len(eval_obj.mistake_explanations))
        self.assertIn("lock-free", eval_obj.correct_explanation.lower())

    def test_smart_answer_correction_off_topic_classification(self):
        """Verify Smart Answer Correction strictly enforces Off-topic classification and score cap."""
        from app import AnswerEvaluation

        data = {
            "score": 1.0,
            "classification": "Off-topic",
            "relevance": "Completely off-topic. Discusses hash table bucket array concepts when asked about distributed rate limiting.",
            "technical_accuracy": "Hash map definition is accurate for hash maps, but factually non-responsive to distributed systems.",
            "clarity": "Articulate and grammatically fluent text, but irrelevant.",
            "completeness": "Zero coverage of rate limiting algorithms, synchronization, or distributed caching.",
            "correct_concepts": [
                "Accurate general description of hash map bucket arrays and chaining"
            ],
            "incorrect_statements": [
                "Candidate presented a hash map definition as an answer to a distributed rate limiter prompt"
            ],
            "mistake_explanations": [
                "A hash map is an in-memory data structure for key-value lookups, not an architecture for distributed rate limiting across multi-region networks"
            ],
            "missing_concepts": [
                "Token Bucket, Leaky Bucket, or Sliding Window algorithms",
                "Distributed in-memory storage (e.g. Redis)",
                "Race condition mitigation and cross-region synchronization",
                "HTTP 429 response handling"
            ],
            "correct_explanation": "The submitted response defines an in-memory hash map data structure, which does not address how to design a distributed rate limiter for 100k requests/second across multiple cloud regions.",
            "ideal_answer": "A distributed rate limiter uses centralized Redis token buckets updated via atomic Lua scripts to prevent race conditions across server nodes, shedding load with HTTP 429.",
            "strengths": ["Grammatically articulate text"],
            "weaknesses": ["Completely off-topic response that ignores the prompt"],
            "suggestions": ["Carefully read the prompt and focus on distributed rate limiting rather than introductory data structures"],
            "follow_up_question": "Can you explain the Token Bucket algorithm used in distributed rate limiters?"
        }
        eval_obj = AnswerEvaluation(**data)
        self.assertEqual(eval_obj.classification, "Off-topic")
        self.assertLessEqual(eval_obj.score, 2.0)
        self.assertIn("off-topic", eval_obj.relevance.lower())
        self.assertIn("does not address", eval_obj.correct_explanation.lower())
        self.assertTrue(len(eval_obj.ideal_answer) > 0)

    def test_personality_selection_and_configurations(self):
        """Verify interviewer personality configurations, properties, and fallback logic."""
        from app import INTERVIEWER_PERSONALITIES, DEFAULT_PERSONALITY, get_personality_details

        expected_keys = ["Friendly Mentor", "Strict Technical Interviewer", "FAANG-Style Interviewer"]
        for key in expected_keys:
            self.assertIn(key, INTERVIEWER_PERSONALITIES)
            details = INTERVIEWER_PERSONALITIES[key]
            self.assertEqual(details["title"], key)
            self.assertTrue(len(details["badge"]) > 0)
            self.assertTrue(len(details["description"]) > 0)
            self.assertTrue(len(details["question_guidance"]) > 0)
            self.assertTrue(len(details["evaluation_guidance"]) > 0)

        # Test fallback
        self.assertEqual(get_personality_details("Friendly Mentor")["title"], "Friendly Mentor")
        self.assertEqual(get_personality_details("Strict Technical Interviewer")["title"], "Strict Technical Interviewer")
        self.assertEqual(get_personality_details("FAANG-Style Interviewer")["title"], "FAANG-Style Interviewer")
        self.assertEqual(get_personality_details(None)["title"], DEFAULT_PERSONALITY)
        self.assertEqual(get_personality_details("NonExistentPersonality")["title"], DEFAULT_PERSONALITY)

    def test_question_prompt_personality_adaptation(self):
        """Verify question prompt dynamically adapts tone and style to selected personality."""
        from app import get_question_prompt

        # 1. Friendly Mentor
        prompt_mentor = get_question_prompt(
            role="Software Engineer",
            difficulty="Medium",
            interview_type="Technical",
            interviewer_personality="Friendly Mentor"
        )
        self.assertIn("Friendly Mentor", prompt_mentor)
        self.assertIn("encouraging", prompt_mentor.lower())
        self.assertIn("Software Engineer", prompt_mentor)

        # 2. Strict Technical Interviewer
        prompt_strict = get_question_prompt(
            role="Data Scientist",
            difficulty="Hard",
            interview_type="Technical",
            interviewer_personality="Strict Technical Interviewer"
        )
        self.assertIn("Strict Technical Interviewer", prompt_strict)
        self.assertIn("demanding", prompt_strict.lower())
        self.assertIn("Data Scientist", prompt_strict)

        # 3. FAANG-Style Interviewer
        prompt_faang = get_question_prompt(
            role="Software Engineer",
            difficulty="Hard",
            interview_type="Technical",
            question_number=8,
            previous_question="What is LRU cache?",
            interviewer_personality="FAANG-Style Interviewer"
        )
        self.assertIn("FAANG-Style Interviewer", prompt_faang)
        self.assertIn("faang", prompt_faang.lower())
        self.assertIn("Stage 2 of 3", prompt_faang)
        self.assertIn("IMPORTANT REQUIREMENT:", prompt_faang)
        self.assertIn("What is LRU cache?", prompt_faang)

    def test_evaluation_prompt_personality_followup_adaptation(self):
        """Verify evaluation prompt incorporates personality guidance for tone and follow-ups without altering scoring."""
        from app import get_evaluation_prompt

        # Without personality (backward compatibility)
        prompt_clean = get_evaluation_prompt(
            role="Software Engineer",
            difficulty="Medium",
            interview_type="Technical",
            question="What is a binary search tree?",
            candidate_answer="A tree where left is smaller and right is larger."
        )
        self.assertNotIn("Interviewer Personality & Tone Directive", prompt_clean)
        self.assertIn("Scoring Scale (0.0 to 10.0)", prompt_clean)

        # With Friendly Mentor
        prompt_mentor = get_evaluation_prompt(
            role="Software Engineer",
            difficulty="Medium",
            interview_type="Technical",
            question="What is a binary search tree?",
            candidate_answer="A tree where left is smaller and right is larger.",
            interviewer_personality="Friendly Mentor"
        )
        self.assertIn("Interviewer Personality & Tone Directive", prompt_mentor)
        self.assertIn("Friendly Mentor", prompt_mentor)
        self.assertIn("encouraging", prompt_mentor.lower())
        self.assertIn("Scoring Scale (0.0 to 10.0)", prompt_mentor)

        # With Strict Technical Interviewer
        prompt_strict = get_evaluation_prompt(
            role="Software Engineer",
            difficulty="Hard",
            interview_type="Technical",
            question="Explain CAP theorem.",
            candidate_answer="You can have consistency and availability.",
            interviewer_personality="Strict Technical Interviewer"
        )
        self.assertIn("Strict Technical Interviewer", prompt_strict)
        self.assertIn("challenge", prompt_strict.lower())

        # With FAANG-Style Interviewer
        prompt_faang = get_evaluation_prompt(
            role="Software Engineer",
            difficulty="Hard",
            interview_type="Technical",
            question="Design distributed cache.",
            candidate_answer="Use Redis with consistent hashing.",
            interviewer_personality="FAANG-Style Interviewer"
        )
        self.assertIn("FAANG-Style Interviewer", prompt_faang)
        self.assertIn("trade-offs", prompt_faang.lower())

    def test_pressure_mode_timer_configuration(self):
        """Verify pressure mode initialization and timer duration formatting."""
        from app import init_pressure_mode, format_timer_display

        pm_120 = init_pressure_mode(enabled=True, duration=120)
        self.assertTrue(pm_120["enabled"])
        self.assertEqual(pm_120["duration"], 120)
        self.assertFalse(pm_120["expired"])

        pm_60 = init_pressure_mode(enabled=True, duration=60)
        self.assertEqual(pm_60["duration"], 60)

        pm_180 = init_pressure_mode(enabled=True, duration=180)
        self.assertEqual(pm_180["duration"], 180)

        # Invalid duration falls back to 120 default
        pm_invalid = init_pressure_mode(enabled=True, duration=999)
        self.assertEqual(pm_invalid["duration"], 120)

        # Time formatting
        self.assertEqual(format_timer_display(120), "02:00")
        self.assertEqual(format_timer_display(60), "01:00")
        self.assertEqual(format_timer_display(65), "01:05")
        self.assertEqual(format_timer_display(15), "00:15")
        self.assertEqual(format_timer_display(0), "00:00")
        self.assertEqual(format_timer_display(-5), "00:00")

    def test_pressure_mode_timer_expiry_and_remaining(self):
        """Verify remaining time calculation and expiry detection."""
        from app import get_timer_remaining, is_timer_expired

        start_t = 1000.0
        duration = 120

        # At start
        self.assertEqual(get_timer_remaining(start_t, duration, current_time=1000.0), 120)
        self.assertFalse(is_timer_expired(start_t, duration, current_time=1000.0))

        # Midway
        self.assertEqual(get_timer_remaining(start_t, duration, current_time=1050.0), 70)
        self.assertFalse(is_timer_expired(start_t, duration, current_time=1050.0))

        # 1 second before expiry
        self.assertEqual(get_timer_remaining(start_t, duration, current_time=1119.0), 1)
        self.assertFalse(is_timer_expired(start_t, duration, current_time=1119.0))

        # Exactly expired
        self.assertEqual(get_timer_remaining(start_t, duration, current_time=1120.0), 0)
        self.assertTrue(is_timer_expired(start_t, duration, current_time=1120.0))

        # Over-time (never negative)
        self.assertEqual(get_timer_remaining(start_t, duration, current_time=1150.0), 0)
        self.assertTrue(is_timer_expired(start_t, duration, current_time=1150.0))

    def test_pressure_mode_turn_recording_and_no_penalty(self):
        """Verify turn recording preserves personality, pressure mode metadata, and preserves candidate answer text."""
        from app import init_interview_session, record_session_turn, can_advance_session

        session = init_interview_session(total_questions=15)
        eval_dict = {
            "score": 8.0,
            "classification": "Correct",
            "relevance": "Direct answer",
            "technical_accuracy": "Sound",
            "clarity": "Clear",
            "completeness": "Complete",
            "correct_concepts": ["Valid point"],
            "incorrect_statements": [],
            "mistake_explanations": [],
            "missing_concepts": [],
            "correct_explanation": "Explanation",
            "ideal_answer": "Model answer",
            "strengths": ["Strong explanation"],
            "weaknesses": [],
            "suggestions": [],
            "follow_up_question": "Follow-up question?"
        }

        turn = record_session_turn(
            session=session,
            question="What is an index in PostgreSQL?",
            answer="A B-tree data structure that accelerates lookups at the expense of write overhead.",
            evaluation=eval_dict,
            role="Software Engineer",
            difficulty="Medium",
            interview_type="Technical",
            personality="Strict Technical Interviewer",
            pressure_mode=True
        )

        self.assertEqual(turn["personality"], "Strict Technical Interviewer")
        self.assertTrue(turn["pressure_mode"])
        self.assertEqual(turn["answer"], "A B-tree data structure that accelerates lookups at the expense of write overhead.")
        self.assertEqual(turn["score"], 8.0)

        # Advancing session requires non-empty answer and valid evaluation
        self.assertTrue(can_advance_session(turn["answer"], turn["evaluation"]))
        # Blank answer cannot advance (prevents accidental skipping)
        self.assertFalse(can_advance_session("", turn["evaluation"]))
        self.assertFalse(can_advance_session("   ", turn["evaluation"]))


if __name__ == "__main__":
    unittest.main()
