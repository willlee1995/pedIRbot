# LangSmith Observability Setup Guide

This guide explains how to set up and use LangSmith for observability and evaluation in the PedIR RAG bot.

## Overview

LangSmith provides:

- **Tracing**: Track all LLM calls, RAG pipeline steps, and API requests
- **Evaluation**: Monitor system performance and quality metrics
- **Feedback Collection**: Capture user feedback for continuous improvement
- **Monitoring**: View dashboards with latency, error rates, and other metrics

## Setup Instructions

### 1. Install LangSmith

The `langsmith` package has been added to `requirements.txt`. Install it with:

```bash
pip install langsmith
```

Or if using the requirements file:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Add the following to your `.env` file:

```env
# LangSmith Configuration
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<YOUR_LANGSMITH_API_KEY>
LANGSMITH_PROJECT=pedir-bot
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

**Important**: Replace `<YOUR_LANGSMITH_API_KEY>` with your actual API key from the LangSmith dashboard at https://smith.langchain.com/settings/api-keys

**Note**: Your LangSmith API key has been provided. Make sure to add it to your `.env` file (create one from `env.example` if it doesn't exist).

### 3. Verify Setup

Once the environment variables are set, LangSmith tracing will automatically be enabled when you start the application. You should see a log message like:

```
LangSmith tracing enabled for project: pedir-bot
```

## What's Being Traced

### Automatic Tracing

The following components are automatically traced:

1. **LLM Calls**: All LangChain LLM invocations (OpenAI and Ollama) are automatically traced
2. **RAG Pipeline**: The main `generate_response` function is traced with metadata
3. **Agentic RAG Nodes**:
   - `generate_query_or_respond` - Orchestrator node
   - `grade_documents` - Document grading node
   - `rewrite_question` - Question rewriting node
   - `generate_answer` - Final answer generation node
4. **API Endpoints**: The `/query` endpoint is traced with request/response details

### Trace Structure

Each trace includes:

- Inputs (queries, prompts, etc.)
- Outputs (responses, tool results, etc.)
- Metadata (model names, node types, component names)
- Timing information (latency, token usage)
- Error information (if any)

## Using LangSmith Dashboard

### Viewing Traces

1. Navigate to [https://smith.langchain.com](https://smith.langchain.com)
2. Log in with your LangSmith account
3. Select the `pedir-bot` project
4. View traces in the "Traces" tab

### Filtering Traces

You can filter traces by:

- **Metadata**: Filter by `component`, `node`, `endpoint`, etc.
- **Time Range**: Filter by date/time
- **Status**: Filter by success/failure
- **Model**: Filter by LLM provider/model

### Monitoring Dashboard

View monitoring charts in the "Monitor" tab:

- Request counts over time
- Average latency
- Error rates
- Token usage
- Feedback scores (after collecting feedback)

### A/B Testing

Group monitoring charts by metadata attributes to compare:

- Different LLM models
- Different retrieval strategies
- Different prompt versions

## Feedback Collection

### API Endpoint

The API now includes a `/feedback` endpoint for collecting user feedback:

```bash
POST /feedback
{
    "run_id": "uuid-from-query-response",
    "score": 0.8,  # 0.0 to 1.0
    "comment": "Very helpful response"  # Optional
}
```

### Using Feedback

1. Get `run_id` from query response:

   ```python
   response = client.post("/query", json={"query": "What is PICC?"})
   run_id = response.json()["run_id"]
   ```

2. Submit feedback:

   ```python
   client.post("/feedback", json={
       "run_id": run_id,
       "score": 0.9,
       "comment": "Accurate and helpful"
   })
   ```

3. View feedback in LangSmith dashboard:
   - Go to the "Traces" tab
   - Click on a trace to view associated feedback
   - Filter traces by feedback score

## Evaluation Setup

For systematic evaluation:

1. Run evaluation scripts (e.g., `scripts/run_evaluation.py`)
2. Traces will be automatically created for each evaluation run
3. View evaluation results in LangSmith:
   - Filter by evaluation metadata
   - Compare different model configurations
   - Track improvements over time

## Advanced Usage

### Adding Custom Metadata

You can add custom metadata to traces by modifying the `@traceable` decorators:

```python
@traceable(
    name="custom_function",
    metadata={
        "custom_key": "custom_value",
        "version": "1.0.0"
    }
)
def my_function():
    ...
```

### Runtime Metadata

For metadata that's only known at runtime, pass it via `langsmith_extra`:

```python
rag_pipeline.generate_response(
    query="What is PICC?",
    langsmith_extra={
        "metadata": {
            "user_id": "user123",
            "session_id": "session456"
        }
    }
)
```

## Troubleshooting

### Tracing Not Working

1. **Check environment variables**: Ensure `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` is set
2. **Check logs**: Look for "LangSmith tracing enabled" message
3. **Verify API key**: Test the API key in LangSmith dashboard

### No Traces in Dashboard

1. **Check project name**: Ensure `LANGSMITH_PROJECT` matches the project name in dashboard
2. **Check time range**: Traces may be in a different time range
3. **Check filters**: Remove any active filters in the dashboard

### Feedback Not Saving

1. **Verify LangSmith client**: Check that `langsmith_client` is initialized in `api.py`
2. **Check API key**: Ensure the API key has permissions to create feedback
3. **Check run_id**: Ensure the `run_id` exists in LangSmith (trace must be created first)

## Best Practices

1. **Use consistent project names**: Use different projects for development, staging, and production
2. **Add meaningful metadata**: Include version numbers, deployment info, etc.
3. **Collect feedback regularly**: User feedback helps identify improvement areas
4. **Monitor error rates**: Set up alerts for high error rates
5. **Review slow traces**: Identify bottlenecks by examining high-latency traces

## Additional Resources

- [LangSmith Documentation](https://docs.langchain.com/langsmith)
- [LangSmith Tutorial](https://docs.langchain.com/langsmith/observability-llm-tutorial)
- [LangSmith Python SDK](https://python.langchain.com/docs/langsmith)

## LangGraph Studio Integration

LangGraph Studio is a powerful IDE for visualizing, interacting with, and debugging your agent. It integrates seamlessly with LangSmith for tracing, evaluation, and prompt engineering.

### Prerequisites

- Python >= 3.11
- LangSmith API key (already configured above)
- `.env` file with `LANGSMITH_API_KEY` set

### Setup Steps

#### 1. Install LangGraph CLI

The `langgraph-cli` package has been added to `requirements.txt`. Install it with:

```bash
pip install --upgrade "langgraph-cli[inmem]"
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

#### 2. Install Project Dependencies

In the root of your project, install the project in editable mode:

**Using uv (Recommended - Much Faster):**

```bash
uv pip install -e .
```

**Using pip:**

```bash
pip install -e .
```

#### 3. Verify Configuration

The project already includes:

- `langgraph.json` - Configuration file pointing to the agent
- `src/langgraph_agent.py` - Entry point that exports the agent graph

The `langgraph.json` file is configured as:

```json
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./src/langgraph_agent.py:agent"
  },
  "env": ".env"
}
```

#### 4. Start LangGraph Server

Start the LangGraph development server:

```bash
langgraph dev
```

**Note for Safari users**: Safari blocks `localhost` connections to Studio. Use the `--tunnel` flag to access Studio via a secure tunnel:

```bash
langgraph dev --tunnel
```

#### 5. Access Studio UI

Once the server is running, you can access:

- **API endpoint**: `http://127.0.0.1:2024`
- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

### Using LangGraph Studio

#### Features

- **Visual Graph View**: See the complete flow of your agent with all nodes and edges
- **Step-by-Step Debugging**: Inspect each step of agent execution
- **Prompt Engineering**: Edit prompts and tool signatures with hot-reload
- **Replay Conversations**: Re-run conversations from any step to verify behavior
- **Tool Inspection**: See exact tool arguments, return values, and execution timing
- **Error Tracking**: View exceptions with surrounding state for easier debugging

#### Agent Chat UI in Studio

The Studio includes an Agent Chat UI for interactive evaluation:

1. **Open Studio**: Navigate to the Studio UI URL
2. **Select Thread**: Start a new conversation or continue an existing thread
3. **Send Messages**: Ask questions to test your agent
4. **View Execution**: See each step of the agent's decision-making process
5. **Inspect Tools**: Click on tool calls to see arguments and results
6. **Review Traces**: All interactions are automatically traced in LangSmith

### Using Standalone Agent Chat UI

LangChain provides a hosted Agent Chat UI that works with your local LangGraph server. This is separate from Studio and provides a clean chat interface.

#### Quick Start with Hosted Agent Chat UI

1. **Start your LangGraph server** (must be running):

   ```bash
   langgraph dev
   ```

   The server will start at `http://127.0.0.1:2024`

2. **Visit Agent Chat UI**:

   - Go to [https://smith.langchain.com/chat](https://smith.langchain.com/chat)
   - Or access via Studio: [https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)

3. **Configure Connection**:

   - **Graph ID**: Enter `agent` (this matches the graph name in your `langgraph.json`)
   - **Deployment URL**: `http://127.0.0.1:2024` (for local development)
   - **LangSmith API Key (optional)**: Add your LangSmith API key if you want tracing

4. **Start Chatting**: The UI will automatically detect and render tool calls, interrupts, and state changes.

#### Connection Settings Reference

Based on your `langgraph.json`:

```json
{
  "graphs": {
    "agent": "./src/langgraph_agent.py:agent"
  }
}
```

Your connection settings should be:

- **Graph ID**: `agent`
- **Deployment URL**: `http://127.0.0.1:2024` (local) or your deployed URL
- **LangSmith API Key**: Your key from `.env` (optional but recommended)

#### Features of Agent Chat UI

- **Real-time Chat**: Interactive conversation interface
- **Tool Visualization**: Automatically renders tool calls and results
- **Time-travel Debugging**: Navigate through conversation history
- **State Inspection**: View and modify agent state at any point
- **Human-in-the-loop**: Built-in support for reviewing agent requests
- **Generative UI**: Supports dynamic UI generation (if implemented in your agent)

#### Troubleshooting Agent Chat UI Connection

**Issue: "Failed to connect" or connection timeout**

1. **Verify server is running**:

   ```bash
   # Check if server is running on port 2024
   curl http://127.0.0.1:2024/health
   ```

2. **Check Graph ID**: Ensure you're using `agent` (from your `langgraph.json`)

3. **Check URL format**: Use `http://127.0.0.1:2024` (not `http://localhost:2024` if you have DNS issues)

4. **Check firewall**: Ensure your firewall allows connections to port 2024

5. **Update LangGraph CLI**: Ensure you have the latest version:
   ```bash
   uv pip install --upgrade "langgraph-cli[inmem]>=0.0.40"
   ```

**Issue: "AttributeError: 'EventSourceResponse' object has no attribute 'listen_for_exit_signal'"**

This indicates a version mismatch. Update LangGraph CLI:

```bash
uv pip install --upgrade "langgraph-cli[inmem]"
```

**Issue: Tools not showing in UI**

- Ensure your agent uses `create_agent` or properly defines tools in your LangGraph
- Check that tool calls are properly formatted as LangChain tool messages
- Verify tool definitions in `src/tools.py` are correct

#### Workflow Visualization

The agent graph structure includes:

- `generate_query_or_respond` - Orchestrator node that decides to retrieve or respond
- `retrieve` - Tool execution node for knowledge base retrieval
- `grade_documents` - Grading node that checks document relevance
- `rewrite_question` - Question rewriting node for better retrieval
- `generate_answer` - Final answer generation node

You can see the complete flow and conditional routing in Studio's visual graph view.

#### Hot Reload

Studio supports hot-reload:

1. Keep the `langgraph dev` server running
2. Edit prompts or tool signatures in your code
3. Studio will automatically reload changes
4. Re-run conversations to verify the changes

#### Thread Management

Studio maintains conversation threads:

- Each conversation is a separate thread
- Threads persist across Studio sessions
- Replay threads from any step to debug issues
- Compare different conversation flows

### Troubleshooting Studio

#### Server Won't Start

1. **Check Python version**: Ensure Python >= 3.11
2. **Check dependencies**: Run `pip install -e .` to install project dependencies
3. **Check .env file**: Ensure `LANGSMITH_API_KEY` is set
4. **Check port**: Port 2024 might be in use, check for conflicts

#### Agent Not Loading

1. **Check langgraph.json**: Verify the path to the agent entry point
2. **Check imports**: Ensure all dependencies are installed
3. **Check logs**: Look at the terminal output for import errors
4. **Verify vector store**: Ensure the ChromaDB collection exists

#### Studio Not Connecting

1. **Check server**: Verify `langgraph dev` is running
2. **Check URL**: Ensure the base URL matches `http://127.0.0.1:2024`
3. **Try tunnel**: Use `--tunnel` flag if on Safari
4. **Check firewall**: Ensure localhost connections are allowed

### Additional Resources

- [LangGraph Studio Documentation](https://docs.langchain.com/oss/python/langchain/studio)
- [LangGraph Configuration Reference](https://langchain-ai.github.io/langgraph/reference/cli/)
- [Agent Chat UI Guide](https://docs.langchain.com/oss/python/langchain/studio#agent-chat-ui)

## Next Steps

1. Set up your `.env` file with the LangSmith API key
2. Install LangGraph CLI: `pip install --upgrade "langgraph-cli[inmem]"`
3. Start LangGraph server: `langgraph dev`
4. Open Studio UI and interact with your agent
5. Check the LangSmith dashboard to see traces from Studio interactions
6. Use the Agent Chat UI for interactive evaluation and testing
7. Set up monitoring dashboards for key metrics
8. Implement feedback collection in your frontend (if applicable)
