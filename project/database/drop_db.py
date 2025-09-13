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

def delete_database(db_key):
    """Supprime une base de données spécifique si elle existe."""
    db_name = DATABASES.get(db_key)

    if not db_name:
        print(f"The database '{db_key}' is not configured in .env.")
        return

    try:
        connection = psycopg2.connect(
            dbname="postgres",  # Se connecter à la base par défaut pour exécuter DROP DATABASE
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        connection.autocommit = True  # Obligatoire pour DROP DATABASE
        cursor = connection.cursor()

        # Suppression de la base sélectionnée
        cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))
        print(f"Database '{db_name}' has been deleted successfully!")

    except Exception as error:
        print(f"Error deleting '{db_name}':", error)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

"""Fournis par ChatGPT"""
# Ajout d'arguments pour choisir la base à supprimer
parser = argparse.ArgumentParser(description="Supprime une ou plusieurs bases de données PostgreSQL.")
parser.add_argument("db", choices=["cont", "isol", "all"], help="Base de données à supprimer ('cont', 'isol', ou 'all')")

args = parser.parse_args()

# Exécuter la suppression en fonction du choix de l'utilisateur
if args.db == "all":
    delete_database("cont")
    delete_database("isol")
else:
    delete_database(args.db)
