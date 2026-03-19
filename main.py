from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

from ocr import extract_text_from_image
from processing import clean_and_extract
from classifier import full_analysis
from personalization import personalise

app = FastAPI(title="AI Ingredient Transparency System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FullScanRequest(BaseModel):
    raw_text: str
    is_diabetic: bool = False
    allergies: list[str] = []

@app.get("/")
def root():
    return {"message": "Backend is running!"}

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type")
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    result = extract_text_from_image(image_bytes, file.filename or "upload.jpg")
    return JSONResponse(content=result)

@app.post("/full-scan")
def full_scan(body: FullScanRequest):
    if not body.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text empty")
    processing_result = clean_and_extract(body.raw_text)
    analysis = full_analysis(processing_result["ingredients_list"])
    personal_result = personalise(
        classified=analysis["classified"],
        health_score=analysis["health_score"],
        is_diabetic=body.is_diabetic,
        user_allergies=body.allergies,
    )
    return JSONResponse(content={
        "ingredients_raw_block": processing_result["ingredients_raw_block"],
        "ingredients_list": processing_result["ingredients_list"],
        **analysis,
        "personalisation": personal_result,
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
