from fastapi import FastAPI, UploadFile, File, Path, Depends, HTTPException, Security
from fastapi.security import HTTPBearer
from database import Base, engine, SessionLocal
from services.document_service import process_and_store_document, query_documents
import models
import os
from dotenv import load_dotenv
from models import DocumentUpdate
from auth import router as auth_router, get_current_user

load_dotenv()
os.makedirs("uploaded_files", exist_ok=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Simple Document Q&A")

# Include Auth routes
app.include_router(auth_router, prefix="/auth", tags=["Auth"])

# Protected routes (all require authentication)
@app.post("/upload", tags=["Documents"], 
          summary="Upload Document",
          description="Only authenticated users can upload documents.",
          dependencies=[Depends(get_current_user)])
async def upload(file: UploadFile = File(...)):
    return await process_and_store_document(file)


@app.get("/query", tags=["Documents"],
         summary="Query Document",
         dependencies=[Depends(get_current_user)])
async def query(q: str):
    return query_documents(q)


@app.get("/documents", tags=["Documents"],
         summary="List Documents",
         dependencies=[Depends(get_current_user)])
async def list_documents():
    db = SessionLocal()
    docs = db.query(models.Document).all()
    db.close()
    return [
        {"id": d.id, "filename": d.filename, "file_type": d.file_type, "content_preview": d.content[:200]}
        for d in docs
    ]


@app.delete("/documents/{doc_id}", tags=["Documents"],
            summary="Delete Document",
            dependencies=[Depends(get_current_user)])
async def delete_document(doc_id: int = Path(...)):
    db = SessionLocal()
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        db.close()
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    db.close()
    return {"msg": f"Document '{doc.filename}' deleted successfully."}


@app.put("/documents/{doc_id}", tags=["Documents"],
         summary="Update Document",
         dependencies=[Depends(get_current_user)])
async def update_document(doc_id: int, update: DocumentUpdate):
    db = SessionLocal()
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        db.close()
        raise HTTPException(status_code=404, detail="Document not found")

    if update.filename:
        doc.filename = update.filename
    if update.content:
        doc.content = update.content

    db.commit()
    db.refresh(doc)
    db.close()
    return {"msg": f"Document '{doc.filename}' updated successfully."}
