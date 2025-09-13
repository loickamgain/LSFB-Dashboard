import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.sql import select
from schema.models_cont import ContInstance, WordAnnotation, SubtitleAnnotation, ContPose, ContVideo
from schema.models_isol import IsolInstance, IsolPose, IsolVideo
# --------------------------------------------------------------------
"""Fonctions pour insérer les données"""
# --------------------------------------------------------------------

# --- CONT -------------------------------------------

    # ---videos-------------------------------------------
async def insert_videos_cont(session: AsyncSession, cont_folder_path: str):
    video_folder = Path(cont_folder_path) / 'videos'
    assert video_folder.exists(), f"Le dossier 'videos' n'existe pas : {video_folder}"

    # Parcours du dossier et ajout des fichiers vidéo par ordre alphabétique croissant
    video_files = sorted(video_folder.glob('*.mp4'), key=lambda x: x.stem)

    for video_file in video_files:
        video_name = video_file.stem
        video_path = str(video_file)  # Le chemin complet vers la vidéo
        print(f"Traitement de la vidéo : {video_name}, Chemin : {video_path}")

        # Vérifier si l'instance_id existe dans la table 'instances_cont'
        result = await session.execute(select(ContInstance).filter_by(id=video_name))
        instance = result.scalars().first()  # On récupère le premier résultat (s'il existe)
        
        if instance:
            # L'instance existe, insérer la vidéo
            video = ContVideo(instance_id=video_name, path=video_path)
            session.add(video)
            print(f"Vidéo ajoutée : {video_name}, Chemin : {video_path}")
        else:
            # L'instance n'existe pas, passer à la suivante
            print(f"L'instance {video_name} n'existe pas dans la table 'instances_cont'. La vidéo est ignorée.")

    # Commit des changements dans la base de données
    try:
        await session.commit()
        print("Les vidéos ont été insérées avec succès.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde dans la base de données : {e}")


    # ---instances-------------------------------------------
# 1. Charger les données depuis le fichier CSV avec tabulation comme séparateur
def load_data_from_csv(file_path):
    # Charge le fichier CSV dans un DataFrame Pandas en utilisant le séparateur ;
    return pd.read_csv(file_path, sep=';')

# 2. Fonction d'insertion dans la base de données (à personnaliser selon votre modèle)
async def insert_instance_to_db(session: AsyncSession, id: str, signer_id: int, session_id: int, task_id: int, n_frames: int, n_signs: int):
    # Insère les données dans la base de données
    query = text("""
    INSERT INTO instances_cont (id, signer_id, session_id, task_id, n_frames, n_signs)
    VALUES (:id, :signer_id, :session_id, :task_id, :n_frames, :n_signs)
    """)
    await session.execute(query, {'id': id, 'signer_id': signer_id, 'session_id': session_id, 'task_id': task_id, 'n_frames': n_frames, 'n_signs': n_signs})
    await session.commit()

# 3. Fonction principale pour insérer les données dans la base
async def insert_instances_cont(session: AsyncSession, file_path: str):
    # Charger les données depuis le CSV
    df = load_data_from_csv(file_path)
    
    # Itérer sur chaque ligne du DataFrame et insérer les données
    for _, row in df.iterrows():
        # Extraire les valeurs de chaque colonne
        id = row['id']
        signer_id = row['signer_id']
        session_id = row['session_id']
        task_id = row['task_id']
        n_frames = row['n_frames']
        n_signs = row['n_signs']

        # Appeler la fonction d'insertion
        await insert_instance_to_db(session, id, signer_id, session_id, task_id, n_frames, n_signs)


    #---word_annotations-------------------------------------------
async def insert_word_annotations_cont(session: AsyncSession, cont_folder_path: str):
    ANNOT_FILES = {
        "signs_left_hand.json": {"hand_type": "left_hand", "sign_type": "normal"},
        "signs_right_hand.json": {"hand_type": "right_hand", "sign_type": "normal"},
        "signs_both_hands.json": {"hand_type": "both_hands", "sign_type": "normal"},
        "special_signs_left_hand.json": {"hand_type": "left_hand", "sign_type": "special"},
        "special_signs_right_hand.json": {"hand_type": "right_hand", "sign_type": "special"},
        "special_signs_both_hands.json": {"hand_type": "both_hands", "sign_type": "special"},
    }

    annotations_folder = os.path.join(cont_folder_path, 'annotations')
    assert os.path.exists(annotations_folder), f"Le dossier 'annotations' n'existe pas : {annotations_folder}"
    
    for annotation_file, metadata in ANNOT_FILES.items():
        annotation_file_path = os.path.join(annotations_folder, annotation_file)
        assert os.path.exists(annotation_file_path), f"Le fichier d'annotation n'existe pas : {annotation_file_path}"
        
        with open(annotation_file_path, 'r') as f:
            annotations_data = json.load(f)

        for instance_id, annotations in annotations_data.items():
            for annotation in annotations:
                word_annotation = WordAnnotation(
                    instance_id=instance_id,
                    sign_type=metadata['sign_type'],
                    hand_type=metadata['hand_type'],
                    word=annotation['value'],
                    start_time=annotation['start'],
                    end_time=annotation['end']
                )
                session.add(word_annotation)

    await session.commit()

    #---subtitles-------------------------------------------
import os
import json
from sqlalchemy.future import select

async def insert_subtitles_cont(session: AsyncSession, cont_folder_path: str):
    subtitles_file_path = os.path.join(cont_folder_path, 'annotations', 'subtitles.json')
    assert os.path.exists(subtitles_file_path), f"Le fichier 'subtitles.json' n'existe pas : {subtitles_file_path}"
    
    with open(subtitles_file_path, 'r') as f:
        subtitles_data = json.load(f)

    for instance_id, subtitles in subtitles_data.items():
        # Vérifier si l'instance_id existe dans 'instances_cont'
        result = await session.execute(select(ContInstance).filter_by(id=instance_id))
        instance = result.scalars().first()  # Récupère l'instance si elle existe
        
        if instance:
            # Si l'instance existe, insérer les sous-titres
            for subtitle in subtitles:
                subtitle_annotation = SubtitleAnnotation(
                    instance_id=instance_id,
                    text=subtitle['value'],
                    start_time=subtitle['start'],
                    end_time=subtitle['end']
                )
                session.add(subtitle_annotation)
            print(f"Sous-titres ajoutés pour l'instance {instance_id}")
        else:
            # Si l'instance n'existe pas, ignorer les sous-titres
            print(f"L'instance {instance_id} n'existe pas dans la table 'instances_cont'. Les sous-titres sont ignorés.")

    # Commit des changements dans la base de données
    try:
        await session.commit()
        print("Les sous-titres ont été insérés avec succès.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde dans la base de données : {e}")


    #---poses-------------------------------------------
async def insert_poses_cont(session: AsyncSession, cont_folder_path: str):
    poses_folder = Path(cont_folder_path) / 'poses'
    assert poses_folder.exists(), f"Le dossier 'poses' n'existe pas : {poses_folder}"

    body_parts = ['face', 'left_hand', 'pose', 'right_hand']
    poses_dict = {}

    # Parcours des fichiers de poses pour chaque partie du corps
    for body_part in body_parts:
        body_part_folder = poses_folder / body_part
        if not body_part_folder.exists():
            continue

        # Trie les fichiers .npy par ordre alphabétique croissant
        pose_files = sorted(body_part_folder.glob('*.npy'), key=lambda x: x.stem)

        for pose_file in pose_files:
            pose_name = pose_file.stem  # Nom du fichier sans l'extension

            # Regroupe les poses par leur nom (sans partie du corps)
            if pose_name not in poses_dict:
                poses_dict[pose_name] = []
            poses_dict[pose_name].append((body_part, pose_file))

    # Ajouter les poses regroupées à la session
    for pose_name, parts in poses_dict.items():
        for body_part, pose_file in sorted(parts, key=lambda x: x[0]):  # Trie les poses par partie du corps
            pose_part = body_part
            pose = ContPose(
                instance_id=pose_name,
                pose_part=pose_part,
                pose_path=str(pose_file)  # Chemin complet vers le fichier de pose
            )
            session.add(pose)

    # Commit les changements dans la base de données
    await session.commit()
    print("Les poses ont été insérées avec succès.")


# --- ISOL -------------------------------------------

    #---videos-------------------------------------------
async def insert_videos_isol(session: AsyncSession, isol_folder_path: str):
    video_folder = os.path.join(isol_folder_path, 'videos')
    assert os.path.exists(video_folder), f"Le dossier 'videos' n'existe pas : {video_folder}"

    # Liste et trie les fichiers vidéo .mp4 par ordre alphabétique croissant
    video_files = sorted([f for f in os.listdir(video_folder) if f.endswith('.mp4')], key=lambda x: x.lower())

    for video_file in video_files:
        video_name = os.path.splitext(video_file)[0]
        video_path = os.path.join(video_folder, video_file)
        print(f"Vidéo ajoutée : {video_name}, Chemin : {video_path}")
        
        # Créer un objet vidéo et l'ajouter à la session
        video = IsolVideo(instance_id=video_name, path=video_path)
        session.add(video)

    # Commit les changements dans la base de données
    await session.commit()

    #---instances-------------------------------------------
async def insert_instances_isol(session: AsyncSession, isol_folder_path: str):
    instance_csv_path = os.path.join(isol_folder_path, 'instances.csv')
    assert os.path.exists(instance_csv_path), f"Le fichier 'instances.csv' n'existe pas : {instance_csv_path}"
    
    # Chargement des données CSV
    instances_df = pd.read_csv(instance_csv_path, delimiter=',')
    instances_data = instances_df.to_dict(orient='records')

    # Parcours des données du CSV et ajout à la session
    for instance_data in instances_data:
        isol_instance = IsolInstance(
            id=instance_data['id'],
            sign=instance_data['sign'],
            signer=instance_data['signer'],
            start=instance_data['start'],
            end=instance_data['end']
        )
        session.add(isol_instance)

    # Commit les changements dans la base de données
    await session.commit()

    #---poses-------------------------------------------
async def insert_poses_isol(session: AsyncSession, isol_folder_path: str):
    poses_folder = os.path.join(isol_folder_path, 'poses')
    assert os.path.exists(poses_folder), f"Le dossier 'poses' n'existe pas : {poses_folder}"

    body_parts = ['face', 'left_hand', 'pose', 'right_hand']
    poses_dict = {}

    # Parcours des fichiers de poses pour chaque partie du corps
    for body_part in body_parts:
        body_part_folder = os.path.join(poses_folder, body_part)
        if not os.path.exists(body_part_folder):
            continue

        # Trie les fichiers .npy par ordre alphabétique croissant
        pose_files = sorted([f for f in os.listdir(body_part_folder) if f.endswith('.npy')], key=lambda x: x.lower())

        for pose_file in pose_files:
            pose_name = os.path.splitext(pose_file)[0]  # Nom de la pose sans l'extension

            # Regroupe les poses par leur nom (sans partie du corps)
            if pose_name not in poses_dict:
                poses_dict[pose_name] = []
            poses_dict[pose_name].append((body_part, os.path.join(body_part_folder, pose_file)))

    # Ajouter les poses regroupées à la session
    for pose_name, parts in poses_dict.items():
        for body_part, pose_file_path in sorted(parts, key=lambda x: x[0]):  # Trie les poses par partie du corps
            pose_part = body_part

            pose = IsolPose(
                instance_id=pose_name,
                pose_part=pose_part,
                pose_path=pose_file_path  # Chemin complet vers le fichier de pose
            )
            session.add(pose)

    # Commit les changements dans la base de données
    await session.commit()