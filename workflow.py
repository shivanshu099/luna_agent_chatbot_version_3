import os
from dotenv import load_dotenv

load_dotenv()

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from tools import tool_define

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

def create_workflow(provider: str = "groq", ollama_model: str = "llama"):
    tools = tool_define()
    
    # Initialize the LLM based on user choice
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.5).bind_tools(tools)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=ollama_model, temperature=0.5).bind_tools(tools)
    else:  # groq default
        from langchain_groq import ChatGroq
        llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.0).bind_tools(tools)

    def agent_node(state: AgentState):
        from langchain_core.messages import SystemMessage
        
        system_prompt = (
            "You are Luna, a highly capable AI assistant created by Shivanshu Prajapati. "
            "Respond in a natural, conversational tone with short sentences and occasional thoughtful pauses using punctuation like '...' or ',' when appropriate."
            "You are smart, polite, and eager to help. You have access to a suite of desktop tools "
            "allowing you to read files, manage to-do lists, check the latest news, capture "
            "screenshots, search Google Maps, send emails, and control local audio. Use these tools "
            "effectively when the user asks you to perform corresponding actions.\n\n"
            "MEMORY INSTRUCTIONS: You have long-term memory powered by ChromaDB. "
            "1. PROACTIVELY SAVE: When the user shares personal details (name, birthday, preferences, "
            "likes/dislikes, work info, family details, goals, or any important fact), ALWAYS use the "
            "save_memory tool to store it WITHOUT being asked. Categorize memories as: 'personal', "
            "'preference', 'fact', 'work', or 'general'.\n"
            "2. PROACTIVELY RECALL: When the user asks a question that might relate to something they "
            "told you before, use search_memory to check your memory first before responding.\n"
            "3. When the user asks 'what do you remember about me' or similar, use view_all_memories.\n\n"
            "CRITICAL TOOL INSTRUCTION: When outputting tool calls, you MUST NOT forget the closing angle bracket `>` for the function name tag. "
            "For example, you must output `<function=search_google_maps>{\"query\":\"...\"}</function>`. "
            "NEVER output `<function=search_google_maps{\"query\":...` without the `>`."
        )
        
        
        messages = list(state["messages"])
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=system_prompt))
            
        response = llm.invoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        return END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        },
    )

    workflow.add_edge("tools", "agent")

    app = workflow.compile()
    return app






