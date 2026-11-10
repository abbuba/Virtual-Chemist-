import os

from sqlalchemy import create_engine, text

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv



load_dotenv()



DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/Chemist")



engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()



# Human-friendly read-only views for pgAdmin (no raw ids needed)
VIEWS = [
    "DROP VIEW IF EXISTS v_activity, v_discoveries, v_leaderboard, v_users, v_molecules CASCADE",
    """CREATE VIEW v_users AS
       SELECT u.username, u.email, u.password_hash, u.created_at AS joined,
              (SELECT COUNT(*) FROM discoveries d WHERE d.user_id = u.id) AS molecules_found
       FROM users u ORDER BY u.created_at DESC""",
    """CREATE VIEW v_discoveries AS
       SELECT u.username, u.email, m.formula, m.name AS molecule, m.recipe AS atoms_used, d.discovered_at
       FROM discoveries d
       JOIN users u ON u.id = d.user_id
       JOIN molecules m ON m.id = d.molecule_id
       ORDER BY d.discovered_at DESC""",
    """CREATE VIEW v_leaderboard AS
       SELECT u.username,
              COUNT(d.id) AS molecules_found,
              (SELECT COUNT(*) FROM molecules) AS total_molecules,
              ROUND(100.0 * COUNT(d.id) / NULLIF((SELECT COUNT(*) FROM molecules), 0), 1) AS percent_complete,
              MAX(d.discovered_at) AS last_discovery
       FROM users u LEFT JOIN discoveries d ON d.user_id = u.id
       GROUP BY u.username ORDER BY molecules_found DESC, u.username""",
    """CREATE VIEW v_molecules AS
       SELECT m.formula, m.name, m.recipe AS atoms_needed,
              (SELECT COUNT(*) FROM discoveries d WHERE d.molecule_id = m.id) AS times_discovered,
              m.description, m.safety_warnings, m.industrial_uses
       FROM molecules m ORDER BY m.formula""",
    """CREATE VIEW v_activity AS
       SELECT created_at AS happened_at, username, event AS what_happened
       FROM login_events
       UNION ALL
       SELECT d.discovered_at, u.username, 'discovered ' || m.name || ' (' || m.formula || ')'
       FROM discoveries d JOIN users u ON u.id = d.user_id JOIN molecules m ON m.id = d.molecule_id
       UNION ALL
       SELECT created_at, username, 'account created' FROM users
       ORDER BY happened_at DESC""",
]


def init_db():

    """Creates missing tables and adds columns introduced after the first release."""

    from app.models import models  # noqa: F401  (registers models on Base)

    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:

        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(254)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
        conn.execute(text("ALTER TABLE molecules ADD COLUMN IF NOT EXISTS recipe VARCHAR(60)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_molecules_recipe ON molecules (recipe)"))
        for statement in VIEWS:
            conn.execute(text(statement))



def get_db():

    """Dependency generator that yields db sessions per request lifecycle."""

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()