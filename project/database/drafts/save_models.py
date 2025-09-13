#---ContSigner---#
class ContSigner(BaseCont):
    __tablename__ = "signers_cont"  

    signer_id: Mapped[str] = mapped_column(String, primary_key=True)
    age: Mapped[int] = mapped_column(Integer)
    region: Mapped[str] = mapped_column(String)
    gender: Mapped[str] = mapped_column(String)

    # Relation one-to-many avec Instance
    instances_cont: Mapped[list["ContInstance"]] = relationship("ContInstance", back_populates="signer_cont")

    def __repr__(self):
        return f"<ContSigner(signer_id='{self.signer_id}', age={self.age}, region='{self.region}', gender='{self.gender}')>"
    
# relation  instance_cont : # Relation many-to-one avec Signer
    signer_cont: Mapped["ContSigner"] = relationship("ContSigner", back_populates="instances_cont")



#---IsolSigner---#
class IsolSigner(BaseIsol):
    __tablename__ = "signers_iso"
    
    signer_id: Mapped[str] = mapped_column(String, primary_key=True)
    age: Mapped[int] = mapped_column(Integer)
    region: Mapped[str] = mapped_column(String)
    gender: Mapped[str] = mapped_column(String)
    
    # Relation one-to-many avec IsolInstance
    instances_iso: Mapped[list["IsolInstance"]] = relationship("IsolInstance", back_populates="signer_iso")
    
    def __repr__(self):
        return (f"<IsolSigner(signer_id='{self.signer_id}', age={self.age}, "
                f"region='{self.region}', gender='{self.gender}')>")
# Relation many-to-one avec IsolSigner
    signer_iso: Mapped["IsolSigner"] = relationship("IsolSigner", back_populates="instances_iso")