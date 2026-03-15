from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import schema, analysis, rf, android

app = FastAPI(
    title="Analysis Service API",
    description="RF試験データ + Android試験結果 分析 REST API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schema.router)
app.include_router(analysis.router)
app.include_router(rf.router)
app.include_router(android.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Analysis Service API is running"}
