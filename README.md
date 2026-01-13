"# LangGraph Tutorial

This repository contains a collection of examples demonstrating the usage of LangGraph for building stateful, multi-agent systems with conditional logic, tool integration, and persistent storage.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd agent
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install langgraph langchain-core langchain-google-genai python-dotenv
   ```

## Requirements

- Python 3.8+
- Google API Key (for Google Generative AI integration)

## Setup

1. Copy the `.env` file and add your Google API key:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

## Files Overview

### Basic Examples
- `GRAPHS/1_basic_graph.py` - Basic LangGraph usage with StateGraph
- `GRAPHS/2_conditional_edges.py` - Conditional routing in graphs
- `GRAPHS/3_conditional_loop.py` - Loops with conditional logic

### Advanced Examples
- `GRAPHS/4_persist_storage.py` - Persistent storage with MemorySaver
- `GRAPHS/5_tool_usage.py` - Tool integration with agents
- `GRAPHS/6_agent_with_tool_routing.py` - Agent with tool routing
- `GRAPHS/7_multi_agent_graph.py` - Multi-agent systems
- `GRAPHS/8_advanced_multi_agent.py` - Advanced multi-agent patterns
- `GRAPHS/9_subgraph_composition.py` - Subgraph composition

### Documentation
- `GRAPHS/10_advanced_theory.md` - Advanced theory and concepts

## Usage

Each Python file contains runnable examples. Start with the basic examples and progress to more advanced ones. Make sure to set your `GOOGLE_API_KEY` in the `.env` file before running examples that use Google Generative AI.

Example:
```bash
python GRAPHS/1_basic_graph.py
```

## Dependencies

- `langgraph` - Core LangGraph library for building graphs
- `langchain-core` - Core LangChain components
- `langchain-google-genai` - Google Generative AI integration
- `python-dotenv` - Environment variable management" 
