from datetime import datetime  # Added datetime import
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder  # Added MessagesPlaceholder
from src.config.constants import DEFAULT_MODEL

def create_specialized_agent(name, description, tools):
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a friendly {name} agent in the insurance domain.
{description}
Respond in a conversational, helpful tone.
You have access to tools: {[t.name for t in tools]}
Current time: {datetime.now().strftime("%Y-%m-%d %H:%M")}"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    llm = ChatOpenAI(model=DEFAULT_MODEL)
    return AgentExecutor(
        agent=create_openai_tools_agent(llm, tools, prompt),
        tools=tools
    )