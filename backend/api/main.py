from fastapi import FastAPI
from . import models
from .db import engine
from .routes import router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="OMR Evaluation API")
app.include_router(router, prefix="/api")
