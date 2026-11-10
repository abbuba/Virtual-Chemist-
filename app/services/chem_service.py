from itertools import combinations
from sqlalchemy.orm import Session
from app.models.models import User
from app.services.embedding_service import embed_text
from app.models.models import Molecule, Discovery
from app.repositories.molecule_repo import MoleculeRepository

class ChemicalService:
    @staticmethod
    def evaluate_combination(db: Session, atoms: list[str], user: User):
        symbols = [a.strip().capitalize() for a in atoms if a.strip().isalpha()]
        recipes = MoleculeRepository.get_recipe_map(db)

        # Atoms arrive closest-first; prefer the biggest molecule that can be built from them
        molecule, used = None, []
        for size in range(len(symbols), 1, -1):
            for combo in combinations(range(len(symbols)), size):
                chosen = sorted(symbols[i] for i in combo)
                molecule = recipes.get("-".join(chosen))
                if molecule:
                    used = chosen
                    break
            if molecule:
                break

        if not molecule:
            return {"success": False, "message": "Invalid molecular combination!"}

        _, created = MoleculeRepository.record_discovery(db, user.id, molecule.id)

        return {
            "success": True,
            "saved": True,
            "new_discovery": created,
            "message": "Added to your profile!" if created else "Already in your collection.",
            "used_atoms": used,
            "formula": molecule.formula,
            "name": molecule.name,
            "description": molecule.description,
            "safety_warnings": molecule.safety_warnings,
            "industrial_uses": molecule.industrial_uses
        }

    @staticmethod
    def get_profile(db: Session, user: User):
        rows = MoleculeRepository.get_user_discoveries(db, user.id)
        return {
            "username": user.username,
            "joined": user.created_at,
            "total_molecules": MoleculeRepository.count_molecules(db),
            "discovered_count": len(rows),
            "discoveries": [
                {
                    "formula": molecule.formula,
                    "name": molecule.name,
                    "description": molecule.description,
                    "safety_warnings": molecule.safety_warnings,
                    "industrial_uses": molecule.industrial_uses,
                    "discovered_at": discovery.discovered_at,
                }
                for discovery, molecule in rows
            ],
        }

    @staticmethod
    def _card(m, similarity=None, found=False):
        card = {
            "formula": m.formula, "name": m.name, "atoms": (m.recipe or "").split("-"),
            "description": m.description, "discovered": found,
        }
        if similarity is not None:
            card["similarity"] = round(similarity, 3)
        return card

    @staticmethod
    def search(db: Session, query: str, user: User, limit: int = 3):
        """RAG retrieval: embed the question, then ask pgvector for the nearest molecules."""
        vec = embed_text(query)
        distance = Molecule.embedding.cosine_distance(vec)
        rows = db.query(Molecule, distance).filter(Molecule.recipe.isnot(None)).order_by(distance).limit(limit).all()
        mine = {d.molecule_id for d in db.query(Discovery).filter_by(user_id=user.id)}
        return {"query": query, "results": [ChemicalService._card(m, 1 - d, m.id in mine) for m, d in rows]}

    @staticmethod
    def hint(db: Session, user: User):
        mine = {d.molecule_id for d in db.query(Discovery).filter_by(user_id=user.id)}
        todo = [m for m in db.query(Molecule).filter(Molecule.recipe.isnot(None)).all() if m.id not in mine]
        if not todo:
            return {"done": True}
        # nudge beginners toward small molecules first
        todo.sort(key=lambda m: len(m.recipe.split("-")))
        import random
        return {"done": False, **ChemicalService._card(random.choice(todo[:4]))}
