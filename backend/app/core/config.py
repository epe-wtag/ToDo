from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://0.0.0.0",
    "http://0.0.0.0:3000",
    "http://0.0.0.0:8000",
    
]


def cors_middleware(app):
    return CORSMiddleware(
        app,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
