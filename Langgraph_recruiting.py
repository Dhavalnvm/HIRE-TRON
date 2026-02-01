"""
LangGraph Implementation of Multi-Agent HR Recruiting System
This version uses LangGraph for orchestration and graph visualization
"""

from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
import json

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
    
    # Metadata
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_step: str


# Agent Node Functions
def job_parser_agent(state: RecruitingState) -> RecruitingState:
    """Parse job description and extract structured information"""
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    system_prompt = """You are an expert HR analyst specializing in parsing job descriptions.
Extract and structure key information from job descriptions.
Return JSON with: job_title, experience_level, employment_type, required_skills (array), 
nice_to_have_skills (array), responsibilities (array), qualifications (array)."""
    
    user_message = f"""Analyze this job description:

Job Description: {state['job_description']}
Department: {state['department']}

Provide comprehensive analysis in JSON format."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    
    response = llm.invoke(messages)
    
    try:
        job_analysis = json.loads(response.content)
    except:
        job_analysis = {
            "job_title": "Software Engineer",
            "experience_level": "3+ years",
            "employment_type": "Full-time",
            "required_skills": ["Python"],
            "nice_to_have_skills": ["AWS"],
            "responsibilities": ["Develop software"],
            "qualifications": ["Bachelor's degree"]
        }
    
    state['job_analysis'] = job_analysis
    state['messages'] = state.get('messages', []) + [
        HumanMessage(content=f"Job Parser completed: {job_analysis.get('job_title')}")
    ]
    
    return state


def candidate_sourcing_agent(state: RecruitingState) -> RecruitingState:
    """Create candidate sourcing strategy"""
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    system_prompt = """You are an expert talent acquisition specialist.
Create comprehensive candidate sourcing strategies.
Return JSON with: platforms (array of {name, reason}), search_keywords (array), 
sourcing_channels (array), outreach_strategy (string), timeline (string)."""
    
    user_message = f"""Create sourcing strategy for:

Job Description: {state['job_description']}

Provide platforms, keywords, channels, outreach strategy, and timeline in JSON."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    
    response = llm.invoke(messages)
    
    try:
        sourcing_strategy = json.loads(response.content)
    except:
        sourcing_strategy = {
            "platforms": [{"name": "LinkedIn", "reason": "Professional network"}],
            "search_keywords": ["Python Developer"],
            "sourcing_channels": ["Job boards"],
            "outreach_strategy": "Direct outreach",
            "timeline": "2-4 weeks"
        }
    
    state['sourcing_strategy'] = sourcing_strategy
    state['messages'] = state.get('messages', []) + [
        HumanMessage(content=f"Sourcing strategy created with {len(sourcing_strategy.get('platforms', []))} platforms")
    ]
    
    return state


def screening_agent(state: RecruitingState) -> RecruitingState:
    """Create screening criteria and questions"""
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    system_prompt = """You are an expert HR interviewer.
Create comprehensive screening criteria and questions.
Return JSON with: must_have_criteria (array), nice_to_have_criteria (array), 
screening_questions (array), technical_assessment (string), evaluation_rubric (string)."""
    
    user_message = f"""Create screening materials for:

Job Description: {state['job_description']}

Include criteria, questions, assessment, and rubric in JSON."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    
    response = llm.invoke(messages)
    
    try:
        screening_criteria = json.loads(response.content)
    except:
        screening_criteria = {
            "must_have_criteria": ["Relevant experience"],
            "nice_to_have_criteria": ["Advanced skills"],
            "screening_questions": ["Tell me about your experience"],
            "technical_assessment": "Coding challenge",
            "evaluation_rubric": "Standard evaluation"
        }
    
    state['screening_criteria'] = screening_criteria
    state['messages'] = state.get('messages', []) + [
        HumanMessage(content=f"Screening criteria created with {len(screening_criteria.get('screening_questions', []))} questions")
    ]
    
    return state


def compensation_agent(state: RecruitingState) -> RecruitingState:
    """Analyze and create compensation package"""
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    system_prompt = """You are an expert compensation analyst.
Analyze market data and create competitive compensation packages.
Return JSON with: market_analysis (string), recommended_salary_range ({min, max}), 
target_salary (number), benefits_package (array), equity_structure (string), justification (string)."""
    
    user_message = f"""Create compensation package for:

Job Description: {state['job_description']}
Budget Range: ${state['min_salary']:,} - ${state['max_salary']:,}

Provide analysis, salary, benefits, equity, and justification in JSON."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    
    response = llm.invoke(messages)
    
    try:
        comp_package = json.loads(response.content)
    except:
        comp_package = {
            "market_analysis": "Competitive market",
            "recommended_salary_range": {"min": state['min_salary'], "max": state['max_salary']},
            "target_salary": (state['min_salary'] + state['max_salary']) // 2,
            "benefits_package": ["Health insurance", "PTO"],
            "equity_structure": "Standard equity",
            "justification": "Market competitive"
        }
    
    state['compensation_package'] = comp_package
    state['messages'] = state.get('messages', []) + [
        HumanMessage(content=f"Compensation package created: ${comp_package.get('target_salary', 0):,}")
    ]
    
    return state


def offer_letter_agent(state: RecruitingState) -> RecruitingState:
    """Generate professional offer letter"""
    
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

Job Description: {state['job_description']}

Benefits: {', '.join(benefits) if benefits else 'Competitive benefits package'}

Include: company header, position details, compensation, benefits, start date (TBD), 
contingencies, and signature section."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    
    response = llm.invoke(messages)
    
    state['offer_letter'] = response.content
    state['messages'] = state.get('messages', []) + [
        HumanMessage(content=f"Offer letter generated for {job_title}")
    ]
    
    return state


# Build the LangGraph
def create_recruiting_graph():
    """Create the LangGraph workflow for HR recruiting"""
    
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
    # Phase 1: Parse job first (needs to complete before sourcing/screening/compensation)
    workflow.add_edge("parse_job", "source_candidates")
    workflow.add_edge("parse_job", "create_screening")
    workflow.add_edge("parse_job", "analyze_compensation")
    
    # Phase 2: Generate offer letter after compensation is done
    workflow.add_edge("analyze_compensation", "generate_offer")
    
    # End conditions
    workflow.add_edge("source_candidates", END)
    workflow.add_edge("create_screening", END)
    workflow.add_edge("generate_offer", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app


# Visualization function
def visualize_graph(graph, output_path="recruiting_workflow.png"):
    """Visualize the LangGraph workflow"""
    try:
        from IPython.display import Image, display
        
        # Generate graph visualization
        png_data = graph.get_graph().draw_mermaid_png()
        
        # Save to file
        with open(output_path, "wb") as f:
            f.write(png_data)
        
        print(f"Graph visualization saved to {output_path}")
        
        # Try to display if in Jupyter
        try:
            display(Image(png_data))
        except:
            pass
            
    except Exception as e:
        print(f"Could not generate visualization: {e}")
        print("Generating text representation instead...")
        
        # Text representation
        print("\nWorkflow Graph Structure:")
        print("=" * 50)
        print("START")
        print("  ↓")
        print("parse_job (Job Parser Agent)")
        print("  ├──→ source_candidates (Sourcing Agent) → END")
        print("  ├──→ create_screening (Screening Agent) → END")
        print("  └──→ analyze_compensation (Compensation Agent)")
        print("         ↓")
        print("       generate_offer (Offer Letter Agent) → END")
        print("=" * 50)


# Example usage
if __name__ == "__main__":
    import os
    
    # Set OpenAI API key
    # os.environ["OPENAI_API_KEY"] = "your-api-key-here"
    
    # Create the graph
    recruiting_graph = create_recruiting_graph()
    
    # Visualize the workflow
    visualize_graph(recruiting_graph)
    
    # Example input
    initial_state = {
        "job_description": """Senior Python Developer
        
We're seeking an experienced Python developer with 5+ years experience.
Must have Django, AWS, and SQL knowledge. Will lead backend architecture.""",
        "company_name": "TechCorp Inc.",
        "department": "Engineering",
        "min_salary": 120000,
        "max_salary": 160000,
        "messages": []
    }
    
    # Run the workflow
    print("\nRunning workflow...")
    final_state = recruiting_graph.invoke(initial_state)
    
    # Print results
    print("\n" + "=" * 50)
    print("WORKFLOW COMPLETED")
    print("=" * 50)
    
    print(f"\nJob Title: {final_state.get('job_analysis', {}).get('job_title', 'N/A')}")
    print(f"Target Salary: ${final_state.get('compensation_package', {}).get('target_salary', 0):,}")
    print(f"Platforms: {len(final_state.get('sourcing_strategy', {}).get('platforms', []))}")
    print(f"Screening Questions: {len(final_state.get('screening_criteria', {}).get('screening_questions', []))}")
    print(f"\nOffer Letter Generated: {len(final_state.get('offer_letter', ''))} characters")
    
    # Print workflow messages
    print("\nWorkflow Steps:")
    for msg in final_state.get('messages', []):
        print(f"  • {msg.content}")
