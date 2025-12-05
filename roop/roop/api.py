from fastapi import FastAPI, UploadFile, File, HTTPException
from .supabase_utils import upload_image_and_generate_qr

app = FastAPI()

@app.post("/upload/")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    name = file.filename or "generated.png"
    result = upload_image_and_generate_qr(data, name)
    return result