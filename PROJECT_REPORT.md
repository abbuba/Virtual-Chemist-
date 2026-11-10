# The Virtual Chemist: Project Report

## 1. Abstract
The Virtual Chemist is a web game where players combine atoms (H, O, C, N, Cl, Na, S, Si) into molecules using a mouse, touch, or webcam hand tracking. The server checks whether the combination is a real compound, and if so saves the discovery to the player's profile. Players log in with a password plus a one-time code (OTP) sent by email. A chat tab lets players search molecules in plain English using AI embeddings.

## 2. Objectives
- Show a full DBMS-backed application: relational schema, constraints, views, and vector search.
- Secure authentication: password, email OTP, sessions.
- An engaging interface: minimal neo-brutalist design, hand tracking, animated bot.

## 3. Technology Stack
| Layer | Technology | Purpose |
|---|---|---|
| Frontend | HTML, CSS, vanilla JavaScript, Canvas | Single-page UI, atom physics, rendering |
| Hand tracking | MediaPipe Hands (in browser) | 21 hand landmarks from webcam |
| Backend | Python 3.12, FastAPI, Uvicorn | REST API and static file serving |
| ORM | SQLAlchemy 2.0 | Python classes mapped to tables |
| Database | PostgreSQL 18 + pgvector | Relational data and vector similarity |
| Cache/session store | Redis | OTPs, sessions, login lockout |
| AI | sentence-transformers (all-MiniLM-L6-v2) | 384-dimension text embeddings |
| Email | SMTP (Gmail, App Password) | Deliver OTP codes |
| Validation | Pydantic | Request/response schemas |
| Config | python-dotenv, `.env` | Secrets and settings |

## 4. Architecture
```
Browser (index.html)
  |  HTTP + JSON, Authorization: Bearer <token>
FastAPI (routers -> services -> repositories)
  |-- PostgreSQL (users, atoms, molecules, discoveries, login_events, views)
  |-- Redis (otp:*, session:*, loginfail:*)
  |-- SMTP (OTP email)
  |-- Embedding model (in-process)
```
Layers:
- **Routers** (`app/routers`) receive HTTP requests and return responses.
- **Services** (`app/services`) hold the business logic (auth, chemistry, email, embeddings).
- **Repositories** (`app/repositories`) hold database queries.
- **Models** (`app/models`) define the tables.

## 5. Database Design
Tables:
- `users`: id, username, email, password_hash, created_at.
- `atoms`: id, symbol, name, atomic_number, valence.
- `molecules`: id, formula, name, description, safety_warnings, recipe, embedding (vector(384)).
- `discoveries`: id, user_id, molecule_id, discovered_at (unique per user and molecule).
- `login_events`: user activity log.

Views (for pgAdmin, no raw ids): `v_users`, `v_discoveries`, `v_leaderboard`, `v_molecules`, `v_activity`.

Key concepts: primary keys, foreign keys, unique constraints, many-to-many (users and molecules via discoveries), indexes, views, and an idempotent seed (re-running never duplicates data).

## 6. Features
1. **Registration and login**: username or email, plus a password.
2. **Email OTP** (second factor).
3. **Lab**: drag atoms; when they are close they link, and releasing sends the cluster (up to 6 atoms) to `/api/chemist/combine`.
4. **Recipe engine**: each molecule has a recipe such as `H-H-O`. The server tries the largest subset of the nearby atoms that matches a recipe. There are 23 molecules.
5. **Profile**: the user's discoveries and progress.
6. **Chat tab**: the "Beaker" bot answers questions via semantic search and dances on success.
7. **Hint line**: suggestions that update under the lab canvas.
8. **Hand mode**: webcam pinch to grab, calibration, fist to clear, larger atoms, help window.
9. **Result popup** that auto-hides after 4 seconds.

## 7. API Endpoints
| Method | Path | Description |
|---|---|---|
| POST | /api/auth/register | Create account |
| POST | /api/auth/login | Check password, send OTP |
| POST | /api/auth/verify-otp | Check OTP, return session token |
| GET | /api/auth/me | Current user |
| POST | /api/auth/logout | End session |
| POST | /api/chemist/combine | Evaluate atoms, save discovery |
| GET | /api/chemist/profile | Player's discoveries |
| GET | /api/chemist/search?q= | Semantic molecule search |
| GET | /api/chemist/hint | Next suggestion |

(Check `app/routers` for the exact URL prefixes.)

## 8. Security
- Passwords are hashed with scrypt, never stored in plain text.
- OTPs are stored hashed in Redis, expire in 300 seconds, allow 5 attempts, and are single-use.
- Session tokens are random, stored as `sha256(token)` in Redis with a 24-hour expiry.
- Login lockout after repeated failures.
- Secrets live in `.env`, which must never be committed.
- SQL injection is avoided by using the ORM's parameterized queries.

## 9. Testing Done
- Service-level tests of combination logic, auth/OTP flow (with fakeredis), and search.
- `node --check` on the frontend script.
- Not tested yet: hand mode on a real webcam, and automated browser tests.

## 10. Limitations and Future Work
- Sessions are opaque tokens, not JWT (a possible switch).
- Some semantic searches are weak (for example "what keeps rockets flying"); more molecule descriptions would help.
- Hand-mode thresholds need real-world tuning; an open-palm swipe is not built.
- No automated test suite or CI yet.

## 11. Conclusion
The project joins a relational database, a vector database, a cache, email, AI embeddings, and browser-side computer vision into one working application.

---

# Appendix A: Concepts Explained

- **FastAPI**: Python framework for building web APIs. It auto-validates input and generates docs at `/docs`.
- **Uvicorn**: the server program that runs FastAPI.
- **REST API / JSON**: the browser calls URLs and exchanges data as JSON.
- **SQLAlchemy (ORM)**: lets you write Python classes instead of SQL; it turns them into tables and queries.
- **PostgreSQL**: the main relational database.
- **pgvector**: a PostgreSQL extension that stores vectors (lists of numbers) and finds the nearest ones.
- **Embedding**: text turned into 384 numbers where similar meanings are close together. `all-MiniLM-L6-v2` does this.
- **RAG (retrieval)**: find the most relevant stored records first (retrieval), then build the answer from them. Here, the molecule database is the knowledge source, searched by cosine similarity.
- **Cosine similarity**: measures the angle between two vectors; a smaller angle means more similar meaning.
- **Redis**: a very fast in-memory store with automatic expiry (TTL), ideal for OTPs and sessions.
- **OTP**: a one-time password. It proves you can read the email account too.
- **Hashing (sha256, scrypt)**: one-way scrambling. scrypt is deliberately slow, which protects passwords.
- **Session token vs JWT**: our token is a random string, and the server looks it up in Redis (stateful, and easy to revoke). A JWT is a signed token containing the user data, which the server verifies without a lookup.
- **Bearer token**: sent in the `Authorization: Bearer ...` header on every request.
- **SMTP / App Password**: the protocol for sending email. Gmail needs a special App Password, not your real password.
- **Pydantic**: validates the shape of data in requests.
- **Views**: saved SQL queries that look like tables.
- **Idempotent seed**: safe to run repeatedly.
- **MediaPipe Hands**: Google's model that finds 21 points on a hand in each webcam frame, running in the browser.
- **Pinch detection**: distance between thumb tip and index tip divided by hand size, so it works at any distance from the camera. Calibration learns your personal thresholds.
- **One Euro filter**: smooths jittery tracking. It smooths heavily when moving slowly and lightly when moving fast, so there is no lag.
- **Canvas**: the HTML element used to draw atoms.
- **`.env`**: a file of settings and secrets read at startup.

---

# Appendix B: Run Locally

Prerequisites: Python 3.12, PostgreSQL 18 with pgvector, Redis (or Memurai/Docker on Windows).

```powershell
cd C:\Users\abbub\OneDrive\Desktop\DBMS_Project\virtual-chemist
..\venv\Scripts\activate
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cpu   # if not installed
# make sure Postgres and Redis are running
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000. Tables, views and seed data are created on startup.

`.env` keys: `DATABASE_URL`, `REDIS_URL`, `OTP_DEV_MODE`, `SMTP_USER`, `SMTP_PASS`, `SMTP_SERVER`, `SMTP_PORT`.

# Appendix C: Deploy

Recommended simple path: **Docker Compose on a VPS**, or a platform such as Render/Railway.

1. **Managed services**: PostgreSQL with pgvector (Supabase, Neon or Railway all support it) and Redis (Upstash or Render Redis). Run `CREATE EXTENSION IF NOT EXISTS vector;`.
2. **Dockerfile**:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
3. **Environment variables**: set the `.env` values in the platform dashboard, not in the image. Set `OTP_DEV_MODE` to false.
4. **HTTPS is required**: browsers only allow the webcam on HTTPS (or localhost). Platforms provide this automatically. On a VPS, put Nginx or Caddy in front with a Let's Encrypt certificate.
5. **Run in production**: no `--reload`; use `uvicorn ... --workers 2` or gunicorn with uvicorn workers.
6. **Checklist**: rotate the Gmail App Password, keep `.env` out of git, enable database backups, and allow enough RAM (~1 GB) for the embedding model.


---

# Tomorrow: Start the Project Again

Everything was closed, so follow these steps in order.

1. **Start PostgreSQL.** Press Win+R, type `services.msc`, find `postgresql-x64-18`, and start it if it isn't running. It usually starts by itself.
2. **Start Redis.** Redis must be running (Memurai, Docker, or WSL). Without it, login with OTP will fail. With Docker: `docker run -d -p 6379:6379 redis`.
3. **Open a terminal in the project folder:**
   ```powershell
   cd C:\Users\abbub\OneDrive\Desktop\DBMS_Project\virtual-chemist
   ```
4. **Activate the virtual environment:**
   ```powershell
   ..\venv\Scripts\activate
   ```
5. **Start the server:**
   ```powershell
   uvicorn app.main:app --reload
   ```
6. **Open the app** at http://127.0.0.1:8000 and press Ctrl+F5 once so the browser loads the latest page.
7. **Stop it** with Ctrl+C in the terminal.

Notes:
- The first start takes a few seconds because the AI model loads.
- Tables, views and the 23 molecules are created or updated automatically on startup.
- If the server won't start, check that `.env` exists and that Postgres and Redis are running.
- Hand mode needs a webcam, and the camera permission must be allowed in the browser.