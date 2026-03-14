import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore

app = FastAPI(title="StegXtreme")

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
    allow_methods=["*"], allow_headers=["*"])

from backend.api import embed, extract, analyze, visualise  # type: ignore

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(embed.router)
app.include_router(extract.router)
app.include_router(analyze.router)
app.include_router(visualise.router)

