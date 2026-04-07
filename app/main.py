# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.orchestrator import handle_query

from app.tools.swagger_loader import load_swagger
from app.tools.swagger_parser import parse_swagger
from app.tools.registry import register_tools
from app.tools.tool_builder import build_llm_tools
from app.core.config import SWAGGER_URL

import logging

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading Swagger documentation...")

    swagger = load_swagger(SWAGGER_URL)
    parsed_tools = parse_swagger(swagger)
    llm_tools = build_llm_tools(parsed_tools)

    register_tools(parsed_tools, llm_tools)

    print(f"✅ Loaded {len(parsed_tools)} tools")

    yield
    print("🛑 Shutdown complete")


app = FastAPI(lifespan=lifespan)

# Security scheme (Swagger compatible)
security = HTTPBearer(auto_error=False)

class QueryRequest(BaseModel):
    query: str


# 🔍 Middleware to debug headers (temporary)
@app.middleware("http")
async def log_headers(request: Request, call_next):
    logging.info(f"Incoming headers: {dict(request.headers)}")
    response = await call_next(request)
    return response


@app.post("/chat")
def chat(
    req: QueryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    logging.info(f"Received query: {req.query}")

    # 🔥 Step 1 — Validate credentials object
    if credentials is None:
        logging.error("No credentials received")
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 🔥 Step 2 — Extract token
    token = credentials.credentials
    scheme = credentials.scheme

    logging.info(f"Scheme: {scheme}")
    logging.info(f"Token (masked): {token[:10]}****")

    # 🔥 Step 3 — Validate scheme
    if scheme.lower() != "bearer":
        logging.error("Invalid auth scheme")
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    # 🔥 Step 4 — Call orchestrator
    try:
        response = handle_query(req.query, token)
        return {"response": response}

    except Exception as e:
        logging.exception("Error in processing request")
        raise HTTPException(status_code=500, detail=str(e))