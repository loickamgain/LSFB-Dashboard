from pydantic import BaseModel
from typing import Optional, List

# BaseModel pour ISOL (Iso)
class BaseIso(BaseModel):
    class Config:
        orm_mode = True

# Schéma pour une instance dans iso (table instances_iso)
class InstanceIsoSchema(BaseIso):
    id: str
    sign: str       # Le signe effectué
    signer: str     # Identifiant du signataire (clé étrangère vers signers_iso)
    start: int      # Temps de début du signe
    end: int        # Temps de fin du signe

# Schéma pour un signataire dans iso (table signers_iso)
class SignerIsoSchema(BaseIso):
    signer_id: str
    age: Optional[int] = None          # L'âge du signataire, peut être optionnel
    region: Optional[str] = None       # La région du signataire, peut être optionnel
    gender: Optional[str] = None       # Le genre du signataire, peut être optionnel
    total_instances: Optional[int] = None           # Nombre total d'instances pour ce signataire, peut être optionnel

# Schéma pour une pose dans iso (table poses_iso)
class PoseIsoSchema(BaseIso):
    pose_id: int
    instance_id: str   # ID de l'instance associée (clé étrangère vers instances_iso)
    pose_part: str     # Partie du corps concernée par la pose
    pose_path: str     # Chemin d'accès au fichier de la pose

# Schéma pour une vidéo dans iso (table videos_iso)
class VideoIsoSchema(BaseIso):
    video_id: int
    path: str         # Chemin d'accès de la vidéo
    instance_id: str

# Schéma de réponse de recherche pour la base ISOL
class IsoSearchResponseSchema(BaseIso):
    query: str                              # Le mot ou la phrase recherchée
    instance_ids: List[str]                 # Liste des IDs des instances correspondantes dans iso
    occurrences: int                        # Nombre total d'occurrences
    average_sign_duration: Optional[float] = None  # Durée moyenne du signe
    videos: List[VideoIsoSchema]  # Liste de vidéos correspondantes
