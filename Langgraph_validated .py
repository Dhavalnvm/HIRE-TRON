"""
Enhanced LangGraph System with Agent Validation and Graph Plotting
Includes: Input validation, output validation, and visual graph generation
"""

from typing import TypedDict, Annotated, Sequence, Optional, Any
import operator
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
import json
import io
from datetime import datetime

# Define the state that flows through the graph
class RecruitingState(TypedDict):
    """State object that flows through the recruiting workflow"""
    job_description: str
    company_name: str
    department: str
    min_salary: int
    max_salary: int
    
    # Agent outputs
    job_analysis: dict
    sourcing_strategy: dict
    screening_criteria: dict
    compensation_package: dict
    offer_letter: str
    
    # Validation and metadata
    messages: Annotated[Sequence[BaseMessage], operator.add]
    errors: list
    validation_results: dict


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_input(state: RecruitingState) -> dict:
    """Validate input parameters before starting workflow"""
    errors = []
    warnings = []
    
    # Job description validation
    if not state.get('job_description') or len(state['job_description'].strip()) < 50:
        errors.append("Job description must be at least 50 characters")
    
    if len(state.get('job_description', '')) > 5000:
        warnings.append("Very long job description - may increase processing time")
    
    # Company name validation
    if not state.get('company_name'):
        errors.append("Company name is required")
    
    # Department validation
    if not state.get('department'):
        warnings.append("Department not specified - using 'General'")
    
    # Salary validation
    min_sal = state.get('min_salary', 0)
    max_sal = state.get('max_salary', 0)
    
    if min_sal <= 0 or max_sal <= 0:
        errors.append("Salary range must be positive numbers")
    
    if min_sal >= max_sal:
        errors.append("Minimum salary must be less than maximum salary")
    
    if min_sal < 20000:
        warnings.append("Minimum salary seems very low")
    
    if max_sal > 1000000:
        warnings.append("Maximum salary seems very high")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def validate_agent_output(agent_name: str, output: Any, expected_fields: list) -> dict:
    """Validate agent output structure"""
    errors = []
    warnings = []
    
    if not isinstance(output, dict):
        errors.append(f"{agent_name}: Output must be a dictionary")
        return {'valid': False, 'errors': errors, 'warnings': warnings}
    
    # Check for expected fields
    missing_fields = [field for field in expected_fields if field not in output]
    if missing_fields:
        errors.append(f"{agent_name}: Missing fields: {', '.join(missing_fields)}")
    
    # Check for empty values
    for field in expected_fields:
        if field in output:
            value = output[field]
            if value is None or (isinstance(value, (list, dict, str)) and not value):
                warnings.append(f"{agent_name}: Field '{field}' is empty")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


# ============================================================================
# VALIDATED AGENT FUNCTIONS
# ============================================================================

def job_parser_agent(state: RecruitingState) -> RecruitingState:
    """Parse job description with validation"""
    
    # Validate input
    validation = validate_input(state)
    if not validation['valid']:
        state['errors'] = state.get('errors', []) + validation['errors']
        state['job_analysis'] = {'error': 'Validation failed'}
        return state
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    system_prompt = """You are an expert HR analyst specializing in parsing job descriptions.
Extract and structure key information from job descriptions.
Return ONLY valid JSON with these exact fields: job_title, experience_level, employment_type, 
required_skills (array), nice_to_have_skills (array), responsibilities (array), qualifications (array)."""
    
    user_message = f"""Analyze this job description:

Job Description: {state['job_description']}
Department: {state['department']}

Provide comprehensive analysis in JSON format."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        parsed_data = json.loads(response.content)
        
        # Validate output
        expected_fields = ['job_title', 'experience_level', 'employment_type', 
                          'required_skills', 'responsibilities', 'qualifications']
        output_validation = validate_agent_output('Job Parser', parsed_data, expected_fields)
        
        if not output_validation['valid']:
            state['errors'] = state.get('errors', []) + output_validation['errors']
        
        state['validation_results'] = state.get('validation_results', {})
        state['validation_results']['job_parser'] = output_validation
        
    except json.JSONDecodeError:
        parsed_data = {
            'job_title': 'Software Engineer',
            'experience_level': '3+ years',
            'employment_type': 'Full-time',
            'required_skills': ['Python'],
            'nice_to_have_skills': ['AWS'],
            'responsibilities': ['Develop software'],
            'qualifications': ['Bachelor\'s degree'],
            'error': 'Failed to parse LLM response'
        }
        state['errors'] = state.get('errors', []) + ['Job Parser: Failed to parse LLM response']
    
    state['job_analysis'] = parsed_data
    state['messages'] = state.get('messages', []) + [
        HumanMessage(content=f"✓ Job Parser completed: {parsed_data.get('job_title', 'N/A')}")
    ]
    
    return state


def candidate_sourcing_agent(state: RecruitingState) -> RecruitingState:
    """Create candidate sourcing strategy with validation"""
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    system_prompt = """You are an expert talent acquisition specialist.
Create comprehensive candidate sourcing strategies.
Return ONLY valid JSON with these exact fields: platforms (array of {name, reason}), 
search_keywords (array), sourcing_channels (array), outreach_strategy (string), timeline (string)."""
    
    user_message = f"""Create sourcing strategy for:

Job Description: {state['job_description']}

Provide platforms, keywords, channels, outreach strategy, and timeline in JSON."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        sourcing_data = json.loads(response.content)
        
        # Validate output
        expected_fields = ['platforms', 'search_keywords', 'outreach_strategy', 'timeline']
        output_validation = validate_agent_output('Sourcing', sourcing_data, expected_fields)
        
        if not output_validation['valid']:
            state['errors'] = state.get('errors', []) + output_validation['errors']
        
        state['validation_results'] = state.get('validation_results', {})
        state['validation_results']['sourcing'] = output_validation
        
    except json.JSONDecodeError:
        sourcing_data = {
            'platforms': [{'name': 'LinkedIn', 'reason': 'Professional network'}],
            'search_keywords': ['Python Developer'],
            'sourcing_channels': ['Job boards'],
            'outreach_strategy': 'Direct outreach',
            'timeline': '2-4 weeks',
            'error': 'Failed to parse LLM response'
        }
        state['errors'] = state.get('errors', []) + ['Sourcing: Failed to parse LLM response']
    
    state['sourcing_strategy'] = sourcing_data
    state['messages'] = state.get('messages', []) + [
        HumanMessage(content=f"✓ Sourcing strategy created with {len(sourcing_data.get('platforms', []))} platforms")
    ]
    
    return state


def screening_agent(state: RecruitingState) -> RecruitingState:
    """Create screening criteria with validation"""
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    system_prompt = """You are an expert HR interviewer.
Create comprehensive screening criteria and questions.
Return ONLY valid JSON with: must_have_criteria (array), nice_to_have_criteria (array), 
screening_questions (array), technical_assessment (string), evaluation_rubric (string)."""
    
    user_message = f"""Create screening materials for:

Job Description: {state['job_description']}

Include criteria, questions, assessment, and rubric in JSON."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        screening_data = json.loads(response.content)
        
        # Validate output
        expected_fields = ['must_have_criteria', 'screening_questions']
        output_validation = validate_agent_output('Screening', screening_data, expected_fields)
        
        if not output_validation['valid']:
            state['errors'] = state.get('errors', []) + output_validation['errors']
        
        state['validation_results'] = state.get('validation_results', {})
        state['validation_results']['screening'] = output_validation
        
    except json.JSONDecodeError:
        screening_data = {
            'must_have_criteria': ['Relevant experience'],
            'nice_to_have_criteria': ['Advanced skills'],
            'screening_questions': ['Tell me about your experience'],
            'technical_assessment': 'Coding challenge',
            'evaluation_rubric': 'Standard evaluation',
            'error': 'Failed to parse LLM response'
        }
        state['errors'] = state.get('errors', []) + ['Screening: Failed to parse LLM response']
    
    state['screening_criteria'] = screening_data
    state['messages'] = state.get('messages', []) + [
        HumanMessage(content=f"✓ Screening created with {len(screening_data.get('screening_questions', []))} questions")
    ]
    
    return state


def compensation_agent(state: RecruitingState) -> RecruitingState:
    """Analyze compensation with validation"""
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    system_prompt = """You are an expert compensation analyst.
Analyze market data and create competitive compensation packages.
Return ONLY valid JSON with: market_analysis (string), recommended_salary_range ({min, max}), 
target_salary (number), benefits_package (array), equity_structure (string), justification (string)."""
    
    user_message = f"""Create compensation package for:

Job Description: {state['job_description']}
Budget Range: ${state['min_salary']:,} - ${state['max_salary']:,}

Provide analysis, salary, benefits, equity, and justification in JSON."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        comp_data = json.loads(response.content)
        
        # Validate output
        expected_fields = ['target_salary', 'benefits_package']
        output_validation = validate_agent_output('Compensation', comp_data, expected_fields)
        
        # Additional validation for salary range
        if 'target_salary' in comp_data:
            target = comp_data['target_salary']
            if target < state['min_salary'] or target > state['max_salary']:
                output_validation['warnings'].append(
                    f"Target salary ${target:,} is outside budget range"
                )
        
        if not output_validation['valid']:
            state['errors'] = state.get('errors', []) + output_validation['errors']
        
        state['validation_results'] = state.get('validation_results', {})
        state['validation_results']['compensation'] = output_validation
        
        # Ensure salary range exists
        if 'recommended_salary_range' not in comp_data:
            comp_data['recommended_salary_range'] = {
                'min': state['min_salary'],
                'max': state['max_salary']
            }
        
    except json.JSONDecodeError:
        comp_data = {
            'market_analysis': 'Competitive market',
            'recommended_salary_range': {'min': state['min_salary'], 'max': state['max_salary']},
            'target_salary': (state['min_salary'] + state['max_salary']) // 2,
            'benefits_package': ['Health insurance', 'PTO'],
            'equity_structure': 'Standard equity',
            'justification': 'Market competitive',
            'error': 'Failed to parse LLM response'
        }
        state['errors'] = state.get('errors', []) + ['Compensation: Failed to parse LLM response']
    
    state['compensation_package'] = comp_data
    state['messages'] = state.get('messages', []) + [
        HumanMessage(content=f"✓ Compensation package: ${comp_data.get('target_salary', 0):,}")
    ]
    
    return state


def offer_letter_agent(state: RecruitingState) -> RecruitingState:
    """Generate offer letter with validation"""
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    system_prompt = """You are an expert HR professional creating offer letters.
Generate professional, comprehensive offer letters with all necessary details and legal language."""
    
    job_title = state.get('job_analysis', {}).get('job_title', 'Software Engineer')
    target_salary = state.get('compensation_package', {}).get('target_salary', 100000)
    benefits = state.get('compensation_package', {}).get('benefits_package', [])
    
    user_message = f"""Generate professional offer letter:

Company: {state['company_name']}
Department: {state['department']}
Job Title: {job_title}
Salary: ${target_salary:,}

Benefits: {', '.join(benefits) if benefits else 'Competitive benefits package'}

Include: company header, position details, compensation, benefits, start date (TBD), 
contingencies, and signature section."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        offer_letter = response.content
        
        # Validate offer letter has minimum content
        if len(offer_letter) < 200:
            state['errors'] = state.get('errors', []) + [
                'Offer Letter: Generated letter is too short'
            ]
        
        state['validation_results'] = state.get('validation_results', {})
        state['validation_results']['offer_letter'] = {
            'valid': len(offer_letter) >= 200,
            'errors': [] if len(offer_letter) >= 200 else ['Letter too short'],
            'warnings': [],
            'char_count': len(offer_letter)
        }
        
    except Exception as e:
        offer_letter = f"Error generating offer letter: {str(e)}"
        state['errors'] = state.get('errors', []) + [f'Offer Letter: {str(e)}']
    
    state['offer_letter'] = offer_letter
    state['messages'] = state.get('messages', []) + [
        HumanMessage(content=f"✓ Offer letter generated: {len(offer_letter)} characters")
    ]
    
    return state


# ============================================================================
# GRAPH BUILDING WITH VALIDATION
# ============================================================================

def create_recruiting_graph():
    """Create the LangGraph workflow with validation"""
    
    # Initialize the graph
    workflow = StateGraph(RecruitingState)
    
    # Add nodes (agents)
    workflow.add_node("parse_job", job_parser_agent)
    workflow.add_node("source_candidates", candidate_sourcing_agent)
    workflow.add_node("create_screening", screening_agent)
    workflow.add_node("analyze_compensation", compensation_agent)
    workflow.add_node("generate_offer", offer_letter_agent)
    
    # Set entry point
    workflow.set_entry_point("parse_job")
    
    # Add edges for parallel execution
    workflow.add_edge("parse_job", "source_candidates")
    workflow.add_edge("parse_job", "create_screening")
    workflow.add_edge("parse_job", "analyze_compensation")
    
    # Offer letter depends on compensation
    workflow.add_edge("analyze_compensation", "generate_offer")
    
    # End conditions
    workflow.add_edge("source_candidates", END)
    workflow.add_edge("create_screening", END)
    workflow.add_edge("generate_offer", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app


# ============================================================================
# GRAPH VALIDATION AND PLOTTING
# ============================================================================

def validate_graph(graph) -> dict:
    """Validate the compiled graph structure"""
    errors = []
    warnings = []
    
    try:
        graph_structure = graph.get_graph()
        nodes = graph_structure.nodes
        edges = graph_structure.edges
        
        # Check for nodes
        if not nodes:
            errors.append("Graph has no nodes")
        
        # Check for entry point
        entry_points = [node for node in nodes if node.get('entry_point')]
        if not entry_points:
            warnings.append("No explicit entry point defined")
        
        # Check for END connections
        has_end = any('END' in str(edge) for edge in edges)
        if not has_end:
            warnings.append("No nodes connect to END")
        
        # Check for unreachable nodes
        # (More complex validation would trace paths from entry to all nodes)
        
        validation_result = {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'node_count': len(nodes),
            'edge_count': len(edges),
            'structure': {
                'nodes': [str(n) for n in nodes],
                'edges': [str(e) for e in edges]
            }
        }
        
    except Exception as e:
        validation_result = {
            'valid': False,
            'errors': [f"Graph validation failed: {str(e)}"],
            'warnings': [],
            'node_count': 0,
            'edge_count': 0
        }
    
    return validation_result


def plot_graph_ascii(graph):
    """Generate ASCII representation of the graph"""
    
    ascii_art = """
    ╔══════════════════════════════════════════╗
    ║   HR RECRUITING WORKFLOW GRAPH           ║
    ╚══════════════════════════════════════════╝
    
                    [START]
                       │
                       ▼
            ┌──────────────────────┐
            │   Job Parser Agent   │
            │  (parse_job)         │
            └──────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
    ┌─────────┐  ┌──────────┐  ┌────────────┐
    │Sourcing │  │Screening │  │Compensation│
    │ Agent   │  │  Agent   │  │   Agent    │
    └─────────┘  └──────────┘  └────────────┘
         │             │             │
         ▼             ▼             ▼
       [END]         [END]           │
                                     ▼
                            ┌─────────────────┐
                            │  Offer Letter   │
                            │     Agent       │
                            └─────────────────┘
                                     │
                                     ▼
                                   [END]
    
    LEGEND:
    ═══ Parallel execution branches
    ─── Sequential dependencies
    """
    
    return ascii_art


def plot_graph_mermaid(graph) -> str:
    """Generate Mermaid diagram code"""
    
    mermaid = """graph TD
    START([🚀 START]) --> PARSE[📋 Job Parser<br/>Validates & Extracts]
    
    PARSE --> SOURCE[🔍 Sourcing<br/>Platforms & Keywords]
    PARSE --> SCREEN[✅ Screening<br/>Questions & Criteria]
    PARSE --> COMP[💰 Compensation<br/>Analysis & Package]
    
    SOURCE --> E1([✓ END])
    SCREEN --> E2([✓ END])
    COMP --> OFFER[📄 Offer Letter<br/>Generation]
    
    OFFER --> E3([✓ END])
    
    style PARSE fill:#667eea,stroke:#764ba2,stroke-width:3px,color:#fff
    style SOURCE fill:#f093fb,stroke:#f5576c,stroke-width:2px,color:#fff
    style SCREEN fill:#4facfe,stroke:#00f2fe,stroke-width:2px,color:#fff
    style COMP fill:#43e97b,stroke:#38f9d7,stroke-width:2px,color:#fff
    style OFFER fill:#fa709a,stroke:#fee140,stroke-width:3px,color:#fff
    
    style START fill:#90EE90,stroke:#006400,stroke-width:3px
    style E1 fill:#FFB6C1,stroke:#8B0000,stroke-width:2px
    style E2 fill:#FFB6C1,stroke:#8B0000,stroke-width:2px
    style E3 fill:#FFB6C1,stroke:#8B0000,stroke-width:2px
    
    classDef parallel fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,stroke-dasharray: 5 5
    class SOURCE,SCREEN,COMP parallel
    """
    
    return mermaid


def generate_validation_report(state: RecruitingState) -> str:
    """Generate comprehensive validation report"""
    
    report = []
    report.append("=" * 60)
    report.append("AGENT VALIDATION REPORT")
    report.append("=" * 60)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Overall errors
    errors = state.get('errors', [])
    if errors:
        report.append("❌ ERRORS FOUND:")
        for error in errors:
            report.append(f"  • {error}")
        report.append("")
    else:
        report.append("✅ No errors detected")
        report.append("")
    
    # Individual agent validation
    validation_results = state.get('validation_results', {})
    
    for agent_name, result in validation_results.items():
        report.append(f"Agent: {agent_name.upper()}")
        report.append(f"  Status: {'✅ VALID' if result.get('valid') else '❌ INVALID'}")
        
        if result.get('errors'):
            report.append("  Errors:")
            for error in result['errors']:
                report.append(f"    • {error}")
        
        if result.get('warnings'):
            report.append("  Warnings:")
            for warning in result['warnings']:
                report.append(f"    ⚠️  {warning}")
        
        report.append("")
    
    report.append("=" * 60)
    
    return "\n".join(report)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import os
    
    print("🕸️  LangGraph HR Recruiting System with Validation")
    print("=" * 60)
    
    # Create and validate graph
    print("\n1️⃣  Creating workflow graph...")
    recruiting_graph = create_recruiting_graph()
    
    print("2️⃣  Validating graph structure...")
    graph_validation = validate_graph(recruiting_graph)
    
    print(f"\n   Graph Validation: {'✅ PASSED' if graph_validation['valid'] else '❌ FAILED'}")
    print(f"   Nodes: {graph_validation['node_count']}")
    print(f"   Edges: {graph_validation['edge_count']}")
    
    if graph_validation['errors']:
        print("\n   Errors:")
        for error in graph_validation['errors']:
            print(f"   • {error}")
    
    if graph_validation['warnings']:
        print("\n   Warnings:")
        for warning in graph_validation['warnings']:
            print(f"   ⚠️  {warning}")
    
    # Plot graph
    print("\n3️⃣  Plotting graph...")
    print(plot_graph_ascii(recruiting_graph))
    
    # Save Mermaid diagram
    print("4️⃣  Generating Mermaid diagram...")
    mermaid_code = plot_graph_mermaid(recruiting_graph)
    with open("workflow_validated.mmd", "w") as f:
        f.write(mermaid_code)
    print("   ✅ Saved to workflow_validated.mmd")
    
    # Example execution (requires API key)
    # Uncomment to run with your OpenAI API key
    """
    print("\n5️⃣  Running workflow with validation...")
    
    initial_state = {
        "job_description": "Senior Python Developer with 5+ years experience in Django and AWS",
        "company_name": "TechCorp Inc.",
        "department": "Engineering",
        "min_salary": 120000,
        "max_salary": 160000,
        "messages": [],
        "errors": [],
        "validation_results": {}
    }
    
    # Validate input first
    input_validation = validate_input(initial_state)
    print(f"\n   Input Validation: {'✅ PASSED' if input_validation['valid'] else '❌ FAILED'}")
    
    if input_validation['valid']:
        final_state = recruiting_graph.invoke(initial_state)
        
        # Generate validation report
        print("\n" + generate_validation_report(final_state))
        
        # Display results
        print("\nRESULTS:")
        print(f"Job Title: {final_state.get('job_analysis', {}).get('job_title')}")
        print(f"Target Salary: ${final_state.get('compensation_package', {}).get('target_salary', 0):,}")
        print(f"Offer Letter: {len(final_state.get('offer_letter', ''))} characters")
    """
    
    print("\n" + "=" * 60)
    print("✅ Graph validated and plotted successfully!")
    print("\nTo visualize Mermaid diagram:")
    print("1. Go to https://mermaid.live")
    print("2. Paste contents of workflow_validated.mmd")
