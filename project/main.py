import logging
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database.db_init import get_db_cont, get_db_isol
from route.route import router
import dash
from dash_app import app as dash_app  # Assure-toi que dash_app est importé correctement
import json

# Création de l'application FastAPI
app = FastAPI()
app.include_router(router)

# Utilisation de chaînes brutes pour éviter les erreurs avec les barres obliques inverses
BASE_DIR_CONT = Path(r"E:\lsfb dataset\cont")
BASE_DIR_ISOL = Path(r"E:\lsfb dataset\isol")
BASE_DIR_CONT_POSES = Path(r"E:\lsfb dataset\cont\poses")
BASE_DIR_ISOL_POSES = Path(r"E:\lsfb dataset\isol\poses")

# Montage des fichiers statiques
app.mount("/cont", StaticFiles(directory=str(BASE_DIR_CONT)), name="static_cont")
app.mount("/isol", StaticFiles(directory=str(BASE_DIR_ISOL)), name="static_isol")
app.mount("/cont_poses", StaticFiles(directory=str(BASE_DIR_CONT_POSES)), name="cont_poses")
app.mount("/isol_poses", StaticFiles(directory=str(BASE_DIR_ISOL_POSES)), name="isol_poses")
app.mount("/static", StaticFiles(directory=r"D:\Etudes\Bachelier Informatique Unamur\Bloc 3\Projet\lsfb_projet\static"), name="static")

# Montage  l'application Dash à l'URL "/dash"
app.mount("/dash", dash_app.server)

templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"🔹 Requête : {request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"🔹 Réponse : {response.status_code}")
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Erreur interne : {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Une erreur interne est survenue. Veuillez réessayer plus tard."},
    )


@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/index.html", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.on_event("startup")
async def startup_event():
    get_db_cont()
    get_db_isol()


# Lancer le serveur FastAPI avec Dash intégré
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
