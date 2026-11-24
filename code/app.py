import os
import json
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Pydantic schema for structured evaluation
class AnswerEvaluation(BaseModel):
    score: float = Field(description="Overall evaluation score between 0.0 and 10.0")
    relevance: str = Field(description="Evaluation of relevance: did the candidate directly address the question?")
    technical_accuracy: str = Field(description="Evaluation of technical accuracy: is the answer factually and conceptually correct?")
    clarity: str = Field(description="Evaluation of clarity: is the answer coherent, structured, and easy to understand?")
    completeness: str = Field(description="Evaluation of completeness: did the candidate cover key aspects, depth, and trade-offs?")
    strengths: list[str] = Field(description="2 to 4 key strengths demonstrated in the response")
    weaknesses: list[str] = Field(description="1 to 4 areas where the answer was lacking, incomplete, or inaccurate")
    suggestions: list[str] = Field(description="2 to 4 specific, actionable improvement suggestions")
    follow_up_question: str = Field(description="One relevant follow-up interview question based on the candidate's answer")


# Callback functions for clean state transitions without widget conflicts
def clear_answer():
    st.session_state.candidate_answer = ""
    st.session_state.evaluation_result = None


def practice_followup(question_text):
    if st.session_state.get("current_question"):
        prev = st.session_state.current_question.strip()
        if prev and prev not in st.session_state.question_history:
            st.session_state.question_history.append(prev)
    st.session_state.current_question = question_text
    st.session_state.candidate_answer = ""
    st.session_state.evaluation_result = None


def generate_interview_question(
    client: genai.Client,
    role: str,
    difficulty: str,
    interview_type: str,
    previous_question: str = "",
    history: list[str] | None = None
) -> str:
    """Generate a fresh interview question using gemini-3.5-flash-lite, avoiding previous questions."""
    prompt = f"""Act as a professional interviewer.

Generate ONE interview question for:
Job Role: {role}
Difficulty: {difficulty}
Interview Type: {interview_type}

The question must be relevant, technically sound, and appropriate for the selected difficulty level."""

    if previous_question and previous_question.strip():
        prompt += f"""

IMPORTANT REQUIREMENT:
The previous question was:
"{previous_question.strip()}"

Do NOT repeat, rephrase, or ask about the same topic or concept as the previous question.
Generate a completely DIFFERENT interview question testing a distinct topic, concept, or scenario."""

    if history:
        recent_history = [q.strip() for q in history[-5:] if q.strip() and q.strip() != previous_question.strip()]
        if recent_history:
            formatted_history = "\n".join(f"- {q}" for q in recent_history)
            prompt += f"""

Also avoid covering the same concepts as these previously asked questions:
{formatted_history}"""

    prompt += "\n\nReturn only the interview question text without any greeting, preamble, or metadata."

    config = types.GenerateContentConfig(
        temperature=0.85
    )

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=config
    )
    return response.text.strip() if response and response.text else ""


def get_evaluation_prompt(role: str, difficulty: str, interview_type: str, question: str, candidate_answer: str) -> str:
    """Load and format the final evaluation prompt template from prompts/final/prompt.txt."""
    prompt_file = os.path.join(os.path.dirname(__file__), "prompts", "final", "prompt.txt")
    if os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            template = f.read()
    else:
        template = """Act as an expert, hiring-manager-level interviewer conducting a rigorous interview evaluation for a {role} position.

Interview Context:
- Target Job Role: {role}
- Difficulty Level: {difficulty}
- Interview Type: {interview_type}

Interview Question:
"{question}"

Candidate's Answer:
"{candidate_answer}"

Evaluation Instructions:
Thoroughly assess the candidate's answer across the four core dimensions using evidence-based observations:
1. Relevance: Did the answer address the specific question directly and appropriately?
2. Technical Accuracy: Is the content conceptually, mathematically, and architecturally sound for the role and difficulty level? Cite specific correct or incorrect assertions from the candidate's answer.
3. Clarity: Is the explanation articulate, well-structured, professional, and logically sequenced?
4. Completeness: Were key elements, depth, practical examples, failure modes, and trade-offs sufficiently covered without major omissions?

Strict Guardrails & Scoring Calibration:
- Off-Topic / Evasive Responses: If the answer does not address the question asked (e.g., discussing hash maps or general syntax when asked about distributed systems, or discussing unrelated concepts), assign a maximum score between 0.0 and 2.0 regardless of how well-written or fluent the text is.
- Scoring Scale (0.0 to 10.0):
  * 9.0 - 10.0: Outstanding / Senior-ready. Precise, comprehensive, technically rigorous, covers trade-offs.
  * 7.5 - 8.9: Strong. Accurate and relevant with minor omissions or slight lack of depth.
  * 5.5 - 7.4: Fair / Average. Partially correct; misses critical concepts, depth, or practical edge cases.
  * 3.5 - 5.4: Below Expectations. Significant inaccuracies, shallow explanations, or noticeable confusion.
  * 0.0 - 3.4: Inadequate / Off-Topic. Irrelevant, factually incorrect, or non-responsive.

Required Output Structure (JSON Schema):
- score: Overall score out of 10.0 (rounded to one decimal place)
- relevance: Concise analysis evaluating direct relevance and adherence to prompt (1-3 sentences)
- technical_accuracy: Evidence-based analysis evaluating technical correctness with specific references to candidate statements (1-3 sentences)
- clarity: Concise analysis of structural clarity, communication tone, and vocabulary (1-3 sentences)
- completeness: Concise analysis of depth, coverage of trade-offs, and missing concepts (1-3 sentences)
- strengths: 2 to 4 concrete bullet points highlighting specific strengths demonstrated in the response
- weaknesses: 1 to 4 concrete bullet points identifying specific technical gaps, inaccuracies, or omissions
- suggestions: 2 to 4 actionable, high-impact suggestions for how the candidate can elevate this answer
- follow_up_question: Exactly ONE thoughtful follow-up interview question that probes deeper into technical boundaries, edge cases, or trade-offs based on the candidate's answer
"""
    return template.format(
        role=role,
        difficulty=difficulty,
        interview_type=interview_type,
        question=question,
        candidate_answer=candidate_answer
    )


def main():
    # Load API key from .env
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    st.set_page_config(
        page_title="AI Mock Interview Coach",
        page_icon="🎯",
        layout="wide"
    )

    # Initialize session state variables
    if "current_question" not in st.session_state:
        st.session_state.current_question = ""
    if "question_history" not in st.session_state:
        st.session_state.question_history = []
    if "candidate_answer" not in st.session_state:
        st.session_state.candidate_answer = ""
    if "evaluation_result" not in st.session_state:
        st.session_state.evaluation_result = None
    if "evaluated_role" not in st.session_state:
        st.session_state.evaluated_role = "Software Engineer"
    if "evaluated_difficulty" not in st.session_state:
        st.session_state.evaluated_difficulty = "Medium"
    if "evaluated_type" not in st.session_state:
        st.session_state.evaluated_type = "Technical"

    # Header
    st.title("🎯 AI Mock Interview Coach")
    st.write("Practice interviews with AI-powered questions and real-time structured feedback.")

    # Validate API Key
    if not api_key:
        st.error("⚠️ Gemini API key not found. Check your .env file.")
        st.stop()

    # Connect to Gemini client safely
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize Gemini client: {e}")
        st.stop()

    st.success("Gemini AI connected successfully!")

    st.divider()

    # Configuration Section
    st.subheader("Configure Your Interview")

    col1, col2, col3 = st.columns(3)
    with col1:
        role = st.selectbox(
            "Select your target job role",
            ["Data Scientist", "Data Analyst", "Software Engineer"]
        )
    with col2:
        difficulty = st.selectbox(
            "Select difficulty",
            ["Easy", "Medium", "Hard"]
        )
    with col3:
        interview_type = st.selectbox(
            "Select interview type",
            ["Technical", "HR", "Mixed"]
        )

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        generate_clicked = st.button(
            "Generate Interview Question",
            type="primary" if not st.session_state.current_question else "secondary",
            use_container_width=True
        )
    with col_btn2:
        regenerate_clicked = st.button(
            "🔄 Regenerate Question" if st.session_state.current_question else "🔄 Generate Another Question",
            use_container_width=True,
            disabled=not bool(st.session_state.current_question),
            help="Generate a fresh, distinct question testing a different topic."
        )

    # Handle Question Generation & Regeneration
    if generate_clicked or regenerate_clicked:
        with st.spinner("Gemini is preparing your interview question..."):
            try:
                prev_q = st.session_state.get("current_question", "")
                history = st.session_state.get("question_history", [])

                new_question = generate_interview_question(
                    client=client,
                    role=role,
                    difficulty=difficulty,
                    interview_type=interview_type,
                    previous_question=prev_q,
                    history=history
                )

                if new_question:
                    # Save previous question into history
                    if prev_q and prev_q not in history:
                        st.session_state.question_history.append(prev_q)

                    st.session_state.current_question = new_question
                    st.session_state.candidate_answer = ""
                    st.session_state.evaluation_result = None
                    st.session_state.evaluated_role = role
                    st.session_state.evaluated_difficulty = difficulty
                    st.session_state.evaluated_type = interview_type
                    st.rerun()
                else:
                    st.error("No question was returned by the model. Please try again.")

            except Exception as e:
                st.error(f"Gemini error generating question: {e}")

    # Display Question and Answer Input if question exists
    if st.session_state.current_question:
        st.divider()
        st.subheader("📝 Your Interview Question")

        # Clear Question Card
        with st.container(border=True):
            col_meta, col_card_btn = st.columns([3, 1])
            with col_meta:
                st.caption(
                    f"🎯 **Role:** {st.session_state.evaluated_role} | "
                    f"⚡ **Difficulty:** {st.session_state.evaluated_difficulty} | "
                    f"📋 **Type:** {st.session_state.evaluated_type}"
                )
            with col_card_btn:
                if st.button("🔄 Regenerate", key="btn_card_regenerate", help="Generate a different question for this role and difficulty.", use_container_width=True):
                    with st.spinner("Gemini is preparing a different question..."):
                        try:
                            prev_q = st.session_state.get("current_question", "")
                            history = st.session_state.get("question_history", [])

                            new_question = generate_interview_question(
                                client=client,
                                role=st.session_state.evaluated_role,
                                difficulty=st.session_state.evaluated_difficulty,
                                interview_type=st.session_state.evaluated_type,
                                previous_question=prev_q,
                                history=history
                            )

                            if new_question:
                                if prev_q and prev_q not in history:
                                    st.session_state.question_history.append(prev_q)
                                st.session_state.current_question = new_question
                                st.session_state.candidate_answer = ""
                                st.session_state.evaluation_result = None
                                st.rerun()
                            else:
                                st.error("No question was returned. Please try again.")
                        except Exception as e:
                            st.error(f"Gemini error: {e}")

            st.markdown(f"### {st.session_state.current_question}")

        st.write("")
        st.subheader("✍️ Your Answer")

        # Candidate Answer Area
        st.text_area(
            "Type your answer:",
            height=180,
            placeholder="Type your structured answer here... Explain your thought process, technical reasoning, examples, and trade-offs.",
            key="candidate_answer"
        )

        col_eval_btn, col_reset_btn = st.columns([3, 1])

        with col_eval_btn:
            evaluate_clicked = st.button("🎯 Evaluate My Answer", type="primary", use_container_width=True)

        with col_reset_btn:
            st.button("🔄 Clear Answer", use_container_width=True, on_click=clear_answer)

        # Evaluation Trigger
        if evaluate_clicked:
            user_answer = st.session_state.get("candidate_answer", "").strip()
            if not user_answer:
                st.warning("⚠️ Please enter your answer before requesting an evaluation.")
            else:
                with st.spinner("Gemini is evaluating your response against professional benchmarks..."):
                    try:
                        eval_prompt = get_evaluation_prompt(
                            role=st.session_state.evaluated_role,
                            difficulty=st.session_state.evaluated_difficulty,
                            interview_type=st.session_state.evaluated_type,
                            question=st.session_state.current_question,
                            candidate_answer=user_answer
                        )

                        config = types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=AnswerEvaluation
                        )

                        eval_response = client.models.generate_content(
                            model="gemini-3.5-flash-lite",
                            contents=eval_prompt,
                            config=config
                        )

                        # Parse output safely
                        raw_text = eval_response.text.strip() if eval_response.text else "{}"
                        if raw_text.startswith("```"):
                            lines = raw_text.splitlines()
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].startswith("```"):
                                lines = lines[:-1]
                            raw_text = "\n".join(lines).strip()

                        eval_data = json.loads(raw_text)
                        st.session_state.evaluation_result = eval_data

                    except json.JSONDecodeError as jde:
                        st.error(f"Failed to parse evaluation response: {jde}")
                    except Exception as e:
                        st.error(f"Gemini evaluation error: {e}")

    # Render Evaluation Results
    if st.session_state.get("evaluation_result"):
        eval_result = st.session_state.evaluation_result
        st.divider()
        st.subheader("📊 Evaluation & Feedback")

        # Score Overview
        raw_score = eval_result.get("score", 0.0)
        try:
            score_val = float(raw_score)
        except Exception:
            score_val = 0.0

        score_col, status_col = st.columns([1, 2])
        with score_col:
            st.metric(label="Overall Score", value=f"{score_val:.1f} / 10.0")

        with status_col:
            progress_val = min(max(score_val / 10.0, 0.0), 1.0)
            st.write("**Performance Level:**")
            st.progress(progress_val)
            if score_val >= 8.5:
                st.success("🌟 **Excellent** — Strong, comprehensive, and interview-ready response!")
            elif score_val >= 7.0:
                st.info("👍 **Good** — Solid foundation with a few minor opportunities for improvement.")
            elif score_val >= 5.0:
                st.warning("⚠️ **Average** — Partial coverage; requires more technical depth and structure.")
            else:
                st.warning("🔻 **Needs Improvement** — Substantial gaps or inaccuracies to address.")

        st.write("")

        # 4 Core Dimensions
        st.markdown("#### 🔍 Core Evaluation Criteria")
        dim1, dim2 = st.columns(2)
        with dim1:
            with st.container(border=True):
                st.markdown("##### 🎯 Relevance")
                st.write(eval_result.get("relevance", "N/A"))
            with st.container(border=True):
                st.markdown("##### 💡 Clarity & Structure")
                st.write(eval_result.get("clarity", "N/A"))
        with dim2:
            with st.container(border=True):
                st.markdown("##### ⚙️ Technical Accuracy")
                st.write(eval_result.get("technical_accuracy", "N/A"))
            with st.container(border=True):
                st.markdown("##### 📦 Completeness & Depth")
                st.write(eval_result.get("completeness", "N/A"))

        st.write("")

        # Strengths and Weaknesses
        col_str, col_weak = st.columns(2)
        with col_str:
            st.markdown("#### 🌟 Key Strengths")
            strengths = eval_result.get("strengths", [])
            if isinstance(strengths, list) and strengths:
                for item in strengths:
                    st.markdown(f"- ✅ {item}")
            else:
                st.write("No specific strengths recorded.")

        with col_weak:
            st.markdown("#### ⚠️ Areas for Improvement")
            weaknesses = eval_result.get("weaknesses", [])
            if isinstance(weaknesses, list) and weaknesses:
                for item in weaknesses:
                    st.markdown(f"- 🔸 {item}")
            else:
                st.write("No significant weaknesses identified.")

        st.write("")

        # Suggestions
        st.markdown("#### 🚀 Actionable Improvement Suggestions")
        suggestions = eval_result.get("suggestions", [])
        if isinstance(suggestions, list) and suggestions:
            for item in suggestions:
                st.markdown(f"- 💡 {item}")
        else:
            st.write("Continue practicing with similar questions.")

        st.write("")

        # Follow-up Question
        follow_up = eval_result.get("follow_up_question")
        if follow_up:
            st.markdown("#### 🔄 Recommended Follow-Up Question")
            with st.container(border=True):
                st.markdown(f"**Interviewer Follow-Up:**\n\n> *\"{follow_up}\"*")
                st.caption("Probe deeper to test your conceptual boundaries.")
                st.button(
                    "👉 Practice This Follow-up Question",
                    key="btn_practice_followup",
                    on_click=practice_followup,
                    args=(follow_up,)
                )

    elif not st.session_state.get("current_question"):
        st.info("💡 Select your interview preferences above and click **'Generate Interview Question'** to begin your mock interview!")


if __name__ == "__main__":
    main()
