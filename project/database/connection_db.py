import os
import psycopg2
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Paramètres de connexion pour les deux bases
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

def test_database_connection(db_key):
    """Teste la connexion à une base de données spécifique (cont ou isol)."""
    db_config = DATABASES[db_key]

    try:
        # Tentative de connexion
        connection = psycopg2.connect(
            dbname=db_config["dbname"],
            user=db_config["user"],
            password=db_config["password"],
            host=db_config["host"],
            port=db_config["port"]
        )
        print(f"The database '{db_config['dbname']}' is available and connected.")

    except psycopg2.OperationalError as e:
        # Gestion des erreurs de connexion
        if "does not exist" in str(e):
            print(f" Error: The database '{db_config['dbname']}' does not exist.")
        else:
            print(f" Error: Unable to connect to '{db_config['dbname']}'\n{e}")
    
    finally:
        # Vérification de l'état de la connexion
        if 'connection' in locals() and connection:
            print(f"🔹 Active connection for '{db_config['dbname']}'.")
            connection.close()  # Fermer proprement
        else:
            print(f" No active connections detected for '{db_config['dbname']}'.")

# Tester les connexions pour les deux bases
if __name__ == "__main__":
    test_database_connection("cont")
    test_database_connection("isol")
