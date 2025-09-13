import matplotlib as mpl
mpl.rcParams['animation.ffmpeg_path'] = r"C:\ffmpeg\bin\ffmpeg.exe"  # Chemin vers ffmpeg
import asyncio
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import io
import base64
import json, urllib.parse
import os
import math
import numpy as np
from pymediainfo import MediaInfo
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func, distinct, cast
from sqlalchemy import Float
from math import ceil
from database.db_init import get_db_cont, get_db_isol
from schema.models_cont import ContInstance, ContVideo, WordAnnotation, SubtitleAnnotation, ContPose
from schema.models_isol import IsolInstance, IsolVideo, IsolPose
from typing import Optional, List, Dict


# 1) Créer un router
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 2) Définir les routes
# --- Pages HTML simples ---
@router.get("/about.html", response_class=HTMLResponse)
async def read_about(request: Request):
    return templates.TemplateResponse(request, "about.html", {"request": request})

@router.get("/contact.html", response_class=HTMLResponse)
async def read_contact(request: Request):
    return templates.TemplateResponse(request, "contact.html", {"request": request})

@router.get("/lsfb.html", response_class=HTMLResponse)
async def read_lsfb(request: Request):
    return templates.TemplateResponse(request, "lsfb.html", {})

"""@router.get("/results_cont.html", response_class=HTMLResponse)
async def read_results_cont_html(request: Request):
    # Ce n’est qu’une page statique si vous voulez l’afficher directement
    return templates.TemplateResponse(request, "results_cont.html", {"request": request})

@router.get("/results_isol.html", response_class=HTMLResponse)
async def read_results_isol_html(request: Request):
    # Ce n’est qu’une page statique si vous voulez l’afficher directement
    return templates.TemplateResponse(request, "results_isol.html", {"request": request})"""

@router.get("/statistics.html", response_class=HTMLResponse)
async def read_statistics_html(request: Request):
    # Ce n’est qu’une page statique si vous voulez l’afficher directement
    return templates.TemplateResponse(request, "statistics.html", {"request": request})

@router.get("/suggestions.html", response_class=HTMLResponse)
async def read_suggestions(request: Request):
    return templates.TemplateResponse(request, "suggestions.html", {"request": request})

@router.get("/video_view_cont.html", response_class=HTMLResponse)
async def read_video_view(request: Request):
    return templates.TemplateResponse(request, "video_view_cont.html", {"request": request})

@router.get("/video_view_isol.html", response_class=HTMLResponse)
async def read_video_view(request: Request):
    return templates.TemplateResponse(request, "video_view_isol.html", {"request": request})


""""""""""""""""""""
#fonction générée par ChatGPT pour determiner la durée réelle d'une vidéo de cont
DURATIONS_CACHE = {}# Dictionnaire pour mettre en cache les durées déjà calculées

def get_real_video_duration_s(video_path: str) -> float:
    """
    Retourne la durée réelle d'une vidéo (en secondes) en utilisant pymediainfo.
    Stocke le résultat dans un cache (DURATIONS_CACHE) pour éviter de recalculer
    la durée pour le même fichier.
    
    Nécessite que la bibliothèque pymediainfo soit installée et que MediaInfo
    soit disponible sur le système.
    """
    # Si la durée a déjà été calculée, la renvoyer directement
    if video_path in DURATIONS_CACHE:
        return DURATIONS_CACHE[video_path]

    # Vérifier que le fichier existe
    if not os.path.isfile(video_path):
        print(f"[WARN] Fichier introuvable: {video_path}")
        DURATIONS_CACHE[video_path] = 0.0
        return 0.0

    try:
        # Récupérer les métadonnées du fichier vidéo
        media_info = MediaInfo.parse(video_path)
        # Parcourir les pistes pour trouver la piste vidéo et sa durée
        for track in media_info.tracks:
            if track.track_type == "Video" and track.duration:
                # La durée est en millisecondes, conversion en secondes
                duration = float(track.duration) / 1000.0
                DURATIONS_CACHE[video_path] = duration
                return duration
        # Aucune durée trouvée
        DURATIONS_CACHE[video_path] = 0.0
        return 0.0
    except Exception as e:
        print(f"[WARN] Erreur MediaInfo pour {video_path}: {e}")
        DURATIONS_CACHE[video_path] = 0.0
        return 0.0

#Fonction de conversion de millisecondes en format MM:SS   
def format_time(ms):
    """Convertir les millisecondes en format MM:SS."""
    
    # Vérifie si l'input est déjà un format MM:SS
    if isinstance(ms, str) and ':' in ms:
        # Si l'entrée est déjà sous le format MM:SS, on la retourne telle quelle
        return ms
    
    # Si c'est un nombre (en millisecondes)
    if isinstance(ms, (int, float)):
        seconds = ms / 1000  # Conversion des millisecondes en secondes
        minutes = int(seconds // 60)  # Calcul des minutes
        seconds = int(seconds % 60)   # Calcul des secondes restantes
        return f"{minutes:02}:{seconds:02}"
    
    # Si l'input est ni un nombre ni un format valide, retourner un message d'erreur ou une valeur par défaut
    return "Invalid time format"


# --- Route de recherche : /results_cont ---
@router.get("/results_cont", response_class=HTMLResponse)
async def results_cont(
    request: Request,
    submitType: str = Query("filter", description="Détermine si c'est une nouvelle recherche (search) ou un filtrage (filter)"),
    term: str = Query("", description="Mot ou phrase recherchée"),
    signer: Optional[str] = Query(None, description="Signataire"),
    hand_type: Optional[str] = Query(None, description="Main (left, right, both)"),
    sign_type: Optional[str] = Query(None, description="Type de signe (normal, special)"),
    session_id: Optional[str] = Query(None, description="Session"),
    task_id: Optional[str] = Query(None, description="Task"),
    min_duration_str: Optional[str] = Query(None, description="Durée min (en millisecondes)"),
    max_duration_str: Optional[str] = Query(None, description="Durée max (en millisecondes)"),
    page: int = Query(1, description="Page de pagination"),
    db_cont: AsyncSession = Depends(get_db_cont),
):
    """
    Recherche CONT avec jointures et filtres.
    - Recherche par mot (`WordAnnotation`) ou phrase (`SubtitleAnnotation`).
    - Calcule la durée réelle des vidéos.
    - Transmet les segments à `video_view_cont.html`.
    - Garde les statistiques pour analyse.
    """

    #Conversion des durées (en millisecondes)
    min_duration = int(min_duration_str) if min_duration_str and min_duration_str.strip() != "" else None
    max_duration = int(max_duration_str) if max_duration_str and max_duration_str.strip() != "" else None

    term_lower = term.strip().lower()
    search_type = "phrase" if " " in term_lower else "word"  # Déterminer le type de recherche

    #Construction de la requête principale avec jointures
    if search_type == "phrase":
        query_global = (
            select(ContVideo)
            .join(ContInstance)
            .join(SubtitleAnnotation)
            .filter(SubtitleAnnotation.text.ilike(f"%{term_lower}%"))
            .options(
                selectinload(ContVideo.instance_cont).selectinload(ContInstance.subtitle_annotations),
                selectinload(ContVideo.instance_cont).selectinload(ContInstance.word_annotations),
            )
            .distinct()
        )
    else:
        query_global = (
            select(ContVideo)
            .join(ContInstance)
            .join(WordAnnotation)
            .filter(WordAnnotation.word.ilike(f"%{term_lower}%"))
            .options(
                selectinload(ContVideo.instance_cont).selectinload(ContInstance.subtitle_annotations),
                selectinload(ContVideo.instance_cont).selectinload(ContInstance.word_annotations),
            )
            .distinct()
        )

    #Exécution de la requête
    result_global = await db_cont.execute(query_global)
    global_results = result_global.scalars().all()

    #Appliquer les filtres supplémentaires
    if submitType == "filter":
        filtered_results = []
        for video in global_results:
            instance = video.instance_cont

            # Filtrage sur signer, session, task
            if signer and str(instance.signer_id).lower() != signer.lower():
                continue
            if session_id and str(instance.session_id).lower() != session_id.lower():
                continue
            if task_id and str(instance.task_id).lower() != task_id.lower():
                continue

            meets_filters = True
            annotations = instance.subtitle_annotations if search_type == "phrase" else instance.word_annotations

            # Filtres spécifiques
            if min_duration is not None:
                annotations = [a for a in annotations if (a.end_time - a.start_time) >= min_duration]
            if max_duration is not None:
                annotations = [a for a in annotations if (a.end_time - a.start_time) <= max_duration]
            if hand_type and search_type == "word":
                annotations = [a for a in annotations if a.hand_type.lower() == hand_type.lower()]
            if sign_type and search_type == "word":
                annotations = [a for a in annotations if a.sign_type.lower() == sign_type.lower()]

            if not annotations:
                meets_filters = False

            if meets_filters:
                filtered_results.append(video)

        global_results = filtered_results

    #Récupération des statistiques
    stats = {}
    if term_lower:
        if search_type == "phrase":
            stats = await get_phrase_stats(term_lower, db_cont)
        else:
            stats = await get_word_stats(term_lower, db_cont)

    #Construction de la liste des vidéos avec leurs segments
    videos_with_segments = []
    if global_results:
        for vid in global_results:
            instance = vid.instance_cont
            annotations = instance.subtitle_annotations if search_type == "phrase" else instance.word_annotations
            matched = [a for a in annotations if term_lower in (a.text if search_type == "phrase" else a.word).lower()]
            segs = [{"start": format_time(a.start_time), "end": format_time(a.end_time)} for a in matched]

            videos_with_segments.append({
                "video": vid,
                "segments": segs,
                "search_type": search_type
            })

    #Calcul de la durée réelle des vidéos via MediaInfo
    for vid in global_results:
        real_seconds = get_real_video_duration_s(vid.path)
        # Ajout d'un attribut éphémère pour la durée
        vid.real_duration_s = real_seconds

    # Pagination
    ITEMS_PAR_PAGE = 15
    total_results = len(global_results)
    total_pages = ceil(total_results / ITEMS_PAR_PAGE)
    start_index = (page - 1) * ITEMS_PAR_PAGE
    end_index = start_index + ITEMS_PAR_PAGE
    paginated_results = global_results[start_index:end_index]

    #Rendu du template avec les résultats
    return templates.TemplateResponse(
        request,
        "results_cont.html",
        {
            "request": request,
            "submitType": submitType,
            "term": term,
            "signer": signer,
            "hand_type": hand_type,
            "sign_type": sign_type,
            "session_id": session_id,
            "task_id": task_id,
            "min_duration": min_duration,
            "max_duration": max_duration,
            "stats": stats,
            "no_results": total_results == 0,
            "cont_videos": paginated_results,
            "videos_with_segments": videos_with_segments,
            "current_page": page,
            "total_pages": total_pages if total_pages else 1,
            "search_type": search_type,
        },
    )

#--- Route d'affichage vidéo cont: /video/cont/{video_id} ---
# Définir le chemin de base du dataset "cont"
BASE_DIR_CONT = Path(r"E:\lsfb dataset\cont")
BASE_DIR_CONT_POSES = Path(r"E:\lsfb dataset\cont\poses")
@router.get("/video/cont/{video_id}", response_class=HTMLResponse)
async def get_video_cont(
    request: Request,
    video_id: str,
    previous_term: str = "",
    db_cont: AsyncSession = Depends(get_db_cont)
):
    """
    Route pour afficher la vidéo CONT et le squelette 3D associé à partir des poses.
    Cette route récupère les poses associées à la vidéo,
    """
    if not previous_term:
        raise HTTPException(status_code=422, detail="previous_term est requis")
    
    # 1. Récupérer les informations de la vidéo depuis la base de données
    query_cont = select(ContVideo).filter(ContVideo.instance_id == video_id)  # Requête pour récupérer la vidéo avec l'ID donné
    result_cont = await db_cont.execute(query_cont)  # Exécution de la requête
    video_cont = result_cont.scalar_one_or_none()  # Récupération de la vidéo ou None si elle n'existe pas

    # 2. Si la vidéo n'existe pas, renvoyer une page avec des valeurs par défaut
    if not video_cont:
        return templates.TemplateResponse(
            "video_view_cont.html",  # Rendu du template vidéo avec une page d'erreur si la vidéo n'existe pas
            {
                "request": request,
                "instance_id": video_id,
                "video_path": "",  # Aucun chemin vidéo
                "dataset": "none",  # Indique que le dataset est "none" puisque la vidéo est introuvable
                "previous_term": previous_term,
            }
        )


    # 3. Transformation du chemin absolu de la vidéo en URL relative pour la rendre accessible depuis le frontend
    video_abs_path = Path(video_cont.path)  # On récupère le chemin absolu de la vidéo
    try:
        relative_video_path = video_abs_path.relative_to(BASE_DIR_CONT)  # On calcule le chemin relatif de la vidéo
        video_url = f"/cont/{relative_video_path.as_posix()}"  # Création de l'URL de la vidéo
    except ValueError:
        video_url = video_cont.path  # Si le calcul échoue, on garde le chemin absolu

    # 4. Retourner la réponse HTML avec les données nécessaires pour l'affichage
    return templates.TemplateResponse(
        "video_view_cont.html",  # Le template HTML qui sera renvoyé avec les données
        {
            "request": request,
            "instance_id": video_id,
            "video_path": video_url,  # L'URL de la vidéo à afficher
            "previous_term": previous_term,  # Le terme précédent de recherche
            "format_time": format_time,
            "dataset": "cont",  # Nom du dataset (ici "cont")
        }
    )

@router.get("/get_segments/{video_id}")
async def get_segments(
    video_id: str,
    previous_term: str = "",
    db_cont: AsyncSession = Depends(get_db_cont)
):
    segments_query = None
    segments_list = []
    if previous_term:
        # Si le terme précédent contient plusieurs mots, on suppose que c'est une phrase
        if ' ' in previous_term:  
            # Recherche par phrase dans SubtitleAnnotation
            segments_query = select(SubtitleAnnotation.start_time, SubtitleAnnotation.end_time).filter(
                SubtitleAnnotation.instance_id == video_id,  # Filtrer les annotations de sous-titres pour la vidéo
                SubtitleAnnotation.text.ilike(f"%{previous_term}%")  # Recherche par phrase dans les sous-titres
            )
        else:
            # Recherche par mot dans WordAnnotation
            segments_query = select(WordAnnotation.start_time, WordAnnotation.end_time).filter(
                WordAnnotation.instance_id == video_id,  # Filtrer les annotations de mots pour la vidéo
                WordAnnotation.word.ilike(f"%{previous_term}%")  # Recherche par mot (terme précédent)
            )
    if segments_query is not None:
        segments = await db_cont.execute(segments_query)
        segments_list = [{"start": format_time(row.start_time), "end": format_time(row.end_time)} for row in segments.all()]
    return {"segments_list": segments_list}  # Envoie les données sous forme de dictionnaire directement

# --- Route de recherche : /results_isol ---
@router.get("/results_isol", response_class=HTMLResponse)
async def results_isol(
    request: Request,
    submitType: str = Query("filter", description="search ou filter"),
    term: str = Query("", description="Terme de recherche"),
    signer: Optional[str] = Query(None, description="Signataire"),
    # Paramètres de durée sous forme de chaîne, à convertir en int
    min_duration: Optional[str] = Query(None, description="Durée min (en millisecondes)"),
    max_duration: Optional[str] = Query(None, description="Durée max (en millisecondes)"),
    page: int = Query(1, ge=1),  # Paramètre de pagination (page actuelle, minimum 1)
    db_isol: AsyncSession = Depends(get_db_isol),
):
    # Fonction pour une conversion sûre en entier
    def safe_int(value: Optional[str]) -> Optional[int]:
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    # Conversion sécurisée des chaînes en int
    min_duration_val = safe_int(min_duration)
    max_duration_val = safe_int(max_duration)
    # Nettoyage du terme de recherche
    term_lower = term.strip().lower()

    limit = 15  # Nombre d'éléments à afficher par page
    offset = (page - 1) * limit  # Calcul du décalage pour la pagination

    # Construction de la requête en joignant les tables concernées
    query_isol = select(IsolVideo).join(IsolInstance).options(selectinload(IsolVideo.instance_iso))

    if submitType == "search":
        if term_lower:
            query_isol = query_isol.filter(IsolInstance.sign.ilike(f"%{term_lower}%"))
    else:
        if term_lower:
            query_isol = query_isol.filter(IsolInstance.sign.ilike(f"%{term_lower}%"))
        if signer:
            query_isol = query_isol.filter(IsolInstance.signer == signer)
        if min_duration_val is not None:
            query_isol = query_isol.filter((IsolInstance.end - IsolInstance.start) >= min_duration_val)
        if max_duration_val is not None:
            query_isol = query_isol.filter((IsolInstance.end - IsolInstance.start) <= max_duration_val)

    # Exécution initiale pour compter le total des résultats
    total_results = (await db_isol.execute(query_isol)).scalars().all()
    total_count = len(total_results)

    # Application de la pagination à la requête
    query_isol_paginated = query_isol.offset(offset).limit(limit)

    # Récupération des résultats paginés
    result_paginated = await db_isol.execute(query_isol_paginated)
    isol_videos = result_paginated.scalars().all()

    # Vérification si aucun résultat n'est trouvé
    no_results = len(isol_videos) == 0

    # Récupération des statistiques du signe si un terme est spécifié
    stats = await get_isol_sign_statistics(term_lower, db_isol) if term_lower else None

    # Calcul du nombre total de pages nécessaires
    total_pages = (total_count // limit) + (1 if total_count % limit else 0)

    # Rendu du template avec toutes les données nécessaires à l'affichage
    return templates.TemplateResponse(
        request,
        "results_isol.html",
        {
            "request": request,
            "submitType": submitType,
            "term": term,
            "signer": signer,
            "min_duration": min_duration_val,
            "max_duration": max_duration_val,
            "isol_videos": isol_videos,
            "no_results": no_results,
            "stats": stats,
            "current_page": page,
            "total_pages": total_pages if total_pages else 1,
        },
    )

@router.get("/cont_poses/{video_id}")
async def get_cont_poses(
    video_id: str,
    db_cont: AsyncSession = Depends(get_db_cont)
):
    # Si vidéo trouvée dans CONT, récupérer les poses associées
    poses_query = select(ContPose).filter(ContPose.instance_id == video_id)  # Requête pour récupérer les poses associées à la vidéo
    poses_data = await db_cont.execute(poses_query)
    
    # Création du dictionnaire avec les parties du corps et leurs chemins de pose
    poses_dict = {}
    for pose in poses_data.scalars().all():
        pose_part = pose.pose_part
        pose_path = pose.pose_path
        if pose_part not in poses_dict:
            poses_dict[pose_part] = []
        poses_dict[pose_part].append(pose_path)

    # Retourner un dictionnaire avec les parties du corps comme clés et les chemins des poses comme valeurs
    return {"pose_paths": poses_dict}


#--- Route d'affichage vidéo isol : /video/isol/{video_id} ---
# Définir le chemin de base du dataset "isol"
BASE_DIR_ISOL = Path(r"E:\lsfb dataset\isol")
BASE_DIR_ISOL_POSES = Path(r"E:\lsfb dataset\isol\poses")
@router.get("/video/isol/{video_id}", response_class=HTMLResponse)
async def get_video_isol(
    request: Request,
    video_id: str,
    previous_term: str = "",
    db_isol: AsyncSession = Depends(get_db_isol)
):
    """
    Route pour afficher la vidéo ISOL et le squelette 3D associé à partir des poses.
    Cette route récupère les poses associées à la vidéo 
    """

    # 1. Récupérer les informations de la vidéo depuis la base de données
    query_isol = select(IsolVideo).filter(IsolVideo.instance_id == video_id)  # Sélectionner la vidéo en fonction de l'ID
    result_isol = await db_isol.execute(query_isol)  # Exécution de la requête
    video_isol = result_isol.scalar_one_or_none()  # Retourne une vidéo ou None si elle n'existe pas

    # 2. Si la vidéo n'existe pas, renvoyer une page avec des valeurs par défaut
    if not video_isol:
        return templates.TemplateResponse(
            request,
            "video_view_isol.html",  # Rendre le template HTML avec des valeurs par défaut si la vidéo n'est pas trouvée
            {
                "instance_id": video_id,
                "video_path": "",  # Aucun chemin vidéo
                "previous_term": previous_term,  # Term précédent de la recherche
                "dataset": "none"  # Dataset "none" si la vidéo est introuvable
            }
        )

    # 3. Transformation du chemin absolu de la vidéo en URL relative pour la rendre accessible depuis le frontend
    video_abs_path = Path(video_isol.path)  # On récupère le chemin absolu de la vidéo
    try:
        # 7.1 Calculer le chemin relatif de la vidéo par rapport à `BASE_DIR_ISOL`
        relative_video_path = video_abs_path.relative_to(BASE_DIR_ISOL)  # Transforme le chemin absolu en relatif
        video_url = f"/isol/{relative_video_path.as_posix()}"  # Créer une URL relative pour la vidéo
    except ValueError:
        video_url = video_isol.path  # Si une erreur se produit, utiliser le chemin absolu de la vidéo

    # 4. Retourner la réponse HTML avec les données nécessaires pour l'affichage
    return templates.TemplateResponse(
        request,
        "video_view_isol.html",  # Le template HTML à rendre
        {
            "request": request,
            "instance_id": video_id,  # Passer l'ID de la vidéo
            "video_path": video_url,  # L'URL de la vidéo à afficher
            "previous_term": previous_term,  # Le terme de recherche précédent
            "dataset": "isol"  # Nom du dataset (ici, "isol")
        }
    )

@router.get("/isol_poses/{video_id}")
async def get_isol_poses(
    video_id: str,
    db_isol: AsyncSession = Depends(get_db_isol)
):
    # Si vidéo trouvée dans ISOL, récupérer les poses associées
    poses_query = select(IsolPose).filter(IsolPose.instance_id == video_id)  # Requête pour récupérer les poses associées à la vidéo
    poses_data = await db_isol.execute(poses_query)
    
    # Création du dictionnaire avec les parties du corps et leurs chemins de pose
    poses_dict = {}
    for pose in poses_data.scalars().all():
        pose_part = pose.pose_part
        pose_path = pose.pose_path
        if pose_part not in poses_dict:
            poses_dict[pose_part] = []
        poses_dict[pose_part].append(pose_path)

    # Retourner un dictionnaire avec les parties du corps comme clés et les chemins des poses comme valeurs
    return {"pose_paths": poses_dict}


# Fonctions asynchrones pour calculer les statistiques
# --- Statistiques sur les mots ou les phrases dans Cont ---
async def get_word_stats(word: str, db_session: AsyncSession):
    # Recherche dans SubtitleAnnotation toutes les phrases contenant le mot (insensible à la casse)
    query_subs = select(SubtitleAnnotation).filter(
        SubtitleAnnotation.text.ilike(f"%{word}%")
    )
    result_subs = await db_session.execute(query_subs)
    subtitle_annotations = result_subs.scalars().all()
    
    total_occurrences = 0
    phrases_count = 0
    for ann in subtitle_annotations:
        # Comptage insensible à la casse
        count = ann.text.lower().count(word.lower())
        if count > 0:
            total_occurrences += count
            phrases_count += 1

    # Nombre d'annotations dans WordAnnotation contenant le mot (insensible à la casse)
    query_word = select(func.count(WordAnnotation.word_id)).filter(
        WordAnnotation.word.ilike(f"%{word}%")
    )
    result_word = await db_session.execute(query_word)
    word_annotations_count = result_word.scalar()
    
    return {
        "total_occurrences_in_phrases": total_occurrences,
        "number_of_phrases": phrases_count,
        "word_annotations_count": word_annotations_count,
    }

# --- Statistiques sur les phrases dans Cont ---
async def get_phrase_stats(phrase: str, db_session: AsyncSession):
    # Nombre d'occurrences de la phrase dans SubtitleAnnotation (insensible à la casse)
    query_phrase = select(func.count(SubtitleAnnotation.sub_id)).filter(
        SubtitleAnnotation.text.ilike(f"%{phrase}%")
    )
    result_phrase = await db_session.execute(query_phrase)
    phrase_occurrences = result_phrase.scalar()
    
    # Nombre distinct de signataires ayant prononcé cette phrase
    query_signers = (
        select(func.count(distinct(ContInstance.signer_id))).
        join(SubtitleAnnotation, SubtitleAnnotation.instance_id == ContInstance.id).
        filter(SubtitleAnnotation.text.ilike(f"%{phrase}%"))
    )
    result_signers = await db_session.execute(query_signers)
    distinct_signers = result_signers.scalar()

    return {
        "phrase_occurrences": phrase_occurrences,
        "distinct_signers": distinct_signers,
    }
# --- Statistiques particulières par signe dans Isolé ---
async def get_isol_sign_statistics(sign: str, session: AsyncSession):
    # Conversion en minuscules pour une comparaison insensible à la casse
    sign_lower = sign.lower()
    
    # Nombre d'occurrences du signe (insensible à la casse)
    count = await session.scalar(
        select(func.count()).select_from(IsolInstance)
        .where(func.lower(IsolInstance.sign) == sign_lower)
    )
    
    # Durée moyenne du signe (calculée sur la différence entre end et start)
    avg_duration = await session.scalar(
        select(func.avg(IsolInstance.end - IsolInstance.start))
        .where(func.lower(IsolInstance.sign) == sign_lower)
    )
    
    # Nombre de signataires distincts ayant réalisé ce signe
    distinct_signers_count = await session.scalar(
        select(func.count(func.distinct(IsolInstance.signer)))
        .where(func.lower(IsolInstance.sign) == sign_lower)
    )
    
    # Récupérer les durées pour chaque occurrence
    query = select(IsolInstance.start, IsolInstance.end).where(func.lower(IsolInstance.sign) == sign_lower)
    results = await session.execute(query)
    durations = [(row.end - row.start) for row in results]
    
    # S'il n'y a pas de durées, renvoyer des statistiques par défaut
    if not durations:
        return {
            "sign": sign,
            "occurrences": 0,
            "average_duration": 0,
            "min_duration": 0,
            "max_duration": 0,
            "distinct_signers": 0,
            "graph": ""
        }
    
    # Calcul des durées minimale et maximale à partir de la liste obtenue
    min_duration_value = min(durations)
    max_duration_value = max(durations)
    
    # Génération d'un histogramme des durées
    plt.figure(figsize=(8, 5))
    plt.hist(durations, bins=10, alpha=0.7, color='blue', edgecolor='black')
    plt.axvline(avg_duration, color='red', linestyle='dashed', linewidth=2,
                label=f"Durée moyenne: {avg_duration:.2f} ms")
    plt.xlabel("Durée (millisecondes)")
    plt.ylabel("Nombre d'occurrences")
    plt.title(f"Distribution des durées pour le signe '{sign}'")
    plt.legend()
    
    # Sauvegarde de l'image dans un buffer en mémoire
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    plt.close()  # Libère la mémoire en fermant la figure
    img_buf.seek(0)
    img_base64 = base64.b64encode(img_buf.getvalue()).decode('utf-8')
    
    # Retourne un dictionnaire avec toutes les statistiques calculées
    return {
        "sign": sign,
        "occurrences": count,
        "average_duration": avg_duration,
        "min_duration": min_duration_value,
        "max_duration": max_duration_value,
        "distinct_signers": distinct_signers_count,
        "graph": f"data:image/png;base64,{img_base64}"
    }


# --- Statistiques générales ---
# --- Statistiques générales sur les instances ---
@router.get("/stats/general")
async def get_general_statistics(
    session_cont: AsyncSession = Depends(get_db_cont),
    session_isol: AsyncSession = Depends(get_db_isol)
):
    # CONT
    total_clips_cont = await session_cont.scalar(select(func.count()).select_from(ContInstance))
    total_glosses_cont = await session_cont.scalar(select(func.count(distinct(WordAnnotation.word))))
    total_signers_cont = await session_cont.scalar(select(func.count(distinct(ContInstance.signer_id))))

    # Moyenne de la durée des clips CONT
    avg_clip_duration_cont = await session_cont.scalar(select(func.avg(cast(WordAnnotation.end_time - WordAnnotation.start_time, Float))))

    # Moyenne des clips par gloss CONT
    subq_clips_per_gloss_cont = select(func.count(WordAnnotation.word_id).label("count")).group_by(WordAnnotation.word).subquery()
    avg_clips_per_gloss_cont = await session_cont.scalar(select(func.avg(cast(subq_clips_per_gloss_cont.c.count, Float))))


    # Moyenne de gloss par vidéo CONT
    subq_glosses_per_video_cont = select(
        ContVideo.instance_id,
        func.count(WordAnnotation.word_id).label('count')
    ).join(
        ContInstance, ContInstance.id == ContVideo.instance_id
    ).join(
        WordAnnotation, WordAnnotation.instance_id == ContInstance.id
    ).group_by(ContVideo.instance_id).subquery()
    avg_glosses_per_video_cont = await session_cont.scalar(select(func.avg(cast(subq_glosses_per_video_cont.c.count, Float))))

    # Statistiques ISOL
    total_clips_isol = await session_isol.scalar(select(func.count()).select_from(IsolInstance))
    total_glosses_isol = await session_isol.scalar(select(func.count(distinct(IsolInstance.sign))))
    total_signers_isol = await session_isol.scalar(select(func.count(distinct(IsolInstance.signer))))

    # Moyenne durée des clips ISOL
    avg_clip_duration_isol = await session_isol.scalar(select(func.avg(cast(IsolInstance.end - IsolInstance.start, Float))))

    # Moyenne des clips par gloss ISOL
    subq_clips_per_gloss_isol = select(func.count(IsolInstance.id).label('count')).group_by(IsolInstance.sign).subquery()
    avg_clips_per_gloss_isol = await session_isol.scalar(select(func.avg(cast(subq_clips_per_gloss_isol.c.count, Float))))

    # Moyenne des gloss par vidéo ISOL (toujours 1 gloss par vidéo dans isol)
    avg_glosses_per_video_isol = 1

    # Moyenne de phrases par vidéo CONT
    subq_phrases_per_video_cont = select(ContVideo.instance_id,func.count(SubtitleAnnotation.sub_id).label('count')).join(ContInstance, ContInstance.id == ContVideo.instance_id
    ).join(SubtitleAnnotation, SubtitleAnnotation.instance_id == ContInstance.id).group_by(ContVideo.instance_id).subquery()

    avg_phrases_per_video_cont = await session_cont.scalar(select(func.avg(cast(subq_phrases_per_video_cont.c.count, Float))))

    # --- Arrondir les moyennes vers le bas (floor) si elles ne sont pas None ---
    if avg_clip_duration_cont is not None:
        avg_clip_duration_cont = math.floor(avg_clip_duration_cont)
    if avg_clip_duration_isol is not None:
        avg_clip_duration_isol = math.floor(avg_clip_duration_isol)
    if avg_clips_per_gloss_cont is not None:
        avg_clips_per_gloss_cont = math.floor(avg_clips_per_gloss_cont)
    if avg_clips_per_gloss_isol is not None:
        avg_clips_per_gloss_isol = math.floor(avg_clips_per_gloss_isol)
    if avg_glosses_per_video_cont is not None:
        avg_glosses_per_video_cont = math.floor(avg_glosses_per_video_cont)
    # Pour ISOL, on laisse "1" en dur, donc pas besoin de floor
    if avg_phrases_per_video_cont is not None:
        avg_phrases_per_video_cont = math.floor(avg_phrases_per_video_cont)


    # Retour des résultats
    return {
        "total_clips_cont": total_clips_cont,
        "total_clips_isol": total_clips_isol,
        "total_glosses_cont": total_glosses_cont,
        "total_glosses_isol": total_glosses_isol,
        "total_signers_cont": total_signers_cont,
        "total_signers_isol": total_signers_isol,
        "avg_clip_duration_cont": avg_clip_duration_cont,
        "avg_clip_duration_isol": avg_clip_duration_isol,
        "avg_clips_per_gloss_cont": avg_clips_per_gloss_cont,
        "avg_clips_per_gloss_isol": avg_clips_per_gloss_isol,
        "avg_glosses_per_video_cont": avg_glosses_per_video_cont,
        "avg_glosses_per_video_isol": avg_glosses_per_video_isol,
        "avg_phrases_per_video_cont": avg_phrases_per_video_cont
    }

# --- Statistiques sur les vidéos ---
@router.get("/stats/videos/info")
async def get_videos_info(session: AsyncSession = Depends(get_db_cont)):
    """
    Renvoie un dictionnaire de la forme :
    {
      "instance_id_1": {
        "signer_id": ...,
        "session_id": ...,
        "task_id": ...,
        "n_frames": ...,
        "n_signs": ...
      },
      "instance_id_2": { ... },
      ...
    }
    """
    results = await session.execute(select(ContInstance))
    instances = results.scalars().all()

    data = {}
    for inst in instances:
        data[inst.id] = {
            "signer_id": inst.signer_id,
            "session_id": inst.session_id,
            "task_id": inst.task_id,
            "n_frames": inst.n_frames,
            "n_signs": inst.n_signs
        }
    return data

# --- Statistiques sur les poses et mouvements ---
@router.get("/stats/poses/distribution")
async def get_pose_distribution(session: AsyncSession = Depends(get_db_cont)):
    query = select(
        ContPose.pose_part, func.count(ContPose.pose_id).label("count")).group_by(ContPose.pose_part)

    results = await session.execute(query)
    # Retourne la distribution des poses par partie du corps
    return {part: count for part, count in results.all()}


# --- Statistiques sur les signers ---
@router.get("/stats/signers/variability")
async def get_signer_variability(session: AsyncSession = Depends(get_db_cont)):
    query = select(
        ContInstance.signer_id,func.count(distinct(WordAnnotation.word)).label("unique_glosses")
    ).join(WordAnnotation, ContInstance.id == WordAnnotation.instance_id).group_by(ContInstance.signer_id)

    results = await session.execute(query)
    # Variabilité des signers : nombre de gloss uniques signés par chaque signer
    # => Convertissons signer_id en chaîne pour être cohérent dans le JSON
    return {str(signer_id): gloss_count for signer_id, gloss_count in results.all()}

from fastapi import Query

# --- Visualisations des glosses les plus fréquents ---
@router.get("/stats/visualizations/histogram")
async def get_gloss_histogram(
    top: int = Query(10, le=20, ge=5),  # Valeur par défaut 10, minimum 5, maximum 20
    session: AsyncSession = Depends(get_db_cont)
):
    query = (
        select(WordAnnotation.word, func.count(WordAnnotation.word_id).label("count"))
        .group_by(WordAnnotation.word)
        .order_by(func.count(WordAnnotation.word_id).desc())
        .limit(top)
    )

    results = await session.execute(query)
    return {word: count for word, count in results.all()}


# --- Visualisations des sous-titres(expressions) les plus fréquents ---
@router.get("/stats/visualizations/top_subtitles")
async def get_top_subtitles(
    top: int = Query(10, le=20, ge=5),
    session: AsyncSession = Depends(get_db_cont)
):
    """
    Renvoie les N sous-titres les plus utilisés,
    sous la forme { "Sous-titre 1": 12, "Sous-titre 2": 9, ... }.
    L'utilisateur peut spécifier le nombre de résultats via le paramètre 'top' (entre 1 et 20).
    """
    query = (
        select(SubtitleAnnotation.text, func.count(SubtitleAnnotation.sub_id).label("count"))
        .group_by(SubtitleAnnotation.text)
        .order_by(func.count(SubtitleAnnotation.sub_id).desc())
        .limit(top)
    )
    results = await session.execute(query)
    return {text: count for text, count in results.all()}



# --- Statistiques sur les glosses ---
@router.get("/stats/glosses/frequency")
async def get_gloss_frequency(session: AsyncSession = Depends(get_db_cont)):
    # Compte les occurrences de chaque gloss dans les annotations
    query = select(WordAnnotation.word,func.count(WordAnnotation.word_id).label("frequency")).group_by(WordAnnotation.word).order_by(func.count(WordAnnotation.word_id).desc())
    results = await session.execute(query)
    # Retourne un dictionnaire {gloss: fréquence}
    return {word: freq for word, freq in results.all()}

# --- Statistiques sur les phrases (analyse de cooccurrence) ---
"""from collections import Counter
@router.get("/stats/phrases/cooccurrence")
async def get_gloss_cooccurrence(session: AsyncSession = Depends(get_db_cont)):
    # Récupération des gloss regroupés par instance
    query = select(
        WordAnnotation.instance_id,
        func.array_agg(WordAnnotation.word).label("words")
    ).group_by(WordAnnotation.instance_id)

    results = await session.execute(query)

    # Calcul de la fréquence des combinaisons de gloss
    cooccurrences = Counter()
    for instance_id, words in results.all():
        key = tuple(sorted(words))
        cooccurrences[key] = cooccurrences.get(key, 0) + 1

    # Retourne un dictionnaire avec les cooccurrences et leur fréquence
    return {"; ".join(key): val for key, val in cooccurrences.items()}"""
