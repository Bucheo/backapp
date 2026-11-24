import os
from urllib.parse import urlsplit
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI):
    # 쿠키 인증에서는 * 대신 실제 프론트 origin을 허용합니다.
    urls = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8081",
            "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://127.0.0.1:8081",
            os.getenv("FRONTEND_URL", ""), os.getenv("DOCTOR_FRONTEND_URL", "")]
    urls.extend(os.getenv("CORS_ORIGINS", "").split(","))
    origins = sorted({f"{parts.scheme}://{parts.netloc}" for url in urls
                      if (parts := urlsplit(url.strip())).scheme in {"http", "https"} and parts.netloc})
    app.add_middleware(CORSMiddleware, allow_origins=origins,
                       allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
