# 🕸️ LangGraph Multi-Agent HR Recruiting System

## Overview

This is an advanced version of the HR recruiting system that uses **LangGraph** for workflow orchestration. LangGraph provides a powerful framework for building multi-agent systems with clear graph-based execution flows.

## What is LangGraph?

LangGraph is a library for building stateful, multi-agent applications with LLMs. It allows you to:

- **Define workflows as graphs** with nodes (agents) and edges (transitions)
- **Manage state** across the entire workflow
- **Execute agents in parallel** or sequentially based on dependencies
- **Visualize workflows** to understand execution flow
- **Handle complex routing** and conditional logic

## System Architecture

### Graph Structure

```
                    START
                      ↓
              ┌──────────────┐
              │  Job Parser  │
              │    Agent     │
              └──────────────┘
                      ↓
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
   ┌────────┐   ┌─────────┐   ┌──────────┐
   │Sourcing│   │Screening│   │  Comp    │
   │ Agent  │   │  Agent  │   │  Agent   │
   └────────┘   └─────────┘   └──────────┘
        ↓             ↓             ↓
       END           END            ↓
                              ┌──────────┐
                              │  Offer   │
                              │  Letter  │
                              │  Agent   │
                              └──────────┘
                                    ↓
                                   END
```

### Key Components

1. **State Object** (`RecruitingState`):
   - Flows through the entire graph
   - Contains all inputs and outputs
   - Tracks workflow progress

2. **Nodes** (Agents):
   - Each node is a function that processes the state
   - Uses OpenAI GPT-4 for intelligent processing
   - Returns updated state

3. **Edges**:
   - Define execution order and dependencies
   - Enable parallel execution where possible
   - Control workflow routing

## Installation

```bash
# Install all dependencies
pip install -r requirements_langgraph.txt

# Or install individually
pip install streamlit openai langgraph langchain langchain-openai
```

## Usage

### Option 1: Command Line Execution

```python
# Run the standalone LangGraph script
python langgraph_recruiting.py
```

This will:
1. Create the workflow graph
2. Display a text visualization
3. Execute the workflow with example data
4. Print results

### Option 2: Streamlit Web Interface

```bash
# Run the Streamlit app
streamlit run app_langgraph.py
```

This provides:
- Visual graph representation
- Interactive workflow execution
- Real-time status updates
- Detailed result views

## How It Works

### 1. Define State

```python
class RecruitingState(TypedDict):
    # Inputs
    job_description: str
    company_name: str
    department: str
    min_salary: int
    max_salary: int
    
    # Outputs
    job_analysis: dict
    sourcing_strategy: dict
    screening_criteria: dict
    compensation_package: dict
    offer_letter: str
    
    # Metadata
    messages: Annotated[Sequence[BaseMessage], operator.add]
```

### 2. Create Agent Nodes

Each agent is a function that:
- Receives the current state
- Calls OpenAI GPT-4 with specialized prompts
- Updates the state with results
- Returns the modified state

```python
def job_parser_agent(state: RecruitingState) -> RecruitingState:
    llm = ChatOpenAI(model="gpt-4o-mini")
    # ... prompt and processing
    state['job_analysis'] = result
    return state
```

### 3. Build the Graph

```python
workflow = StateGraph(RecruitingState)

# Add nodes
workflow.add_node("parse_job", job_parser_agent)
workflow.add_node("source_candidates", candidate_sourcing_agent)
# ... more nodes

# Define edges
workflow.add_edge("parse_job", "source_candidates")
workflow.add_edge("parse_job", "create_screening")
# ... more edges

# Compile
app = workflow.compile()
```

### 4. Execute the Workflow

```python
initial_state = {
    "job_description": "...",
    "company_name": "...",
    # ... other inputs
}

# Run the graph
final_state = app.invoke(initial_state)
```

## Advantages of LangGraph Approach

### 1. **Clear Workflow Visualization**
- See exactly how agents are connected
- Understand dependencies at a glance
- Easy to debug and modify

### 2. **State Management**
- Central state object flows through all agents
- No need to manually pass data between agents
- Automatic state tracking and history

### 3. **Parallel Execution**
- LangGraph automatically parallelizes independent nodes
- Sourcing, Screening, and Compensation run simultaneously
- Maximum efficiency without manual async code

### 4. **Conditional Routing**
- Can add conditional edges based on state
- Route to different agents based on conditions
- Handle errors and retries gracefully

### 5. **Extensibility**
- Easy to add new agents (just add a node)
- Simple to modify workflow (change edges)
- Can create complex multi-path workflows

## Comparison: Async vs LangGraph

### Original Async Approach
```python
# Manual parallel execution
tasks = [
    asyncio.create_task(agent1.process()),
    asyncio.create_task(agent2.process()),
]
results = await asyncio.gather(*tasks)
```

**Pros:**
- Direct control
- Lighter dependencies

**Cons:**
- Manual state management
- No visualization
- Complex for large workflows

### LangGraph Approach
```python
# Declarative graph definition
workflow.add_node("agent1", agent1_func)
workflow.add_node("agent2", agent2_func)
workflow.add_edge("agent1", "agent2")
final_state = workflow.compile().invoke(initial_state)
```

**Pros:**
- Automatic parallelization
- Built-in state management
- Visual workflow representation
- Easy to extend and modify

**Cons:**
- Additional dependencies
- Slight learning curve

## Advanced Features

### 1. Conditional Edges

```python
def should_generate_offer(state: RecruitingState) -> str:
    if state['compensation_package']['target_salary'] > 0:
        return "generate_offer"
    return "skip_offer"

workflow.add_conditional_edges(
    "analyze_compensation",
    should_generate_offer,
    {
        "generate_offer": "generate_offer",
        "skip_offer": END
    }
)
```

### 2. Error Handling

```python
def safe_agent_wrapper(agent_func):
    def wrapper(state: RecruitingState) -> RecruitingState:
        try:
            return agent_func(state)
        except Exception as e:
            state['error'] = str(e)
            state['messages'].append(HumanMessage(f"Error: {e}"))
            return state
    return wrapper
```

### 3. Streaming Results

```python
# Stream results as they complete
for event in app.stream(initial_state):
    print(f"Event: {event}")
```

## Visualization Options

### 1. Text Visualization (Built-in)
```python
print(graph.get_graph().draw_ascii())
```

### 2. Mermaid Diagram
```python
png_data = graph.get_graph().draw_mermaid_png()
```

### 3. Interactive (Streamlit)
See `app_langgraph.py` for full interactive visualization

## Extending the System

### Adding a New Agent

1. **Create the agent function:**
```python
def interview_scheduler_agent(state: RecruitingState) -> RecruitingState:
    llm = ChatOpenAI(model="gpt-4o-mini")
    # ... your logic
    state['interview_schedule'] = result
    return state
```

2. **Add to the graph:**
```python
workflow.add_node("schedule_interview", interview_scheduler_agent)
workflow.add_edge("create_screening", "schedule_interview")
workflow.add_edge("schedule_interview", END)
```

3. **Update the state definition:**
```python
class RecruitingState(TypedDict):
    # ... existing fields
    interview_schedule: dict  # Add new field
```

### Adding Conditional Logic

```python
def check_budget(state: RecruitingState) -> str:
    target = state['compensation_package']['target_salary']
    max_budget = state['max_salary']
    
    if target <= max_budget:
        return "approve"
    else:
        return "review"

workflow.add_conditional_edges(
    "analyze_compensation",
    check_budget,
    {
        "approve": "generate_offer",
        "review": "budget_review_agent"
    }
)
```

## Performance Considerations

### Parallel Execution
LangGraph automatically parallelizes these nodes:
- `source_candidates`
- `create_screening`  
- `analyze_compensation`

They all start after `parse_job` completes.

### API Costs
With GPT-4o-mini:
- Job Parser: ~$0.01
- Sourcing: ~$0.01
- Screening: ~$0.01
- Compensation: ~$0.01
- Offer Letter: ~$0.02

**Total: ~$0.06 per workflow execution**

## Troubleshooting

### Graph won't compile
```python
# Check for cycles
graph.get_graph().print_ascii()

# Ensure all nodes have paths to END
```

### State not updating
```python
# Make sure to return the modified state
def agent(state):
    state['field'] = value
    return state  # Don't forget this!
```

### Parallel execution not working
```python
# Check edges - parallel nodes should branch from same source
workflow.add_edge("source", "parallel1")
workflow.add_edge("source", "parallel2")  # Both from "source"
```

## Best Practices

1. **Keep agents focused**: Each agent should do one thing well
2. **Use type hints**: Helps catch errors early
3. **Log progress**: Add messages to track execution
4. **Handle errors**: Wrap agents in try-catch
5. **Validate state**: Check required fields before processing
6. **Document nodes**: Add docstrings to agent functions
7. **Test incrementally**: Build graph step by step

## Resources

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **LangChain Docs**: https://python.langchain.com/
- **OpenAI API**: https://platform.openai.com/docs

## Next Steps

1. **Add more agents**: Interview scheduling, reference checking, etc.
2. **Add persistence**: Save state to database
3. **Add human-in-the-loop**: Approval steps
4. **Add streaming**: Real-time updates
5. **Add memory**: Context across multiple runs
6. **Deploy**: Host on Streamlit Cloud or similar

---

**Built with LangGraph, LangChain, and OpenAI GPT-4** 🚀
