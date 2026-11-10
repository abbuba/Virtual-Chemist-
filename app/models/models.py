from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint

from sqlalchemy.orm import relationship

from sqlalchemy.sql import func

from pgvector.sqlalchemy import Vector

from app.database import Base



class User(Base):

    __tablename__ = "users"



    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(50), unique=True, nullable=False)

    password_hash = Column(String, nullable=True)
    email = Column(String(254), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())



    discoveries = relationship("Discovery", back_populates="user")





class Atom(Base):

    __tablename__ = "atoms"



    id = Column(Integer, primary_key=True, index=True)

    symbol = Column(String(5), unique=True, nullable=False, index=True)  # e.g., "H", "O", "Si"

    name = Column(String(50), nullable=False)                            # e.g., "Hydrogen", "Oxygen"

    atomic_number = Column(Integer, nullable=False)

    valence = Column(Integer, nullable=False)





class Molecule(Base):

    __tablename__ = "molecules"



    id = Column(Integer, primary_key=True, index=True)

    formula = Column(String(50), unique=True, nullable=False, index=True) # e.g., "SiO2"

    recipe = Column(String(60), unique=True, nullable=True)              # sorted atoms, e.g., "H-H-O"

    name = Column(String(100), nullable=False)                           # e.g., "Silicon Dioxide (Glass)"

    description = Column(String, nullable=False)

    safety_warnings = Column(String, nullable=False)

    industrial_uses = Column(String, nullable=False)

    # pgvector embedding column for RAG similarity search (e.g., 384 dimensions for miniLM or 1536 for OpenAI)

    embedding = Column(Vector(384))



    discoveries = relationship("Discovery", back_populates="molecule")





class Discovery(Base):

    __tablename__ = "discoveries"



    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    molecule_id = Column(Integer, ForeignKey("molecules.id"), nullable=False)

    discovered_at = Column(DateTime(timezone=True), server_default=func.now())



    user = relationship("User", back_populates="discoveries")

    molecule = relationship("Molecule", back_populates="discoveries")



    __table_args__ = (

        UniqueConstraint('user_id', 'molecule_id', name='uq_user_molecule'),

    )


class LoginEvent(Base):
    """Audit trail of sign-in activity (never stores passwords or codes)."""
    __tablename__ = "login_events"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(254), nullable=False, index=True)
    event = Column(String(40), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
