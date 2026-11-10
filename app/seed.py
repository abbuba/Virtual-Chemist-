from app.database import SessionLocal, init_db
from app.models.models import Atom, Molecule
from app.services.embedding_service import embed_text, molecule_text
from app.seed_data import ELEMENTS, MOLECULES, recipe_key


def seed_database(verbose: bool = True) -> None:
    """Adds any missing elements/molecules and fills in recipes. Safe to run many times."""
    init_db()
    db = SessionLocal()
    try:
        have_atoms = {a.symbol for a in db.query(Atom).all()}
        for symbol, name, number, valence in ELEMENTS:
            if symbol not in have_atoms:
                db.add(Atom(symbol=symbol, name=name, atomic_number=number, valence=valence))

        existing = {m.formula: m for m in db.query(Molecule).all()}
        added = 0
        for formula, name, atoms, description, safety, uses in MOLECULES:
            vector = embed_text(molecule_text(formula, name, description, safety, uses))
            molecule = existing.get(formula)
            if molecule is None:
                db.add(Molecule(
                    formula=formula, name=name, recipe=recipe_key(atoms),
                    description=description, safety_warnings=safety, industrial_uses=uses,
                    embedding=vector,
                ))
                added += 1
            else:
                molecule.recipe = recipe_key(atoms)
                molecule.embedding = vector
        db.commit()
        if verbose:
            print(f"Seed complete: {added} new molecule(s), {db.query(Molecule).count()} total.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
