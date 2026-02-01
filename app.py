"""
Streamlit App with LangGraph Integration
Shows the workflow graph and executes the multi-agent system
"""

import streamlit as st
import asyncio
from datetime import datetime
import io
import base64
from langgraph_recruiting import create_recruiting_graph, RecruitingState

st.set_page_config(
    page_title="LangGraph HR Recruiting System",
    page_icon="🕸️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .graph-container {
        border: 2px solid #4CAF50;
        border-radius: 10px;
        padding: 20px;
        background-color: #f9f9f9;
        margin: 20px 0;
    }
    .node-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🕸️ LangGraph Multi-Agent HR Recruiting System")
    st.markdown("**AI-Powered Workflow Graph Orchestration**")
    
    # Initialize session state
    if 'graph' not in st.session_state:
        st.session_state.graph = None
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    
    # Sidebar
    with st.sidebar:
        st.header("🔑 Configuration")
        
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Required for LangGraph agents",
            value=st.session_state.get('api_key', '')
        )
        
        if api_key:
            import os
            os.environ["OPENAI_API_KEY"] = api_key
            st.session_state.api_key = api_key
            st.success("✅ API Key configured!")
            
            # Initialize graph
            if st.session_state.graph is None:
                with st.spinner("Building LangGraph workflow..."):
                    st.session_state.graph = create_recruiting_graph()
                st.success("✅ Graph compiled!")
        else:
            st.warning("⚠️ Enter OpenAI API key to start")
        
        st.divider()
        
        st.header("📝 Job Input")
        
        job_description = st.text_area(
            "Job Description",
            height=200,
            placeholder="Senior Python Developer with 5+ years...",
            value=st.session_state.get('job_description', '')
        )
        
        company_name = st.text_input("Company Name", value="TechCorp Inc.")
        department = st.text_input("Department", value="Engineering")
        
        col1, col2 = st.columns(2)
        with col1:
            min_salary = st.number_input("Min Salary ($)", value=120000, step=5000)
        with col2:
            max_salary = st.number_input("Max Salary ($)", value=160000, step=5000)
        
        st.divider()
        
        if st.button("🚀 Execute Workflow", type="primary", disabled=not api_key or st.session_state.processing):
            if job_description:
                st.session_state.job_description = job_description
                st.session_state.processing = True
                st.rerun()
            else:
                st.error("Please enter a job description!")
        
        if st.button("🔄 Reset"):
            for key in ['results', 'processing', 'job_description']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Main content
    if st.session_state.graph:
        display_graph_visualization()
    
    if st.session_state.processing and st.session_state.graph:
        execute_workflow(
            st.session_state.graph,
            job_description,
            company_name,
            department,
            min_salary,
            max_salary
        )
    
    if st.session_state.results:
        display_results()

def display_graph_visualization():
    """Display the LangGraph workflow visualization"""
    st.header("🕸️ Workflow Graph")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="graph-container">
        <h3 style="text-align: center; color: #4CAF50;">LangGraph Execution Flow</h3>
        
        <div style="font-family: monospace; line-height: 2;">
        <div style="text-align: center; font-size: 18px; color: #2196F3;">⬇️ START ⬇️</div>
        <br>
        <div class="node-box">📋 Job Parser Agent</div>
        <div style="text-align: center;">⬇️ ⬇️ ⬇️</div>
        <div style="display: flex; justify-content: space-around;">
            <div class="node-box" style="width: 30%;">🔍 Sourcing Agent</div>
            <div class="node-box" style="width: 30%;">✅ Screening Agent</div>
            <div class="node-box" style="width: 30%;">💰 Compensation Agent</div>
        </div>
        <div style="text-align: center; margin-top: 10px;">⬇️</div>
        <div class="node-box" style="margin: 0 auto; width: 60%;">📄 Offer Letter Agent</div>
        <div style="text-align: center; font-size: 18px; color: #4CAF50; margin-top: 10px;">⬇️ END ⬇️</div>
        </div>
        
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("Graph Properties")
        st.metric("Total Nodes", "5")
        st.metric("Parallel Branches", "3")
        st.metric("Graph Type", "DAG")
        
        st.info("""
        **Execution Strategy:**
        1. Job Parser runs first
        2. Sourcing, Screening, and Compensation run in parallel
        3. Offer Letter waits for Compensation
        4. Multiple END states for parallel completion
        """)
    
    # Show node details
    with st.expander("📊 Node Details"):
        nodes = [
            {"name": "parse_job", "agent": "Job Parser", "inputs": ["job_description"], "outputs": ["job_analysis"]},
            {"name": "source_candidates", "agent": "Sourcing", "inputs": ["job_description"], "outputs": ["sourcing_strategy"]},
            {"name": "create_screening", "agent": "Screening", "inputs": ["job_description"], "outputs": ["screening_criteria"]},
            {"name": "analyze_compensation", "agent": "Compensation", "inputs": ["job_description", "salary_range"], "outputs": ["compensation_package"]},
            {"name": "generate_offer", "agent": "Offer Letter", "inputs": ["job_analysis", "compensation_package"], "outputs": ["offer_letter"]},
        ]
        
        for node in nodes:
            st.markdown(f"""
            **{node['agent']} Agent** (`{node['name']}`)
            - Inputs: {', '.join(node['inputs'])}
            - Outputs: {', '.join(node['outputs'])}
            """)

def execute_workflow(graph, job_desc, company, dept, min_sal, max_sal):
    """Execute the LangGraph workflow"""
    
    st.header("🔄 Workflow Execution")
    
    status_container = st.container()
    
    with status_container:
        st.info("⏳ Executing LangGraph workflow...")
        
        # Create initial state
        initial_state = {
            "job_description": job_desc,
            "company_name": company,
            "department": dept,
            "min_salary": min_sal,
            "max_salary": max_sal,
            "messages": []
        }
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Execute the graph
            with st.spinner("Running agents..."):
                status_text.text("Starting workflow...")
                progress_bar.progress(10)
                
                final_state = graph.invoke(initial_state)
                
                progress_bar.progress(100)
                status_text.text("Workflow completed!")
            
            st.success("✅ All agents completed successfully!")
            
            # Display execution log
            with st.expander("📜 Execution Log"):
                for msg in final_state.get('messages', []):
                    st.text(f"✓ {msg.content}")
            
            # Save results
            st.session_state.results = final_state
            st.session_state.processing = False
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error during execution: {str(e)}")
            st.session_state.processing = False

def display_results():
    """Display workflow results"""
    st.header("📊 Workflow Results")
    
    results = st.session_state.results
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        job_title = results.get('job_analysis', {}).get('job_title', 'N/A')
        st.metric("Job Title", job_title)
    
    with col2:
        target_salary = results.get('compensation_package', {}).get('target_salary', 0)
        st.metric("Target Salary", f"${target_salary:,}")
    
    with col3:
        platforms = len(results.get('sourcing_strategy', {}).get('platforms', []))
        st.metric("Sourcing Platforms", platforms)
    
    with col4:
        questions = len(results.get('screening_criteria', {}).get('screening_questions', []))
        st.metric("Screening Questions", questions)
    
    # Tabs for detailed results
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Job Analysis",
        "🔍 Sourcing",
        "✅ Screening",
        "💰 Compensation",
        "📄 Offer Letter"
    ])
    
    with tab1:
        display_job_analysis(results.get('job_analysis', {}))
    
    with tab2:
        display_sourcing(results.get('sourcing_strategy', {}))
    
    with tab3:
        display_screening(results.get('screening_criteria', {}))
    
    with tab4:
        display_compensation(results.get('compensation_package', {}))
    
    with tab5:
        display_offer_letter(results.get('offer_letter', ''))

def display_job_analysis(data):
    st.subheader("Job Analysis Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Job Title:**", data.get('job_title', 'N/A'))
        st.write("**Experience Level:**", data.get('experience_level', 'N/A'))
        st.write("**Employment Type:**", data.get('employment_type', 'N/A'))
    
    with col2:
        st.write("**Required Skills:**")
        for skill in data.get('required_skills', []):
            st.write(f"- {skill}")
    
    st.write("**Responsibilities:**")
    for resp in data.get('responsibilities', []):
        st.write(f"• {resp}")

def display_sourcing(data):
    st.subheader("Sourcing Strategy")
    
    st.write("**Timeline:**", data.get('timeline', 'N/A'))
    
    st.write("**Platforms:**")
    for platform in data.get('platforms', []):
        if isinstance(platform, dict):
            st.write(f"- **{platform.get('name')}**: {platform.get('reason')}")
    
    st.write("**Keywords:**", ', '.join(data.get('search_keywords', [])))

def display_screening(data):
    st.subheader("Screening Criteria")
    
    st.write("**Must-Have:**")
    for item in data.get('must_have_criteria', []):
        st.write(f"✅ {item}")
    
    st.write("**Questions:**")
    for i, q in enumerate(data.get('screening_questions', []), 1):
        st.write(f"{i}. {q}")

def display_compensation(data):
    st.subheader("Compensation Package")
    
    st.write("**Market Analysis:**")
    st.info(data.get('market_analysis', 'N/A'))
    
    st.write("**Benefits:**")
    for benefit in data.get('benefits_package', []):
        st.write(f"- {benefit}")

def display_offer_letter(letter):
    st.subheader("Generated Offer Letter")
    
    st.text_area("Letter", letter, height=400)
    
    st.download_button(
        "📥 Download Offer Letter",
        letter,
        file_name=f"offer_letter_{datetime.now().strftime('%Y%m%d')}.txt"
    )

if __name__ == "__main__":
    main()
