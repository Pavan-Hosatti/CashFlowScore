from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from services.batch_scorer import score_excel
from .scoring_service import score_business
app = FastAPI(
    title="CashFlowScore API",
    version="1.0"
)
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "loaded",
        "redis": "connected"
    }

@app.get("/")
def home():
    return {
        "message": "CashFlowScore API Running 🚀"
    }

@app.post("/score")
def score(payload: dict):
    return score_business(payload)
@app.post("/score-batch")
async def score_batch(file: UploadFile = File(...)):

    input_path = "data/upload.xlsx"
    output_path = "data/scored_output.xlsx"

    with open(input_path, "wb") as f:
        f.write(await file.read())

    score_excel(input_path, output_path)

    return FileResponse(
        output_path,
        filename="scored_output.xlsx"
    )    