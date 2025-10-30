# services/document_service.py
import os
import tempfile
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Pinecone as PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from pinecone import Pinecone
from database import SessionLocal
import models


load_dotenv()

# -----------------------------
# ENV CONFIG
# -----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "document-index")

embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini")

# -----------------------------
# Pinecone Init
# -----------------------------
pc = Pinecone(api_key=PINECONE_API_KEY)
if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(name=PINECONE_INDEX_NAME, dimension=1536, metric="cosine")

# -----------------------------
# Upload document
# -----------------------------
async def process_and_store_document(file):
    ext = file.filename.split(".")[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(await file.read())
        temp_path = tmp.name

    # Load file
    if ext == "pdf":
        loader = PyPDFLoader(temp_path)
    elif ext == "txt":
        loader = TextLoader(temp_path)
    else:
        return {"error": "Unsupported file type."}

    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)

    # Save embeddings to Pinecone
    PineconeVectorStore.from_documents(docs, embedding=embeddings, index_name=PINECONE_INDEX_NAME)

    # Save metadata to DB
    pinecone_id = f"{file.filename}_{os.urandom(4).hex()}"
    db = SessionLocal()
    new_doc = models.Document(
        filename=file.filename,
        file_type=ext,
        content=" ".join([d.page_content[:300] for d in docs]),
        pinecone_id=pinecone_id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    db.close()
    os.remove(temp_path)

    return {"message": f"Document '{file.filename}' stored successfully."}

# -----------------------------
# Query documents (Full RAG)
# -----------------------------
def query_documents(query: str):
    vectorstore = PineconeVectorStore.from_existing_index(index_name=PINECONE_INDEX_NAME, embedding=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # RAG prompt
    prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant. Use the context below to answer the user's question.

Context:
{context}

Question:
{question}
""")

    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    result = rag_chain.invoke(query)
    return {"answer": result}
