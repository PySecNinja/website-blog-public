from pathlib import Path
import uuid
from fastapi import FastAPI, Request, Form, HTTPException, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

import config
from utils.markdown_parser import (
    parse_markdown_file,
    get_all_posts,
    get_all_projects,
    save_markdown_file,
    delete_content_file,
)

app = FastAPI(title=config.SITE_NAME)

app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

templates = Jinja2Templates(directory=config.TEMPLATES_DIR)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with custom templates."""
    if exc.status_code == 404:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "site_name": config.SITE_NAME, "site_author": config.SITE_AUTHOR},
            status_code=404
        )
    if exc.status_code == 500:
        return templates.TemplateResponse(
            "500.html",
            {"request": request, "site_name": config.SITE_NAME, "site_author": config.SITE_AUTHOR},
            status_code=500
        )
    return HTMLResponse(content=str(exc.detail), status_code=exc.status_code)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with 500 template."""
    import traceback
    traceback.print_exc()
    return templates.TemplateResponse(
        "500.html",
        {"request": request, "site_name": config.SITE_NAME, "site_author": config.SITE_AUTHOR},
        status_code=500
    )


def get_base_context(request: Request) -> dict:
    """Get base context for all templates."""
    return {
        "request": request,
        "site_name": config.SITE_NAME,
        "site_description": config.SITE_DESCRIPTION,
        "site_author": config.SITE_AUTHOR,
    }


def is_authenticated(request: Request) -> bool:
    """Check if user is authenticated."""
    return request.session.get("authenticated", False)


def require_auth(request: Request):
    """Dependency to require authentication."""
    if not is_authenticated(request):
        raise HTTPException(status_code=303, headers={"Location": "/admin"})


# Public Routes

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Homepage with recent posts and featured projects."""
    posts = get_all_posts(config.POSTS_DIR)[:5]
    projects = get_all_projects(config.PROJECTS_DIR)[:3]
    context = get_base_context(request)
    context.update({"posts": posts, "projects": projects})
    return templates.TemplateResponse("index.html", context)


@app.get("/blog", response_class=HTMLResponse)
async def blog_list(request: Request, q: str = "", tag: str = "", page: int = 1):
    """List all blog posts with search, tag filter, and pagination."""
    all_posts = get_all_posts(config.POSTS_DIR)

    # Collect all tags for the filter
    all_tags = set()
    for post in all_posts:
        all_tags.update(post.get("tags", []))

    # Filter by search query
    if q:
        q_lower = q.lower()
        all_posts = [
            p for p in all_posts
            if q_lower in p["title"].lower()
            or q_lower in p.get("description", "").lower()
            or q_lower in p.get("raw_content", "").lower()
        ]

    # Filter by tag
    if tag:
        all_posts = [p for p in all_posts if tag in p.get("tags", [])]

    # Pagination
    per_page = config.POSTS_PER_PAGE
    total_posts = len(all_posts)
    total_pages = max(1, (total_posts + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    posts = all_posts[start:start + per_page]

    context = get_base_context(request)
    context.update({
        "posts": posts,
        "search_query": q,
        "current_tag": tag,
        "all_tags": sorted(all_tags),
        "page": page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    })
    return templates.TemplateResponse("blog.html", context)


@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_post(request: Request, slug: str):
    """View a single blog post."""
    post_path = config.POSTS_DIR / f"{slug}.md"
    post = parse_markdown_file(post_path)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    context = get_base_context(request)
    context["post"] = post
    return templates.TemplateResponse("post.html", context)


@app.get("/projects", response_class=HTMLResponse)
async def projects_list(request: Request):
    """List all projects."""
    projects = get_all_projects(config.PROJECTS_DIR)
    context = get_base_context(request)
    context["projects"] = projects
    return templates.TemplateResponse("projects.html", context)


@app.get("/projects/{slug}", response_class=HTMLResponse)
async def project_detail(request: Request, slug: str):
    """View a single project."""
    project_path = config.PROJECTS_DIR / f"{slug}.md"
    project = parse_markdown_file(project_path)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    context = get_base_context(request)
    context["project"] = project
    return templates.TemplateResponse("project.html", context)


@app.get("/resume", response_class=HTMLResponse)
async def resume(request: Request):
    """Display resume."""
    resume_data = parse_markdown_file(config.RESUME_PATH)
    context = get_base_context(request)
    context["resume"] = resume_data
    return templates.TemplateResponse("resume.html", context)


@app.get("/feed.xml")
async def rss_feed(request: Request):
    """Generate RSS feed for blog posts."""
    posts = get_all_posts(config.POSTS_DIR)[:20]
    base_url = str(request.base_url).rstrip("/")

    items = ""
    for post in posts:
        pub_date = post["date"].strftime("%a, %d %b %Y %H:%M:%S +0000")
        description = post.get("description", "")
        items += f"""
        <item>
            <title><![CDATA[{post["title"]}]]></title>
            <link>{base_url}/blog/{post["slug"]}</link>
            <guid>{base_url}/blog/{post["slug"]}</guid>
            <pubDate>{pub_date}</pubDate>
            <description><![CDATA[{description}]]></description>
        </item>"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>{config.SITE_NAME}</title>
        <link>{base_url}</link>
        <description>{config.SITE_DESCRIPTION}</description>
        <language>en-us</language>
        <atom:link href="{base_url}/feed.xml" rel="self" type="application/rss+xml"/>
        {items}
    </channel>
</rss>"""

    return Response(content=rss.strip(), media_type="application/xml")


# Admin Routes

@app.get("/admin", response_class=HTMLResponse)
async def admin_login(request: Request):
    """Admin login page."""
    if is_authenticated(request):
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    context = get_base_context(request)
    context["error"] = request.query_params.get("error")
    return templates.TemplateResponse("admin/login.html", context)


@app.post("/admin/login")
async def admin_login_post(request: Request, password: str = Form(...)):
    """Process admin login."""
    if password == config.ADMIN_PASSWORD:
        request.session["authenticated"] = True
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    return RedirectResponse(url="/admin?error=Invalid+password", status_code=303)


@app.get("/admin/logout")
async def admin_logout(request: Request):
    """Log out of admin."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard."""
    if not is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)
    posts = get_all_posts(config.POSTS_DIR, include_drafts=True)
    projects = get_all_projects(config.PROJECTS_DIR)
    context = get_base_context(request)
    context.update({"posts": posts, "projects": projects})
    return templates.TemplateResponse("admin/dashboard.html", context)


@app.post("/admin/upload-image")
async def admin_upload_image(request: Request, image: UploadFile = File(...)):
    """Upload an image and return its URL."""
    if not is_authenticated(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if image.content_type not in allowed_types:
        return JSONResponse({"error": "Invalid file type"}, status_code=400)

    # Generate unique filename
    ext = image.filename.split(".")[-1] if "." in image.filename else "jpg"
    filename = f"{uuid.uuid4().hex[:12]}.{ext}"

    # Ensure uploads directory exists
    config.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Save file
    file_path = config.UPLOADS_DIR / filename
    content = await image.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Return the URL
    url = f"/static/images/{filename}"
    return JSONResponse({"url": url, "filename": filename})


@app.get("/admin/posts/new", response_class=HTMLResponse)
async def admin_new_post(request: Request):
    """Create new post form."""
    if not is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)
    context = get_base_context(request)
    context["content_type"] = "post"
    context["item"] = None
    return templates.TemplateResponse("admin/editor.html", context)


@app.post("/admin/posts/new")
async def admin_create_post(
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    content: str = Form(...),
    published: str = Form(""),
):
    """Create a new post."""
    if not is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    file_path = config.POSTS_DIR / f"{slug}.md"
    is_published = published == "on"
    save_markdown_file(file_path, title, content, description=description, tags=tag_list, published=is_published)
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@app.get("/admin/posts/{slug}/edit", response_class=HTMLResponse)
async def admin_edit_post(request: Request, slug: str):
    """Edit post form."""
    if not is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)

    post_path = config.POSTS_DIR / f"{slug}.md"
    post = parse_markdown_file(post_path)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    context = get_base_context(request)
    context["content_type"] = "post"
    context["item"] = post
    return templates.TemplateResponse("admin/editor.html", context)


@app.post("/admin/posts/{slug}/edit")
async def admin_update_post(
    request: Request,
    slug: str,
    title: str = Form(...),
    new_slug: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    content: str = Form(...),
    published: str = Form(""),
):
    """Update an existing post."""
    if not is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)

    old_path = config.POSTS_DIR / f"{slug}.md"
    new_path = config.POSTS_DIR / f"{new_slug}.md"

    if old_path != new_path and old_path.exists():
        old_path.unlink()

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    is_published = published == "on"
    save_markdown_file(new_path, title, content, description=description, tags=tag_list, published=is_published)
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@app.post("/admin/posts/{slug}/delete")
async def admin_delete_post(request: Request, slug: str):
    """Delete a post."""
    if not is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)

    file_path = config.POSTS_DIR / f"{slug}.md"
    delete_content_file(file_path)
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@app.get("/admin/projects/new", response_class=HTMLResponse)
async def admin_new_project(request: Request):
    """Create new project form."""
    if not is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)
    context = get_base_context(request)
    context["content_type"] = "project"
    context["item"] = None
    return templates.TemplateResponse("admin/editor.html", context)


@app.post("/admin/projects/new")
async def admin_create_project(
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    github_url: str = Form(""),
    live_url: str = Form(""),
    content: str = Form(...),
):
    """Create a new project."""
    if not is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    file_path = config.PROJECTS_DIR / f"{slug}.md"
    save_markdown_file(
        file_path, title, content,
        description=description,
        tags=tag_list,
        github_url=github_url,
        live_url=live_url
    )
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@app.get("/admin/projects/{slug}/edit", response_class=HTMLResponse)
async def admin_edit_project(request: Request, slug: str):
    """Edit project form."""
    if not is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)

    project_path = config.PROJECTS_DIR / f"{slug}.md"
    project = parse_markdown_file(project_path)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    context = get_base_context(request)
    context["content_type"] = "project"
    context["item"] = project
    return templates.TemplateResponse("admin/editor.html", context)


@app.post("/admin/projects/{slug}/edit")
async def admin_update_project(
    request: Request,
    slug: str,
    title: str = Form(...),
    new_slug: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    github_url: str = Form(""),
    live_url: str = Form(""),
    content: str = Form(...),
):
    """Update an existing project."""
    if not is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)

    old_path = config.PROJECTS_DIR / f"{slug}.md"
    new_path = config.PROJECTS_DIR / f"{new_slug}.md"

    if old_path != new_path and old_path.exists():
        old_path.unlink()

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    save_markdown_file(
        new_path, title, content,
        description=description,
        tags=tag_list,
        github_url=github_url,
        live_url=live_url
    )
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@app.post("/admin/projects/{slug}/delete")
async def admin_delete_project(request: Request, slug: str):
    """Delete a project."""
    if not is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)

    file_path = config.PROJECTS_DIR / f"{slug}.md"
    delete_content_file(file_path)
    return RedirectResponse(url="/admin/dashboard", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
