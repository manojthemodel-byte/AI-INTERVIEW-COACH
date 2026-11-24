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

if __name__ == "__main__":
    unittest.main()
