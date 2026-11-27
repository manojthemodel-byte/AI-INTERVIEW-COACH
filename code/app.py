import os
import json
import time
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Interviewer Personalities configuration
INTERVIEWER_PERSONALITIES = {
    "Friendly Mentor": {
        "title": "Friendly Mentor",
        "badge": "🌱 Friendly Mentor",
        "description": "Encouraging, supportive, and patient. Provides constructive feedback to help you build confidence.",
        "question_guidance": (
            "Adopt an encouraging, approachable tone. Frame the question around real-world application, practical learning, "
            "and foundational problem-solving, welcoming structured reasoning."
        ),
        "evaluation_guidance": (
            "Adopt an encouraging, patient, and constructive tone. Acknowledge valid intuitions, frame weaknesses as growth areas, "
            "and craft a supportive follow-up question that gently guides the candidate to explore related concepts or expand on their ideas."
        )
    },
    "Strict Technical Interviewer": {
        "title": "Strict Technical Interviewer",
        "badge": "⚖️ Strict Technical Interviewer",
        "description": "Professional, rigorous, and demanding. Challenges vague answers, requires technical justification, and rejects hand-waving.",
        "question_guidance": (
            "Adopt a direct, demanding, and uncompromising tone. Ask a precise, rigorous technical question that leaves no room "
            "for superficial generalizations and requires deep mechanical understanding and architectural justification."
        ),
        "evaluation_guidance": (
            "Adopt a demanding, no-nonsense, and professional tone. Directly challenge hand-waving, unverified claims, or fuzzy explanations. "
            "Craft a probing follow-up question that aggressively challenges candidate assumptions and demands formal technical justification."
        )
    },
    "FAANG-Style Interviewer": {
        "title": "FAANG-Style Interviewer",
        "badge": "🚀 FAANG-Style Interviewer",
        "description": "Big-tech caliber. Focuses on system scalability, algorithmic optimization, distributed trade-offs, and failure edge cases.",
        "question_guidance": (
            "Adopt a high-bar big-tech (FAANG) engineering style. Focus on large-scale distributed architecture, algorithmic efficiency, "
            "high-concurrency bottlenecks, and measurable technical trade-offs under production constraints."
        ),
        "evaluation_guidance": (
            "Adopt an analytical, systems-oriented big-tech interviewer tone. Evaluate through the lens of high scale, reliability, and engineering trade-offs. "
            "Craft a deeper follow-up question probing extreme scale (e.g. millions of users/QPS), latency bottlenecks, distributed failure modes, or Big-O boundaries."
        )
    }
}

DEFAULT_PERSONALITY = "Friendly Mentor"


def get_personality_details(personality_name: str | None = None) -> dict:
    """Return personality configuration dictionary with safe fallback."""
    if personality_name and personality_name in INTERVIEWER_PERSONALITIES:
        return INTERVIEWER_PERSONALITIES[personality_name]
    return INTERVIEWER_PERSONALITIES[DEFAULT_PERSONALITY]


# Pressure Mode helper functions
def init_pressure_mode(enabled: bool = False, duration: int = 120) -> dict:
    """Initialize pressure mode state dictionary."""
    valid_durations = [60, 120, 180]
    dur = duration if duration in valid_durations else 120
    return {
        "enabled": bool(enabled),
        "duration": dur,
        "start_time": time.time(),
        "expired": False
    }


def get_timer_remaining(start_time: float, duration: int, current_time: float | None = None) -> int:
    """Calculate remaining seconds for the active question."""
    now = current_time if current_time is not None else time.time()
    elapsed = max(0.0, now - float(start_time))
    return max(0, int(float(duration) - elapsed))


def is_timer_expired(start_time: float, duration: int, current_time: float | None = None) -> bool:
    """Check if the question timer has elapsed."""
    now = current_time if current_time is not None else time.time()
    return (now - float(start_time)) >= float(duration)


def format_timer_display(remaining_seconds: int) -> str:
    """Format seconds into MM:SS display format."""
    secs = max(0, int(remaining_seconds))
    mins = secs // 60
    rem_s = secs % 60
    return f"{mins:02d}:{rem_s:02d}"


def reset_question_timer():
    """Reset question timer timestamp and expired status for a new question."""
    if "question_start_time" in st.session_state:
        st.session_state.question_start_time = time.time()
    if "timer_expired" in st.session_state:
        st.session_state.timer_expired = False

# Pydantic schema for structured evaluation
class AnswerEvaluation(BaseModel):
    score: float = Field(description="Overall evaluation score between 0.0 and 10.0")
    classification: str = Field(
        default="Partially Correct",
        description="Classification of candidate answer: exactly one of 'Correct', 'Partially Correct', 'Incorrect', 'Off-topic'"
    )
    relevance: str = Field(description="Evaluation of relevance: did the candidate directly address the question?")
    technical_accuracy: str = Field(description="Evaluation of technical accuracy: is the answer factually and conceptually correct?")
    clarity: str = Field(description="Evaluation of clarity: is the answer coherent, structured, and easy to understand?")
    completeness: str = Field(description="Evaluation of completeness: did the candidate cover key aspects, depth, and trade-offs?")
    correct_concepts: list[str] = Field(
        default_factory=list,
        description="1 to 4 bullet points identifying factually or conceptually sound statements made by the candidate"
    )
    incorrect_statements: list[str] = Field(
        default_factory=list,
        description="Specific flawed, inaccurate, or fallacious technical claims in the answer (empty if none)"
    )
    mistake_explanations: list[str] = Field(
        default_factory=list,
        description="Detailed explanations clarifying why each identified mistake is technically incorrect"
    )
    missing_concepts: list[str] = Field(
        default_factory=list,
        description="Key technical concepts, architectural components, or trade-offs omitted from a complete response"
    )
    correct_explanation: str = Field(
        default="",
        description="A concise, technically accurate educational explanation addressing the core question and resolving misconceptions"
    )
    ideal_answer: str = Field(
        default="",
        description="A model, interview-ready answer demonstrating exemplary technical depth, structure, and clarity"
    )
    strengths: list[str] = Field(description="2 to 4 key strengths demonstrated in the response")
    weaknesses: list[str] = Field(description="1 to 4 areas where the answer was lacking, incomplete, or inaccurate")
    suggestions: list[str] = Field(description="2 to 4 specific, actionable improvement suggestions")
    follow_up_question: str = Field(description="One relevant follow-up interview question based on the candidate's answer")


# Callback and helper functions for clean state transitions without widget conflicts
def reset_candidate_answer_state():
    """Reset the candidate answer state and increment the widget key ID to ensure a fresh text area."""
    st.session_state.candidate_answer = ""
    st.session_state.answer_widget_id = st.session_state.get("answer_widget_id", 0) + 1


def clear_answer():
    reset_candidate_answer_state()
    st.session_state.evaluation_result = None


def practice_followup(question_text):
    if st.session_state.get("current_question"):
        prev = st.session_state.current_question.strip()
        if prev and prev not in st.session_state.question_history:
            st.session_state.question_history.append(prev)
    st.session_state.current_question = question_text
    reset_candidate_answer_state()
    reset_question_timer()
    st.session_state.evaluation_result = None


def init_interview_session(total_questions: int = 15) -> dict:
    """Initialize a clean multi-question interview session dictionary."""
    total = max(1, total_questions)
    history_records: list[dict] = []
    return {
        "active": False,
        "current_index": 1,
        "total_questions": total,
        "history": history_records,
        "turns": history_records,
        "completed": False,
        "current_question": None,
        "current_answer": "",
        "current_evaluation": None
    }


def calculate_session_progress(current_index: int, total_questions: int) -> tuple[float, str]:
    """Calculate progress ratio (0.0 to 1.0) and display label (e.g., 'Question 3 of 15')."""
    total = max(1, total_questions)
    current = min(max(1, current_index), total)
    ratio = min(max(current / total, 0.0), 1.0)
    label = f"Question {current} of {total}"
    return ratio, label


def can_advance_session(current_answer: str, evaluation_result: dict | None) -> bool:
    """Check if the candidate has submitted and evaluated their answer before advancing."""
    if not current_answer or not current_answer.strip():
        return False
    if evaluation_result is None or not isinstance(evaluation_result, dict):
        return False
    return True


def record_session_turn(
    session: dict,
    question: str,
    answer: str,
    evaluation: dict,
    role: str = "",
    difficulty: str = "",
    interview_type: str = "",
    personality: str = "",
    pressure_mode: bool = False
) -> dict:
    """Record an evaluated question-answer pair into session history."""
    score_val = 0.0
    if isinstance(evaluation, dict) and "score" in evaluation:
        try:
            score_val = float(evaluation["score"])
        except (ValueError, TypeError):
            score_val = 0.0

    turn = {
        "question_number": session.get("current_index", len(session.get("history", [])) + 1),
        "question": question,
        "answer": answer,
        "evaluation": evaluation,
        "score": score_val,
        "role": role,
        "difficulty": difficulty,
        "interview_type": interview_type,
        "personality": personality,
        "pressure_mode": pressure_mode
    }

    history = session.setdefault("history", [])
    existing_idx = None
    for idx, rec in enumerate(history):
        if rec.get("question_number") == turn["question_number"]:
            existing_idx = idx
            break
    if existing_idx is not None:
        history[existing_idx] = turn
    else:
        history.append(turn)

    session["turns"] = history
    session["current_question"] = question
    session["current_answer"] = answer
    session["current_evaluation"] = evaluation

    return turn


def advance_session(session: dict) -> dict:
    """Advance session to next question or complete it if at the end."""
    current = session.get("current_index", 1)
    total = session.get("total_questions", 15)
    if current >= total:
        session["completed"] = True
    else:
        session["current_index"] = current + 1
    session["current_question"] = None
    session["current_answer"] = ""
    session["current_evaluation"] = None
    return session


def calculate_performance_rating(avg_score: float) -> str:
    """Return the 5-tier calibrated performance rating based on average score."""
    if avg_score >= 9.0:
        return "Outstanding"
    elif avg_score >= 7.5:
        return "Strong"
    elif avg_score >= 5.0:
        return "Fair"
    elif avg_score >= 3.0:
        return "Below Expectations"
    else:
        return "Inadequate"


def calculate_session_metrics(history: list[dict]) -> dict:
    """Calculate aggregated session performance metrics safely from session history."""
    if not history or not isinstance(history, list):
        return {
            "total_completed": 0,
            "average_score": 0.0,
            "highest_score": 0.0,
            "highest_turn": None,
            "lowest_score": 0.0,
            "lowest_turn": None,
            "performance_rating": "Inadequate",
            "scores": []
        }

    scores: list[float] = []
    valid_turns: list[dict] = []
    for turn in history:
        if not isinstance(turn, dict):
            continue
        valid_turns.append(turn)
        raw_score = turn.get("score")
        if raw_score is None and isinstance(turn.get("evaluation"), dict):
            raw_score = turn["evaluation"].get("score")
        try:
            score_val = float(raw_score) if raw_score is not None else 0.0
        except (ValueError, TypeError):
            score_val = 0.0
        scores.append(score_val)

    if not scores:
        return {
            "total_completed": len(valid_turns),
            "average_score": 0.0,
            "highest_score": 0.0,
            "highest_turn": None,
            "lowest_score": 0.0,
            "lowest_turn": None,
            "performance_rating": "Inadequate",
            "scores": []
        }

    avg_score = round(sum(scores) / len(scores), 2)
    max_score = max(scores)
    min_score = min(scores)

    highest_idx = scores.index(max_score)
    lowest_idx = scores.index(min_score)

    return {
        "total_completed": len(valid_turns),
        "average_score": avg_score,
        "highest_score": max_score,
        "highest_turn": valid_turns[highest_idx],
        "lowest_score": min_score,
        "lowest_turn": valid_turns[lowest_idx],
        "performance_rating": calculate_performance_rating(avg_score),
        "scores": scores
    }


def get_question_analysis_table(history: list[dict]) -> list[dict]:
    """Format individual question analysis rows for tabular display."""
    if not history or not isinstance(history, list):
        return []

    rows: list[dict] = []
    for idx, turn in enumerate(history):
        if not isinstance(turn, dict):
            continue
        eval_data = turn.get("evaluation")
        if not isinstance(eval_data, dict):
            eval_data = {}

        raw_score = turn.get("score")
        if raw_score is None:
            raw_score = eval_data.get("score", 0.0)
        try:
            score_val = float(raw_score)
        except (ValueError, TypeError):
            score_val = 0.0

        q_num = turn.get("question_number", idx + 1)
        q_text = turn.get("question", "N/A")

        rows.append({
            "Question #": q_num,
            "Interview Question": q_text,
            "Score": round(score_val, 1),
            "Relevance": eval_data.get("relevance", "N/A"),
            "Technical Accuracy": eval_data.get("technical_accuracy", "N/A"),
            "Clarity": eval_data.get("clarity", "N/A"),
            "Completeness": eval_data.get("completeness", "N/A")
        })

    return rows


def aggregate_feedback(history: list[dict]) -> dict:
    """Aggregate strengths, weaknesses, and improvement suggestions across interview history."""
    if not history or not isinstance(history, list):
        return {
            "recurring_strengths": [],
            "common_weaknesses": [],
            "key_suggestions": []
        }

    strengths_counter: dict[str, int] = {}
    weaknesses_counter: dict[str, int] = {}
    suggestions_seen: list[str] = []

    def _extract_items(raw_items) -> list[str]:
        if isinstance(raw_items, list):
            return [str(item).strip() for item in raw_items if item and str(item).strip()]
        elif isinstance(raw_items, str) and raw_items.strip():
            return [raw_items.strip()]
        return []

    for turn in history:
        if not isinstance(turn, dict):
            continue
        eval_data = turn.get("evaluation")
        if not isinstance(eval_data, dict):
            continue

        for s in _extract_items(eval_data.get("strengths")):
            strengths_counter[s] = strengths_counter.get(s, 0) + 1

        for w in _extract_items(eval_data.get("weaknesses")):
            weaknesses_counter[w] = weaknesses_counter.get(w, 0) + 1

        for sug in _extract_items(eval_data.get("suggestions")):
            if sug not in suggestions_seen:
                suggestions_seen.append(sug)

    sorted_strengths = sorted(strengths_counter.items(), key=lambda x: (-x[1], x[0]))
    sorted_weaknesses = sorted(weaknesses_counter.items(), key=lambda x: (-x[1], x[0]))

    formatted_strengths = []
    for text, count in sorted_strengths:
        if count > 1:
            formatted_strengths.append(f"{text} (Observed across {count} questions)")
        else:
            formatted_strengths.append(text)

    formatted_weaknesses = []
    for text, count in sorted_weaknesses:
        if count > 1:
            formatted_weaknesses.append(f"{text} (Observed across {count} questions)")
        else:
            formatted_weaknesses.append(text)

    return {
        "recurring_strengths": formatted_strengths,
        "common_weaknesses": formatted_weaknesses,
        "key_suggestions": suggestions_seen
    }


def should_display_dashboard(session: dict) -> bool:
    """Return True only if the interview session is active and marked completed."""
    if not isinstance(session, dict):
        return False
    return bool(session.get("completed", False))


def render_performance_dashboard(
    session: dict,
    role: str = "",
    difficulty: str = "",
    interview_type: str = "",
    personality: str = "",
    pressure_mode: bool = False,
    pressure_time_limit: int = 120
):
    """Render the comprehensive final interview performance dashboard with premium SaaS styling."""
    history = session.get("history", [])
    metrics = calculate_session_metrics(history)
    analysis_table = get_question_analysis_table(history)
    feedback = aggregate_feedback(history)
    total_q = session.get("total_questions", 15)

    pers_badge = get_personality_details(personality)["badge"]
    mode_text = f"⚡ Pressure Mode ({pressure_time_limit}s limit)" if pressure_mode else "Standard Mode (Untimed)"

    st.markdown(f"""
    <div class="command-deck-header">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
            <div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <span style="background: #06241b; color: #34d399; border: 1.5px solid #059669; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 800; letter-spacing: 0.8px;">
                        ● SESSION COMPLETED
                    </span>
                    <span style="background: #1e1b4b; color: #a5b4fc; border: 1.5px solid #6366f1; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 800; letter-spacing: 0.8px;">
                        3D COMMAND TELEMETRY
                    </span>
                </div>
                <h2 style="margin: 0; font-size: 26px; font-weight: 800; color: #ffffff; letter-spacing: -0.4px;">
                    Executive Performance Evaluation
                </h2>
                <p style="margin: 6px 0 0 0; color: #cbd5e1; font-size: 14px; font-weight: 500;">
                    Comprehensive assessment report for <strong style="color: #ffffff;">{role or 'Candidate'}</strong> ({difficulty or 'Standard'} Difficulty, {interview_type or 'Technical'} Format).
                </p>
            </div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <span class="badge-pill badge-persona">{pers_badge}</span>
                <span class="badge-pill badge-stage">{mode_text}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. High-Level Metrics Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Completed", f"{metrics['total_completed']} / {total_q}")
    with col2:
        st.metric("Average Score", f"{metrics['average_score']:.1f} / 10.0")
    with col3:
        st.metric("Overall Rating", metrics["performance_rating"])
    with col4:
        st.metric("Score Spread", f"{metrics['lowest_score']:.1f} – {metrics['highest_score']:.1f}")

    # Highest and Lowest Question Highlights
    h_turn = metrics.get("highest_turn")
    l_turn = metrics.get("lowest_turn")
    if h_turn and l_turn:
        st.write("")
        st.markdown("#### 🎯 Performance Highlights")
        col_high, col_low = st.columns(2)
        with col_high:
            st.markdown(f"""
            <div style="background: #06241b; border: 1.5px solid #059669; border-radius: 12px; padding: 18px 22px; box-shadow: 0 6px 16px rgba(0, 0, 0, 0.6);">
                <div style="font-size: 12.5px; font-weight: 800; color: #34d399; text-transform: uppercase; letter-spacing: 0.5px;">
                    🌟 Strongest Response (Q{h_turn.get('question_number', 1)}) — Score: {h_turn.get('score', 0.0):.1f} / 10.0
                </div>
                <div style="font-size: 14.5px; font-style: italic; color: #f1f5f9; margin-top: 8px; line-height: 1.5;">
                    "{h_turn.get('question', '')}"
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_low:
            st.markdown(f"""
            <div style="background: #241804; border: 1.5px solid #d97706; border-radius: 12px; padding: 18px 22px; box-shadow: 0 6px 16px rgba(0, 0, 0, 0.6);">
                <div style="font-size: 12.5px; font-weight: 800; color: #fbbf24; text-transform: uppercase; letter-spacing: 0.5px;">
                    ⚠️ Opportunity for Improvement (Q{l_turn.get('question_number', 1)}) — Score: {l_turn.get('score', 0.0):.1f} / 10.0
                </div>
                <div style="font-size: 14.5px; font-style: italic; color: #f1f5f9; margin-top: 8px; line-height: 1.5;">
                    "{l_turn.get('question', '')}"
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 2. Score Visualization
    st.write("")
    st.markdown("### 📈 Question Score Trajectory")
    if history:
        chart_data = {
            f"Q{turn.get('question_number', idx + 1)}": float(turn.get("score", 0.0))
            for idx, turn in enumerate(history)
        }
        st.bar_chart(chart_data)

    # 3. Individual Question Analysis Table
    st.write("")
    st.markdown("### 📋 Individual Question Analysis")
    if analysis_table:
        try:
            st.dataframe(analysis_table, use_container_width=True)
        except Exception:
            st.table(analysis_table)

    # 4. Aggregated Qualitative Feedback
    st.write("")
    st.markdown("### 🔍 Aggregated Feedback & Recommendations")
    col_str, col_weak = st.columns(2)
    with col_str:
        with st.container(border=True):
            st.markdown("#### ✅ Recurring Strengths")
            if feedback["recurring_strengths"]:
                for item in feedback["recurring_strengths"]:
                    st.markdown(f"- {item}")
            else:
                st.caption("No specific strengths recorded.")

    with col_weak:
        with st.container(border=True):
            st.markdown("#### ⚠️ Common Areas for Improvement")
            if feedback["common_weaknesses"]:
                for item in feedback["common_weaknesses"]:
                    st.markdown(f"- {item}")
            else:
                st.caption("No specific weaknesses recorded.")

    st.write("")
    with st.container(border=True):
        st.markdown("#### 💡 Priority Improvement Suggestions")
        if feedback["key_suggestions"]:
            for item in feedback["key_suggestions"]:
                st.markdown(f"- {item}")
        else:
            st.caption("No specific suggestions recorded.")

    # 5. Expandable Turn-by-Turn Review
    st.write("")
    st.markdown("### 🔎 Detailed Question-by-Question Review")
    st.caption("Expand any question to review your submitted answer and the full AI evaluation.")
    for idx, turn in enumerate(history):
        q_num = turn.get("question_number", idx + 1)
        q_text = turn.get("question", "")
        q_score = float(turn.get("score", 0.0))
        eval_data = turn.get("evaluation") or {}

        expander_title = f"Question {q_num}: {q_text[:75]}... — Score: {q_score:.1f}/10.0"
        with st.expander(expander_title):
            st.markdown(f"**Interview Question:**\n{q_text}")
            st.markdown(f"**Your Answer:**\n{turn.get('answer', '*(No answer recorded)*')}")
            st.markdown(f"**Evaluated Score:** `{q_score:.1f} / 10.0`")

            if isinstance(eval_data, dict) and eval_data:
                if eval_data.get("classification"):
                    st.markdown(f"- **Assessment Classification:** `{eval_data.get('classification')}`")

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"- **Relevance:** {eval_data.get('relevance', 'N/A')}")
                    st.markdown(f"- **Technical Accuracy:** {eval_data.get('technical_accuracy', 'N/A')}")
                with c2:
                    st.markdown(f"- **Clarity:** {eval_data.get('clarity', 'N/A')}")
                    st.markdown(f"- **Completeness:** {eval_data.get('completeness', 'N/A')}")

                if eval_data.get("strengths"):
                    st.markdown("**Key Strengths:**")
                    for s in eval_data["strengths"]:
                        st.markdown(f"- {s}")
                if eval_data.get("weaknesses"):
                    st.markdown("**Weaknesses:**")
                    for w in eval_data["weaknesses"]:
                        st.markdown(f"- {w}")
                if eval_data.get("correct_explanation"):
                    st.markdown(f"**Correct Explanation:**\n{eval_data['correct_explanation']}")
                if eval_data.get("ideal_answer"):
                    with st.expander("💡 View Ideal Answer"):
                        st.markdown(eval_data["ideal_answer"])
                if eval_data.get("suggestions"):
                    st.markdown("**Actionable Suggestions:**")
                    for sug in eval_data["suggestions"]:
                        st.markdown(f"- {sug}")
                if eval_data.get("follow_up_question"):
                    st.markdown(f"**Interviewer Follow-up Question:** *{eval_data['follow_up_question']}*")

    # 6. Fresh Start Action
    st.write("")
    if st.button("🔄 Start Fresh Interview Session", type="primary", use_container_width=True, key="btn_restart_fresh_session"):
        st.session_state.session = init_interview_session(total_questions=15)
        st.session_state.current_question = ""
        reset_candidate_answer_state()
        reset_question_timer()
        st.session_state.evaluation_result = None
        st.session_state.question_history = []
        st.rerun()


def get_interview_stage(question_number: int | None = None) -> tuple[str, str]:
    """Return the interview stage name and focus description based on question number.
    
    Stages for a 15-question interview:
    - Questions 1–4: Foundational concepts and definitions.
    - Questions 5–11: Technical implementation, algorithms, architecture and trade-offs.
    - Questions 12–15: Advanced scenarios, debugging, failure modes and decision-making.
    - None / default: Comprehensive technical assessment.
    """
    if question_number is None or question_number <= 0:
        return (
            "General Technical Practice",
            "Comprehensive technical assessment covering core concepts, implementation details, and practical problem-solving."
        )
    elif 1 <= question_number <= 4:
        return (
            "Foundational Concepts & Core Principles (Stage 1 of 3: Questions 1–4)",
            "Foundational concepts, fundamental definitions, and core terminology appropriate for the role and difficulty level."
        )
    elif 5 <= question_number <= 11:
        return (
            "Technical Implementation & Architecture (Stage 2 of 3: Questions 5–11)",
            "Technical implementation details, algorithms, data structures, system architecture, and engineering trade-offs."
        )
    else:
        return (
            "Advanced Scenarios, Debugging & Decisions (Stage 3 of 3: Questions 12–15)",
            "Advanced real-world scenarios, debugging complex failures, edge cases, system reliability, and high-stakes technical decision-making."
        )


def get_question_prompt(
    role: str,
    difficulty: str,
    interview_type: str,
    question_number: int | None = None,
    previous_question: str = "",
    history: list[str] | None = None,
    interviewer_personality: str | None = None
) -> str:
    """Load and format the question generation prompt from prompts/question/prompt.txt safely."""
    prompt_file = os.path.join(os.path.dirname(__file__), "prompts", "question", "prompt.txt")
    if os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            template = f.read()
    else:
        template = """Act as a professional interviewer conducting an interview for a {role} position.

Interviewer Persona & Style:
- Interviewer Personality: {interviewer_personality}
- Persona Style & Tone: {personality_question_instructions}

Interview Context:
- Target Job Role: {role}
- Difficulty Level: {difficulty}
- Interview Type: {interview_type}
- Interview Stage: {stage_name}
- Stage Focus: {stage_focus}
{question_number_context}

Instructions:
Generate exactly ONE interview question appropriate for the specified job role, difficulty level, and interview type.
The question must directly align with the current interview stage focus described above:
- Questions 1–4 (Foundational Concepts): Focus on foundational concepts, core definitions, and fundamental terminology.
- Questions 5–11 (Technical Implementation): Focus on practical implementation details, algorithms, system architecture, and technical trade-offs.
- Questions 12–15 (Advanced Scenarios): Focus on advanced real-world scenarios, debugging complex failures, system reliability, and high-stakes technical decision-making.
- Single-Question Practice: Provide a balanced, comprehensive assessment testing core competence and practical problem-solving for the role.
{anti_repetition_instructions}

Interviewer Persona Guidelines:
- Reflect the "{interviewer_personality}" style and expectations in the question phrasing and technical angle.
- Return only the interview question text without any greeting, preamble, character labels, or metadata.
"""

    stage_name, stage_focus = get_interview_stage(question_number)
    persona_data = get_personality_details(interviewer_personality)
    personality_title = persona_data["title"]
    personality_question_instructions = persona_data["question_guidance"]

    if question_number and question_number > 0:
        question_number_context = f"- Question Progress: Question {question_number} of 15"
    else:
        question_number_context = "- Practice Mode: Single-Question Practice"

    anti_rep_blocks = []
    if previous_question and previous_question.strip():
        anti_rep_blocks.append(
            f"""IMPORTANT REQUIREMENT:
The previous question was:
\"{previous_question.strip()}\"

Do NOT repeat, rephrase, or ask about the same topic or concept as the previous question.
Generate a completely DIFFERENT interview question testing a distinct topic, concept, or scenario."""
        )

    if history:
        recent_history = [q.strip() for q in history[-5:] if q.strip() and q.strip() != previous_question.strip()]
        if recent_history:
            formatted_history = "\n".join(f"- {q}" for q in recent_history)
            anti_rep_blocks.append(
                f"""Also avoid covering the same concepts as these previously asked questions:
{formatted_history}"""
            )

    if anti_rep_blocks:
        anti_repetition_instructions = "\n\n" + "\n\n".join(anti_rep_blocks)
    else:
        anti_repetition_instructions = ""

    return template.format(
        role=role,
        difficulty=difficulty,
        interview_type=interview_type,
        stage_name=stage_name,
        stage_focus=stage_focus,
        question_number_context=question_number_context,
        anti_repetition_instructions=anti_repetition_instructions,
        interviewer_personality=personality_title,
        personality_question_instructions=personality_question_instructions
    )


def generate_interview_question(
    client: genai.Client,
    role: str,
    difficulty: str,
    interview_type: str,
    previous_question: str = "",
    history: list[str] | None = None,
    question_number: int | None = None,
    interviewer_personality: str | None = None
) -> str:
    """Generate a fresh interview question using gemini-3.5-flash-lite, avoiding previous questions and adapting to interview stage and personality."""
    prompt = get_question_prompt(
        role=role,
        difficulty=difficulty,
        interview_type=interview_type,
        question_number=question_number,
        previous_question=previous_question,
        history=history,
        interviewer_personality=interviewer_personality
    )

    config = types.GenerateContentConfig(
        temperature=0.85
    )

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=config
    )
    return response.text.strip() if response and response.text else ""


def get_evaluation_prompt(
    role: str,
    difficulty: str,
    interview_type: str,
    question: str,
    candidate_answer: str,
    interviewer_personality: str | None = None
) -> str:
    """Load and format the final evaluation prompt template from prompts/final/prompt.txt, optionally adapting tone to personality."""
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
    prompt_text = template.format(
        role=role,
        difficulty=difficulty,
        interview_type=interview_type,
        question=question,
        candidate_answer=candidate_answer
    )

    if interviewer_personality:
        p_info = get_personality_details(interviewer_personality)
        persona_block = f"""

Interviewer Personality & Tone Directive:
- Selected Interviewer: {p_info['title']}
- Personality Profile: {p_info['description']}
- Tone & Follow-Up Guidance: {p_info['evaluation_guidance']}
- IMPORTANT: The interviewer personality MUST shape the communication tone of feedback and especially the style, depth, and angle of the follow_up_question. It must NOT alter the objective numerical scoring weights (0.0 to 10.0 scale), core evaluation criteria thresholds, or factual assessment standards."""
        prompt_text += persona_block

    return prompt_text


def main():
    # Load API key from .env
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    st.set_page_config(
        page_title="AI Mock Interview Coach",
        page_icon="🎯",
        layout="wide"
    )

    # Professional Commercial 3D AI Command Center Theme & High-Contrast Styling
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #f8fafc !important;
    }

    /* 3D Deep Space AI Command Deck Canvas */
    .stApp {
        background: #060913 !important;
        background-image: 
            radial-gradient(ellipse 90% 60% at 50% -20%, rgba(30, 41, 89, 0.5) 0%, rgba(6, 9, 19, 0.98) 75%),
            linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px) !important;
        background-size: 100% 100%, 40px 40px, 40px 40px !important;
        color: #f8fafc !important;
    }

    /* Streamlit Header & Top Toolbar */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Global Typography & Muted Text Contrast */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px !important;
    }
    p, span, label, div {
        color: #f1f5f9;
    }
    .stCaption, [data-testid="stCaptionContainer"] p, [data-testid="stCaptionContainer"] {
        color: #cbd5e1 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }

    /* ========================================================================= */
    /* CRITICAL BUTTON DESIGN SYSTEM — 100% OPAQUE, HIGH-CONTRAST 3D BUTTONS   */
    /* ========================================================================= */

    /* Base Button Styling (Flat Solid Surfaces, Zero 3D) */
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 14.5px !important;
        padding: 10px 20px !important;
        letter-spacing: 0.2px !important;
        position: relative !important;
        transition: background-color 0.15s ease, border-color 0.15s ease !important;
        cursor: pointer !important;
        box-shadow: none !important;
        text-shadow: none !important;
        transform: none !important;
    }

    /* 1. PRIMARY BUTTONS: Solid Electric Indigo */
    div.stButton > button[kind="primary"],
    div.stButton > button[data-testid="baseButton-primary"],
    div.stButton > button[data-testid="stBaseButton-primary"] {
        background: #4F46E5 !important;
        background-color: #4F46E5 !important;
        background-image: none !important;
        color: #ffffff !important;
        border: 1.5px solid #6366F1 !important;
        box-shadow: none !important;
        text-shadow: none !important;
        transform: none !important;
        opacity: 1 !important;
    }

    div.stButton > button[kind="primary"]:hover,
    div.stButton > button[data-testid="baseButton-primary"]:hover,
    div.stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: #4338CA !important;
        background-color: #4338CA !important;
        border-color: #818cf8 !important;
        color: #ffffff !important;
        box-shadow: none !important;
        transform: none !important;
    }

    div.stButton > button[kind="primary"]:active,
    div.stButton > button[data-testid="baseButton-primary"]:active,
    div.stButton > button[data-testid="stBaseButton-primary"]:active {
        background: #3730A3 !important;
        background-color: #3730A3 !important;
        box-shadow: none !important;
        transform: none !important;
    }

    /* 2. SECONDARY BUTTONS: Solid Dark Slate */
    div.stButton > button[kind="secondary"],
    div.stButton > button[data-testid="baseButton-secondary"],
    div.stButton > button[data-testid="stBaseButton-secondary"],
    div.stButton > button:not([kind="primary"]) {
        background: #1E293B !important;
        background-color: #1E293B !important;
        background-image: none !important;
        color: #ffffff !important;
        border: 1.5px solid #475569 !important;
        box-shadow: none !important;
        text-shadow: none !important;
        transform: none !important;
        opacity: 1 !important;
    }

    div.stButton > button[kind="secondary"]:hover,
    div.stButton > button[data-testid="baseButton-secondary"]:hover,
    div.stButton > button[data-testid="stBaseButton-secondary"]:hover,
    div.stButton > button:not([kind="primary"]):hover {
        background: #334155 !important;
        background-color: #334155 !important;
        border-color: #64748B !important;
        color: #ffffff !important;
        box-shadow: none !important;
        transform: none !important;
    }

    div.stButton > button[kind="secondary"]:active,
    div.stButton > button[data-testid="baseButton-secondary"]:active,
    div.stButton > button[data-testid="stBaseButton-secondary"]:active,
    div.stButton > button:not([kind="primary"]):active {
        background: #0F172A !important;
        background-color: #0F172A !important;
        box-shadow: none !important;
        transform: none !important;
    }

    /* 3. DISABLED BUTTONS */
    div.stButton > button:disabled,
    div.stButton > button[disabled] {
        background: #0F172A !important;
        background-color: #0F172A !important;
        color: #64748b !important;
        border: 1.5px solid #1e293b !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
        opacity: 0.65 !important;
        transform: none !important;
        text-shadow: none !important;
    }

    /* Focus Visible Accessibility Rings */
    div.stButton > button:focus-visible {
        outline: 2px solid #6366F1 !important;
        outline-offset: 2px !important;
    }

    /* ========================================================================= */
    /* REGENERATE BUTTONS (SOLID DARK INDIGO #3730A3 - NO 3D/GLOW/GRADIENTS)     */
    /* ========================================================================= */
    div[data-testid="stColumn"]:has(.regenerate-scope-marker) button,
    div[data-testid="stVerticalBlock"]:has(.regenerate-scope-marker) button,
    div:has(> .regenerate-scope-marker) ~ div button,
    div.element-container:has(.regenerate-scope-marker) + div.element-container button {
        background: #3730A3 !important;
        background-color: #3730A3 !important;
        background-image: none !important;
        color: #FFFFFF !important;
        border: 1.5px solid #6366F1 !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        text-shadow: none !important;
        opacity: 1 !important;
        font-weight: 700 !important;
        transition: background-color 0.15s ease !important;
    }

    div[data-testid="stColumn"]:has(.regenerate-scope-marker) button *,
    div[data-testid="stVerticalBlock"]:has(.regenerate-scope-marker) button *,
    div:has(> .regenerate-scope-marker) ~ div button *,
    div.element-container:has(.regenerate-scope-marker) + div.element-container button * {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        text-shadow: none !important;
    }

    div[data-testid="stColumn"]:has(.regenerate-scope-marker) button p,
    div[data-testid="stColumn"]:has(.regenerate-scope-marker) button span,
    div[data-testid="stColumn"]:has(.regenerate-scope-marker) button div {
        color: #FFFFFF !important;
    }

    /* Hover State: Lighter Indigo #4F46E5 */
    div[data-testid="stColumn"]:has(.regenerate-scope-marker) button:hover,
    div[data-testid="stVerticalBlock"]:has(.regenerate-scope-marker) button:hover,
    div:has(> .regenerate-scope-marker) ~ div button:hover,
    div.element-container:has(.regenerate-scope-marker) + div.element-container button:hover {
        background: #4F46E5 !important;
        background-color: #4F46E5 !important;
        background-image: none !important;
        border-color: #6366F1 !important;
        color: #FFFFFF !important;
        box-shadow: none !important;
        transform: none !important;
    }

    div[data-testid="stColumn"]:has(.regenerate-scope-marker) button:hover *,
    div[data-testid="stVerticalBlock"]:has(.regenerate-scope-marker) button:hover * {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }

    /* Click / Active State: Darker Indigo #312E81 */
    div[data-testid="stColumn"]:has(.regenerate-scope-marker) button:active,
    div[data-testid="stVerticalBlock"]:has(.regenerate-scope-marker) button:active,
    div:has(> .regenerate-scope-marker) ~ div button:active,
    div.element-container:has(.regenerate-scope-marker) + div.element-container button:active {
        background: #312E81 !important;
        background-color: #312E81 !important;
        background-image: none !important;
        border-color: #6366F1 !important;
        color: #FFFFFF !important;
        box-shadow: none !important;
        transform: none !important;
    }

    div[data-testid="stColumn"]:has(.regenerate-scope-marker) button:active *,
    div[data-testid="stVerticalBlock"]:has(.regenerate-scope-marker) button:active * {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }

    /* Disabled State */
    div[data-testid="stColumn"]:has(.regenerate-scope-marker) button:disabled,
    div[data-testid="stVerticalBlock"]:has(.regenerate-scope-marker) button:disabled {
        background: #3730A3 !important;
        background-color: #3730A3 !important;
        background-image: none !important;
        color: #FFFFFF !important;
        border: 1.5px solid #6366F1 !important;
        opacity: 0.65 !important;
        cursor: not-allowed !important;
        box-shadow: none !important;
    }

    /* ========================================================================= */
    /* 3D FLOATING CARDS & RECESSED PANELS                                       */
    /* ========================================================================= */

    /* Streamlit Border Containers (st.container(border=True)) */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background: #0c1222 !important;
        border: 1px solid rgba(56, 189, 248, 0.22) !important;
        border-radius: 14px !important;
        padding: 22px !important;
        box-shadow: 0 12px 30px -8px rgba(0, 0, 0, 0.75), inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 0 1px 1px rgba(99, 102, 241, 0.12) !important;
    }

    /* Top 3D Command Deck Header */
    .command-deck-header {
        background: linear-gradient(180deg, #10172e 0%, #090e1d 100%);
        border: 1.5px solid rgba(99, 102, 241, 0.45);
        border-radius: 16px;
        padding: 24px 30px;
        margin-bottom: 24px;
        box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(56, 189, 248, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.15);
    }

    /* Section Number Badges */
    .section-badge {
        background: linear-gradient(180deg, #6366f1 0%, #4338ca 100%);
        color: #ffffff;
        width: 26px;
        height: 26px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        font-weight: 800;
        margin-right: 10px;
        border: 1px solid #818cf8;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.35);
    }

    /* Text Area */
    .stTextArea textarea {
        background: #090e1a !important;
        border: 1.5px solid #334155 !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
        padding: 16px !important;
        transition: all 0.2s ease !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.4) !important;
    }
    .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.4) !important;
    }
    .stTextArea textarea:disabled {
        background: #080c14 !important;
        color: #cbd5e1 !important;
        border-color: #ef4444 !important;
        cursor: not-allowed !important;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background: #0d1424 !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 12px !important;
        padding: 18px 22px !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
    }
    [data-testid="stMetricLabel"] p {
        font-size: 12px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
        color: #93c5fd !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #ffffff !important;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #38bdf8 0%, #6366f1 50%, #a855f7 100%) !important;
        border-radius: 6px !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.4) !important;
    }
    .stProgress > div > div {
        background: #172033 !important;
        border-radius: 6px !important;
        height: 10px !important;
        border: 1px solid #1e293b !important;
    }

    /* High-Contrast Badge Pills */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12.5px;
        font-weight: 700;
        letter-spacing: 0.3px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
    }
    .badge-role {
        background: #0e1d3d;
        color: #93c5fd;
        border: 1.5px solid #2563eb;
    }
    .badge-difficulty {
        background: #231806;
        color: #fcd34d;
        border: 1.5px solid #d97706;
    }
    .badge-type {
        background: #08202d;
        color: #7dd3fc;
        border: 1.5px solid #0284c7;
    }
    .badge-persona {
        background: #23103c;
        color: #d8b4fe;
        border: 1.5px solid #9333ea;
    }
    .badge-pressure {
        background: #2b0d12;
        color: #fca5a5;
        border: 1.5px solid #dc2626;
    }
    .badge-stage {
        background: #06241b;
        color: #6ee7b7;
        border: 1.5px solid #059669;
    }

    /* ========================================================================= */
    /* SELECTBOXES, COMBOBOXES & DROPDOWNS (HIGH CONTRAST #111827 / #FFFFFF)     */
    /* ========================================================================= */
    /* Selectbox Outer Group & Inputs */
    div[data-testid="stSelectbox"] [role="group"],
    div[data-testid="stSelectbox"] [data-rac=""][role="group"],
    .react-aria-ComboBox [role="group"],
    div[data-baseweb="select"] > div {
        background: #111827 !important;
        background-color: #111827 !important;
        border: 1.5px solid #475569 !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        box-shadow: none !important;
        min-height: 42px !important;
        display: flex !important;
        align-items: center !important;
        padding: 0 4px 0 10px !important;
    }

    div[data-testid="stSelectbox"] [role="group"]:hover,
    .react-aria-ComboBox [role="group"]:hover,
    div[data-baseweb="select"] > div:hover {
        border-color: #6366F1 !important;
    }

    div[data-testid="stSelectbox"] [role="group"]:focus-within,
    .react-aria-ComboBox [role="group"]:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3) !important;
    }

    /* Input inside selectbox */
    div[data-testid="stSelectbox"] input,
    .react-aria-ComboBox input,
    div[data-baseweb="select"] input {
        background: transparent !important;
        background-color: transparent !important;
        color: #FFFFFF !important;
        font-size: 14.5px !important;
        font-weight: 500 !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        padding: 8px 4px !important;
        width: 100% !important;
    }

    div[data-testid="stSelectbox"] input::placeholder,
    .react-aria-ComboBox input::placeholder {
        color: #94a3b8 !important;
    }

    /* Right-side dropdown arrow button: Clean minimal arrow, NO oversized colored box */
    .react-aria-ComboBox button,
    div[data-testid="stSelectbox"] button,
    div[data-baseweb="select"] button {
        background: transparent !important;
        background-color: transparent !important;
        background-image: none !important;
        border: none !important;
        box-shadow: none !important;
        text-shadow: none !important;
        outline: none !important;
        padding: 6px 8px !important;
        margin: 0 !important;
        width: auto !important;
        height: auto !important;
        min-height: 0 !important;
        color: #94a3b8 !important;
        cursor: pointer !important;
        transform: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    .react-aria-ComboBox button svg,
    div[data-testid="stSelectbox"] button svg,
    div[data-baseweb="select"] svg {
        color: #94a3b8 !important;
        fill: currentColor !important;
        stroke: currentColor !important;
        width: 16px !important;
        height: 16px !important;
    }

    .react-aria-ComboBox button:hover svg,
    div[data-testid="stSelectbox"] button:hover svg {
        color: #FFFFFF !important;
    }

    /* Dropdown Popover Container (React-Aria & BaseWeb) */
    .react-aria-Popover,
    div[data-testid="portal"] [role="listbox"],
    div[data-testid="portal"] [data-rac=""][role="listbox"],
    #stFloatingOverlayPortal [role="listbox"],
    #stFloatingOverlayPortal [data-rac=""][role="listbox"],
    [data-rac=""][role="listbox"],
    .react-aria-ListBox,
    div[data-baseweb="popover"] ul,
    div[data-baseweb="menu"],
    ul[role="listbox"] {
        background: #111827 !important;
        background-color: #111827 !important;
        border: 1.5px solid #475569 !important;
        border-radius: 8px !important;
        padding: 6px !important;
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.8) !important;
        color: #FFFFFF !important;
    }

    /* Dropdown Options */
    [role="option"],
    [data-rac=""][role="option"],
    .react-aria-ListBoxItem,
    .react-aria-Item,
    li[role="option"],
    div[data-baseweb="popover"] li,
    div[data-baseweb="menu"] li {
        background: transparent !important;
        background-color: transparent !important;
        color: #FFFFFF !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        padding: 9px 14px !important;
        border-radius: 6px !important;
        margin: 2px 0 !important;
        cursor: pointer !important;
        transition: background-color 0.1s ease !important;
        display: flex !important;
        align-items: center !important;
    }

    [role="option"] *,
    [data-rac=""][role="option"] *,
    .react-aria-ListBoxItem *,
    .react-aria-Item *,
    li[role="option"] *,
    div[data-baseweb="popover"] li * {
        color: #FFFFFF !important;
    }

    /* Dropdown Option Hover: Visible Indigo Background (#4F46E5) with White Text (#FFFFFF) */
    [role="option"]:hover,
    [role="option"][data-focused="true"],
    [data-rac=""][role="option"]:hover,
    [data-rac=""][role="option"][data-focused="true"],
    .react-aria-ListBoxItem:hover,
    .react-aria-ListBoxItem[data-focused="true"],
    .react-aria-Item:hover,
    li[role="option"]:hover,
    div[data-baseweb="popover"] li:hover {
        background: #4F46E5 !important;
        background-color: #4F46E5 !important;
        color: #FFFFFF !important;
    }

    [role="option"]:hover *,
    [role="option"][data-focused="true"] *,
    [data-rac=""][role="option"]:hover *,
    [data-rac=""][role="option"][data-focused="true"] *,
    .react-aria-ListBoxItem:hover *,
    .react-aria-ListBoxItem[data-focused="true"] *,
    .react-aria-Item:hover *,
    li[role="option"]:hover * {
        color: #FFFFFF !important;
    }

    /* Dropdown Option Selected: Visible Contrasting Dark Indigo Background (#312E81) */
    [role="option"][aria-selected="true"],
    [role="option"][data-selected="true"],
    [data-rac=""][role="option"][data-selected="true"],
    .react-aria-ListBoxItem[aria-selected="true"],
    .react-aria-ListBoxItem[data-selected="true"],
    li[role="option"][aria-selected="true"] {
        background: #312E81 !important;
        background-color: #312E81 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    [role="option"][aria-selected="true"] *,
    [role="option"][data-selected="true"] * {
        color: #FFFFFF !important;
    }

    /* ========================================================================= */
    /* RADIO BUTTONS (READABLE LABELS & CLEAR SELECTION STATES)                  */
    /* ========================================================================= */
    div[data-testid="stRadioGroup"] label,
    div[data-testid="stRadioGroup"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stRadioGroup"] span {
        color: #FFFFFF !important;
        font-size: 14.5px !important;
        font-weight: 500 !important;
    }

    /* Unselected circle */
    div[data-testid="stRadioOption"] > div:first-of-type > div:first-of-type {
        border: 2px solid #475569 !important;
        background-color: #111827 !important;
        border-radius: 50% !important;
    }

    /* Selected circle */
    div[data-testid="stRadioOption"][data-selected="true"] > div:first-of-type > div:first-of-type {
        border-color: #6366F1 !important;
    }

    div[data-testid="stRadioOption"][data-selected="true"] > div:first-of-type > div:first-of-type > div {
        background-color: #6366F1 !important;
        border-radius: 50% !important;
    }

    /* ========================================================================= */
    /* CHECKBOXES & TOGGLES (READABLE LABELS & VISIBLE STATES)                   */
    /* ========================================================================= */
    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stCheckbox"] span {
        color: #FFFFFF !important;
        font-size: 14.5px !important;
        font-weight: 500 !important;
    }

    /* Toggle track (switch) */
    div[data-testid="stCheckbox"] input[role="switch"] ~ div {
        background-color: #334155 !important;
        border: 1.5px solid #475569 !important;
        border-radius: 12px !important;
        transition: background-color 0.2s ease !important;
    }

    div[data-testid="stCheckbox"] input[role="switch"]:checked ~ div {
        background-color: #6366F1 !important;
        border-color: #818cf8 !important;
    }

    div[data-testid="stCheckbox"] input[role="switch"] ~ div > div {
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
    }

    /* ========================================================================= */
    /* TEXT INPUTS & TEXTAREAS (SOLID #111827 / #FFFFFF / #475569)               */
    /* ========================================================================= */
    .stTextInput input,
    .stTextArea textarea,
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea {
        background: #111827 !important;
        background-color: #111827 !important;
        color: #FFFFFF !important;
        border: 1.5px solid #475569 !important;
        border-radius: 8px !important;
        font-size: 14.5px !important;
        box-shadow: none !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus,
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="textarea"]:focus-within {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3) !important;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #94a3b8 !important;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background: #0c1222 !important;
        border: 1.5px solid #1e293b !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
    }
    .streamlit-expanderHeader {
        background: #131b31 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        padding: 14px 18px !important;
    }
    .streamlit-expanderHeader:hover {
        background: #1a2542 !important;
        color: #38bdf8 !important;
    }

    /* ========================================================================= */
    /* ASSESSMENT CLASSIFICATION BANNERS (EXPLICIT HIGH CONTRAST)                */
    /* ========================================================================= */
    .banner-classification {
        border-radius: 12px !important;
        padding: 16px 22px !important;
        margin-top: 12px !important;
        margin-bottom: 18px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6) !important;
        display: flex !important;
        align-items: center !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
    }
    .banner-correct {
        background-color: #04271d !important;
        border: 1.5px solid #10b981 !important;
    }
    .banner-correct, .banner-correct * {
        color: #f1f5f9 !important;
    }
    .banner-correct .banner-label {
        color: #34d399 !important;
        font-weight: 800 !important;
        font-size: 15px !important;
    }

    .banner-partially-correct {
        background-color: #0c1e38 !important;
        border: 1.5px solid #0284c7 !important;
    }
    .banner-partially-correct, .banner-partially-correct * {
        color: #f1f5f9 !important;
    }
    .banner-partially-correct .banner-label {
        color: #38bdf8 !important;
        font-weight: 800 !important;
        font-size: 15px !important;
    }

    .banner-incorrect {
        background-color: #2b0b11 !important;
        border: 1.5px solid #ef4444 !important;
    }
    .banner-incorrect, .banner-incorrect * {
        color: #f1f5f9 !important;
    }
    .banner-incorrect .banner-label {
        color: #f87171 !important;
        font-weight: 800 !important;
        font-size: 15px !important;
    }

    .banner-off-topic {
        background-color: #271405 !important;
        border: 1.5px solid #f97316 !important;
    }
    .banner-off-topic, .banner-off-topic * {
        color: #f1f5f9 !important;
    }
    .banner-off-topic .banner-label {
        color: #fb923c !important;
        font-weight: 800 !important;
        font-size: 15px !important;
    }

    /* ========================================================================= */
    /* TECHNICALLY CORRECT EXPLANATION PANEL                                    */
    /* ========================================================================= */
    .technically-correct-panel {
        background-color: #111827 !important;
        border: 1.5px solid #0284c7 !important;
        border-radius: 12px !important;
        padding: 20px 24px !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.6) !important;
        margin-top: 12px !important;
        margin-bottom: 18px !important;
    }
    .technically-correct-panel * {
        color: #F9FAFB !important;
    }
    .technically-correct-panel p,
    .technically-correct-panel span,
    .technically-correct-panel li,
    .technically-correct-panel div {
        color: #F9FAFB !important;
        font-size: 14.5px !important;
        line-height: 1.6 !important;
    }
    .technically-correct-panel strong {
        color: #38bdf8 !important;
        font-weight: 700 !important;
    }
    .technically-correct-panel code {
        background: #1e293b !important;
        color: #38bdf8 !important;
        border: 1px solid #334155 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .technically-correct-panel h1,
    .technically-correct-panel h2,
    .technically-correct-panel h3,
    .technically-correct-panel h4,
    .technically-correct-panel h5 {
        color: #ffffff !important;
    }

    /* ========================================================================= */
    /* PERFORMANCE CALIBRATION BANNERS                                           */
    /* ========================================================================= */
    .calib-banner {
        border-radius: 10px !important;
        padding: 12px 18px !important;
        margin-top: 8px !important;
        font-size: 14px !important;
        line-height: 1.5 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
    }
    .calib-excellent {
        background-color: #04271d !important;
        border: 1.5px solid #10b981 !important;
    }
    .calib-excellent, .calib-excellent * {
        color: #f1f5f9 !important;
    }
    .calib-excellent strong {
        color: #34d399 !important;
    }

    .calib-good {
        background-color: #0c1e38 !important;
        border: 1.5px solid #0284c7 !important;
    }
    .calib-good, .calib-good * {
        color: #f1f5f9 !important;
    }
    .calib-good strong {
        color: #38bdf8 !important;
    }

    .calib-average {
        background-color: #241604 !important;
        border: 1.5px solid #d97706 !important;
    }
    .calib-average, .calib-average * {
        color: #f1f5f9 !important;
    }
    .calib-average strong {
        color: #fbbf24 !important;
    }

    .calib-needs-improvement {
        background-color: #2b0b11 !important;
        border: 1.5px solid #ef4444 !important;
    }
    .calib-needs-improvement, .calib-needs-improvement * {
        color: #f1f5f9 !important;
    }
    .calib-needs-improvement strong {
        color: #f87171 !important;
    }

    /* ========================================================================= */
    /* STREAMLIT NATIVE ALERT OVERRIDES (ENSURES ZERO PALE BACKGROUNDS)         */
    /* ========================================================================= */
    div[data-testid="stAlert"],
    div[data-testid="stAlertContainer"],
    .stAlert,
    .stAlertContainer {
        border-radius: 12px !important;
        border-width: 1.5px !important;
        border-style: solid !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5) !important;
    }
    div[data-testid="stAlertContainer"] *,
    div[data-testid="stAlert"] * {
        color: #f1f5f9 !important;
    }

    /* Success Alert */
    div[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]),
    div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]),
    div:has(> [data-testid="stAlertContentSuccess"]),
    [data-testid="stAlertContentSuccess"],
    div[data-testid="stAlertSuccess"],
    .stAlert[data-baseweb="notification"][kind="positive"] {
        background-color: #04271d !important;
        border-color: #059669 !important;
    }
    div:has(> [data-testid="stAlertContentSuccess"]) *,
    [data-testid="stAlertContentSuccess"] * {
        color: #f1f5f9 !important;
    }
    div:has(> [data-testid="stAlertContentSuccess"]) strong,
    [data-testid="stAlertContentSuccess"] strong {
        color: #34d399 !important;
    }

    /* Info Alert */
    div[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]),
    div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]),
    div:has(> [data-testid="stAlertContentInfo"]),
    [data-testid="stAlertContentInfo"],
    div[data-testid="stAlertInfo"],
    .stAlert[data-baseweb="notification"][kind="info"] {
        background-color: #0c1e38 !important;
        border-color: #0284c7 !important;
    }
    div:has(> [data-testid="stAlertContentInfo"]) *,
    [data-testid="stAlertContentInfo"] * {
        color: #f1f5f9 !important;
    }
    div:has(> [data-testid="stAlertContentInfo"]) strong,
    [data-testid="stAlertContentInfo"] strong {
        color: #38bdf8 !important;
    }

    /* Warning Alert (Eliminate Pale Yellow) */
    div[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]),
    div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]),
    div:has(> [data-testid="stAlertContentWarning"]),
    [data-testid="stAlertContentWarning"],
    div[data-testid="stAlertWarning"],
    .stAlert[data-baseweb="notification"][kind="warning"] {
        background-color: #241604 !important;
        border-color: #d97706 !important;
    }
    div:has(> [data-testid="stAlertContentWarning"]) *,
    [data-testid="stAlertContentWarning"] * {
        color: #f1f5f9 !important;
    }
    div:has(> [data-testid="stAlertContentWarning"]) strong,
    [data-testid="stAlertContentWarning"] strong {
        color: #fbbf24 !important;
    }

    /* Error Alert */
    div[data-testid="stAlert"]:has([data-testid="stAlertContentError"]),
    div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]),
    div:has(> [data-testid="stAlertContentError"]),
    [data-testid="stAlertContentError"],
    div[data-testid="stAlertError"],
    .stAlert[data-baseweb="notification"][kind="negative"] {
        background-color: #2b0b11 !important;
        border-color: #dc2626 !important;
    }
    div:has(> [data-testid="stAlertContentError"]) *,
    [data-testid="stAlertContentError"] * {
        color: #f1f5f9 !important;
    }
    div:has(> [data-testid="stAlertContentError"]) strong,
    [data-testid="stAlertContentError"] strong {
        color: #f87171 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state variables
    if "practice_mode" not in st.session_state:
        st.session_state.practice_mode = "Single Question Practice"
    if "session" not in st.session_state:
        st.session_state.session = init_interview_session(total_questions=15)
    if "current_question" not in st.session_state:
        st.session_state.current_question = ""
    if "question_history" not in st.session_state:
        st.session_state.question_history = []
    if "answer_widget_id" not in st.session_state:
        st.session_state.answer_widget_id = 0
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
    if "interviewer_personality" not in st.session_state:
        st.session_state.interviewer_personality = DEFAULT_PERSONALITY
    if "evaluated_personality" not in st.session_state:
        st.session_state.evaluated_personality = DEFAULT_PERSONALITY
    if "pressure_mode_enabled" not in st.session_state:
        st.session_state.pressure_mode_enabled = False
    if "pressure_time_limit" not in st.session_state:
        st.session_state.pressure_time_limit = 120
    if "question_start_time" not in st.session_state:
        st.session_state.question_start_time = time.time()
    if "timer_expired" not in st.session_state:
        st.session_state.timer_expired = False

    # Top 3D AI Command Deck Header
    st.markdown("""
    <div class="command-deck-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
            <div style="display: flex; align-items: center; gap: 18px;">
                <div style="position: relative; width: 52px; height: 52px; border-radius: 14px; background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%); border: 1.5px solid #818cf8; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 20px rgba(99, 102, 241, 0.5), inset 0 0 12px rgba(56, 189, 248, 0.3);">
                    <span style="font-size: 26px; filter: drop-shadow(0 0 6px rgba(99, 102, 241, 0.8));">🎯</span>
                </div>
                <div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <h1 style="margin: 0; font-size: 25px; font-weight: 800; letter-spacing: -0.4px; color: #ffffff;">
                            AI Mock Interview Coach
                        </h1>
                        <span style="background: #1e1b4b; color: #a5b4fc; border: 1px solid #6366f1; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;">v3.0 HUD</span>
                    </div>
                    <p style="margin: 4px 0 0 0; font-size: 13.5px; color: #cbd5e1; font-weight: 500;">
                        3D AI Command Deck • Enterprise Technical Interview Simulation & Real-Time Evaluative Feedback
                    </p>
                </div>
            </div>
            <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                <span class="badge-pill badge-stage">● Core Online</span>
                <span class="badge-pill badge-role">⚡ Gemini 3.5 Flash-Lite</span>
                <span class="badge-pill badge-persona">🛡️ Enterprise HUD</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

    # Mode Selection
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <span class="section-badge">1</span>
        <span style="font-size: 16px; font-weight: 700; color: #f1f5f9;">Choose Practice Mode</span>
    </div>
    """, unsafe_allow_html=True)

    practice_mode = st.radio(
        "Select your interview mode:",
        ["Single Question Practice", "Complete Interview Session (15 Questions)"],
        horizontal=True,
        key="practice_mode_radio",
        label_visibility="collapsed"
    )
    is_session_mode = (practice_mode == "Complete Interview Session (15 Questions)")

    st.write("")

    # Configuration Section
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 12px;">
        <span class="section-badge">2</span>
        <span style="font-size: 16px; font-weight: 700; color: #f1f5f9;">Configure Your Interview Session</span>
    </div>
    """, unsafe_allow_html=True)

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

    # Personality and Pressure Mode Configuration
    col_pers, col_press = st.columns([2, 1])
    with col_pers:
        pers_options = list(INTERVIEWER_PERSONALITIES.keys())
        default_pers_idx = (
            pers_options.index(st.session_state.get("interviewer_personality", DEFAULT_PERSONALITY))
            if st.session_state.get("interviewer_personality") in pers_options else 0
        )
        selected_personality = st.selectbox(
            "Choose Your Interviewer",
            pers_options,
            index=default_pers_idx,
            help="Select the AI interviewer personality to adapt question style, tone, and follow-up rigor."
        )
        st.session_state.interviewer_personality = selected_personality
        pers_details = get_personality_details(selected_personality)
        st.caption(f"{pers_details['badge']} — *{pers_details['description']}*")

    with col_press:
        press_enabled = st.toggle(
            "⚡ Interview Pressure Mode",
            value=bool(st.session_state.get("pressure_mode_enabled", False)),
            help="Enforces a countdown timer for answering each question."
        )
        st.session_state.pressure_mode_enabled = press_enabled
        if press_enabled:
            durations = [60, 120, 180]
            current_dur = st.session_state.get("pressure_time_limit", 120)
            dur_idx = durations.index(current_dur) if current_dur in durations else 1
            selected_duration = st.selectbox(
                "Timer Duration",
                durations,
                index=dur_idx,
                format_func=lambda s: f"{s} seconds ({s//60} min{'s' if s > 60 else ''})",
                help="Allowed time per question. Edits are disabled when time expires."
            )
            st.session_state.pressure_time_limit = selected_duration

    # Session Completion Screen & Final Performance Dashboard
    if is_session_mode and should_display_dashboard(st.session_state.session):
        render_performance_dashboard(
            session=st.session_state.session,
            role=st.session_state.get("evaluated_role", role),
            difficulty=st.session_state.get("evaluated_difficulty", difficulty),
            interview_type=st.session_state.get("evaluated_type", interview_type),
            personality=st.session_state.get("evaluated_personality", selected_personality),
            pressure_mode=st.session_state.get("pressure_mode_enabled", False),
            pressure_time_limit=st.session_state.get("pressure_time_limit", 120)
        )
        return

    # Controls for Session Start vs Single Question Generation
    if is_session_mode:
        if not st.session_state.session.get("active"):
            st.markdown("""
            <div style="background: #0c1222; border: 1.5px solid rgba(56, 189, 248, 0.3); border-radius: 14px; padding: 24px 26px; margin-bottom: 22px; box-shadow: 0 12px 30px -8px rgba(0, 0, 0, 0.7);">
                <div style="font-size: 15px; font-weight: 800; color: #ffffff; margin-bottom: 14px; display: flex; align-items: center; gap: 8px;">
                    <span style="color: #38bdf8;">⚡</span> 15-Question Structured Interview Curriculum
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; margin-bottom: 14px;">
                    <div style="background: #071915; border: 1.5px solid #059669; border-radius: 10px; padding: 14px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);">
                        <div style="font-weight: 800; font-size: 13.5px; color: #34d399; margin-bottom: 4px;">🟢 Stage 1: Questions 1–4</div>
                        <div style="font-size: 12.5px; color: #e2e8f0; font-weight: 500;">Foundational concepts, fundamental definitions, and core terminology.</div>
                    </div>
                    <div style="background: #1c1505; border: 1.5px solid #d97706; border-radius: 10px; padding: 14px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);">
                        <div style="font-weight: 800; font-size: 13.5px; color: #fbbf24; margin-bottom: 4px;">🟡 Stage 2: Questions 5–11</div>
                        <div style="font-size: 12.5px; color: #e2e8f0; font-weight: 500;">Technical implementation, algorithms, architecture, and engineering trade-offs.</div>
                    </div>
                    <div style="background: #200a0e; border: 1.5px solid #dc2626; border-radius: 10px; padding: 14px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);">
                        <div style="font-weight: 800; font-size: 13.5px; color: #f87171; margin-bottom: 4px;">🔴 Stage 3: Questions 12–15</div>
                        <div style="font-size: 12.5px; color: #e2e8f0; font-weight: 500;">Advanced production scenarios, debugging, edge cases, failure modes, and architectural decisions.</div>
                    </div>
                </div>
                <div style="font-size: 12.5px; color: #cbd5e1; font-style: italic; font-weight: 500;">
                    Questions are paced sequentially. Each answer is evaluated by AI before progressing to the next stage.
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Start 15-Question Interview Session", type="primary", use_container_width=True, key="btn_start_session"):
                with st.spinner("Preparing Question 1 (Foundational Stage)..."):
                    try:
                        st.session_state.session = init_interview_session(total_questions=15)
                        st.session_state.session["active"] = True
                        new_q = generate_interview_question(
                            client=client,
                            role=role,
                            difficulty=difficulty,
                            interview_type=interview_type,
                            previous_question="",
                            history=[],
                            question_number=1,
                            interviewer_personality=selected_personality
                        )
                        if new_q:
                            st.session_state.current_question = new_q
                            reset_candidate_answer_state()
                            reset_question_timer()
                            st.session_state.evaluation_result = None
                            st.session_state.evaluated_role = role
                            st.session_state.evaluated_difficulty = difficulty
                            st.session_state.evaluated_type = interview_type
                            st.session_state.evaluated_personality = selected_personality
                            st.rerun()
                        else:
                            st.error("No question was returned by the model. Please try again.")
                    except Exception as e:
                        st.error(f"Gemini error starting session: {e}")
        else:
            # Active session progress display
            st.divider()
            curr_idx = st.session_state.session.get("current_index", 1)
            tot_q = st.session_state.session.get("total_questions", 15)
            progress_ratio, progress_label = calculate_session_progress(curr_idx, tot_q)
            stage_name, _ = get_interview_stage(curr_idx)

            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 13px; font-weight: 800; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">Session Progress</span>
                    <span class="badge-pill badge-stage">{progress_label}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 13px; font-weight: 800; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">Curriculum Phase</span>
                    <span class="badge-pill badge-persona">{stage_name}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(progress_ratio)
    else:
        # Single Question Practice controls
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            generate_clicked = st.button(
                "🎯 Generate Interview Question",
                type="primary" if not st.session_state.current_question else "secondary",
                use_container_width=True
            )
        with col_btn2:
            st.markdown('<span class="regenerate-scope-marker" style="display:none;"></span>', unsafe_allow_html=True)
            regenerate_clicked = st.button(
                "🔄 Regenerate Question" if st.session_state.current_question else "🔄 Generate Another Question",
                key="btn_regenerate_question",
                use_container_width=True,
                disabled=not bool(st.session_state.current_question),
                help="Generate a fresh, distinct question testing a different topic."
            )

        # Handle Single Question Generation & Regeneration
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
                        history=history,
                        question_number=None,
                        interviewer_personality=selected_personality
                    )

                    if new_question:
                        if prev_q and prev_q not in history:
                            st.session_state.question_history.append(prev_q)

                        st.session_state.current_question = new_question
                        reset_candidate_answer_state()
                        reset_question_timer()
                        st.session_state.evaluation_result = None
                        st.session_state.evaluated_role = role
                        st.session_state.evaluated_difficulty = difficulty
                        st.session_state.evaluated_type = interview_type
                        st.session_state.evaluated_personality = selected_personality
                        st.rerun()
                    else:
                        st.error("No question was returned by the model. Please try again.")

                except Exception as e:
                    st.error(f"Gemini error generating question: {e}")

    # Display Question and Answer Input if question exists
    if st.session_state.current_question:
        st.divider()
        st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <span class="section-badge">3</span>
            <span style="font-size: 16px; font-weight: 700; color: #f1f5f9;">Active Interview Question</span>
        </div>
        """, unsafe_allow_html=True)

        # Clear Question Card
        with st.container(border=True):
            col_meta, col_card_btn = st.columns([3, 1])
            pers_details = get_personality_details(st.session_state.get("evaluated_personality", DEFAULT_PERSONALITY))
            pers_badge = pers_details["badge"]
            press_time = st.session_state.get("pressure_time_limit", 120)
            is_press = bool(st.session_state.get("pressure_mode_enabled"))

            with col_meta:
                if is_session_mode:
                    curr_idx = st.session_state.session.get("current_index", 1)
                    tot_q = st.session_state.session.get("total_questions", 15)
                    st.markdown(f"""
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 8px;">
                        <span class="badge-pill badge-role">🎯 {st.session_state.evaluated_role}</span>
                        <span class="badge-pill badge-difficulty">⚡ {st.session_state.evaluated_difficulty}</span>
                        <span class="badge-pill badge-type">📋 {st.session_state.evaluated_type}</span>
                        <span class="badge-pill badge-persona">👤 {pers_badge}</span>
                        <span class="badge-pill badge-stage">📊 Question {curr_idx} of {tot_q}</span>
                        {'<span class="badge-pill badge-pressure">⚡ Pressure Mode (' + str(press_time) + 's)</span>' if is_press else ''}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 8px;">
                        <span class="badge-pill badge-role">🎯 {st.session_state.evaluated_role}</span>
                        <span class="badge-pill badge-difficulty">⚡ {st.session_state.evaluated_difficulty}</span>
                        <span class="badge-pill badge-type">📋 {st.session_state.evaluated_type}</span>
                        <span class="badge-pill badge-persona">👤 {pers_badge}</span>
                        {'<span class="badge-pill badge-pressure">⚡ Pressure Mode (' + str(press_time) + 's)</span>' if is_press else ''}
                    </div>
                    """, unsafe_allow_html=True)

            with col_card_btn:
                st.markdown('<span class="regenerate-scope-marker" style="display:none;"></span>', unsafe_allow_html=True)
                if st.button("🔄 Regenerate", key="btn_card_regenerate", help="Generate a different question for this role and difficulty.", use_container_width=True):
                    with st.spinner("Gemini is preparing a different question..."):
                        try:
                            prev_q = st.session_state.get("current_question", "")
                            history = st.session_state.get("question_history", [])
                            q_num = st.session_state.session.get("current_index") if is_session_mode else None

                            new_question = generate_interview_question(
                                client=client,
                                role=st.session_state.evaluated_role,
                                difficulty=st.session_state.evaluated_difficulty,
                                interview_type=st.session_state.evaluated_type,
                                previous_question=prev_q,
                                history=history,
                                question_number=q_num,
                                interviewer_personality=st.session_state.get("evaluated_personality", DEFAULT_PERSONALITY)
                            )

                            if new_question:
                                if prev_q and prev_q not in history:
                                    st.session_state.question_history.append(prev_q)
                                st.session_state.current_question = new_question
                                reset_candidate_answer_state()
                                reset_question_timer()
                                st.session_state.evaluation_result = None
                                st.rerun()
                            else:
                                st.error("No question was returned. Please try again.")
                        except Exception as e:
                            st.error(f"Gemini error: {e}")

            st.markdown(f"""
            <div style="font-size: 18px; font-weight: 700; color: #ffffff; line-height: 1.5; padding: 4px 0;">
                {st.session_state.current_question}
            </div>
            """, unsafe_allow_html=True)

        # Pressure Mode Countdown Timer (active only when unevaluated)
        is_pressure_active = bool(st.session_state.get("pressure_mode_enabled", False))
        has_evaluated = bool(st.session_state.get("evaluation_result"))
        time_limit_sec = int(st.session_state.get("pressure_time_limit", 120))
        q_start_t = float(st.session_state.get("question_start_time", time.time()))

        is_expired = False
        if is_pressure_active and not has_evaluated:
            is_expired = is_timer_expired(q_start_t, time_limit_sec) or bool(st.session_state.get("timer_expired", False))
            if is_expired:
                st.session_state.timer_expired = True
                st.error("⏰ **Time's Up!** The time limit for this question has expired. Further edits are disabled, but your answer is preserved below. Click **🎯 Evaluate My Answer** to submit.")
            else:
                @st.fragment(run_every=1)
                def render_pressure_countdown(start_t: float, limit_s: int):
                    remaining_s = get_timer_remaining(start_t, limit_s)
                    disp_str = format_timer_display(remaining_s)
                    pct = max(0.0, min(1.0, remaining_s / max(1, limit_s)))
                    if remaining_s > 0:
                        ct1, ct2 = st.columns([1, 2])
                        with ct1:
                            if remaining_s <= 20:
                                st.error(f"⏳ **Time Remaining:** `{disp_str}`")
                            elif remaining_s <= 45:
                                st.warning(f"⏳ **Time Remaining:** `{disp_str}`")
                            else:
                                st.info(f"⏳ **Time Remaining:** `{disp_str}`")
                        with ct2:
                            st.progress(pct)
                    else:
                        st.session_state.timer_expired = True
                        st.rerun(scope="app")

                render_pressure_countdown(q_start_t, time_limit_sec)

        st.write("")
        st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <span class="section-badge">4</span>
            <span style="font-size: 16px; font-weight: 700; color: #f1f5f9;">Your Response</span>
        </div>
        """, unsafe_allow_html=True)

        # Candidate Answer Area (using decoupled widget key to prevent Streamlit state mutation error)
        widget_key = f"candidate_answer_widget_{st.session_state.get('answer_widget_id', 0)}"
        is_input_disabled = bool(is_pressure_active and is_expired and not has_evaluated)
        answer_text = st.text_area(
            "Type your answer:",
            value=st.session_state.get("candidate_answer", ""),
            height=180,
            placeholder="Type your structured answer here... Explain your thought process, technical reasoning, examples, and trade-offs.",
            key=widget_key,
            disabled=is_input_disabled
        )
        st.session_state.candidate_answer = answer_text

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
                            candidate_answer=user_answer,
                            interviewer_personality=st.session_state.get("evaluated_personality", DEFAULT_PERSONALITY)
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

                        # If in session mode, record this turn into session history
                        if is_session_mode:
                            record_session_turn(
                                st.session_state.session,
                                question=st.session_state.current_question,
                                answer=user_answer,
                                evaluation=eval_data,
                                role=st.session_state.evaluated_role,
                                difficulty=st.session_state.evaluated_difficulty,
                                interview_type=st.session_state.evaluated_type,
                                personality=st.session_state.get("evaluated_personality", DEFAULT_PERSONALITY),
                                pressure_mode=st.session_state.get("pressure_mode_enabled", False)
                            )

                    except json.JSONDecodeError as jde:
                        st.error(f"Failed to parse evaluation response: {jde}")
                    except Exception as e:
                        st.error(f"Gemini evaluation error: {e}")

    # Render Evaluation Results
    if st.session_state.get("evaluation_result"):
        eval_result = st.session_state.evaluation_result
        st.divider()
        st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 16px;">
            <span class="section-badge">5</span>
            <span style="font-size: 17px; font-weight: 700; color: #f1f5f9;">Evaluation & Detailed Feedback</span>
        </div>
        """, unsafe_allow_html=True)

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
            st.markdown("<div style='font-size: 13.5px; font-weight: 700; color: #f1f5f9; margin-bottom: 6px;'>Performance Calibration:</div>", unsafe_allow_html=True)
            st.progress(progress_val)
            if score_val >= 8.5:
                calib_html = """<div class="calib-banner calib-excellent">
                    <strong style="color: #34d399; font-size: 14px;">🌟 Excellent</strong> — <span style="color: #f1f5f9; font-size: 13.5px;">Strong, comprehensive, and interview-ready response!</span>
                </div>"""
            elif score_val >= 7.0:
                calib_html = """<div class="calib-banner calib-good">
                    <strong style="color: #38bdf8; font-size: 14px;">👍 Good</strong> — <span style="color: #f1f5f9; font-size: 13.5px;">Solid foundation with a few minor opportunities for improvement.</span>
                </div>"""
            elif score_val >= 5.0:
                calib_html = """<div class="calib-banner calib-average">
                    <strong style="color: #fbbf24; font-size: 14px;">⚠️ Average</strong> — <span style="color: #f1f5f9; font-size: 13.5px;">Partial coverage; requires more technical depth and structure.</span>
                </div>"""
            else:
                calib_html = """<div class="calib-banner calib-needs-improvement">
                    <strong style="color: #f87171; font-size: 14px;">🔻 Needs Improvement</strong> — <span style="color: #f1f5f9; font-size: 13.5px;">Substantial gaps or inaccuracies to address.</span>
                </div>"""
            st.markdown(calib_html, unsafe_allow_html=True)

        # Answer Classification Callout
        classification = eval_result.get("classification", "Partially Correct")
        if classification == "Correct":
            banner_html = """<div class="banner-classification banner-correct">
                <span class="banner-label">🟢 Assessment Classification: Correct</span>
                <span style="color: #94a3b8; margin: 0 4px;">—</span>
                <span style="color: #f1f5f9; font-size: 14px;">Factually accurate, technically sound, and addresses the question directly.</span>
            </div>"""
        elif classification == "Partially Correct":
            banner_html = """<div class="banner-classification banner-partially-correct">
                <span class="banner-label">🟡 Assessment Classification: Partially Correct</span>
                <span style="color: #94a3b8; margin: 0 4px;">—</span>
                <span style="color: #f1f5f9; font-size: 14px;">Demonstrates core understanding, with notable technical gaps or omissions.</span>
            </div>"""
        elif classification == "Incorrect":
            banner_html = """<div class="banner-classification banner-incorrect">
                <span class="banner-label">🔴 Assessment Classification: Incorrect</span>
                <span style="color: #94a3b8; margin: 0 4px;">—</span>
                <span style="color: #f1f5f9; font-size: 14px;">Contains fundamental technical errors, invalid premises, or misconceptions.</span>
            </div>"""
        elif classification == "Off-topic":
            banner_html = """<div class="banner-classification banner-off-topic">
                <span class="banner-label">🟠 Assessment Classification: Off-topic</span>
                <span style="color: #94a3b8; margin: 0 4px;">—</span>
                <span style="color: #f1f5f9; font-size: 14px;">Does not address the interview question asked.</span>
            </div>"""
        else:
            banner_html = f"""<div class="banner-classification banner-partially-correct">
                <span class="banner-label">📌 Assessment Classification: {classification}</span>
            </div>"""
        st.markdown(banner_html, unsafe_allow_html=True)

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
            with st.container(border=True):
                st.markdown("#### 🌟 Key Strengths")
                strengths = eval_result.get("strengths", [])
                if isinstance(strengths, list) and strengths:
                    for item in strengths:
                        st.markdown(f"- ✅ {item}")
                else:
                    st.write("No specific strengths recorded.")

        with col_weak:
            with st.container(border=True):
                st.markdown("#### ⚠️ Areas for Improvement")
                weaknesses = eval_result.get("weaknesses", [])
                if isinstance(weaknesses, list) and weaknesses:
                    for item in weaknesses:
                        st.markdown(f"- 🔸 {item}")
                else:
                    st.write("No significant weaknesses identified.")

        st.write("")

        # Suggestions
        with st.container(border=True):
            st.markdown("#### 🚀 Actionable Improvement Suggestions")
            suggestions = eval_result.get("suggestions", [])
            if isinstance(suggestions, list) and suggestions:
                for item in suggestions:
                    st.markdown(f"- 💡 {item}")
            else:
                st.write("Continue practicing with similar questions.")

        st.write("")

        # Smart Answer Correction & Technical Feedback
        st.markdown("#### 🎓 Smart Answer Correction & Detailed Diagnostics")

        col_corr, col_err = st.columns(2)
        with col_corr:
            with st.container(border=True):
                st.markdown("##### ✅ Correct Concepts in Your Answer")
                corr_points = eval_result.get("correct_concepts", [])
                if isinstance(corr_points, list) and corr_points:
                    for pt in corr_points:
                        st.markdown(f"- 🟢 {pt}")
                else:
                    st.caption("No clearly valid technical concepts identified in the response.")

        with col_err:
            with st.container(border=True):
                st.markdown("##### ❌ Technical Mistakes & Misconceptions")
                mistakes = eval_result.get("incorrect_statements", [])
                explanations = eval_result.get("mistake_explanations", [])
                if isinstance(mistakes, list) and mistakes:
                    for idx, m in enumerate(mistakes):
                        st.markdown(f"- 🔴 **Claim:** *\"{m}\"*")
                        if idx < len(explanations) and explanations[idx]:
                            st.markdown(f"  ↳ **Why it's wrong:** {explanations[idx]}")
                else:
                    st.caption("No explicit technical errors or false claims identified.")

        # Missing Important Concepts
        missing = eval_result.get("missing_concepts", [])
        if isinstance(missing, list) and missing:
            with st.container(border=True):
                st.markdown("##### ⚠️ Missing Important Concepts")
                for item in missing:
                    st.markdown(f"- 🔸 {item}")

        # Technically Correct Educational Explanation
        corr_exp = eval_result.get("correct_explanation", "")
        if corr_exp:
            st.markdown(f"""
            <div class="technically-correct-panel">
                <div style="color: #38bdf8; font-weight: 800; font-size: 14.5px; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">📖</span> Technically Correct Explanation
                </div>
                <div style="color: #F9FAFB; font-size: 14.5px; line-height: 1.6;">
                    {corr_exp}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Ideal Interview-Ready Answer (Expandable Section)
        ideal_ans = eval_result.get("ideal_answer", "")
        if ideal_ans:
            with st.expander("💡 View Ideal Answer", expanded=False):
                st.markdown(f"""
                <div style="color: #F9FAFB; font-size: 14.5px; line-height: 1.6; padding: 4px 0;">
                    {ideal_ans}
                </div>
                """, unsafe_allow_html=True)

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

        # Next Question Button in Session Mode
        if is_session_mode and not st.session_state.session.get("completed"):
            st.divider()
            curr_idx = st.session_state.session.get("current_index", 1)
            tot_q = st.session_state.session.get("total_questions", 15)
            is_last = (curr_idx >= tot_q)
            next_btn_label = "🏁 Complete Interview Session" if is_last else f"Next Question ({curr_idx + 1} of {tot_q}) ➡️"

            if st.button(next_btn_label, type="primary", use_container_width=True, key="btn_next_session_q"):
                user_answer = st.session_state.get("candidate_answer", "").strip()
                eval_res = st.session_state.get("evaluation_result")
                if not can_advance_session(user_answer, eval_res):
                    st.warning("⚠️ Please submit and evaluate your answer before proceeding.")
                else:
                    record_session_turn(
                        st.session_state.session,
                        question=st.session_state.current_question,
                        answer=user_answer,
                        evaluation=eval_res,
                        role=st.session_state.evaluated_role,
                        difficulty=st.session_state.evaluated_difficulty,
                        interview_type=st.session_state.evaluated_type,
                        personality=st.session_state.get("evaluated_personality", DEFAULT_PERSONALITY),
                        pressure_mode=st.session_state.get("pressure_mode_enabled", False)
                    )
                    advance_session(st.session_state.session)
                    if st.session_state.session.get("completed"):
                        st.session_state.current_question = ""
                        reset_candidate_answer_state()
                        reset_question_timer()
                        st.session_state.evaluation_result = None
                        st.rerun()
                    else:
                        next_idx = st.session_state.session.get("current_index", 1)
                        with st.spinner(f"Preparing Question {next_idx} of {tot_q}..."):
                            try:
                                prev_q = st.session_state.get("current_question", "")
                                history = st.session_state.get("question_history", [])
                                if prev_q and prev_q not in history:
                                    st.session_state.question_history.append(prev_q)

                                next_q = generate_interview_question(
                                    client=client,
                                    role=st.session_state.evaluated_role,
                                    difficulty=st.session_state.evaluated_difficulty,
                                    interview_type=st.session_state.evaluated_type,
                                    previous_question=prev_q,
                                    history=st.session_state.question_history,
                                    question_number=next_idx,
                                    interviewer_personality=st.session_state.get("evaluated_personality", DEFAULT_PERSONALITY)
                                )
                                if next_q:
                                    st.session_state.current_question = next_q
                                    reset_candidate_answer_state()
                                    reset_question_timer()
                                    st.session_state.evaluation_result = None
                                    st.rerun()
                                else:
                                    st.error("No question was returned. Please try again.")
                            except Exception as e:
                                st.error(f"Gemini error: {e}")

    elif not st.session_state.get("current_question"):
        st.info("💡 Select your interview preferences above and start practicing!")


if __name__ == "__main__":
    main()
