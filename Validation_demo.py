"""
Standalone Agent Validation and Graph Plotting Demo
Works without LangGraph - demonstrates the concepts
"""

import json
from typing import Dict, Any, List
from datetime import datetime

# ============================================================================
# VALIDATION FRAMEWORK
# ============================================================================

class AgentValidator:
    """Validates agent inputs and outputs"""
    
    @staticmethod
    def validate_input(state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input parameters"""
        errors = []
        warnings = []
        
        # Job description validation
        job_desc = state.get('job_description', '')
        if not job_desc or len(job_desc.strip()) < 50:
            errors.append("❌ Job description must be at least 50 characters")
        elif len(job_desc) > 5000:
            warnings.append("⚠️  Very long job description - may increase processing time")
        
        # Company name validation
        if not state.get('company_name'):
            errors.append("❌ Company name is required")
        
        # Department validation
        if not state.get('department'):
            warnings.append("⚠️  Department not specified - using 'General'")
        
        # Salary validation
        min_sal = state.get('min_salary', 0)
        max_sal = state.get('max_salary', 0)
        
        if min_sal <= 0 or max_sal <= 0:
            errors.append("❌ Salary range must be positive numbers")
        elif min_sal >= max_sal:
            errors.append("❌ Minimum salary must be less than maximum salary")
        elif min_sal < 20000:
            warnings.append("⚠️  Minimum salary seems very low")
        elif max_sal > 1000000:
            warnings.append("⚠️  Maximum salary seems very high")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def validate_agent_output(agent_name: str, output: Any, expected_fields: List[str]) -> Dict[str, Any]:
        """Validate agent output structure"""
        errors = []
        warnings = []
        
        if not isinstance(output, dict):
            errors.append(f"❌ {agent_name}: Output must be a dictionary, got {type(output).__name__}")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Check for expected fields
        missing_fields = [field for field in expected_fields if field not in output]
        if missing_fields:
            errors.append(f"❌ {agent_name}: Missing required fields: {', '.join(missing_fields)}")
        
        # Check for empty values
        for field in expected_fields:
            if field in output:
                value = output[field]
                if value is None:
                    warnings.append(f"⚠️  {agent_name}: Field '{field}' is None")
                elif isinstance(value, (list, dict, str)) and not value:
                    warnings.append(f"⚠️  {agent_name}: Field '{field}' is empty")
        
        # Type checking
        type_hints = {
            'required_skills': list,
            'responsibilities': list,
            'platforms': list,
            'screening_questions': list,
            'benefits_package': list,
            'target_salary': (int, float),
            'job_title': str,
            'experience_level': str
        }
        
        for field, expected_type in type_hints.items():
            if field in output and output[field] is not None:
                if not isinstance(output[field], expected_type):
                    warnings.append(
                        f"⚠️  {agent_name}: Field '{field}' should be {expected_type}, "
                        f"got {type(output[field]).__name__}"
                    )
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'fields_checked': len(expected_fields),
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def validate_workflow_results(results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete workflow results"""
        errors = []
        warnings = []
        
        required_agents = ['job_parser', 'candidate_sourcing', 'screening', 'compensation', 'offer_letter']
        
        # Check all agents completed
        missing_agents = [agent for agent in required_agents if agent not in results]
        if missing_agents:
            errors.append(f"❌ Missing results from agents: {', '.join(missing_agents)}")
        
        # Check for errors in individual results
        for agent_name, result in results.items():
            if isinstance(result, dict) and result.get('error'):
                errors.append(f"❌ {agent_name} reported error: {result['error']}")
        
        # Cross-agent validation
        if 'compensation' in results and 'offer_letter' in results:
            comp_salary = results['compensation'].get('target_salary', 0)
            if comp_salary == 0:
                warnings.append("⚠️  Compensation has no target salary for offer letter")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'agents_completed': len([a for a in required_agents if a in results]),
            'total_agents': len(required_agents),
            'timestamp': datetime.now().isoformat()
        }


# ============================================================================
# GRAPH STRUCTURE VALIDATION
# ============================================================================

class WorkflowGraph:
    """Represents the workflow graph structure"""
    
    def __init__(self):
        self.nodes = []
        self.edges = []
    
    def add_node(self, name: str, description: str = ""):
        """Add a node to the graph"""
        self.nodes.append({
            'name': name,
            'description': description,
            'type': 'agent'
        })
    
    def add_edge(self, from_node: str, to_node: str, label: str = ""):
        """Add an edge between nodes"""
        self.edges.append({
            'from': from_node,
            'to': to_node,
            'label': label
        })
    
    def validate(self) -> Dict[str, Any]:
        """Validate graph structure"""
        errors = []
        warnings = []
        
        # Check for nodes
        if not self.nodes:
            errors.append("❌ Graph has no nodes")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Check for edges
        if not self.edges:
            warnings.append("⚠️  Graph has no edges (disconnected nodes)")
        
        # Check for entry point (START)
        has_start = any(node['name'] == 'START' for node in self.nodes)
        if not has_start:
            warnings.append("⚠️  No START node defined")
        
        # Check for exit point (END)
        has_end = any(edge['to'] == 'END' for edge in self.edges)
        if not has_end:
            warnings.append("⚠️  No edges connect to END")
        
        # Check for disconnected nodes
        connected_nodes = set()
        for edge in self.edges:
            connected_nodes.add(edge['from'])
            connected_nodes.add(edge['to'])
        
        disconnected = [node['name'] for node in self.nodes 
                       if node['name'] not in connected_nodes 
                       and node['name'] not in ['START', 'END']]
        
        if disconnected:
            warnings.append(f"⚠️  Disconnected nodes: {', '.join(disconnected)}")
        
        # Check for cycles (simple check)
        # More complex cycle detection would require graph traversal
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'node_count': len(self.nodes),
            'edge_count': len(self.edges),
            'connected_nodes': len(connected_nodes)
        }
    
    def plot_ascii(self) -> str:
        """Generate ASCII art representation"""
        
        ascii_art = """
╔════════════════════════════════════════════════════════════╗
║         HR RECRUITING WORKFLOW - VALIDATED GRAPH           ║
╚════════════════════════════════════════════════════════════╝

                        [🚀 START]
                            │
                            ▼
                ┌───────────────────────┐
                │  📋 Job Parser Agent  │ ← Validates input
                │  ✓ Extracts info      │   Checks structure
                └───────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │🔍 Sourcing   │ │✅ Screening  │ │💰 Compensation│
    │   Agent      │ │   Agent      │ │    Agent     │
    │✓ Platforms   │ │✓ Questions   │ │✓ Salary      │
    │✓ Keywords    │ │✓ Criteria    │ │✓ Benefits    │
    └──────────────┘ └──────────────┘ └──────────────┘
            │               │               │
            ▼               ▼               │
          [END]           [END]             ▼
                                    ┌──────────────┐
                                    │📄 Offer      │
                                    │   Letter     │
                                    │✓ Generated   │
                                    └──────────────┘
                                            │
                                            ▼
                                          [END]

VALIDATION POINTS:
═══════════════════════════════════════════════════════════
• Input validation before START
• Output validation after each agent
• Cross-agent validation for offer letter
• Final workflow validation at END

PARALLEL EXECUTION:
═══════════════════════════════════════════════════════════
✓ Sourcing, Screening, Compensation run simultaneously
✓ Offer Letter waits for Compensation to complete
        """
        
        return ascii_art
    
    def plot_mermaid(self) -> str:
        """Generate Mermaid diagram code"""
        
        mermaid = """graph TD
    START([🚀 START<br/>Input Validation]) --> PARSE[📋 Job Parser<br/>✓ Validates Structure<br/>✓ Extracts Fields]
    
    PARSE --> |Parallel| SOURCE[🔍 Sourcing Agent<br/>✓ Platforms<br/>✓ Keywords]
    PARSE --> |Parallel| SCREEN[✅ Screening Agent<br/>✓ Questions<br/>✓ Criteria]
    PARSE --> |Parallel| COMP[💰 Compensation<br/>✓ Salary Analysis<br/>✓ Benefits]
    
    SOURCE --> |Validated| E1([✓ END])
    SCREEN --> |Validated| E2([✓ END])
    COMP --> |Validated| OFFER[📄 Offer Letter<br/>✓ Generated<br/>✓ Cross-Validated]
    
    OFFER --> |Validated| E3([✓ END<br/>Final Report])
    
    style PARSE fill:#667eea,stroke:#764ba2,stroke-width:3px,color:#fff
    style SOURCE fill:#f093fb,stroke:#f5576c,stroke-width:2px,color:#fff
    style SCREEN fill:#4facfe,stroke:#00f2fe,stroke-width:2px,color:#fff
    style COMP fill:#43e97b,stroke:#38f9d7,stroke-width:2px,color:#fff
    style OFFER fill:#fa709a,stroke:#fee140,stroke-width:3px,color:#fff
    
    style START fill:#90EE90,stroke:#006400,stroke-width:3px
    style E1 fill:#98FB98,stroke:#228B22,stroke-width:2px
    style E2 fill:#98FB98,stroke:#228B22,stroke-width:2px
    style E3 fill:#FFD700,stroke:#FF8C00,stroke-width:3px
    
    classDef parallel fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,stroke-dasharray: 5 5
    classDef validated fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    class SOURCE,SCREEN,COMP parallel
    class PARSE,SOURCE,SCREEN,COMP,OFFER validated
        """
        
        return mermaid
    
    def generate_report(self) -> str:
        """Generate graph structure report"""
        
        report = []
        report.append("=" * 70)
        report.append("WORKFLOW GRAPH STRUCTURE REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Nodes
        report.append(f"NODES ({len(self.nodes)}):")
        for node in self.nodes:
            report.append(f"  • {node['name']}: {node.get('description', 'No description')}")
        report.append("")
        
        # Edges
        report.append(f"EDGES ({len(self.edges)}):")
        for edge in self.edges:
            label = f" ({edge['label']})" if edge.get('label') else ""
            report.append(f"  • {edge['from']} → {edge['to']}{label}")
        report.append("")
        
        # Validation
        validation = self.validate()
        report.append("VALIDATION:")
        report.append(f"  Status: {'✅ VALID' if validation['valid'] else '❌ INVALID'}")
        report.append(f"  Connected Nodes: {validation['connected_nodes']}/{validation['node_count']}")
        
        if validation['errors']:
            report.append("\n  ERRORS:")
            for error in validation['errors']:
                report.append(f"    {error}")
        
        if validation['warnings']:
            report.append("\n  WARNINGS:")
            for warning in validation['warnings']:
                report.append(f"    {warning}")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demo_validation():
    """Demonstrate validation features"""
    
    print("🔍 AGENT VALIDATION DEMO")
    print("=" * 70)
    
    # Test input validation
    print("\n1️⃣  INPUT VALIDATION")
    print("-" * 70)
    
    # Valid input
    valid_input = {
        'job_description': 'Senior Python Developer with 5+ years experience in Django and AWS. Must have strong problem-solving skills.',
        'company_name': 'TechCorp Inc.',
        'department': 'Engineering',
        'min_salary': 120000,
        'max_salary': 160000
    }
    
    result = AgentValidator.validate_input(valid_input)
    print(f"Valid Input Test: {'✅ PASSED' if result['valid'] else '❌ FAILED'}")
    if result['warnings']:
        for warning in result['warnings']:
            print(f"  {warning}")
    
    # Invalid input
    invalid_input = {
        'job_description': 'Short',  # Too short
        'company_name': '',  # Missing
        'min_salary': 200000,
        'max_salary': 100000  # Min > Max
    }
    
    result = AgentValidator.validate_input(invalid_input)
    print(f"\nInvalid Input Test: {'✅ PASSED' if not result['valid'] else '❌ FAILED (should be invalid)'}")
    print("Errors found:")
    for error in result['errors']:
        print(f"  {error}")
    
    # Test output validation
    print("\n2️⃣  OUTPUT VALIDATION")
    print("-" * 70)
    
    # Valid output
    valid_output = {
        'job_title': 'Senior Python Developer',
        'experience_level': '5+ years',
        'required_skills': ['Python', 'Django', 'AWS'],
        'responsibilities': ['Design systems', 'Lead team']
    }
    
    result = AgentValidator.validate_agent_output(
        'Job Parser',
        valid_output,
        ['job_title', 'experience_level', 'required_skills', 'responsibilities']
    )
    print(f"Valid Output Test: {'✅ PASSED' if result['valid'] else '❌ FAILED'}")
    
    # Invalid output
    invalid_output = {
        'job_title': 'Senior Python Developer',
        # Missing required fields
    }
    
    result = AgentValidator.validate_agent_output(
        'Job Parser',
        invalid_output,
        ['job_title', 'experience_level', 'required_skills', 'responsibilities']
    )
    print(f"\nInvalid Output Test: {'✅ PASSED' if not result['valid'] else '❌ FAILED (should be invalid)'}")
    print("Errors found:")
    for error in result['errors']:
        print(f"  {error}")
    
    # Test workflow validation
    print("\n3️⃣  WORKFLOW VALIDATION")
    print("-" * 70)
    
    complete_results = {
        'job_parser': {'job_title': 'Senior Dev'},
        'candidate_sourcing': {'platforms': ['LinkedIn']},
        'screening': {'questions': ['Q1', 'Q2']},
        'compensation': {'target_salary': 140000},
        'offer_letter': {'letter_text': 'Offer...'}
    }
    
    result = AgentValidator.validate_workflow_results(complete_results)
    print(f"Complete Workflow: {'✅ PASSED' if result['valid'] else '❌ FAILED'}")
    print(f"Agents Completed: {result['agents_completed']}/{result['total_agents']}")
    
    incomplete_results = {
        'job_parser': {'job_title': 'Senior Dev'},
        'screening': {'error': 'Failed to process'}
    }
    
    result = AgentValidator.validate_workflow_results(incomplete_results)
    print(f"\nIncomplete Workflow: {'✅ PASSED' if not result['valid'] else '❌ FAILED (should be invalid)'}")
    print(f"Agents Completed: {result['agents_completed']}/{result['total_agents']}")
    for error in result['errors']:
        print(f"  {error}")


def demo_graph_plotting():
    """Demonstrate graph plotting features"""
    
    print("\n\n🎨 GRAPH PLOTTING DEMO")
    print("=" * 70)
    
    # Build graph
    graph = WorkflowGraph()
    
    # Add nodes
    graph.add_node('START', 'Workflow entry point with input validation')
    graph.add_node('Job Parser', 'Extracts and validates job requirements')
    graph.add_node('Sourcing', 'Creates candidate sourcing strategy')
    graph.add_node('Screening', 'Develops screening criteria')
    graph.add_node('Compensation', 'Analyzes and recommends compensation')
    graph.add_node('Offer Letter', 'Generates professional offer letter')
    graph.add_node('END', 'Workflow completion')
    
    # Add edges
    graph.add_edge('START', 'Job Parser', 'validates input')
    graph.add_edge('Job Parser', 'Sourcing', 'parallel')
    graph.add_edge('Job Parser', 'Screening', 'parallel')
    graph.add_edge('Job Parser', 'Compensation', 'parallel')
    graph.add_edge('Sourcing', 'END', 'validated')
    graph.add_edge('Screening', 'END', 'validated')
    graph.add_edge('Compensation', 'Offer Letter', 'waits for comp')
    graph.add_edge('Offer Letter', 'END', 'validated')
    
    # Validate graph
    print("\n1️⃣  GRAPH VALIDATION")
    print("-" * 70)
    validation = graph.validate()
    print(f"Graph Structure: {'✅ VALID' if validation['valid'] else '❌ INVALID'}")
    print(f"Nodes: {validation['node_count']}")
    print(f"Edges: {validation['edge_count']}")
    print(f"Connected Nodes: {validation['connected_nodes']}")
    
    if validation['warnings']:
        print("\nWarnings:")
        for warning in validation['warnings']:
            print(f"  {warning}")
    
    # ASCII plot
    print("\n2️⃣  ASCII GRAPH")
    print(graph.plot_ascii())
    
    # Generate report
    print("\n3️⃣  STRUCTURE REPORT")
    print(graph.generate_report())
    
    # Save Mermaid diagram
    print("\n4️⃣  MERMAID DIAGRAM")
    print("-" * 70)
    mermaid_code = graph.plot_mermaid()
    with open('/home/claude/workflow_validated_demo.mmd', 'w') as f:
        f.write(mermaid_code)
    print("✅ Saved Mermaid diagram to: workflow_validated_demo.mmd")
    print("\nTo visualize:")
    print("1. Go to https://mermaid.live")
    print("2. Paste the diagram code")
    print("3. See your validated workflow!")


if __name__ == "__main__":
    print("🕸️  HR RECRUITING SYSTEM - VALIDATION & GRAPH PLOTTING")
    print("=" * 70)
    print()
    
    # Run demonstrations
    demo_validation()
    demo_graph_plotting()
    
    print("\n\n" + "=" * 70)
    print("✅ DEMO COMPLETE!")
    print("=" * 70)
    print("\nKey Features Demonstrated:")
    print("  ✓ Input validation (job description, salary range, etc.)")
    print("  ✓ Output validation (agent results, required fields)")
    print("  ✓ Workflow validation (all agents completed)")
    print("  ✓ Graph structure validation (nodes, edges, connectivity)")
    print("  ✓ ASCII graph plotting")
    print("  ✓ Mermaid diagram generation")
    print("  ✓ Comprehensive reporting")
