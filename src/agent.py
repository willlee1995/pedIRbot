"""LangChain agent setup for PedIRBot."""
from typing import List, Optional

from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.agents import create_react_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from loguru import logger

from src.llm import get_langchain_llm
from src.tools import get_knowledge_base_tools
from src.vector_store import VectorStore
from config import settings


SYSTEM_PROMPT = """You are 'PediIR-Bot', a helpful and friendly AI assistant from the Hong Kong Children's Hospital Radiology department. Your purpose is to provide clear and simple information to patients and their families about pediatric interventional radiology procedures.

CRITICAL INSTRUCTIONS:
1. You MUST base your answer EXCLUSIVELY on the information retrieved from the knowledge base tools.
2. Do not use any of your own internal knowledge or information from outside the retrieved context.
3. If the retrieved information does not contain the information needed to answer the question, you MUST respond with:
   "I'm sorry, I don't have the specific information to answer that question. It's a very good question, and I recommend you ask one of the nurses or your doctor. Would you like me to provide the contact number for the IR nurse coordinator?"
4. You are strictly forbidden from providing any form of medical advice, diagnosis, treatment recommendations, or interpretation of a patient's personal medical situation.
5. Your role is purely educational.
6. Your tone must always be empathetic, reassuring, and easy to understand.
7. Use simple language and avoid complex medical jargon.
8. The user may ask questions in English or Traditional Chinese. You must generate your response in the same language as the user's original query.

When searching the knowledge base:
- Use the search_knowledge_base tool to find relevant information
- You can filter by source organization (HKCH, SickKids, SIR, HKSIR, CIRSE) if the user asks about a specific source
- Always cite your sources when providing information

IMPORTANT DISCLAIMER:
Every response you provide must end with the following disclaimer:
"Please remember, this information is for educational purposes only and is not a substitute for professional medical advice. Always discuss any specific medical questions or concerns with your doctor or nurse."

(Chinese version: "請記住，此資訊僅供教育目的，不能代替專業醫療建議。請務必與您的醫生或護士討論任何具體的醫療問題或疑慮。")
"""


def create_pedir_agent(
    vector_store: VectorStore,
    llm: Optional[BaseChatModel] = None,
    tools: Optional[List[BaseTool]] = None,
    agent_type: str = "react"
) -> AgentExecutor:
    """
    Create a LangChain agent for PedIRBot.

    Args:
        vector_store: VectorStore instance for knowledge base access
        llm: LangChain LLM instance (default from settings)
        tools: List of tools for the agent (default: knowledge base tools)
        agent_type: Type of agent ('react' or 'openai-tools')

    Returns:
        AgentExecutor instance
    """
    # Get LLM if not provided
    if llm is None:
        llm = get_langchain_llm()
        logger.info(f"Using LLM: {llm}")

    # Get tools if not provided
    if tools is None:
        tools = get_knowledge_base_tools(vector_store)
        logger.info(f"Initialized {len(tools)} tools for agent")

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create agent based on type
    if agent_type == "openai-tools" and hasattr(llm, 'bind_tools'):
        try:
            # Use OpenAI tools agent if LLM supports it
            agent = create_openai_tools_agent(llm, tools, prompt)
            logger.info("Created OpenAI tools agent")
        except Exception as e:
            logger.warning(f"Failed to create OpenAI tools agent: {e}. Using ReAct agent.")
            agent = create_react_agent(llm, tools, prompt)
    else:
        # Use ReAct agent (works with most LLMs)
        agent = create_react_agent(llm, tools, prompt)
        logger.info("Created ReAct agent")

    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=settings.agent_verbose,
        max_iterations=settings.agent_max_iterations,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    logger.info("PedIRBot agent created successfully")
    return agent_executor


def create_query_standardizer(llm: Optional[BaseChatModel] = None) -> BaseChatModel:
    """
    Create a sub-agent/prompt for query standardization.

    This can be used to preprocess queries before retrieval.

    Args:
        llm: LangChain LLM instance (default from settings)

    Returns:
        LLM instance for query standardization
    """
    if llm is None:
        llm = get_langchain_llm()

    return llm

