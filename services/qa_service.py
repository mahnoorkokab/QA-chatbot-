import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone as PineconeVectorStore
import pinecone

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)

def query_documents(query: str):
    if PINECONE_INDEX_NAME not in pinecone.list_indexes():
        return {"error": f"❌ Pinecone index '{PINECONE_INDEX_NAME}' not found."}

    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=PINECONE_INDEX_NAME,
        embedding=embeddings
    )

    results = vectorstore.similarity_search(query, k=4)
    if not results:
        return {"answer": "No relevant information found in documents."}

    context = "\n".join([r.page_content for r in results])
    prompt = f"""
You are a helpful assistant. Use the following document context to answer the question accurately.
Context:
{context}

Question:
{query}

Answer:
"""
    response = llm.invoke(prompt)
    return {"answer": response.content}
