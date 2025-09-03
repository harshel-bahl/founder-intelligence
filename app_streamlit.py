#!/usr/bin/env python3
"""
Founder Intelligence Streamlit App
UI-only application that uses the agent module for business logic.
"""

import os
import time
import pandas as pd
import streamlit as st
from agent import (
    sanitize_urls, 
    score_one_profile, 
    validate_apis,
    env_int
)

    

st.set_page_config(page_title="Founder Intelligence", page_icon="🧠", layout="wide")

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧠 Founder Intelligence")



with st.sidebar:
    st.header("Configuration")
    serp_key = st.text_input("SerpAPI Key", value=os.environ.get("SERPAPI_API_KEY", ""), type="password")
    openai_key = st.text_input("OpenAI API Key", value=os.environ.get("OPENAI_API_KEY", ""), type="password")
    model_name = st.text_input("OpenAI Model", value=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
    temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.1)
    max_results_per_query = st.number_input("Results per query", 2, 10, 5, 1)
    per_profile_queries = st.number_input("Search passes", 1, 5, 2, 1)
    linkedin_li_at = st.text_input("LinkedIn cookie (optional)", value=os.environ.get("LINKEDIN_LI_AT", ""), type="password")
    
    if serp_key: os.environ["SERPAPI_API_KEY"] = serp_key
    if openai_key: os.environ["OPENAI_API_KEY"] = openai_key
    os.environ["OPENAI_MODEL"] = model_name
    os.environ["OPENAI_TEMPERATURE"] = str(temperature)
    os.environ["RESULTS_PER_QUERY"] = str(int(max_results_per_query))
    os.environ["PER_PROFILE_QUERIES"] = str(int(per_profile_queries))
    if linkedin_li_at: os.environ["LINKEDIN_LI_AT"] = linkedin_li_at


st.markdown("""
<div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin: 16px 0;">

**Paste LinkedIn URLs below to analyze founder potential.**

The system starts by extracting profile content from LinkedIn, then discovers additional personal sources like blogs, Substack, and Medium pages to build a comprehensive picture.

Next, it searches for entrepreneurial evidence including founder mentions, funding news, and accelerator participation using targeted queries like `{name} founder startup`, `{name} YC accelerator`, and `{name} blog newsletter`.

Finally, an AI model analyzes all collected evidence to score **Entrepreneurial Experience (0-4)** based on founder history and funding success, plus a **Contrarian Multiplier (1.0-2.0)** based on unconventional career choices and risk-taking behavior.

</div>
""", unsafe_allow_html=True)



default_urls = "https://www.linkedin.com/in/example-person-12345/"


col1, col2 = st.columns([4, 1])
with col1:
    urls_text = st.text_area("LinkedIn URLs", value=default_urls, height=140)
with col2:
    st.write("")
    st.write("")
    run = st.button("Run Scoring", type="primary", use_container_width=True)



def create_summary_row(rep: dict) -> dict:
    """Create a summary row for the results dataframe."""
    return {
        "profile_url": rep["profile_url"],
        "name_guess": rep["name_guess"],
        "entrepreneurial_score": rep["entrepreneurial_score"],
        "contrarian_multiplier": rep["contrarian_multiplier"],
        "final_score": rep["final_score"],
        "summary": rep["summary"][:200] + ("..." if len(rep["summary"]) > 200 else ""),
        "confidence": rep["confidence"]
    }

def render_analysis_summary(results: list):
    """Render the analysis summary section."""
    st.subheader("Analysis Summary")
    for rep in results:
        with st.expander(f"{rep['name_guess']} — Final: {rep['final_score']} (E={rep['entrepreneurial_score']}, Cx={rep['contrarian_multiplier']})"):
            st.markdown(f"**Profile:** [{rep['profile_url']}]({rep['profile_url']})")
            st.markdown(f"**Confidence:** {rep['confidence']}")
            st.markdown("**Summary**")
            st.write(rep["summary"])
            
            if rep.get("source_confidence_assessments"):
                st.markdown("**Source Confidence**")
                high_conf_count = len([s for s in rep.get("source_confidence_assessments", []) if s.get("confidence", 0) >= 0.5])
                total_sources = len(rep.get("source_confidence_assessments", []))
                st.write(f"📊 {high_conf_count}/{total_sources} sources used (confidence ≥ 50%)")
                
                with st.expander("View Source Confidence Details"):
                    for assessment in rep.get("source_confidence_assessments", []):
                        conf = assessment.get("confidence", 0)
                        source = assessment.get("source", "Unknown source")
                        reasoning = assessment.get("reasoning", "No reasoning provided")
                        
                        if conf >= 0.8:
                            emoji = "✅"
                            color = "green"
                        elif conf >= 0.5:
                            emoji = "⚠️"
                            color = "orange"
                        else:
                            emoji = "❌"
                            color = "red"
                        
                        st.markdown(f"{emoji} **{conf:.1f}** - {source[:100]}...")
                        st.caption(f"Reasoning: {reasoning}")
            
            st.markdown("**Entrepreneurial Evidence**")
            for point in rep.get("entrepreneurial_evidence_points", []):
                st.write(f"• {point}")
            
            st.markdown("**Contrarian Evidence**")
            for point in rep.get("contrarian_evidence_points", []):
                st.write(f"• {point}")

def render_detailed_reports(results: list):
    """Render the detailed reports section."""
    st.subheader("Detailed Reports")
    for rep in results:
        with st.expander(f"🔍 {rep['name_guess']} - Technical Details"):
            st.markdown(f"**Profile:** [{rep['profile_url']}]({rep['profile_url']})")
            
            if rep.get("source_confidence_assessments"):
                st.markdown("**Source Confidence Assessments**")
                confidence_df = pd.DataFrame(rep["source_confidence_assessments"])
                if not confidence_df.empty:
                    st.dataframe(confidence_df, use_container_width=True, hide_index=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        avg_conf = confidence_df['confidence'].mean()
                        st.metric("Average Confidence", f"{avg_conf:.2f}")
                    with col2:
                        high_conf = len(confidence_df[confidence_df['confidence'] >= 0.5])
                        st.metric("High Confidence Sources", high_conf)
                    with col3:
                        total = len(confidence_df)
                        st.metric("Total Sources", total)
            
            st.markdown("**Page Corpus**")
            if rep["pages"]:
                st.dataframe(pd.DataFrame(rep["pages"]), use_container_width=True, hide_index=True)
            else:
                st.caption("No pages parsed.")
            
            st.markdown("**Search Evidence**")
            if rep["search_evidence"]:
                st.dataframe(pd.DataFrame(rep["search_evidence"]), use_container_width=True, hide_index=True)
            else:
                st.caption("No search evidence found.")
            
            st.markdown("**Traversal Log**")
            st.dataframe(pd.DataFrame(rep["traversal_log"]), use_container_width=True, hide_index=True)



if run:
    if not serp_key:
        st.error("Please provide a SerpAPI key in the sidebar.")
        st.stop()
    if not openai_key:
        st.error("Please provide an OpenAI API key in the sidebar.")
        st.stop()
    
    urls = sanitize_urls(urls_text)
    if not urls:
        st.warning("Please paste at least one LinkedIn URL.")
        st.stop()
    
    api_valid, error_msg = validate_apis()
    if not api_valid:
        st.error(error_msg)
        st.stop()
    
    results = []
    progress = st.progress(0.0)
    status = st.empty()
    
    for i, url in enumerate(urls):
        status.write(f"Analyzing: {url}")
        try:
            rep = score_one_profile(
                url, 
                env_int("RESULTS_PER_QUERY", 5), 
                env_int("PER_PROFILE_QUERIES", 2)
            )
            results.append(rep)
        except Exception as e:
            st.error(f"Error scoring {url}: {e}")
        
        progress.progress((i + 1) / len(urls))
        time.sleep(0.1)
    
    status.empty()
    progress.empty()
    
    if results:
        st.success("Scoring complete.")
        
        df = pd.DataFrame([create_summary_row(r) for r in results])
        
        tab1, tab2 = st.tabs(["Summary & Analysis", "Detailed Reports"])
        
        with tab1:
            st.subheader("Summary")
            st.dataframe(df, use_container_width=True)
            
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download CSV", 
                data=csv_bytes, 
                file_name="founder_scores.csv", 
                mime="text/csv"
            )
            
            render_analysis_summary(results)
        
        with tab2:
            render_detailed_reports(results)



