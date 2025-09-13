from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.db_init import BaseIsol  # Import spécifique pour 'isol'

class IsolInstance(BaseIsol):  # Table des instances isol
    __tablename__ = "instances_iso"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    sign: Mapped[str] = mapped_column(String, nullable=False)
    signer: Mapped[str] = mapped_column(String, nullable=False)
    start: Mapped[int] = mapped_column(Integer, nullable=False)
    end: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Relation one-to-many avec IsolPose
    poses_iso: Mapped[list["IsolPose"]] = relationship("IsolPose", back_populates="instance_iso")
    # Relation one-to-one avec IsolVideo
    video: Mapped["IsolVideo"] = relationship("IsolVideo", back_populates="instance_iso", uselist=False)
    
    def as_dict(self):
        return {
            "id": self.id,
            "sign": self.sign,
            "signer": self.signer,
            "start": self.start,
            "end": self.end,
            "poses_iso": [pose.as_dict() for pose in self.poses_iso],
            "video": self.video.as_dict() if self.video else None
        }

class IsolVideo(BaseIsol):  # Table des vidéos isol
    __tablename__ = "videos_iso"
    
    video_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[str] = mapped_column(String, ForeignKey("instances_iso.id"))
    path: Mapped[str] = mapped_column(String, nullable=False)
    
    # Relation one-to-one avec IsolInstance
    instance_iso: Mapped["IsolInstance"] = relationship("IsolInstance", back_populates="video", uselist=False)
    
    def as_dict(self):
        return {
            "video_id": self.video_id,
            "instance_id": self.instance_id,
            "duration": int(self.instance_iso.end - self.instance_iso.start) if self.instance_iso else None,
            "path": self.path
        }

class IsolPose(BaseIsol):  # Table des poses isol
    __tablename__ = "poses_iso"
    
    pose_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[str] = mapped_column(String, ForeignKey('instances_iso.id'), nullable=False)
    pose_part: Mapped[str] = mapped_column(String, nullable=False)
    pose_path: Mapped[str] = mapped_column(String, nullable=False)
    
    # Relation many-to-one avec IsolInstance
    instance_iso: Mapped["IsolInstance"] = relationship("IsolInstance", back_populates="poses_iso")
    
    def as_dict(self):
        return {
            "pose_id": self.pose_id,
            "instance_id": self.instance_id,
            "pose_part": self.pose_part,
            "pose_path": self.pose_path
        }
