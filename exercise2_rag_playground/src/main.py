import os
from dotenv import load_dotenv

from langchain import hub
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# OpenAI API configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL= os.environ.get("EMBEDDING_MODEL")


def create_rag_chain():
    """Create RAG chain using LCEL pattern"""    
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    vector_store = Chroma(
        collection_name="rag_exercise",
        embedding_function=embeddings,
        persist_directory="./chroma_data", 
    )

    
    # Create retriever
    retriever = vector_store.as_retriever(
        search_kwargs={"k": 4}
    )
    
    # Pull RAG prompt from hub
    prompt = hub.pull("rlm/rag-prompt")
    
    llm = ChatOpenAI(
        model_name=LLM_MODEL,
        temperature=0,
        api_key=OPENAI_API_KEY
    )
    
    # Create LCEL chain
    rag_chain = (
        {
            "context": retriever,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain


def run_test_queries(rag_chain):
    """Run test queries to evaluate retrieval"""
    print("\n Running test queries...")
    
    test_queries = [
        "What are the main principles in our code of conduct?",
        "What constitutes harassment according to our policy?",
        "Who should I contact for policy violations?",
        "What support is available for workplace issues?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 60)
        
        try:
            response = rag_chain.invoke(query)
            print(f"Answer: {response}")
        except Exception as e:
            print(f"Error: {e}")
            
            
def run_interactive_mode(rag_chain):
    """Interactive query mode"""
    print(f"\n{'='*60}")
    print("Ask queries from the doc!")
    print("Type 'quit' to exit")
    print('='*60)
    
    while True:
        question = input("\n Your question: ").strip()
        
        if question.lower() in ['quit', 'q']:
            print("Goodbye!")
            break
            
        if not question:
            continue
            
        try:
            response = rag_chain.invoke(question)
            print(f"\n Answer: {response}")
        except Exception as e:
            print(f" Error: {e}")

                     
def main():
    rag_chain = create_rag_chain()

    # run_test_queries(rag_chain)
    run_interactive_mode(rag_chain)
            
if __name__ == "__main__":
    main()