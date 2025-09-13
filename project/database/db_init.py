import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# --------------------------------------------------------------------
"""Charger les variables d'environnement depuis le fichier .env"""
# --------------------------------------------------------------------
load_dotenv()  # Charge les variables depuis .env

# --------------------------------------------------------------------
"""Configuration des logs pour voir davantage de détails"""
# --------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)  # Active les logs pour une meilleure traçabilité
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)  # Affiche les logs SQLAlchemy

# --------------------------------------------------------------------
"""Récupération des paramètres de connexion depuis les variables d'environnement"""
# --------------------------------------------------------------------
DATABASES = {
    "cont": {
        "dbname": os.getenv("DB_CONT_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
    },
    "isol": {
        "dbname": os.getenv("DB_ISOL_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
    }
}

# Génération des URLs de connexion
DATABASE_URLS = {
    key: (
        f"postgresql+asyncpg://{config['user']}:{config['password']}@"
        f"{config['host']}:{config['port']}/{config['dbname']}"
    )
    for key, config in DATABASES.items()
}

# --------------------------------------------------------------------
"""Création des moteurs asynchrones pour chaque base"""
# --------------------------------------------------------------------
engine_cont = create_async_engine(DATABASE_URLS["cont"], echo=True, future=True)
engine_isol = create_async_engine(DATABASE_URLS["isol"], echo=True, future=True)

# --------------------------------------------------------------------
"""Création des sessions asynchrones"""
# --------------------------------------------------------------------
SessionCont = sessionmaker(autocommit=False, autoflush=False, bind=engine_cont, class_=AsyncSession)
SessionIsol = sessionmaker(autocommit=False, autoflush=False, bind=engine_isol, class_=AsyncSession)

# Déclaration des bases ORM pour chaque base de données directement ici
BaseCont = declarative_base()
BaseIsol = declarative_base()

# --------------------------------------------------------------------
"""Fonction pour récupérer une session asynchrone"""
# --------------------------------------------------------------------
async def get_db_cont():
    async with SessionCont() as session:  # Utilisation de la session asynchrone
        try:
            yield session
        finally:
            await session.close()  # Fermeture de la session après utilisation

async def get_db_isol():
    async with SessionIsol() as session:  # Utilisation de la session asynchrone
        try:
            yield session
        finally:
            await session.close()  # Fermeture de la session après utilisation
