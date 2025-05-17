import streamlit as st
import json
from plan import (
    generate_bio_plan,
    explain_personalized_steps,
)  # Replace with actual filename

st.set_page_config(page_title="BioAPI Planner", layout="wide")

st.title("🧬 Biomedical API Planner UI")

# Input from user
user_query = st.text_input(
    "🔍 Enter your biomedical query",
    placeholder="e.g., Can the KRAS G12D mutation be targeted with any known inhibitors?",
)

if st.button("Generate Plan") and user_query:
    with st.spinner("Generating API plan..."):
        plan = generate_bio_plan(user_query)

        if plan:
            st.subheader("🗂️ Structured API Plan (JSON)")
            st.code(json.dumps(plan, indent=2), language="json")

            st.subheader("📘 Step-by-Step Explanation")
            explanation = explain_personalized_steps(plan)
            st.markdown(explanation)
        else:
            st.error("Failed to generate or parse the plan. Check console logs.")
