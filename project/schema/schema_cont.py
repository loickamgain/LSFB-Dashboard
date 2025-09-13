from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

# Énumérations pour les annotations de signe
class SignTypeEnum(str, Enum):
    normal = "normal"
    special = "special"

class HandTypeEnum(str, Enum):
    both_hands = "both_hands"
    left_hand = "left_hand"
    right_hand = "right_hand"

# BaseModel pour LSFB (Cont)
class BaseCont(BaseModel):
    class Config:
        orm_mode = True

# Schéma pour une instance (table instances_cont)
class InstanceContSchema(BaseCont):
    id: str
    signer_id: str
    session_id: str
    task_id: str
    n_frames: int
    n_signs: int

# Schéma pour un signataire (table signers_cont)
class SignerContSchema(BaseCont):
    signer_id: str
    age: Optional[int] = None
    region: Optional[str] = None
    gender: Optional[str] = None
    total_instances: Optional[int] = None            # Calculé, nombre total d'instances du signataire

# Schéma pour une annotation de signe (table words)
class WordAnnotationContSchema(BaseCont):
    word_id: int
    instance_id: str
    sign_type: SignTypeEnum
    hand_type: HandTypeEnum
    start_time: int
    end_time: int

# Schéma pour une annotation de phrase (table subtitles)
class SubtitleAnnotationContSchema(BaseCont):
    sub_id: int
    instance_id: str
    text: str
    start_time: int
    end_time: int

# Schéma pour une pose (table poses_cont)
class PoseContSchema(BaseCont):
    pose_id: int
    instance_id: str
    pose_part: str
    pose_path: str

# Schéma pour une vidéo (table videos_cont)
class VideoContSchema(BaseCont):
    video_id: int
    path: str
    instance_id: str # Lien optionnel vers l'instance associée, si nécessaire

# Schéma de réponse de recherche (pour la recherche par gloss ou phrase)
class ContSearchResponseSchema(BaseCont):
    query: str                              # Le mot ou la phrase recherchée
    instance_ids: List[str]                 # Liste des IDs des instances correspondantes
    occurrences: int                        # Nombre total d'occurrences trouvées
    average_duration: Optional[float] = None  # Durée moyenne (si applicable)
    videos: List[VideoContSchema] # Liste de vidéos correspondantes
