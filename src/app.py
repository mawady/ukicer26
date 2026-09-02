import os
from pathlib import Path
import pandas as pd
import streamlit as st

from models import ModuleInput, ILO
from rag import KnowledgeEngine
from generator import SuggestionEngine
from verifier import ConsistencyVerifier

# Ensure knowledge directories exist on startup
KNOWLEDGE_DIRS = [
    Path("knowledge/university"),
    Path("knowledge/sector"),
]

for d in KNOWLEDGE_DIRS:
    d.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="AI Module Spec & Quiz Generator", layout="wide")
st.title("AI Module Specification & Quiz Generator")

if "spec" not in st.session_state:
    st.session_state.spec = None
if "checks" not in st.session_state:
    st.session_state.checks = []
if "context" not in st.session_state:
    st.session_state.context = []
if "confirmed" not in st.session_state:
    st.session_state.confirmed = False

with st.sidebar:
    st.header("Settings")
    model_name = st.selectbox(
        "Choose a Model",
        [
            "gemma4:e2b",
            "gemma4:e4b",
            "gemma4:12b",
            "gemma4:26b",
            "gemma4:31b"
        ],
        index=0
    )

    if st.button("Index Local Knowledge Folders"):
        engine = KnowledgeEngine()
        deleted_count = engine.clear_cache()
        n1 = engine.index_directory("knowledge/university", "University")
        n2 = engine.index_directory("knowledge/sector", "Sector")
        if n1 + n2 == 0:
            st.warning("Folders are empty! Place text/docs in 'knowledge/' or rely on model memory.")
        else:
            st.success(f"Cleared {deleted_count} old index file(s) and indexed {n1 + n2} high-quality section chunk(s).")

st.header("1. Quick Module Setup")

col1, col2, col3 = st.columns(3)
with col1:
    title = st.text_input("Module Title", "Introduction to Artificial Intelligence")
    code = st.text_input("Module Code", "CS101")
with col2:
    cats = st.number_input("CATS Credits", value=20.0)
    hours_per_cats = st.number_input("Hours per CATS", value=10.0)
with col3:
    level = st.selectbox("Academic Level", ["SCQF Level 8", "SCQF Level 9", "SCQF Level 10"])
    ects = cats / 2.0  # Auto-calculated ECTS

ilos_text = st.text_area(
    "Intended Learning Outcomes (one per line)",
    "ILO1: Explain fundamental AI concepts and methods.\n"
    "ILO2: Apply AI algorithms to practical problems.\n"
    "ILO3: Critically evaluate AI techniques and their limitations."
)


def parse_ilos(text):
    return [
        ILO(code=f"ILO{i}", description=line.split(":", 1)[-1].strip())
        for i, line in enumerate(text.splitlines(), 1) if line.strip()
    ]


module_input = ModuleInput(
    module_title=title, module_code=code, level=level,
    cats=cats, ects=ects, ilos=parse_ilos(ilos_text)
)

if st.button("Generate Specification & Quizzes", type="primary"):
    st.session_state.confirmed = False
    with st.spinner("Generating specification..."):
        try:
            engine = KnowledgeEngine()
            context = engine.retrieve(f"Design {module_input.level} module titled '{module_input.module_title}'")
            st.session_state.context = context

            generator = SuggestionEngine(model_name)
            verifier = ConsistencyVerifier(hours_per_cats)

            spec = generator.generate(module_input, context)
            checks = verifier.verify(module_input, spec)

            st.session_state.spec = spec
            st.session_state.checks = checks
            st.rerun()
        except Exception as e:
            st.error(f"Generation failed: {str(e)}")

# Display section: handles both empty state and populated state
if st.session_state.spec:
    spec = st.session_state.spec
    checks = st.session_state.checks
    failed_checks = ConsistencyVerifier.failed_checks(checks)
    all_passed = len(failed_checks) == 0

    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Syllabus & Quizzes", "Assessments", "Checks & Review"])

    with tab1:
        st.subheader("Overview")
        st.write(spec.overview)
        st.subheader("Rationale")
        st.write(spec.rationale)

    with tab2:
        st.subheader("Weekly Syllabus & Generated Quizzes")
        for week in spec.syllabus:
            with st.expander(f"Week {week.week}: {week.topic}"):
                st.write("**Mapped ILOs:**", ", ".join(week.ilo_mapping))
                st.write("**Activities:**", ", ".join(week.activities))
                st.write("**Scheduled Hours:**", week.scheduled_learning_hours, "| **Independent Hours:**", week.independent_study_hours)

                if week.quiz:
                    st.divider()
                    st.markdown("#### Weekly Practice Quiz")
                    for q_idx, q in enumerate(week.quiz, 1):
                        st.write(f"**Q{q_idx}: {q.question}**")
                        st.radio(f"Select option for Q{q_idx}", q.options, key=f"w{week.week}_q{q_idx}")
                        st.caption(f"Correct Answer: {q.correct_answer}")

    with tab3:
        for a in spec.assessments:
            st.markdown(f"### {a.title} ({a.weighting}%, {a.type.upper()})")
            st.write("**Purpose:**", a.purpose)
            st.write(a.description)
            st.json(a.rubric)

    with tab4:
        st.subheader("Automated Consistency Checks")

        formatted_checks = [
            {
                "Check Name": c.get("name"),
                "Status": "PASS" if c.get("passed") else "FAIL",
                "Details": c.get("message")
            }
            for c in checks
        ]
        st.dataframe(pd.DataFrame(formatted_checks), width="stretch")

        st.divider()
        st.subheader("Specification Review & Re-generation")

        if all_passed:
            st.success("All automated checks passed!")
            if not st.session_state.confirmed:
                if st.button("Confirm & Accept Specification", type="primary"):
                    st.session_state.confirmed = True
                    st.rerun()
            else:
                st.balloons()
                st.success("Specification locked and confirmed by user!")
        else:
            st.warning("Some checks failed. You can re-generate with optional feedback to address them.")

        user_feedback = st.text_area(
            "Feedback / Instructions for Re-generation (Optional):",
            placeholder="e.g. Adjust independent study hours or add more details to assessment rubrics."
        )

        if st.button("Re-generate Specification"):
            st.session_state.confirmed = False
            with st.spinner("Re-generating specification with your input..."):
                try:
                    generator = SuggestionEngine(model_name)
                    verifier = ConsistencyVerifier(hours_per_cats)

                    new_spec = generator.generate(
                        module_input,
                        st.session_state.context,
                        reviewer_feedback=user_feedback,
                        failed_checks=failed_checks
                    )
                    new_checks = verifier.verify(module_input, new_spec)

                    st.session_state.spec = new_spec
                    st.session_state.checks = new_checks
                    st.rerun()
                except Exception as e:
                    st.error(f"Re-generation failed: {str(e)}")

    if st.session_state.context:
        with st.expander("📚 Retrieved Local Knowledge Context", expanded=False):
            st.caption("Clean context sections extracted from your indexed knowledge base (noise filtered):")

            for idx, item in enumerate(st.session_state.context, 1):
                source_level = item.get("source_level", "General")
                source_file = item.get("source", "Unknown Source")
                section = item.get("section", "Section Overview")
                score = item.get("score", None)
                content = item.get("content", "")

                score_str = f" | 🎯 *Match Score: {score}*" if score is not None else ""
                st.markdown(f"**{idx}. [{source_level}] `{source_file}`** — 📌 **Section:** `{section}`{score_str}")
                st.info(content)
else:
    st.info("Configure your module details above and click 'Generate Specification & Quizzes' to build the interface.")