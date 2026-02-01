"""
Generate Mermaid diagram for the HR Recruiting Workflow
This can be pasted into Mermaid Live Editor: https://mermaid.live
"""

def generate_mermaid_diagram():
    """Generate Mermaid diagram syntax for the workflow"""
    
    diagram = """
graph TD
    START([START]) --> A[Job Parser Agent]
    
    A --> B[Candidate Sourcing Agent]
    A --> C[Screening Agent]
    A --> D[Compensation Agent]
    
    B --> END1([END])
    C --> END2([END])
    D --> E[Offer Letter Agent]
    
    E --> END3([END])
    
    style A fill:#667eea,stroke:#764ba2,stroke-width:3px,color:#fff
    style B fill:#f093fb,stroke:#f5576c,stroke-width:2px,color:#fff
    style C fill:#4facfe,stroke:#00f2fe,stroke-width:2px,color:#fff
    style D fill:#43e97b,stroke:#38f9d7,stroke-width:2px,color:#fff
    style E fill:#fa709a,stroke:#fee140,stroke-width:3px,color:#fff
    
    style START fill:#90EE90,stroke:#006400,stroke-width:2px
    style END1 fill:#FFB6C1,stroke:#8B0000,stroke-width:2px
    style END2 fill:#FFB6C1,stroke:#8B0000,stroke-width:2px
    style END3 fill:#FFB6C1,stroke:#8B0000,stroke-width:2px
    
    classDef parallel fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,stroke-dasharray: 5 5
    class B,C,D parallel
"""
    
    return diagram


def generate_detailed_mermaid():
    """Generate detailed Mermaid diagram with more information"""
    
    diagram = """
graph TB
    subgraph "HR Recruiting Workflow - LangGraph"
        START([📍 START])
        
        START --> PARSE["📋 Job Parser Agent<br/>---<br/>Extract requirements<br/>Identify skills<br/>Parse qualifications"]
        
        PARSE --> PARALLEL{Parallel Execution}
        
        PARALLEL --> SOURCE["🔍 Candidate Sourcing<br/>---<br/>Platform recommendations<br/>Search keywords<br/>Sourcing strategy"]
        PARALLEL --> SCREEN["✅ Screening Agent<br/>---<br/>Interview questions<br/>Evaluation criteria<br/>Assessment plan"]
        PARALLEL --> COMP["💰 Compensation Agent<br/>---<br/>Market analysis<br/>Salary recommendations<br/>Benefits package"]
        
        SOURCE --> E1([🏁 END])
        SCREEN --> E2([🏁 END])
        COMP --> OFFER["📄 Offer Letter Agent<br/>---<br/>Generate offer letter<br/>Include all details<br/>Professional format"]
        
        OFFER --> E3([🏁 END])
    end
    
    style START fill:#90EE90,stroke:#006400,stroke-width:3px
    style PARSE fill:#667eea,stroke:#764ba2,stroke-width:3px,color:#fff
    style PARALLEL fill:#FFA500,stroke:#FF8C00,stroke-width:2px,color:#fff
    style SOURCE fill:#f093fb,stroke:#f5576c,stroke-width:2px,color:#fff
    style SCREEN fill:#4facfe,stroke:#00f2fe,stroke-width:2px,color:#fff
    style COMP fill:#43e97b,stroke:#38f9d7,stroke-width:2px,color:#fff
    style OFFER fill:#fa709a,stroke:#fee140,stroke-width:3px,color:#fff
    style E1 fill:#FFB6C1,stroke:#8B0000,stroke-width:2px
    style E2 fill:#FFB6C1,stroke:#8B0000,stroke-width:2px
    style E3 fill:#FFB6C1,stroke:#8B0000,stroke-width:2px
"""
    
    return diagram


def generate_sequence_diagram():
    """Generate sequence diagram showing agent interactions"""
    
    diagram = """
sequenceDiagram
    participant User
    participant Graph as LangGraph Orchestrator
    participant Parse as Job Parser
    participant Source as Sourcing Agent
    participant Screen as Screening Agent
    participant Comp as Compensation Agent
    participant Offer as Offer Letter Agent
    
    User->>Graph: Submit job description
    Graph->>Parse: Process job description
    Parse-->>Graph: Return job analysis
    
    par Parallel Execution
        Graph->>Source: Generate sourcing strategy
        and
        Graph->>Screen: Create screening criteria
        and
        Graph->>Comp: Analyze compensation
    end
    
    Source-->>Graph: Return sourcing plan
    Screen-->>Graph: Return screening questions
    Comp-->>Graph: Return compensation package
    
    Graph->>Offer: Generate offer letter
    Offer-->>Graph: Return offer letter
    
    Graph-->>User: Return complete results
"""
    
    return diagram


def generate_state_diagram():
    """Generate state diagram showing workflow states"""
    
    diagram = """
stateDiagram-v2
    [*] --> Initialized: Submit Job
    
    Initialized --> ParsingJob: Start Workflow
    ParsingJob --> ParsingComplete: Job Parsed
    
    ParsingComplete --> SourcingCandidates
    ParsingComplete --> CreatingScreening
    ParsingComplete --> AnalyzingCompensation
    
    SourcingCandidates --> SourcingComplete
    CreatingScreening --> ScreeningComplete
    AnalyzingCompensation --> CompensationComplete
    
    CompensationComplete --> GeneratingOffer
    GeneratingOffer --> OfferComplete
    
    SourcingComplete --> [*]
    ScreeningComplete --> [*]
    OfferComplete --> [*]
    
    note right of ParsingComplete
        Parallel execution starts here
        3 agents work simultaneously
    end note
    
    note right of GeneratingOffer
        Waits for compensation
        before generating offer
    end note
"""
    
    return diagram


def save_diagrams():
    """Save all diagrams to files"""
    
    diagrams = {
        "workflow_basic.mmd": generate_mermaid_diagram(),
        "workflow_detailed.mmd": generate_detailed_mermaid(),
        "workflow_sequence.mmd": generate_sequence_diagram(),
        "workflow_state.mmd": generate_state_diagram()
    }
    
    for filename, content in diagrams.items():
        with open(filename, 'w') as f:
            f.write(content.strip())
        print(f"✅ Saved {filename}")
    
    print("\n📊 To visualize these diagrams:")
    print("1. Go to https://mermaid.live")
    print("2. Paste the contents of any .mmd file")
    print("3. See your workflow visualized!")
    
    return diagrams


if __name__ == "__main__":
    print("🎨 Generating Mermaid diagrams for HR Recruiting Workflow...\n")
    
    diagrams = save_diagrams()
    
    print("\n" + "="*60)
    print("BASIC WORKFLOW DIAGRAM")
    print("="*60)
    print(diagrams["workflow_basic.mmd"])
    
    print("\n" + "="*60)
    print("To use in Markdown/GitHub, wrap in:")
    print("```mermaid")
    print("... paste diagram here ...")
    print("```")
    print("="*60)
