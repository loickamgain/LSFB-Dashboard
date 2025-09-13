import os
import psycopg2
import argparse
from psycopg2 import sql
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration des bases disponibles
DATABASES = {
    "cont": os.getenv("DB_CONT_NAME"),
    "isol": os.getenv("DB_ISOL_NAME")
}

def create_database(db_key):
    """Crée une base de données spécifique si elle n'existe pas déjà."""
    db_name = DATABASES.get(db_key)

    if not db_name:
        print(f"The database '{db_key}' is not configured in .env.")
        return

    try:
        connection = psycopg2.connect(
            dbname="postgres",  # Se connecter à la base par défaut pour exécuter CREATE DATABASE
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        connection.autocommit = True  # Obligatoire pour CREATE DATABASE
        cursor = connection.cursor()

        # Création de la base sélectionnée
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        print(f"Database '{db_name}' has been created successfully!")

    except Exception as error:
        print(f"Error creating '{db_name}':", error)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

# Ajout d'arguments pour choisir la base à créer
parser = argparse.ArgumentParser(description="Crée une ou plusieurs bases de données PostgreSQL.")
parser.add_argument("db", choices=["cont", "isol", "all"], help="Base de données à créer ('cont', 'isol', ou 'all')")

args = parser.parse_args()

# Exécuter la création en fonction du choix de l'utilisateur
if args.db == "all":
    create_database("cont")
    create_database("isol")
else:
    create_database(args.db)
