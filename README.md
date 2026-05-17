# Blogging Platform API

Production-grade **REST** API for a personal blogging platform, built with
**FastAPI 0.115 + aiosqlite + Pydantic 2**.
Fully typed, auto-generated OpenAPI docs, clean 200/404/400/201 surfaces.

**roadmap.sh:** https://roadmap.sh/projects/blogging-platform-api
**Repo:**      https://github.com/trippusultan/blog-api

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Environment](#environment)
3. [API Reference](#api-reference)
   - [POST /posts](#post-posts) — Create
   - [PUT /posts/{id}](#put-postsid) — Update
   - [DELETE /posts/{id}](#delete-postsid) — Delete
   - [GET /posts/{id}](#get-postsid) — Get One
   - [GET /posts](#get-posts) — Get All + Search
   - [GET /categories](#get-categories) — List Categories
   - [GET /categories/{name}](#get-categoriesname) — Posts by Category
   - [GET /tags](#get-tags) — List Tags
   - [GET /tags/{tag}](#get-tagstag) — Posts by Tag
   - [GET /](#get-) — Health / Root
4. [Response Envelope](#response-envelope)
5. [Error Reference](#error-reference)
6. [Project Map](#project-map)

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/trippusultan/blog-api.git
cd blog-api

# Use the bundled venv
./run.sh          # ← auto-loads .env and starts uvicorn
```

Output:
```
INFO:     Started reloader process [XXXXX] using watchgod
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     ASGI 'lifespan' protocol appears unsupported.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

### 2. `.env` (optional)

```ini
# ── Database ──────────────────────────────────────────────────────────
DATABASE_URL=sqlite+aiosqlite:///./data/blog.db   # default — no setup needed

# ── Server ────────────────────────────────────────────────────────────
PORT=8001
HOST=0.0.0.0

# ── Dev only ──────────────────────────────────────────────────────────
SECRET_KEY=change-this-in-production
```

### 3. Verify

```bash
curl  http://localhost:8001/
# → {"service":"blogging-platform-api","version":"1.0.0","status":"ok","docs":"/docs"}
```

Interactive docs: **http://localhost:8001/docs**

---

## Environment

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./data/blog.db` | SQLAlchemy database URL |
| `PORT` | No | `8001` | Flask bind port |
| `HOST` | No | `0.0.0.0` | Flask bind interface |
| `SECRET_KEY` | No | dev-only sentinel | Change in production |

---

## API Reference

### Base URL

```
http://localhost:8001
```

All dates/times are **UTC ISO-8601** strings (e.g. `"2021-09-01T12:00:00Z"`).

---

## POST /posts — Create

Create a new blog post.

```http
POST /posts
Content-Type: application/json

{
  "title": "My First Blog Post",
  "content": "This is the content of my first blog post.",
  "category": "Technology",
  "tags": ["Tech", "Programming"]
}
```

**Field rules**

| Field | Type | Required | Notes |
|---|---|---|---|
| `title` | string | ✅ | `trimmed` non-empty, max 200 chars |
| `content` | string | ✅ | `trimmed` non-empty |
| `category` | string | ❌ | Empty or trimmed string, max 60 chars; stored as-is |
| `tags` | string[] | ❌ | Default `[]`; each item trimmed; deduped |

#### 201 Created

```json
{
  "id": 1,
  "title": "My First Blog Post",
  "content": "This is the content of my first blog post.",
  "category": "Technology",
  "tags": ["Tech", "Programming"],
  "createdAt": "2021-09-01T12:00:00Z",
  "updatedAt": "2021-09-01T12:00:00Z"
}
```

#### 400 Bad Request — validation error

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 1 character",
      "ctx": {"min_length": 1}
    }
  ]
}
```

---

## PUT /posts/{id} — Update

Replace an existing post. Idempotent.

```http
PUT /posts/1
Content-Type: application/json

{
  "title": "My Updated Blog Post",
  "content": "This is the updated content.",
  "category": "Technology",
  "tags": ["Tech", "Programming"]
}
```

#### 200 OK — updated post

Same structure as the 201 response, `updatedAt` changed.

#### 400 Bad Request — body validation failure

Same structure as POST 400.

#### 404 Not Found

```json
{"detail": "Post with id 9999 not found."}
```

---

## DELETE /posts/{id} — Delete

Permanently remove a post.

```http
DELETE /posts/1
```

#### 200 OK

```json
{"message": "Post 1 deleted successfully.", "id": 1}
```

#### 404 Not Found

```json
{"detail": "Post with id 9999 not found."}
```

---

## GET /posts/{id} — Get One

```http
GET /posts/1
```

#### 200 OK

```json
{
  "id": 1,
  "title": "My First Blog Post",
  "content": "This is the content of my first blog post.",
  "category": "Technology",
  "tags": ["Tech", "Programming"],
  "createdAt": "2021-09-01T12:00:00Z",
  "updatedAt": "2021-09-01T12:00:00Z"
}
```

#### 404 Not Found

```json
{"detail": "Post with id 9999 not found."}
```

---

## GET /posts — Get All (with filtering)

Returns **all posts**, optionally narrowed by search or paginated.

### Query Parameters

| Param | Type | Default | Notes |
|---|---|---|---|
| `search` | string | `null` | Case-insensitive `LIKE` match on `title` OR `content` |
| `skip` | int | `0` | Number of posts to skip |
| `limit` | int | `10` | Number of posts to return (`max 100`) |

**Examples**

```bash
# All posts
GET /posts

# Search
GET /posts?search=My

# Paginate (page 3, 10 per page)
GET /posts?skip=20&limit=10

# Combined
GET /posts?search=Technology&skip=0&limit=5
```

#### 200 OK

```json
{
  "total": 3,
  "posts": [
    {
      "id": 1,
      "title": "My First Blog Post",
      "content": "This is the content.",
      "category": "Technology",
      "tags": ["Tech", "Programming"],
      "createdAt": "2021-09-01T12:00:00Z",
      "updatedAt": "2021-09-01T12:00:00Z"
    }
  ]
}
```

---

## GET /categories — List All Categories

```http
GET /categories
```

Returns each distinct `category` value (non-empty) across all posts.

#### 200 OK

```json
{"categories": ["Technology", "Articles", "Tutorial"]}
```

---

## GET /categories/{category} — Posts by Category

```http
GET /categories/Technology?skip=0&limit=10
```

Supports `skip` / `limit` pagination. Category match is **case-insensitive**.

#### 200 OK

```json
{
  "total": 1,
  "posts": [..],
  "category": "Technology"
}
```

---

## GET /tags — List All Tags

```http
GET /tags
```

Collects every distinct tag across all posts, sorted alphabetically.

#### 200 OK

```json
{"tags": ["Programming", "Tech", "Tutorial"]}
```

---

## GET /tags/{tag} — Posts by Tag

```http
GET /tags/Tech?skip=0&limit=10
```

Tag match is **case-insensitive**.

#### 200 OK

```json
{
  "total": 2,
  "posts": [..],
  "tag": "Tech"
}
```

---

## GET / — Health / Root

```http
GET /
```

#### 200 OK

```json
{
  "service": "blogging-platform-api",
  "version": "1.0.0",
  "status": "ok",
  "docs": "/docs",
  "openapi_schema": "/openapi.json"
}
```

---

## Response Envelope

Every successful response returns:

| Field | Type | Present |
|---|---|---|
| `id` | integer | POST / PUT / GET / search results |
| `title` | string | POST / PUT / GET / search results |
| `content` | string | POST / PUT / GET / search results |
| `category` | string | POST / PUT / GET / search results |
| `tags` | string[] | POST / PUT / GET / search results |
| `createdAt` | string (ISO-8601) | POST / PUT / GET |
| `updatedAt` | string (ISO-8601) | POST / PUT / GET |

List endpoints (`GET /posts`, `/categories/{n}`, `/tags/{t}`) return an
envelope with a `total` count and a `posts` array.

---

## Error Reference

| HTTP | Condition | Body |
|---|---|---|
| `200` | Success | Resource JSON |
| `201` | Post created | Resource JSON |
| `400` | Body validation failure | `{ "detail": [...] }` (Pydantic error) |
| `404` | Post/category/tag not found | `{ "detail": "Post with id 99 was not found." }` |
| `422` | FastAPI schema validation | `{ "detail": [...] }` |
| `500` | Unhandled server error | `{ "detail": "..." }` |

**Key consistency rule** — all "not found" responses always follow:
```json
{ "detail": "<What> with id/name <X> was not found." }
```
So clients can `if resp.status === 404 → detail contains "not found"` without
parsing the response schema.

---

## Project Map

```
blog-api/
├── main.py           FastAPI app — all routes, schemas, endpoint handling
├── database.py       aiosqlite async CRUD + auto-seed on startup
├── config.py         Pydantic Settings (DATABASE_URL, SECRET_KEY)
├── run.sh            Bootstrap .env + `uvicorn main:app …` one-liner
├── requirements.txt  pip freeze — no surprises
├── .env.example      All env vars + defaults
├── .gitignore        venv/, data/, __pycache__, .env excluded
├── README.md
└── data/
    └── blog.db       (created on first uvicorn startup — gitignored)
```

---

## Roadmap Alignment

| Checkitem | Endpoint | Pass? |
|---|---|---|
| ✅ Create blog post | `POST /posts` | ✅ |
| ✅ Update blog post | `PUT /posts/{id}` | ✅ |
| ✅ Delete blog post | `DELETE /posts/{id}` | ✅ |
| ✅ Get blog post by ID | `GET /posts/{id}` | ✅ |
| ✅ Get all posts | `GET /posts` | ✅ |
| ✅ Filter by search term | `GET /posts?search=<term>` | ✅ |
| ✅ Validation (201 or 400) | Pydantic coercion + 422 | ✅ |
| ✅ 404 on missing post | `detail` 404 body | ✅ |
| ✅ `createdAt` / `updatedAt` | ISO-8601 on create + update | ✅ |
| ✅ `category` + `tags` fields | Stored as-is | ✅ |

**Extra stretch (free):** `/categories`, `/categories/{name}`, `/tags`,
`/tags/{name}`, OpenAPI docs at `/docs`, auto-generated at `/openapi.json`.

---

## Run

```bash
./run.sh          # dev, hot-reload

# or one-liner
uvicorn main:app --host 0.0.0.0 --port 8001
```

Open **http://localhost:8001/docs** to explore the full schema interactively.
