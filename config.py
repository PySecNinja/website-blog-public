import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Content directories
CONTENT_DIR = BASE_DIR / "content"
POSTS_DIR = CONTENT_DIR / "posts"
PROJECTS_DIR = CONTENT_DIR / "projects"
RESUME_PATH = CONTENT_DIR / "resume.md"

# Static and templates
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
UPLOADS_DIR = STATIC_DIR / "images"

# Site settings
SITE_NAME = "Drew's Portfolio"
SITE_DESCRIPTION = "Tech projects and blog"
SITE_AUTHOR = "Andrew Hendrix"

# Admin settings
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme123")
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")

# Posts per page
POSTS_PER_PAGE = 10
