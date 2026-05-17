# ── Blogging Platform API — FastAPI ──────────────────────────────────
from fastapi import FastAPI, Query, Path, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
import json, time

import database

app = FastAPI(
    title="Blogging Platform API",
    description="RESTful API for a personal blogging platform with SQLite backend. "
                "Supports CRUD on posts, search/filter, categories, and tags.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# ── lifespan: init DB on startup ─────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    await database.init_db()


# ── helpers ─────────────────────────────────────────────────────────

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def row_to_post(row: dict) -> dict:
    tags = json.loads(row.get("tags") or "[]")
    return {
        "id":        row["id"],
        "title":     row["title"],
        "content":   row["content"],
        "category":  row.get("category") or "",
        "tags":      tags,
        "createdAt": row.get("created_at", ""),
        "updatedAt": row.get("updated_at", ""),
    }


# ── schemas ─────────────────────────────────────────────────────────

class PostIn(BaseModel):
    title:    str = Field(..., min_length=1, max_length=200)
    content:  str = Field(..., min_length=1)
    category: Optional[str] = Field("", max_length=60)
    tags:     Optional[list[str]] = Field(default_factory=list)


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    category: str = ""
    tags: list[str] = []
    createdAt: str
    updatedAt: str


class ListResp(BaseModel):
    total: int
    posts: list[PostOut]


# ── CREATE ──────────────────────────────────────────────────────────

@app.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED,
          summary="Create a new blog post",
          responses={400: {"description": "Validation error"}})
async def create_post(post: PostIn):
    if not post.title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"errors": {"title": "must not be empty"}})
    if not post.content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"errors": {"content": "must not be empty"}})

    now = now_iso()
    tags_json = json.dumps(post.tags or [])
    last_id = await database.execute(
        "INSERT INTO posts (title, content, category, tags, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?)",
        (post.title.strip(),
         post.content.strip(),
         post.category.strip(),
         tags_json, now, now))
    row = await database.fetchone(
        "SELECT * FROM posts WHERE id = ?", (last_id,))
    if row is None:
        raise HTTPException(status_code=500, detail="Failed to read back created post")
    return row_to_post(row)


# ── GET single ──────────────────────────────────────────────────────

@app.get("/posts/{post_id}", response_model=PostOut,
         summary="Get a single blog post by ID",
         responses={404: {"description": "Post not found"}})
async def get_post(
    post_id: int = Path(..., ge=1, description="ID of the blog post")
):
    row = await database.fetchone(
        "SELECT * FROM posts WHERE id = ?", (post_id,))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id {post_id} not found.")
    return row_to_post(row)


# ── GET all (with search) ────────────────────────────────────────────

@app.get("/posts", response_model=ListResp,
         summary="Get all blog posts (optionally filtered by search term)",
         responses={400: {"description": "Bad request"}})
async def get_posts(
    search: Optional[str] = Query(
        None,
        description="Filter posts whose title or content contains this term (case-insensitive)"),
    skip: int = Query(0, ge=0, description="Number of posts to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of posts to return"),
):
    all_rows = await database.fetchall("SELECT * FROM posts", params=())

    if search:
        q = search.lower().strip()
        all_rows = [
            r for r in all_rows
            if q in r["title"].lower()
               or q in r["content"].lower()
        ]

    total = len(all_rows)
    sliced = all_rows[skip : skip + limit]
    posts = [row_to_post(r) for r in sliced]
    return {"total": total, "posts": posts}


# ── UPDATE ──────────────────────────────────────────────────────────

@app.put("/posts/{post_id}", response_model=PostOut,
         summary="Update an existing blog post",
         responses={
             400: {"description": "Validation error"},
             404: {"description": "Post not found"},
         })
async def update_post(
    post_id: int = Path(..., ge=1, description="ID of the blog post to update"),
    post: PostIn = ...,
):
    existing = await database.fetchone(
        "SELECT * FROM posts WHERE id = ?", (post_id,))
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id {post_id} not found.")

    if not post.title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"errors": {"title": "must not be empty"}})
    if not post.content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"errors": {"content": "must not be empty"}})

    now = now_iso()
    tags_json = json.dumps(post.tags or [])
    await database.execute(
        "UPDATE posts SET title=?, content=?, category=?, tags=?, updated_at=? WHERE id=?",
        (
            post.title.strip(),
            post.content.strip(),
            post.category.strip() if post.category else "",
            tags_json, now, post_id,
        ))
    row = await database.fetchone(
        "SELECT * FROM posts WHERE id = ?", (post_id,))
    return row_to_post(row)


# ── DELETE ──────────────────────────────────────────────────────────

@app.delete("/posts/{post_id}",
            summary="Delete a blog post",
            responses={
                200:  {"description": "Post deleted"},
                404:  {"description": "Post not found"},
            })
async def delete_post(
    post_id: int = Path(..., ge=1, description="ID of the blog post to delete")
):
    existing = await database.fetchone(
        "SELECT * FROM posts WHERE id = ?", (post_id,))
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id {post_id} not found.")
    await database.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    return {"message": f"Post {post_id} deleted successfully.", "id": post_id}


# ── CATEGORIES ─────────────────────────────────────────────────────

@app.get("/categories", summary="List all distinct categories")
async def list_categories():
    rows = await database.fetchall(
        "SELECT DISTINCT category FROM posts WHERE category IS NOT NULL AND category != ''",
        params=())
    return {"categories": [r["category"] for r in rows if r["category"]]}


@app.get("/categories/{category}", summary="List posts in a specific category")
async def posts_by_category(
    category: str = Path(..., description="Category name (case-insensitive)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    rows = await database.fetchall(
        "SELECT * FROM posts WHERE LOWER(category) = LOWER(?)",
        (category,))
    total = len(rows)
    sliced = rows[skip: skip + limit]
    return {"total": total,
            "posts": [row_to_post(r) for r in sliced],
            "category": category}


# ── TAGS ────────────────────────────────────────────────────────────

@app.get("/tags", summary="List all distinct tags across all posts")
async def list_tags():
    rows = await database.fetchall("SELECT tags FROM posts", params=())
    seen: set = set()
    for r in rows:
        for t in json.loads(r.get("tags") or "[]"):
            if t.strip():
                seen.add(t.strip())
    return {"tags": sorted(seen)}


@app.get("/tags/{tag}", summary="List posts that contain a specific tag")
async def posts_by_tag(
    tag: str = Path(..., description="Tag name (case-insensitive)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    rows = await database.fetchall("SELECT * FROM posts", params=())
    matched = []
    for r in rows:
        tags = [t.lower() for t in json.loads(r.get("tags") or "[]")]
        if tag.lower() in tags:
            matched.append(r)
    total = len(matched)
    sliced = matched[skip: skip + limit]
    return {"total": total,
            "posts": [row_to_post(r) for r in sliced],
            "tag": tag}


# ── ROOT ────────────────────────────────────────────────────────────

@app.get("/", summary="API health / root", tags=["meta"])
async def root():
    return {
        "service":        "blogging-platform-api",
        "version":        "1.0.0",
        "status":         "ok",
        "docs":           "/docs",
        "openapi_schema": "/openapi.json",
    }
