import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import asyncio
from database.db_init import engine_cont, engine_isol
from db_init import SessionCont, SessionIsol
from schema import models_cont, models_isol
from insert_db import insert_videos_cont, insert_instances_cont, insert_word_annotations_cont, insert_subtitles_cont, insert_poses_cont
from insert_db import insert_videos_isol, insert_instances_isol, insert_poses_isol

# --------------------------------------------------------------------
"""Initialisation des bases de données"""
# --------------------------------------------------------------------
async def init_db():
    print("Creating tables in the databases... ... ...")
    
    async with engine_cont.begin() as conn:
        await conn.run_sync(models_cont.BaseCont.metadata.create_all)
        print("Tables created for database 'cont'.")
    
    async with engine_isol.begin() as conn:
        await conn.run_sync(models_isol.BaseIsol.metadata.create_all)
        print("Tables created for database 'isol'.")

# --------------------------------------------------------------------
"""Fonction principale pour exécuter les insertions asynchrones"""
# --------------------------------------------------------------------
async def main():
    # Initialisation de la base de données
    await init_db()

    # Insertions asynchrones des données
    async with SessionCont() as session_cont, SessionIsol() as session_isol:
        # Insertion pour 'cont'
        await insert_instances_cont(session_cont, r"E:\lsfb dataset\cont\instances.csv")
        await insert_videos_cont(session_cont, r"E:\lsfb dataset\cont")
        await insert_word_annotations_cont(session_cont, r"E:\lsfb dataset\cont")
        await insert_subtitles_cont(session_cont, r"E:\lsfb dataset\cont")
        await insert_poses_cont(session_cont, r"E:\lsfb dataset\cont")

        # Insertion pour 'isol'
        await insert_instances_isol(session_isol, r"E:\lsfb dataset\isol")
        await insert_videos_isol(session_isol, r"E:\lsfb dataset\isol")
        await insert_poses_isol(session_isol, r"E:\lsfb dataset\isol")

# Exécution du programme principal
if __name__ == "__main__":
    asyncio.run(main())