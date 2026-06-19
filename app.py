import os
import json
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq
from dotenv import load_dotenv
from fpdf import FPDF

# ---------- Setup ----------
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

st.set_page_config(page_title="SAP S/4HANA Fit-Gap Analyzer", layout="wide")

# Dark-leaning styling
st.markdown(
    """
    <style>
    .main { background-color: #020617; color: #e5e7eb; }
    .stButton>button {
        background-color: #1d4ed8;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.4rem 0.8rem;
    }
    .stDownloadButton>button {
        background-color: #0f766e;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.4rem 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "current_analysis" not in st.session_state:
    st.session_state.current_analysis = None
if "current_name" not in st.session_state:
    st.session_state.current_name = "My Fit-Gap Analysis"
if "saved_analyses" not in st.session_state:
    st.session_state.saved_analyses = {}


# ---------- Helper: call Groq and get structured JSON ----------
def analyze_fit_gap(text: str, module: str, temperature: float, max_tokens: int):
    system_prompt = (
        "You are an SAP S/4HANA Fit-Gap expert with deep knowledge of "
        "SAP Best Practices, WRICEF, integrations, and data migration.\n\n"
        "Your job is to analyze the user's workshop notes, AS-IS processes, "
        "or requirements and return ONLY valid JSON with the following structure:\n\n"
        "{\n"
        '  "fit_gap": [\n'
        '    {\n'
        '      "process_step": "string",\n'
        '      "fit_or_gap": "Fit" or "Gap",\n'
        '      "sap_scope_item": "string or empty",\n'
        '      "module": "FI/CO/MM/SD/PP/QM/PM/EWM/TM/etc.",\n'
        '      "notes": "short explanation"\n'
        "    }\n"
        "  ],\n"
        '  "wricef": [\n'
        '    {\n'
        '      "id": "W001",\n'
        '      "type": "Workflow/Report/Interface/Conversion/Enhancement/Form",\n'
        '      "description": "short description",\n'
        '      "complexity": "Low/Medium/High",\n'
        '      "module": "string"\n'
        "    }\n"
        "  ],\n"
        '  "requirements": ["requirement 1", "requirement 2"],\n'
        '  "user_stories": [\n'
        '    {\n'
        '      "story": "As a <role>, I want <goal> so that <benefit>.",\n'
        '      "acceptance_criteria": ["AC1", "AC2", "AC3"]\n'
        "    }\n"
        "  ],\n"
        '  "integration_impacts": [\n'
        '    {\n'
        '      "system": "Ariba/SuccessFactors/Legacy/etc.",\n'
        '      "impact": "short description",\n'
        '      "type": "API/IDoc/BAPI/CPI/BTP"\n'
        "    }\n"
        "  ],\n"
        '  "data_migration": [\n'
        '    {\n'
        '      "object": "Business object name",\n'
        '      "fields_required": ["Field1", "Field2"],\n'
        '      "risks": "short description"\n'
        "    }\n"
        "  ],\n"
        '  "risks": [\n'
        '    {\n'
        '      "risk": "short description",\n'
        '      "impact": "Low/Medium/High",\n'
        '      "likelihood": "Low/Medium/High",\n'
        '      "mitigation": "short mitigation plan"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- For each relevant process step, classify as 'Fit' or 'Gap'.\n"
        "- If 'Gap', propose WRICEF type.\n"
        "- Map to SAP Best Practice scope items where possible.\n"
        "- Identify impacted SAP modules.\n"
        "- Generate clear, testable requirements.\n"
        "- Generate user stories with 3–5 acceptance criteria each.\n"
        "- Identify integration impacts.\n"
        "- Identify data migration objects and key fields.\n"
        "- Identify key risks with impact, likelihood, and mitigation.\n"
        "- Return ONLY JSON. No commentary, no markdown.\n"
    )

    user_prompt = (
        f"Primary SAP module: {module}\n\n"
        "Workshop notes / requirements:\n"
        f"{text}"
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )

    raw = response.choices[0].message.content

    # Clean whitespace
    raw_stripped = raw.strip()

    # Try direct JSON parse first
    try:
        return json.loads(raw_stripped)
    except json.JSONDecodeError:
        pass

    # Fallback: extract first {...} JSON block
    start = raw_stripped.find("{")
    end = raw_stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = raw_stripped[start:end+1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # If still failing, raise error so Streamlit shows it
    raise json.JSONDecodeError(
        "Could not parse model output as JSON",
        raw_stripped,
        0
    )



# ---------- Helper: PDF export ----------
def generate_pdf(analysis: dict, name: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "SAP S/4HANA Fit-Gap Analysis", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.ln(4)
    pdf.cell(0, 8, f"Analysis Name: {name}", ln=True)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)

    def add_section(title, lines):
        pdf.ln(6)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, title, ln=True)
        pdf.set_font("Arial", "", 11)
        if isinstance(lines, str):
            pdf.multi_cell(0, 6, lines)
        else:
            for line in lines:
                pdf.multi_cell(0, 6, f"- {line}")
        pdf.ln(2)

    # Fit-Gap
    fit_gap = analysis.get("fit_gap", [])
    fg_lines = [
        f"{item.get('process_step','')} "
        f"[{item.get('fit_or_gap','')}] "
        f"Scope: {item.get('sap_scope_item','')} "
        f"Module: {item.get('module','')} "
        f"Notes: {item.get('notes','')}"
        for item in fit_gap
    ]
    add_section("Fit-Gap Matrix", fg_lines)

    # WRICEF
    wricef = analysis.get("wricef", [])
    wr_lines = [
        f"{w.get('id','')} - {w.get('type','')} - {w.get('description','')} "
        f"(Module: {w.get('module','')}, Complexity: {w.get('complexity','')})"
        for w in wricef
    ]
    add_section("WRICEF Register", wr_lines)

    # Requirements
    add_section("Requirements", analysis.get("requirements", []))

    # User Stories
    us = analysis.get("user_stories", [])
    us_lines = []
    for u in us:
        us_lines.append(u.get("story", ""))
        for ac in u.get("acceptance_criteria", []):
            us_lines.append(f"  * {ac}")
    add_section("User Stories", us_lines)

    # Integration Impacts
    ii = analysis.get("integration_impacts", [])
    ii_lines = [
        f"{i.get('system','')} - {i.get('type','')}: {i.get('impact','')}"
        for i in ii
    ]
    add_section("Integration Impacts", ii_lines)

    # Data Migration
    dm = analysis.get("data_migration", [])
    dm_lines = [
        f"{d.get('object','')} - Fields: {', '.join(d.get('fields_required',[]))} "
        f"Risks: {d.get('risks','')}"
        for d in dm
    ]
    add_section("Data Migration Objects", dm_lines)

    # Risks
    risks = analysis.get("risks", [])
    r_lines = [
        f"{r.get('risk','')} "
        f"[Impact: {r.get('impact','')}, Likelihood: {r.get('likelihood','')}] "
        f"Mitigation: {r.get('mitigation','')}"
        for r in risks
    ]
    add_section("Risks & Mitigations", r_lines)

    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    return pdf_bytes


# ---------- Sidebar ----------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Analyzer", "Saved Analyses"])

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Context:** SAP S/4HANA Fit-Gap, WRICEF, integrations, data migration."
)


# ---------- PAGE: Analyzer ----------
if page == "Analyzer":
    st.title("🧩 SAP S/4HANA Fit-Gap Analyzer")

    st.subheader("Input")
    col_top1, col_top2 = st.columns([2, 1])

    with col_top1:
        workshop_text = st.text_area(
            "Paste workshop notes / AS-IS / requirements:",
            height=220,
            placeholder="Example: During the MM procurement workshop, users described..."
        )

    with col_top2:
        module = st.selectbox(
            "Primary SAP module",
            ["MM", "SD", "FI", "CO", "PP", "QM", "PM", "EWM", "TM", "Cross-Module"],
            index=0,
        )
        temperature = st.slider("Creativity", 0.0, 1.0, 0.3)
        max_tokens = st.slider("Max Tokens", 500, 2500, 1400)
        analysis_name = st.text_input(
            "Analysis Name",
            value=st.session_state.current_name,
        )

    analyze = st.button("🔍 Analyze Fit-Gap")

    if analyze:
        if not api_key:
            st.error("Missing GROQ_API_KEY in your .env file.")
        elif not workshop_text.strip():
            st.error("Please paste some workshop notes or requirements.")
        else:
            with st.spinner("Analyzing Fit-Gap and generating structured output..."):
                try:
                    analysis = analyze_fit_gap(
                        workshop_text,
                        module,
                        temperature,
                        max_tokens,
                    )
                    st.session_state.current_analysis = analysis
                    st.session_state.current_name = analysis_name
                    st.success("Fit-Gap analysis generated!")

                except json.JSONDecodeError:
                    st.error("Model returned invalid JSON. Try again with lower creativity.")
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.session_state.current_analysis:
        analysis = st.session_state.current_analysis

        tabs = st.tabs(
            [
                "Fit-Gap Matrix",
                "WRICEF Register",
                "Requirements",
                "User Stories",
                "Integration Impacts",
                "Data Migration",
                "Risks",
                "Export",
            ]
        )

        # Fit-Gap
        with tabs[0]:
            st.subheader("Fit-Gap Matrix")
            fg = analysis.get("fit_gap", [])
            if fg:
                fg_df = pd.DataFrame(fg)
                st.dataframe(fg_df, use_container_width=True)
            else:
                st.info("No fit-gap items returned.")

        # WRICEF
        with tabs[1]:
            st.subheader("WRICEF Register")
            wr = analysis.get("wricef", [])
            if wr:
                wr_df = pd.DataFrame(wr)
                st.dataframe(wr_df, use_container_width=True)
            else:
                st.info("No WRICEF items returned.")

        # Requirements
        with tabs[2]:
            st.subheader("Requirements")
            reqs = analysis.get("requirements", [])
            if reqs:
                for r in reqs:
                    st.markdown(f"- {r}")
            else:
                st.info("No requirements returned.")

        # User Stories
        with tabs[3]:
            st.subheader("User Stories")
            us = analysis.get("user_stories", [])
            if us:
                for i, u in enumerate(us, start=1):
                    with st.expander(f"User Story {i}", expanded=(i == 1)):
                        st.markdown(f"**Story:** {u.get('story','')}")
                        st.markdown("**Acceptance Criteria:**")
                        for ac in u.get("acceptance_criteria", []):
                            st.markdown(f"- {ac}")
            else:
                st.info("No user stories returned.")

        # Integration Impacts
        with tabs[4]:
            st.subheader("Integration Impacts")
            ii = analysis.get("integration_impacts", [])
            if ii:
                ii_df = pd.DataFrame(ii)
                st.dataframe(ii_df, use_container_width=True)
            else:
                st.info("No integration impacts returned.")

        # Data Migration
        with tabs[5]:
            st.subheader("Data Migration Objects")
            dm = analysis.get("data_migration", [])
            if dm:
                dm_df = pd.DataFrame(dm)
                st.dataframe(dm_df, use_container_width=True)
            else:
                st.info("No data migration objects returned.")

        # Risks
        with tabs[6]:
            st.subheader("Risks & Dependencies")
            risks = analysis.get("risks", [])
            if risks:
                r_df = pd.DataFrame(risks)
                st.dataframe(r_df, use_container_width=True)
            else:
                st.info("No risks returned.")

        # Export
        with tabs[7]:
            st.subheader("Export & Save")

            col_a, col_b = st.columns([1, 1])

            with col_a:
                if st.button("💾 Save Analysis"):
                    st.session_state.saved_analyses[analysis_name] = analysis
                    st.success(f"Analysis '{analysis_name}' saved in session.")

            with col_b:
                pdf_bytes = generate_pdf(analysis, analysis_name)
                st.download_button(
                    "📥 Download PDF",
                    data=pdf_bytes,
                    file_name=f"{analysis_name.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                )

            json_bytes = json.dumps(analysis, indent=2).encode("utf-8")
            st.download_button(
                "📥 Download JSON",
                data=json_bytes,
                file_name=f"{analysis_name.replace(' ', '_')}.json",
                mime="application/json",
            )


# ---------- PAGE: Saved Analyses ----------
elif page == "Saved Analyses":
    st.title("📂 Saved Fit-Gap Analyses")

    if not st.session_state.saved_analyses:
        st.info("No saved analyses yet. Run one from the Analyzer page and save it.")
    else:
        names = list(st.session_state.saved_analyses.keys())
        selected = st.selectbox("Select an analysis:", names)

        if selected:
            analysis = st.session_state.saved_analyses[selected]

            tabs = st.tabs(
                [
                    "Fit-Gap Matrix",
                    "WRICEF Register",
                    "Requirements",
                    "User Stories",
                    "Integration Impacts",
                    "Data Migration",
                    "Risks",
                    "Export",
                ]
            )

            # Fit-Gap
            with tabs[0]:
                st.subheader(f"Fit-Gap Matrix – {selected}")
                fg = analysis.get("fit_gap", [])
                if fg:
                    st.dataframe(pd.DataFrame(fg), use_container_width=True)
                else:
                    st.info("No fit-gap items.")

            # WRICEF
            with tabs[1]:
                st.subheader("WRICEF Register")
                wr = analysis.get("wricef", [])
                if wr:
                    st.dataframe(pd.DataFrame(wr), use_container_width=True)
                else:
                    st.info("No WRICEF items.")

            # Requirements
            with tabs[2]:
                st.subheader("Requirements")
                reqs = analysis.get("requirements", [])
                if reqs:
                    for r in reqs:
                        st.markdown(f"- {r}")
                else:
                    st.info("No requirements.")

            # User Stories
            with tabs[3]:
                st.subheader("User Stories")
                us = analysis.get("user_stories", [])
                if us:
                    for i, u in enumerate(us, start=1):
                        with st.expander(f"User Story {i}", expanded=(i == 1)):
                            st.markdown(f"**Story:** {u.get('story','')}")
                            st.markdown("**Acceptance Criteria:**")
                            for ac in u.get("acceptance_criteria", []):
                                st.markdown(f"- {ac}")
                else:
                    st.info("No user stories.")

            # Integration Impacts
            with tabs[4]:
                st.subheader("Integration Impacts")
                ii = analysis.get("integration_impacts", [])
                if ii:
                    st.dataframe(pd.DataFrame(ii), use_container_width=True)
                else:
                    st.info("No integration impacts.")

            # Data Migration
            with tabs[5]:
                st.subheader("Data Migration Objects")
                dm = analysis.get("data_migration", [])
                if dm:
                    st.dataframe(pd.DataFrame(dm), use_container_width=True)
                else:
                    st.info("No data migration objects.")

            # Risks
            with tabs[6]:
                st.subheader("Risks & Dependencies")
                risks = analysis.get("risks", [])
                if risks:
                    st.dataframe(pd.DataFrame(risks), use_container_width=True)
                else:
                    st.info("No risks.")

            # Export
            with tabs[7]:
                st.subheader("Export")

                col1, col2 = st.columns([1, 1])

                with col1:
                    pdf_bytes = generate_pdf(analysis, selected)
                    st.download_button(
                        "📥 Download PDF",
                        data=pdf_bytes,
                        file_name=f"{selected.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                    )

                with col2:
                    json_bytes = json.dumps(analysis, indent=2).encode("utf-8")
                    st.download_button(
                        "📥 Download JSON",
                        data=json_bytes,
                        file_name=f"{selected.replace(' ', '_')}.json",
                        mime="application/json",
                    )
