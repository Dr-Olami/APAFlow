"""
Langfuse configuration for LLM observability and tracing
"""
import os
from langfuse import Langfuse
from langfuse.callback import CallbackHandler

# Initialize Langfuse client
def get_langfuse_handler():
    """
    Initialize Langfuse callback handler for LangChain integration
    
    Set these environment variables:
    - LANGFUSE_SECRET_KEY
    - LANGFUSE_PUBLIC_KEY
    - LANGFUSE_HOST (optional, defaults to https://cloud.langfuse.com)
    """
    return CallbackHandler(
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    )

# Example usage with LangChain
def create_traced_chain(llm, prompt_template):
    """
    Create a LangChain chain with Langfuse tracing
    """
    from langchain.chains import LLMChain
    
    langfuse_handler = get_langfuse_handler()
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt_template,
        callbacks=[langfuse_handler]
    )
    
    return chain

# Example usage with LangGraph
def create_traced_graph():
    """
    Create a LangGraph with Langfuse tracing
    """
    from langgraph.graph import StateGraph
    
    langfuse_handler = get_langfuse_handler()
    
    # Your graph implementation here
    graph = StateGraph()
    
    # Add tracing to graph execution
    return graph.compile(callbacks=[langfuse_handler])
