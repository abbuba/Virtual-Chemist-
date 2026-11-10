from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.models import Molecule, Discovery

class MoleculeRepository:
    @staticmethod
    def get_molecule_by_formula(db: Session, formula: str) -> Molecule:
        return db.query(Molecule).filter(Molecule.formula == formula).first()

    @staticmethod
    def get_recipe_map(db: Session) -> dict:
        return {m.recipe: m for m in db.query(Molecule).filter(Molecule.recipe.isnot(None)).all()}

    @staticmethod
    def record_discovery(db: Session, user_id: int, molecule_id: int) -> tuple[Discovery, bool]:
        """Returns (discovery, created). created is False if the user already had it."""
        existing = db.query(Discovery).filter_by(user_id=user_id, molecule_id=molecule_id).first()
        if existing:
            return existing, False

        discovery = Discovery(user_id=user_id, molecule_id=molecule_id)
        db.add(discovery)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.query(Discovery).filter_by(user_id=user_id, molecule_id=molecule_id).first()
            return existing, False
        db.refresh(discovery)
        return discovery, True

    @staticmethod
    def get_user_discoveries(db: Session, user_id: int):
        return (
            db.query(Discovery, Molecule)
            .join(Molecule, Molecule.id == Discovery.molecule_id)
            .filter(Discovery.user_id == user_id)
            .order_by(Discovery.discovered_at.desc())
            .all()
        )

    @staticmethod
    def count_molecules(db: Session) -> int:
        return db.query(Molecule).count()
