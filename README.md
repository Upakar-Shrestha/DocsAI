# AI Document API

FastAPI backend for user authentication, PDF uploads, PDF text extraction, chunking, Gemini embeddings, and PostgreSQL similarity search using `pgvector`.

## What the project does

The application follows this high-level flow:

1. A user registers or logs in.
2. The API returns a JWT access token.
3. The client sends that token as a Bearer token to protected endpoints.
4. An authenticated user uploads a PDF with a title.
5. The API validates and saves the PDF under `uploads/`.
6. A `documents` row is created with status `PENDING`.
7. FastAPI schedules background processing after the upload response is sent.
8. The processor extracts text with `pypdf`.
9. The text is split into overlapping chunks.
10. Each chunk is sent to Gemini's `text-embedding-004` model.
11. The embedding is stored in PostgreSQL using the `pgvector` extension.
12. The document is marked `COMPLETED`, or `FAILED` if processing raises an error.
13. `similarity_search()` can rank a user's chunks by cosine distance, although no HTTP route currently exposes this function.

## Project structure

```text
.
├── app/
│   ├── main.py                    # FastAPI application and development server
│   ├── api/
│   │   ├── router.py              # Combines all API routers
│   │   ├── auth.py                # Register and login endpoints
│   │   ├── dependencies.py        # DB session and current-user dependencies
│   │   ├── document.py             # Document upload/list endpoints
│   │   └── user.py                 # Current-user endpoint
│   ├── auth/
│   │   ├── schema.py               # Login, registration, and token schemas
│   │   └── service.py              # Authentication and registration orchestration
│   ├── core/
│   │   ├── config.py               # Environment-backed application settings
│   │   ├── schema.py               # Generic response envelope
│   │   └── security.py             # Password hashing and JWT creation
│   ├── document/
│   │   ├── model.py                # Document, Chunk, status enum, and vector column
│   │   ├── schema.py               # Document request/response schemas
│   │   └── service.py               # Upload, extraction, chunking, embeddings, search
│   ├── external/
│   │   └── embeddings.py            # Gemini embedding integration
│   ├── health/
│   │   └── health.py                # Health-check endpoint
│   ├── infrastructure/
│   │   └── database.py              # Async SQLAlchemy engine, session factory, Base
│   └── user/
│       ├── model.py                # User database model
│       ├── schema.py               # User request/response schemas
│       └── service.py              # User creation and password hashing
├── alembic/
│   ├── env.py                      # Async Alembic configuration
│   └── versions/                   # Database migration history
├── docker-compose.yml              # PostgreSQL with pgvector
├── alembic.ini                    # Alembic script location and logging
├── pyproject.toml                 # Python metadata and dependencies
├── uv.lock                        # Locked dependency versions
└── uploads/                       # Local PDF storage directory
```

The `.venv/`, `.env`, generated Python cache files, and uploaded files are intentionally ignored by Git.

## Technology flow

### Application startup

`app/main.py` creates the FastAPI application using `settings.APP_NAME`, then includes the router assembled by `app/api/router.py`.

The configured routers are:

| Router | Prefix | Endpoints |
| --- | --- | --- |
| Authentication | `/auth` | `POST /auth/register`, `POST /auth/login` |
| Users | `/users` | `GET /users/me` |
| Documents | none | `GET /documents`, `POST /documents` |
| Health | none | `GET /health` |

The `run()` function starts Uvicorn on `127.0.0.1:8000` with reload enabled. In development, the application can therefore be started with the project script or directly through Uvicorn.

### Configuration

`app/core/config.py` loads settings from `.env` using Pydantic Settings. All fields are required:

```env
APP_NAME=AI Document API
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_document_db
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10
GEMINI_API_KEY=replace-with-your-gemini-api-key
```

`.env` is ignored by Git and must be created locally. Do not commit the Gemini key or JWT secret.

### Database setup

`app/infrastructure/database.py` creates:

- An async SQLAlchemy engine using `DATABASE_URL`.
- An `async_sessionmaker` used by request dependencies and background processing.
- The declarative `Base` used by the ORM models.

`app/api/dependencies.py` provides `get_db()`. Each request receives an async session that is closed when the dependency finishes.

The Docker service uses `pgvector/pgvector:pg16`, which provides PostgreSQL 16 and the pgvector extension. The migration `e3a555cb53b1_add_embedding_column_to_chunks.py` also runs:

```sql
CREATE EXTENSION IF NOT EXISTS vector
```

The models use PostgreSQL UUID generation through `gen_random_uuid()`. The database must therefore support that PostgreSQL function as well.

### Migration order

Alembic migrations are applied in dependency order:

1. `92e9e5efb07b_create_documents_table.py` creates the initial documents table.
2. `bca64dbf78cb_create_users_table.py` is an empty historical revision.
3. `8829095ef6e0_create_users_table.py` creates the users table.
4. `f96fc3b6cd15_add_fk_constraint_on_documents_user_id.py` links documents to users.
5. `7db7ca6bd3b7_add_file_path_to_documents.py` adds local file storage paths.
6. `739b5589800a_add_new_table_chunk_and_add_new_column_.py` creates chunks and document statuses.
7. `7f0bf2d8c83c_add_unique_constraint_on_chunk_document_.py` prevents duplicate chunk indexes per document.
8. `e3a555cb53b1_add_embedding_column_to_chunks.py` enables pgvector and adds a nullable 768-dimensional embedding column.

The application does not run migrations automatically at startup. Run them explicitly before using the API.

## Authentication flow

### Registration

`POST /auth/register` accepts an email and password. The flow is:

1. `RegisterRequest` validates the request.
2. `auth/service.py` checks whether the email already exists.
3. `user/service.py` hashes the password with bcrypt.
4. The user is inserted into `users`.
5. A JWT containing the user's UUID in the `sub` claim is returned.

### Login

`POST /auth/login`:

1. Looks up the user by email.
2. Verifies the submitted password against the bcrypt hash.
3. Creates a JWT with an expiration time from `ACCESS_TOKEN_EXPIRE_MINUTES`.
4. Returns the token in a `ResponseEnvelope`.

### Protected endpoints

`get_current_user()` reads the `Authorization: Bearer <token>` header, decodes the JWT with `SECRET_KEY` and `ALGORITHM`, obtains the UUID from `sub`, and loads the matching user from PostgreSQL.

Invalid, expired, or userless tokens return HTTP 401. The authenticated user is then passed to protected route handlers.

## Document upload flow

The upload endpoint is:

```text
POST /documents
Content-Type: multipart/form-data
Authorization: Bearer <access-token>
```

Required form fields:

- `title`: document title.
- `file`: PDF file.

The route in `app/api/document.py` performs these steps:

1. Generates a UUID for the document.
2. Calls `save_uploaded_file()`.
3. Validates the MIME type as `application/pdf`.
4. Validates the file extension as `.pdf`.
5. Reads the file and enforces `MAX_UPLOAD_SIZE_MB`.
6. Saves it as `<document-id>.pdf` under `UPLOAD_DIR`.
7. Inserts a document row with status `PENDING`.
8. Adds `process_document(document_id)` to FastAPI's background task list.
9. Returns the document response.

The file name is generated from the UUID rather than the client-provided name, which avoids using an untrusted filename on disk.

## Background document processing

`process_document()` opens its own database session because the request session should not be reused after the upload request completes.

The processing sequence is:

1. Load the document by UUID.
2. Change its status to `PROCESSING` and commit.
3. Read the PDF with `PdfReader`.
4. Join extracted page text into one string.
5. Split the text into 1,000-character chunks with a 200-character overlap.
6. Call `get_embedding()` for each chunk.
7. Run the synchronous Gemini SDK call through `asyncio.to_thread()` so the blocking network request does not occupy the event-loop thread.
8. Add each chunk and its 768-value embedding to `chunks`.
9. Store the full extracted text on the document.
10. Change the document status to `COMPLETED` and commit.

If extraction, embedding, or database persistence fails, the exception handler changes the status to `FAILED`, commits that status, and re-raises the error.

## Gemini embedding flow

`app/external/embeddings.py` configures the legacy `google-generativeai` SDK with `GEMINI_API_KEY` and calls:

```text
models/text-embedding-004
```

The returned embedding is stored in `Chunk.embedding`, which is declared as `Vector(768)`. The model's vector size and the database column size must remain consistent.

The current integration embeds chunks one at a time. It is synchronous at the SDK boundary, so `document/service.py` uses `await asyncio.to_thread(...)` around each call.

## Similarity search flow

`similarity_search()` in `app/document/service.py` accepts:

- An async SQLAlchemy session.
- A query embedding.
- A user UUID.
- A maximum result count, defaulting to five.

It joins `chunks` to `documents`, filters by the owning user, orders by `Chunk.embedding.cosine_distance(query_embedding)`, and returns the nearest chunks.

This is an internal service function at present. There is currently no API endpoint that:

1. Accepts a natural-language search query.
2. Generates an embedding for that query.
3. Calls `similarity_search()`.
4. Returns matching chunks or document context.

That endpoint would be the next layer needed for a complete user-facing semantic search/RAG flow.

## API reference

### `GET /health`

Returns:

```json
{"status": "ok"}
```

This endpoint does not check database connectivity or Gemini availability.

### `POST /auth/register`

Example JSON body:

```json
{
  "email": "user@example.com",
  "password": "strong-password"
}
```

Returns a bearer token wrapped in the standard response envelope.

### `POST /auth/login`

Accepts the same email/password shape as registration and returns a bearer token.

### `GET /users/me`

Requires a bearer token and returns the authenticated user's UUID, email, and creation timestamp.

### `GET /documents`

Requires a bearer token and returns only documents belonging to the authenticated user.

### `POST /documents`

Requires a bearer token and a multipart PDF upload. The response is returned after the file and initial document row are created; PDF extraction and embedding continue as a background task.

## Local setup

### Prerequisites

- Python 3.12 or newer.
- Docker Desktop.
- `uv` installed and available on `PATH`.
- A Gemini API key.

### 1. Create the environment file

Create `.env` in the repository root using the configuration shown above. Use the async PostgreSQL URL:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_document_db
```

### 2. Start PostgreSQL with pgvector

```powershell
docker compose up -d
```

### 3. Install locked dependencies

```powershell
uv sync
```

### 4. Apply database migrations

```powershell
uv run alembic upgrade head
```

### 5. Start the API

```powershell
uv run ai-document
```

The API is available at `http://127.0.0.1:8000`. FastAPI's interactive documentation is available at:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

### 6. Optional database check

```powershell
uv run python -m app.check_db
```

This prints the current database/schema and the tables visible in the `public` schema.

## Example request sequence

Register:

```powershell
curl.exe -X POST http://127.0.0.1:8000/auth/register `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"user@example.com\",\"password\":\"strong-password\"}"
```

Use the returned token to upload a PDF:

```powershell
curl.exe -X POST http://127.0.0.1:8000/documents `
  -H "Authorization: Bearer <access-token>" `
  -F "title=Example document" `
  -F "file=@C:\path\to\document.pdf"
```

Immediately after the upload, the document may still be `PENDING` or `PROCESSING`. Poll `GET /documents` until the status becomes `COMPLETED` or `FAILED`.

## Important operational behavior

- FastAPI background tasks run in the API process. They are not a durable job queue. A process restart can interrupt document processing.
- A document is persisted before its PDF is processed, so clients should rely on the document status rather than assuming processing is complete when the upload response arrives.
- Embedding requests are made once per chunk and currently run sequentially.
- PDF files are stored on the local filesystem. Deployments with multiple API instances need shared storage or an object-storage layer.
- The current health endpoint only reports that the HTTP application is responding.
- Similarity search is implemented in the service layer but is not currently available through an HTTP route.
- The project currently uses Google's legacy `google-generativeai` package. Google's newer `google-genai` SDK is the recommended long-term migration target, but changing SDKs requires updating the embedding adapter and response handling.