# LangSmith Integration Summary

## Overview

LangSmith observability and evaluation have been successfully integrated into the PedIR RAG bot. This enables comprehensive tracing, monitoring, and feedback collection for all LLM interactions.

## What Was Integrated

### 1. **Package Installation**

- Added `langsmith>=0.1.0` to `requirements.txt`

### 2. **Configuration**

- Added LangSmith settings to `config.py`:
  - `langsmith_tracing`: Enable/disable tracing
  - `langsmith_api_key`: Your API key
  - `langsmith_project`: Project name (default: "pedir-bot")
  - `langsmith_endpoint`: LangSmith API endpoint

### 3. **Automatic Tracing Setup**

- **LLM Initialization** (`src/llm.py`): Environment variables are automatically set when LangSmith is enabled
- All LangChain LLM calls (OpenAI and Ollama) are automatically traced

### 4. **Manual Tracing Decorators**

- **RAG Pipeline** (`src/rag_pipeline.py`): `generate_response()` method
- **Agentic RAG Nodes** (`src/agentic_rag.py`):
  - `generate_query_or_respond` - Orchestrator node
  - `grade_documents` - Document grading node
  - `rewrite_question` - Question rewriting node
  - `generate_answer` - Final answer generation node
- **API Endpoints** (`src/api.py`): Query processing function

### 5. **Feedback Collection**

- Added `/feedback` API endpoint for submitting user feedback
- Run ID tracking for associating feedback with traces
- Feedback includes score (0.0-1.0) and optional comments

### 6. **Documentation**

- Created comprehensive setup guide: `docs/LANGSMITH_SETUP.md`
- Updated `env.example` with LangSmith configuration variables

## Your LangSmith API Key

Your API key has been configured:

```
<YOUR_LANGSMITH_API_KEY>
```

**Important**: Replace `<YOUR_LANGSMITH_API_KEY>` with your actual API key from the LangSmith dashboard.

## Next Steps

1. **Install LangSmith** (if not already installed):

   ```bash
   pip install langsmith
   ```

2. **Configure Environment Variables**:
   Add to your `.env` file:

   ```env
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=<YOUR_LANGSMITH_API_KEY>
   LANGSMITH_PROJECT=pedir-bot
   LANGSMITH_ENDPOINT=https://api.smith.langchain.com
   ```

3. **Start the Application**:
   When you start the API server, you should see:

   ```
   LangSmith tracing enabled for project: pedir-bot
   ```

4. **View Traces**:

   - Navigate to https://smith.langchain.com
   - Select the "pedir-bot" project
   - View traces in real-time as you make queries

5. **Test Feedback Collection**:

   ```python
   # After making a query, get the run_id from the response
   response = client.post("/query", json={"query": "What is PICC?"})
   run_id = response.json()["run_id"]

   # Submit feedback
   client.post("/feedback", json={
       "run_id": run_id,
       "score": 0.9,
       "comment": "Very helpful!"
   })
   ```

## Trace Hierarchy

When you make a query, you'll see traces organized as:

```
api_query (API endpoint)
  └── rag_generate_response (RAG pipeline)
      └── LangGraph execution
          ├── generate_query_or_respond (Orchestrator)
          ├── retrieve (Tool execution)
          ├── grade_documents (Grader)
          ├── rewrite_question (Rewriter) [if needed]
          └── generate_answer (Answer generator)
              └── LLM calls (automatically traced)
```

## Features Enabled

✅ **Automatic LLM Tracing**: All LangChain LLM calls are traced
✅ **RAG Pipeline Tracing**: Full visibility into retrieval and generation
✅ **Node-level Tracing**: Individual agentic RAG nodes are traced
✅ **API Tracing**: Request/response tracing for API endpoints
✅ **Feedback Collection**: User feedback can be associated with traces
✅ **Metadata Support**: Custom metadata for filtering and analysis
✅ **Error Tracking**: Errors are automatically captured in traces

## Monitoring & Evaluation

Once you have traces:

- View latency metrics over time
- Monitor error rates
- Track token usage
- Filter by metadata (model, component, etc.)
- Compare different configurations (A/B testing)
- Review user feedback scores

## Documentation

See `docs/LANGSMITH_SETUP.md` for detailed usage instructions, troubleshooting, and best practices.

## Support

For LangSmith-specific issues:

- [LangSmith Documentation](https://docs.langchain.com/langsmith)
- [LangSmith Tutorial](https://docs.langchain.com/langsmith/observability-llm-tutorial)
