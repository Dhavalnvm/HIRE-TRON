"""
HIRE-TRON-X: Multi-Agent AI Recruiting System
Streamlit Web Interface
"""

import streamlit as st
import asyncio
import uuid
import os
from datetime import datetime
import pandas as pd
from typing import List, Dict

from config import Config
from vector_store.db import VectorStore
from services.embedding import EmbeddingService
from services.pdf_reader import PDFReader
from services.retriever import RetrievalService
from agents.orchestrator import OrchestratorAgent

# Page configuration
st.set_page_config(
    page_title="HIRE-TRON-X",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        text-align: center;
        padding-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = VectorStore()
    if 'embedding_service' not in st.session_state:
        st.session_state.embedding_service = EmbeddingService()
    if 'retriever' not in st.session_state:
        st.session_state.retriever = RetrievalService()
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = OrchestratorAgent()
    if 'jds' not in st.session_state:
        st.session_state.jds = []
    if 'resumes' not in st.session_state:
        st.session_state.resumes = []
    if 'screening_results' not in st.session_state:
        st.session_state.screening_results = []


def process_job_description(jd_text: str, jd_name: str) -> bool:
    """Process and store job description"""
    try:
        # Generate unique ID
        jd_id = f"jd_{uuid.uuid4().hex[:8]}"
        
        # Generate embedding
        embedding = st.session_state.embedding_service.generate_embedding(jd_text)
        
        # Parse JD
        parsed_jd = st.session_state.orchestrator.jd_parser.parse(jd_text)
        
        # Prepare metadata
        metadata = {
            'name': jd_name,
            'uploaded_at': datetime.now().isoformat(),
            'title': parsed_jd.get('title', 'Unknown') if parsed_jd else 'Unknown'
        }
        
        if parsed_jd:
            metadata.update({
                'skills': str(parsed_jd.get('skills', [])),
                'experience': str(parsed_jd.get('experience_required', '')),
                'location': str(parsed_jd.get('location', ''))
            })
        
        # Store in vector DB
        success = st.session_state.vector_store.add_job_description(
            jd_id=jd_id,
            text=jd_text,
            embedding=embedding,
            metadata=metadata
        )
        
        if success:
            st.session_state.jds.append({
                'id': jd_id,
                'name': jd_name,
                'title': metadata['title'],
                'text': jd_text
            })
        
        return success
        
    except Exception as e:
        st.error(f"Error processing JD: {e}")
        return False


def process_resume(resume_text: str, resume_name: str) -> bool:
    """Process and store resume"""
    try:
        # Generate unique ID
        resume_id = f"resume_{uuid.uuid4().hex[:8]}"
        
        # Generate embedding
        embedding = st.session_state.embedding_service.generate_embedding(resume_text)
        
        # Prepare metadata
        metadata = {
            'filename': resume_name,
            'uploaded_at': datetime.now().isoformat(),
            'text_length': len(resume_text)
        }
        
        # Store in vector DB
        success = st.session_state.vector_store.add_resume(
            resume_id=resume_id,
            text=resume_text,
            embedding=embedding,
            metadata=metadata
        )
        
        if success:
            st.session_state.resumes.append({
                'id': resume_id,
                'name': resume_name,
                'text': resume_text
            })
        
        return success
        
    except Exception as e:
        st.error(f"Error processing resume: {e}")
        return False


async def find_best_candidates(jd_id: str, top_k: int = 10):
    """Find and screen best candidates for a job"""
    try:
        # Retrieve candidates
        candidates = st.session_state.retriever.retrieve_candidates_for_job(
            jd_id=jd_id,
            top_k=top_k
        )
        
        if not candidates:
            st.warning("No candidates found")
            return []
        
        # Get JD text
        jd_text = st.session_state.retriever.get_jd_text(jd_id)
        
        # Parse JD
        parsed_jd = st.session_state.orchestrator.jd_parser.parse(jd_text)
        
        # Screen candidates
        results = await st.session_state.orchestrator.screen_multiple_candidates(
            jd_text=jd_text,
            candidates=candidates,
            parsed_jd=parsed_jd
        )
        
        # Sort by score
        results.sort(
            key=lambda x: x.get('screening', {}).get('score', 0),
            reverse=True
        )
        
        return results
        
    except Exception as e:
        st.error(f"Error finding candidates: {e}")
        return []


def main():
    """Main application"""
    init_session_state()
    
    # Header
    st.markdown('<div class="main-header">🤖 HIRE-TRON-X</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Multi-Agent AI Recruiting System</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📊 System Status")
        
        jd_count = st.session_state.vector_store.get_collection_count("jd")
        resume_count = st.session_state.vector_store.get_collection_count("resume")
        
        st.metric("Job Descriptions", jd_count)
        st.metric("Resumes", resume_count)
        
        st.divider()
        
        if st.button("🗑️ Clear All Data"):
            if st.checkbox("Confirm deletion"):
                st.session_state.vector_store.clear_collection("jd")
                st.session_state.vector_store.clear_collection("resume")
                st.session_state.jds = []
                st.session_state.resumes = []
                st.session_state.screening_results = []
                st.success("All data cleared!")
                st.rerun()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Upload Data",
        "🔍 Find Candidates",
        "📋 Results",
        "✉️ Generate Offer"
    ])
    
    # TAB 1: Upload Data
    with tab1:
        st.header("Upload Job Descriptions and Resumes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Job Descriptions")
            
            jd_input_method = st.radio(
                "Input Method",
                ["Paste Text", "Upload File"],
                key="jd_method"
            )
            
            if jd_input_method == "Paste Text":
                jd_name = st.text_input("JD Name", value="Job Description 1")
                jd_text = st.text_area("Paste Job Description", height=300)
                
                if st.button("Add Job Description"):
                    if jd_text.strip():
                        with st.spinner("Processing JD..."):
                            if process_job_description(jd_text, jd_name):
                                st.success(f"✅ Added: {jd_name}")
                            else:
                                st.error("Failed to process JD")
                    else:
                        st.warning("Please enter job description text")
            
            else:
                jd_files = st.file_uploader(
                    "Upload JD Files",
                    type=['txt', 'pdf'],
                    accept_multiple_files=True,
                    key="jd_files"
                )
                
                if st.button("Process JD Files"):
                    if jd_files:
                        progress_bar = st.progress(0)
                        for i, file in enumerate(jd_files):
                            with st.spinner(f"Processing {file.name}..."):
                                if file.type == "application/pdf":
                                    text = PDFReader.extract_text_from_upload(file)
                                else:
                                    text = file.read().decode('utf-8')
                                
                                if text:
                                    process_job_description(text, file.name)
                                
                                progress_bar.progress((i + 1) / len(jd_files))
                        
                        st.success(f"✅ Processed {len(jd_files)} JDs")
                    else:
                        st.warning("Please upload files")
        
        with col2:
            st.subheader("👤 Resumes")
            
            resume_files = st.file_uploader(
                "Upload Resumes",
                type=['txt', 'pdf'],
                accept_multiple_files=True,
                key="resume_files"
            )
            
            if st.button("Process Resumes"):
                if resume_files:
                    progress_bar = st.progress(0)
                    success_count = 0
                    
                    for i, file in enumerate(resume_files):
                        with st.spinner(f"Processing {file.name}..."):
                            if file.type == "application/pdf":
                                text = PDFReader.extract_text_from_upload(file)
                            else:
                                text = file.read().decode('utf-8')
                            
                            if text:
                                if process_resume(text, file.name):
                                    success_count += 1
                            
                            progress_bar.progress((i + 1) / len(resume_files))
                    
                    st.success(f"✅ Processed {success_count}/{len(resume_files)} resumes")
                else:
                    st.warning("Please upload resume files")
        
        st.divider()
        
        # Display current data
        if st.session_state.jds or st.session_state.resumes:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.session_state.jds:
                    st.subheader("Uploaded JDs")
                    for jd in st.session_state.jds:
                        with st.expander(f"📄 {jd['name']}"):
                            st.write(f"**Title:** {jd['title']}")
                            st.text_area("Content", jd['text'][:500] + "...", height=100, key=jd['id'])
            
            with col2:
                if st.session_state.resumes:
                    st.subheader("Uploaded Resumes")
                    for resume in st.session_state.resumes[:10]:  # Show first 10
                        st.write(f"📝 {resume['name']}")
                    if len(st.session_state.resumes) > 10:
                        st.write(f"... and {len(st.session_state.resumes) - 10} more")
    
    # TAB 2: Find Candidates
    with tab2:
        st.header("Find Best Candidates")
        
        if not st.session_state.jds:
            st.warning("⚠️ Please upload job descriptions first")
        elif not st.session_state.resumes:
            st.warning("⚠️ Please upload resumes first")
        else:
            # Select job
            jd_options = {jd['id']: f"{jd['name']} - {jd['title']}" for jd in st.session_state.jds}
            selected_jd_id = st.selectbox(
                "Select Job Description",
                options=list(jd_options.keys()),
                format_func=lambda x: jd_options[x]
            )
            
            top_k = st.slider("Number of Candidates to Screen", 5, 20, 10)
            
            if st.button("🔍 Find Best Candidates", type="primary"):
                with st.spinner("Retrieving and screening candidates..."):
                    # Run async function
                    results = asyncio.run(find_best_candidates(selected_jd_id, top_k))
                    
                    if results:
                        st.session_state.screening_results = results
                        st.session_state.selected_jd = selected_jd_id
                        st.success(f"✅ Screened {len(results)} candidates!")
                        st.info("👉 Go to 'Results' tab to view detailed analysis")
                    else:
                        st.error("No results found")
    
    # TAB 3: Results
    with tab3:
        st.header("Screening Results")
        
        if not st.session_state.screening_results:
            st.info("No screening results yet. Go to 'Find Candidates' tab to start.")
        else:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            avg_score = sum(r['screening']['score'] for r in st.session_state.screening_results) / len(st.session_state.screening_results)
            hire_count = sum(1 for r in st.session_state.screening_results if r['screening'].get('recommendation') == 'HIRE')
            maybe_count = sum(1 for r in st.session_state.screening_results if r['screening'].get('recommendation') == 'MAYBE')
            reject_count = sum(1 for r in st.session_state.screening_results if r['screening'].get('recommendation') == 'REJECT')
            
            with col1:
                st.metric("Average Score", f"{avg_score:.1f}")
            with col2:
                st.metric("Recommend HIRE", hire_count)
            with col3:
                st.metric("MAYBE", maybe_count)
            with col4:
                st.metric("REJECT", reject_count)
            
            st.divider()
            
            # Results table
            st.subheader("Ranked Candidates")
            
            table_data = []
            for i, result in enumerate(st.session_state.screening_results):
                table_data.append({
                    'Rank': i + 1,
                    'Resume': result['metadata']['filename'],
                    'Score': result['screening']['score'],
                    'Recommendation': result['screening'].get('recommendation', 'N/A'),
                    'Similarity': f"{result['similarity_score']:.2%}"
                })
            
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
            
            st.divider()
            
            # Detailed view
            st.subheader("Detailed Analysis")
            
            for i, result in enumerate(st.session_state.screening_results):
                with st.expander(
                    f"#{i+1} - {result['metadata']['filename']} - Score: {result['screening']['score']} - {result['screening'].get('recommendation', 'N/A')}"
                ):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**✅ Strengths:**")
                        strengths = result['screening'].get('strengths', [])
                        if isinstance(strengths, list):
                            for strength in strengths:
                                st.write(f"- {strength}")
                        else:
                            st.write(strengths)
                    
                    with col2:
                        st.write("**⚠️ Weaknesses:**")
                        weaknesses = result['screening'].get('weaknesses', [])
                        if isinstance(weaknesses, list):
                            for weakness in weaknesses:
                                st.write(f"- {weakness}")
                        else:
                            st.write(weaknesses)
                    
                    st.write("**📝 Reasoning:**")
                    st.write(result['screening'].get('reasoning', 'N/A'))
                    
                    if st.button(f"View Resume", key=f"view_{i}"):
                        st.text_area(
                            "Resume Content",
                            result['resume_text'],
                            height=300,
                            key=f"resume_text_{i}"
                        )
    
    # TAB 4: Generate Offer
    with tab4:
        st.header("Generate Offer Letter")
        
        if not st.session_state.screening_results:
            st.info("No candidates screened yet. Please screen candidates first.")
        else:
            # Select candidate
            candidate_options = {
                i: f"{r['metadata']['filename']} - Score: {r['screening']['score']}"
                for i, r in enumerate(st.session_state.screening_results)
                if r['screening'].get('recommendation') in ['HIRE', 'MAYBE']
            }
            
            if not candidate_options:
                st.warning("No candidates with HIRE or MAYBE recommendation")
            else:
                selected_candidate_idx = st.selectbox(
                    "Select Candidate",
                    options=list(candidate_options.keys()),
                    format_func=lambda x: candidate_options[x]
                )
                
                # Get selected candidate
                candidate = st.session_state.screening_results[selected_candidate_idx]
                
                # Offer details form
                with st.form("offer_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        candidate_name = st.text_input("Candidate Name", value="Jane Doe")
                        company_name = st.text_input("Company Name", value="TechCorp Inc.")
                        job_title = st.text_input("Job Title", value="Senior Software Engineer")
                    
                    with col2:
                        salary = st.number_input("Annual Salary ($)", value=120000, step=5000)
                        start_date = st.date_input("Start Date")
                        equity = st.text_input("Equity (optional)", value="0.5% stock options")
                    
                    benefits = st.text_area(
                        "Benefits Package",
                        value="Health insurance, 401(k) matching, unlimited PTO, remote work"
                    )
                    
                    submitted = st.form_submit_button("Generate Offer Letter", type="primary")
                
                if submitted:
                    with st.spinner("Generating offer letter..."):
                        additional_details = {
                            'benefits': benefits,
                            'equity': equity
                        }
                        
                        offer_letter = st.session_state.orchestrator.generate_offer_letter_sync(
                            candidate_name=candidate_name,
                            job_title=job_title,
                            company_name=company_name,
                            salary=salary,
                            start_date=start_date.strftime("%B %d, %Y"),
                            additional_details=additional_details
                        )
                        
                        if offer_letter:
                            st.success("✅ Offer letter generated!")
                            st.divider()
                            st.subheader("Offer Letter")
                            st.markdown(offer_letter)
                            
                            # Download button
                            st.download_button(
                                label="📥 Download Offer Letter",
                                data=offer_letter,
                                file_name=f"offer_letter_{candidate_name.replace(' ', '_')}.txt",
                                mime="text/plain"
                            )
                        else:
                            st.error("Failed to generate offer letter")


if __name__ == "__main__":
    main()