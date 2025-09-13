from sqlalchemy import String, Integer, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.db_init import BaseCont  # Import spécifique pour 'cont'

# Définition des ENUMs correctement
hand_enum = Enum('both_hands', 'left_hand', 'right_hand', name='hand_enum')
type_enum = Enum('normal', 'special', name='type_enum')

class ContInstance(BaseCont):  # Table pour stocker les instances
    __tablename__ = "instances_cont"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    signer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    session_id: Mapped[int] = mapped_column(Integer, nullable=False)
    task_id: Mapped[int] = mapped_column(Integer, nullable=False)
    n_frames: Mapped[int] = mapped_column(Integer, nullable=False)
    n_signs: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relations one-to-many
    word_annotations: Mapped[list["WordAnnotation"]] = relationship("WordAnnotation", back_populates="instance_cont")
    subtitle_annotations: Mapped[list["SubtitleAnnotation"]] = relationship("SubtitleAnnotation", back_populates="instance_cont")
    poses_cont: Mapped[list["ContPose"]] = relationship("ContPose", back_populates="instance_cont")
    
    # Relation one-to-one avec Video
    video: Mapped["ContVideo"] = relationship("ContVideo", back_populates="instance_cont", uselist=False)

    
    def as_dict(self):
        return {
            "id": self.id,
            "signer_id": self.signer_id,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "n_frames": self.n_frames,
            "n_signs": self.n_signs,
            "word_annotations": [wa.as_dict() for wa in self.word_annotations],
            "subtitle_annotations": [sa.as_dict() for sa in self.subtitle_annotations],
            "poses_cont": [pose.as_dict() for pose in self.poses_cont],
            "video": self.video.as_dict() if self.video else None
        }

class ContVideo(BaseCont):  # Table pour stocker les vidéos
    __tablename__ = "videos_cont"

    video_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # ID unique de la vidéo
    instance_id: Mapped[str] = mapped_column(String, ForeignKey("instances_cont.id"))  # ID de la vidéo liée
    path: Mapped[str] = mapped_column(String, nullable=False)

    # Relation one-to-one avec ContInstance (chaque vidéo est associée à une seule instance)
    instance_cont: Mapped["ContInstance"] = relationship("ContInstance", back_populates="video", uselist=False, lazy="joined")

    def as_dict(self):
        return {
            "video_id": self.video_id,
            "instance_id": self.instance_id,
            "path": self.path
        }

class WordAnnotation(BaseCont):  # Table pour stocker les annotations de mots
    __tablename__ = "words"

    word_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[str] = mapped_column(String, ForeignKey('instances_cont.id'), nullable=False)
    word: Mapped[str] = mapped_column(String, nullable=False)
    sign_type: Mapped[str] = mapped_column(type_enum, nullable=False)  # Enum normal, special
    hand_type: Mapped[str] = mapped_column(hand_enum, nullable=False)  # Enum both_hands, left_hand, right_hand
    start_time: Mapped[int] = mapped_column(Integer, nullable=False)
    end_time: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relations many-to-one
    instance_cont: Mapped["ContInstance"] = relationship("ContInstance", back_populates="word_annotations")

    def as_dict(self):
        return {
            "word_id": self.word_id,
            "instance_id": self.instance_id,
            "word": self.word,
            "sign_type": self.sign_type,
            "hand_type": self.hand_type,
            "start_time": self.start_time,
            "end_time": self.end_time
        }

class SubtitleAnnotation(BaseCont):  # Table pour stocker les annotations de sous-titres
    __tablename__ = "subtitles"

    sub_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[str] = mapped_column(String, ForeignKey('instances_cont.id'), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[int] = mapped_column(Integer, nullable=False)
    end_time: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relation many-to-one avec Instance
    instance_cont: Mapped["ContInstance"] = relationship("ContInstance", back_populates="subtitle_annotations")

    def as_dict(self):
        return {
            "sub_id": self.sub_id,
            "instance_id": self.instance_id,
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time
        }

class ContPose(BaseCont):  # Table pour stocker les poses
    __tablename__ = 'poses_cont'

    pose_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[str] = mapped_column(String, ForeignKey('instances_cont.id'), nullable=False)
    pose_part: Mapped[str] = mapped_column(String)
    pose_path: Mapped[str] = mapped_column(String)

    # Relation many-to-one avec Instance
    instance_cont: Mapped["ContInstance"] = relationship("ContInstance", back_populates="poses_cont")

    def as_dict(self):
        return {
            "pose_id": self.pose_id,
            "instance_id": self.instance_id,
            "pose_part": self.pose_part,
            "pose_path": self.pose_path
        }
