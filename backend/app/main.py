from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import relays, traffic, analysis, export, auth, webhooks
from app.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TOR - Unveil",
    description="Analytical tool for Tor relay metadata and traffic pattern correlation",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(relays.router, prefix="/api/relays", tags=["relays"])
app.include_router(traffic.router, prefix="/api/traffic", tags=["traffic"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(export.router, tags=["export"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])

@app.get("/")
async def root():
    return {
        "message": "TOR - Unveil API",
        "version": "1.0.0",
        "docs": "/docs",
        "auth": "Powered by Clerk"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
