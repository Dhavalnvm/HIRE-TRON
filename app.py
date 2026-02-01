"""
HIRE-TRON: Streamlit App with Batch Processing
Process multiple job descriptions in a single API call
"""

import streamlit as st
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from langgraph_recruiting import create_recruiting_graph, RecruitingState
import time

st.set_page_config(
    page_title="HIRE-TRON - Batch HR Recruiting",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: bold;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .batch-card {
        border: 2px solid #667eea;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# BATCH PROCESSING FUNCTIONS
# ============================================================================

class BatchProcessor:
    """Handles batch processing of multiple job descriptions"""
    
    def __init__(self, graph):
        self.graph = graph
        self.results = []
        self.errors = []
    
    def process_batch(self, job_configs: List[Dict[str, Any]], progress_callback=None) -> List[Dict[str, Any]]:
        """Process multiple job descriptions"""
        results = []
        total = len(job_configs)
        
        for idx, config in enumerate(job_configs):
            if progress_callback:
                progress_callback(idx, total, config.get('job_title', f'Job {idx+1}'))
            
            try:
                result = self.process_single(config)
                result['batch_index'] = idx
                result['status'] = 'success'
                results.append(result)
            except Exception as e:
                results.append({
                    'batch_index': idx,
                    'status': 'error',
                    'error': str(e),
                    'config': config
                })
        
        return results
    
    def process_single(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single job description"""
        initial_state = {
            "job_description": config['job_description'],
            "company_name": config.get('company_name', 'Company'),
            "department": config.get('department', 'General'),
            "min_salary": config.get('min_salary', 80000),
            "max_salary": config.get('max_salary', 120000),
            "messages": []
        }
        
        final_state = self.graph.invoke(initial_state)
        
        return {
            'config': config,
            'job_analysis': final_state.get('job_analysis', {}),
            'sourcing_strategy': final_state.get('sourcing_strategy', {}),
            'screening_criteria': final_state.get('screening_criteria', {}),
            'compensation_package': final_state.get('compensation_package', {}),
            'offer_letter': final_state.get('offer_letter', ''),
            'messages': final_state.get('messages', [])
        }
    
    def export_results_json(self, results: List[Dict[str, Any]]) -> str:
        """Export results as JSON"""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'total_processed': len(results),
            'successful': len([r for r in results if r.get('status') == 'success']),
            'failed': len([r for r in results if r.get('status') == 'error']),
            'results': results
        }
        return json.dumps(export_data, indent=2)
    
    def export_results_csv(self, results: List[Dict[str, Any]]) -> pd.DataFrame:
        """Export results as CSV"""
        rows = []
        for result in results:
            if result.get('status') == 'success':
                job_analysis = result.get('job_analysis', {})
                comp_package = result.get('compensation_package', {})
                
                rows.append({
                    'Batch Index': result.get('batch_index', 0),
                    'Status': result.get('status', 'unknown'),
                    'Job Title': job_analysis.get('job_title', 'N/A'),
                    'Experience Level': job_analysis.get('experience_level', 'N/A'),
                    'Employment Type': job_analysis.get('employment_type', 'N/A'),
                    'Target Salary': comp_package.get('target_salary', 0),
                    'Required Skills': ', '.join(job_analysis.get('required_skills', [])),
                    'Company': result.get('config', {}).get('company_name', 'N/A'),
                    'Department': result.get('config', {}).get('department', 'N/A')
                })
            else:
                rows.append({
                    'Batch Index': result.get('batch_index', 0),
                    'Status': 'error',
                    'Error': result.get('error', 'Unknown error')
                })
        
        return pd.DataFrame(rows)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize session state variables"""
    if 'graph' not in st.session_state:
        st.session_state.graph = None
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'batch_configs' not in st.session_state:
        st.session_state.batch_configs = []
    if 'api_key_set' not in st.session_state:
        st.session_state.api_key_set = False


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_sidebar():
    """Render sidebar with configuration"""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)
        st.title("⚙️ Configuration")
        
        # API Key
        st.subheader("🔑 API Setup")
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Required for LangGraph agents",
            value=st.session_state.get('api_key', '')
        )
        
        if api_key and not st.session_state.api_key_set:
            import os
            os.environ["OPENAI_API_KEY"] = api_key
            st.session_state.api_key = api_key
            st.session_state.api_key_set = True
            
            # Initialize graph
            if st.session_state.graph is None:
                with st.spinner("🔧 Building LangGraph workflow..."):
                    st.session_state.graph = create_recruiting_graph()
                st.success("✅ Graph compiled!")
        
        if st.session_state.api_key_set:
            st.success("✅ API Key configured!")
        else:
            st.warning("⚠️ Enter OpenAI API key to start")
        
        st.divider()
        
        # Batch Mode Selection
        st.subheader("📊 Processing Mode")
        mode = st.radio(
            "Select Mode",
            ["Single Job", "Batch Processing", "CSV Upload"],
            help="Choose how you want to process jobs"
        )
        
        st.divider()
        
        # Statistics
        if st.session_state.batch_results:
            st.subheader("📈 Batch Statistics")
            results = st.session_state.batch_results
            successful = len([r for r in results if r.get('status') == 'success'])
            failed = len([r for r in results if r.get('status') == 'error'])
            
            st.metric("Total Processed", len(results))
            st.metric("Successful", successful, delta=f"{successful/len(results)*100:.1f}%")
            st.metric("Failed", failed)
        
        st.divider()
        
        # Reset button
        if st.button("🔄 Reset All", type="secondary"):
            for key in ['batch_results', 'processing', 'batch_configs']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        return mode


def render_workflow_graph():
    """Render workflow visualization"""
    with st.expander("🕸️ View Workflow Graph", expanded=False):
        st.markdown("""
        <div style="font-family: monospace; background: #f8f9fa; padding: 20px; border-radius: 10px;">
        <div style="text-align: center; font-size: 20px; color: #2196F3; margin-bottom: 20px;">
        ⬇️ <b>WORKFLOW EXECUTION</b> ⬇️
        </div>
        
        <div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 15px; border-radius: 8px; margin: 10px 0;">
        📋 <b>Job Parser Agent</b><br/>
        <small>Validates & Extracts Requirements</small>
        </div>
        
        <div style="text-align: center; margin: 10px 0;">⬇️ ⬇️ ⬇️</div>
        
        <div style="display: flex; justify-content: space-around; margin: 20px 0;">
            <div style="background: #f093fb; color: white; padding: 15px; border-radius: 8px; width: 30%; text-align: center;">
                🔍 <b>Sourcing</b><br/>
                <small>Platforms & Strategy</small>
            </div>
            <div style="background: #4facfe; color: white; padding: 15px; border-radius: 8px; width: 30%; text-align: center;">
                ✅ <b>Screening</b><br/>
                <small>Questions & Criteria</small>
            </div>
            <div style="background: #43e97b; color: white; padding: 15px; border-radius: 8px; width: 30%; text-align: center;">
                💰 <b>Compensation</b><br/>
                <small>Salary & Benefits</small>
            </div>
        </div>
        
        <div style="text-align: center; margin: 10px 0;">⬇️</div>
        
        <div style="text-align: center; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                    color: white; padding: 15px; border-radius: 8px; margin: 10px 0;">
        📄 <b>Offer Letter Agent</b><br/>
        <small>Professional Generation</small>
        </div>
        
        <div style="text-align: center; font-size: 20px; color: #4CAF50; margin-top: 20px;">
        ⬇️ <b>COMPLETE</b> ⬇️
        </div>
        </div>
        """, unsafe_allow_html=True)


def render_single_job_mode():
    """Render single job processing interface"""
    st.header("📝 Single Job Processing")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        job_description = st.text_area(
            "Job Description",
            height=200,
            placeholder="Senior Python Developer with 5+ years experience...",
            help="Enter the complete job description"
        )
    
    with col2:
        company_name = st.text_input("Company Name", value="TechCorp Inc.")
        department = st.text_input("Department", value="Engineering")
        
        col_a, col_b = st.columns(2)
        with col_a:
            min_salary = st.number_input("Min Salary ($)", value=120000, step=5000)
        with col_b:
            max_salary = st.number_input("Max Salary ($)", value=160000, step=5000)
    
    if st.button("🚀 Process Job", type="primary", disabled=not st.session_state.api_key_set):
        if job_description:
            config = {
                'job_description': job_description,
                'company_name': company_name,
                'department': department,
                'min_salary': min_salary,
                'max_salary': max_salary,
                'job_title': 'Single Job'
            }
            process_batch([config])
        else:
            st.error("❌ Please enter a job description!")


def render_batch_mode():
    """Render batch processing interface"""
    st.header("📦 Batch Processing")
    
    st.info("💡 Add multiple jobs to process them all at once. Each job will be processed through the complete workflow.")
    
    # Batch input form
    with st.expander("➕ Add Job to Batch", expanded=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            batch_job_desc = st.text_area(
                "Job Description",
                height=150,
                key="batch_job_desc",
                placeholder="Enter job description..."
            )
        
        with col2:
            batch_company = st.text_input("Company", value="TechCorp", key="batch_company")
            batch_dept = st.text_input("Department", value="Engineering", key="batch_dept")
        
        with col3:
            batch_min_sal = st.number_input("Min Salary", value=100000, step=5000, key="batch_min")
            batch_max_sal = st.number_input("Max Salary", value=140000, step=5000, key="batch_max")
        
        if st.button("➕ Add to Batch"):
            if batch_job_desc:
                st.session_state.batch_configs.append({
                    'job_description': batch_job_desc,
                    'company_name': batch_company,
                    'department': batch_dept,
                    'min_salary': batch_min_sal,
                    'max_salary': batch_max_sal,
                    'job_title': f'Batch Job {len(st.session_state.batch_configs) + 1}'
                })
                st.success(f"✅ Added job to batch! Total jobs: {len(st.session_state.batch_configs)}")
                st.rerun()
            else:
                st.error("❌ Please enter a job description!")
    
    # Display current batch
    if st.session_state.batch_configs:
        st.subheader(f"📋 Current Batch ({len(st.session_state.batch_configs)} jobs)")
        
        for idx, config in enumerate(st.session_state.batch_configs):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.text(f"Job {idx+1}: {config['company_name']} - {config['department']}")
                    st.caption(config['job_description'][:100] + "...")
                with col2:
                    st.text(f"${config['min_salary']:,} - ${config['max_salary']:,}")
                with col3:
                    if st.button("🗑️ Remove", key=f"remove_{idx}"):
                        st.session_state.batch_configs.pop(idx)
                        st.rerun()
                st.divider()
        
        # Process batch button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Process Batch", type="primary", disabled=not st.session_state.api_key_set):
                process_batch(st.session_state.batch_configs)
    else:
        st.info("📭 No jobs in batch. Add jobs using the form above.")


def render_csv_upload_mode():
    """Render CSV upload interface"""
    st.header("📄 CSV Batch Upload")
    
    st.info("""
    💡 Upload a CSV file with the following columns:
    - `job_description` (required)
    - `company_name` (optional, default: 'Company')
    - `department` (optional, default: 'General')
    - `min_salary` (optional, default: 80000)
    - `max_salary` (optional, default: 120000)
    """)
    
    # Download template
    template_df = pd.DataFrame({
        'job_description': ['Senior Python Developer with 5+ years...', 'Marketing Manager with leadership...'],
        'company_name': ['TechCorp', 'MarketCo'],
        'department': ['Engineering', 'Marketing'],
        'min_salary': [120000, 90000],
        'max_salary': [160000, 130000]
    })
    
    csv_template = template_df.to_csv(index=False)
    st.download_button(
        "📥 Download CSV Template",
        csv_template,
        file_name="batch_template.csv",
        mime="text/csv"
    )
    
    # Upload CSV
    uploaded_file = st.file_uploader("Upload CSV File", type=['csv'])
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ Loaded {len(df)} jobs from CSV")
            st.dataframe(df, use_container_width=True)
            
            # Convert to batch configs
            if st.button("🚀 Process CSV Batch", type="primary", disabled=not st.session_state.api_key_set):
                batch_configs = []
                for idx, row in df.iterrows():
                    batch_configs.append({
                        'job_description': row.get('job_description', ''),
                        'company_name': row.get('company_name', 'Company'),
                        'department': row.get('department', 'General'),
                        'min_salary': int(row.get('min_salary', 80000)),
                        'max_salary': int(row.get('max_salary', 120000)),
                        'job_title': f'CSV Job {idx+1}'
                    })
                
                process_batch(batch_configs)
        
        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")


def process_batch(configs: List[Dict[str, Any]]):
    """Process batch of job configurations"""
    st.session_state.processing = True
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    processor = BatchProcessor(st.session_state.graph)
    
    def update_progress(current, total, job_title):
        progress = (current + 1) / total
        progress_bar.progress(progress)
        status_text.text(f"Processing {current + 1}/{total}: {job_title}")
    
    with st.spinner("⏳ Processing batch..."):
        results = processor.process_batch(configs, update_progress)
    
    st.session_state.batch_results = results
    st.session_state.processing = False
    
    progress_bar.empty()
    status_text.empty()
    
    st.success(f"✅ Batch processing complete! Processed {len(results)} jobs.")
    st.balloons()


def render_results():
    """Render batch processing results"""
    if not st.session_state.batch_results:
        return
    
    st.header("📊 Batch Results")
    
    results = st.session_state.batch_results
    successful = [r for r in results if r.get('status') == 'success']
    failed = [r for r in results if r.get('status') == 'error']
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h1>{len(results)}</h1>
            <p>Total Processed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <h1>{len(successful)}</h1>
            <p>Successful</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
            <h1>{len(failed)}</h1>
            <p>Failed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        success_rate = len(successful) / len(results) * 100 if results else 0
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <h1>{success_rate:.1f}%</h1>
            <p>Success Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Export options
    st.subheader("📥 Export Results")
    col1, col2, col3 = st.columns(3)
    
    processor = BatchProcessor(st.session_state.graph)
    
    with col1:
        json_data = processor.export_results_json(results)
        st.download_button(
            "📄 Download JSON",
            json_data,
            file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col2:
        csv_df = processor.export_results_csv(results)
        csv_data = csv_df.to_csv(index=False)
        st.download_button(
            "📊 Download CSV",
            csv_data,
            file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col3:
        # Export offer letters
        if successful:
            offer_letters = "\n\n" + "="*80 + "\n\n".join([
                f"OFFER LETTER {idx+1}\n{'='*80}\n\n{r.get('offer_letter', '')}"
                for idx, r in enumerate(successful)
            ])
            st.download_button(
                "📝 Download Offer Letters",
                offer_letters,
                file_name=f"offer_letters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    # Detailed results tabs
    tab1, tab2 = st.tabs(["✅ Successful Jobs", "❌ Failed Jobs"])
    
    with tab1:
        if successful:
            for idx, result in enumerate(successful):
                render_job_result(result, idx)
        else:
            st.info("No successful jobs to display")
    
    with tab2:
        if failed:
            for idx, result in enumerate(failed):
                st.error(f"**Job {result.get('batch_index', idx)+1}**: {result.get('error', 'Unknown error')}")
                with st.expander("View Configuration"):
                    st.json(result.get('config', {}))
        else:
            st.success("No failed jobs!")


def render_job_result(result: Dict[str, Any], idx: int):
    """Render individual job result"""
    job_analysis = result.get('job_analysis', {})
    comp_package = result.get('compensation_package', {})
    sourcing = result.get('sourcing_strategy', {})
    screening = result.get('screening_criteria', {})
    
    with st.expander(f"📋 Job {idx+1}: {job_analysis.get('job_title', 'N/A')}", expanded=False):
        # Summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Job Title", job_analysis.get('job_title', 'N/A'))
        with col2:
            st.metric("Target Salary", f"${comp_package.get('target_salary', 0):,}")
        with col3:
            st.metric("Platforms", len(sourcing.get('platforms', [])))
        with col4:
            st.metric("Questions", len(screening.get('screening_questions', [])))
        
        # Detailed tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Analysis", "🔍 Sourcing", "✅ Screening", "💰 Compensation", "📄 Offer"
        ])
        
        with tab1:
            st.write("**Experience Level:**", job_analysis.get('experience_level', 'N/A'))
            st.write("**Required Skills:**")
            for skill in job_analysis.get('required_skills', []):
                st.write(f"- {skill}")
        
        with tab2:
            st.write("**Timeline:**", sourcing.get('timeline', 'N/A'))
            st.write("**Platforms:**")
            for platform in sourcing.get('platforms', []):
                if isinstance(platform, dict):
                    st.write(f"- **{platform.get('name')}**: {platform.get('reason')}")
        
        with tab3:
            st.write("**Screening Questions:**")
            for i, q in enumerate(screening.get('screening_questions', []), 1):
                st.write(f"{i}. {q}")
        
        with tab4:
            st.write("**Market Analysis:**")
            st.info(comp_package.get('market_analysis', 'N/A'))
            st.write("**Benefits:**")
            for benefit in comp_package.get('benefits_package', []):
                st.write(f"- {benefit}")
        
        with tab5:
            offer_letter = result.get('offer_letter', '')
            st.text_area("Offer Letter", offer_letter, height=300, key=f"offer_{idx}")


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    init_session_state()
    
    # Title
    st.markdown("""
    <h1 style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                font-size: 3em; margin-bottom: 0;'>
    🎯 HIRE-TRON
    </h1>
    <p style='text-align: center; font-size: 1.2em; color: #666; margin-top: 0;'>
    Multi-Agent HR Recruiting System with Batch Processing
    </p>
    """, unsafe_allow_html=True)
    
    # Render sidebar and get mode
    mode = render_sidebar()
    
    # Render workflow graph
    render_workflow_graph()
    
    st.divider()
    
    # Render appropriate mode
    if not st.session_state.api_key_set:
        st.warning("⚠️ Please configure your OpenAI API key in the sidebar to begin.")
        return
    
    if mode == "Single Job":
        render_single_job_mode()
    elif mode == "Batch Processing":
        render_batch_mode()
    elif mode == "CSV Upload":
        render_csv_upload_mode()
    
    # Render results if available
    if st.session_state.batch_results:
        st.divider()
        render_results()


if __name__ == "__main__":
    main()
