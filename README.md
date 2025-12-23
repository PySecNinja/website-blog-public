# Portfolio Blog

A lightweight, fast portfolio and blog built with FastAPI. Features markdown content management, an admin panel, and a clean responsive design.

## Features

- **Blog** with search, tag filtering, and pagination
- **Projects** showcase
- **Resume** page
- **Admin panel** for content management
- **Dark mode** with OS preference detection
- **RSS feed** at `/feed.xml`
- **Markdown editor** with live preview
- **Image uploads**
- **Draft posts** support
- **Reading time** estimates
- **Table of contents** auto-generation
- **Custom 404/500** error pages

## Tech Stack

- **Backend:** FastAPI, Python 3.12+
- **Templating:** Jinja2
- **Content:** Markdown with YAML frontmatter
- **Styling:** Vanilla CSS with CSS variables
- **Storage:** File-based (no database required)

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd website-blog

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

The site will be available at `http://localhost:8000`

## Configuration

Edit `config.py` to customize your site:

```python
SITE_NAME = "My Portfolio"
SITE_DESCRIPTION = "Tech projects and blog"
SITE_AUTHOR = "Your Name"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme123")
```

For production, set environment variables:

```bash
export ADMIN_PASSWORD="your-secure-password"
export SECRET_KEY="your-secret-key"
```

## Project Structure

```
website-blog/
├── main.py                 # FastAPI application
├── config.py               # Site configuration
├── requirements.txt        # Python dependencies
├── utils/
│   └── markdown_parser.py  # Markdown processing
├── content/                # Markdown content files
│   ├── posts/              # Blog posts
│   ├── projects/           # Project pages
│   └── resume.md           # Resume content
├── templates/              # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── blog.html
│   ├── post.html
│   ├── projects.html
│   ├── project.html
│   ├── resume.html
│   ├── 404.html
│   ├── 500.html
│   └── admin/
│       ├── login.html
│       ├── dashboard.html
│       └── editor.html
└── static/
    ├── css/
    │   └── style.css
    └── images/             # Uploaded images
```

## Content Format

### Blog Posts

Create markdown files in `content/posts/`:

```markdown
---
title: My First Post
description: A brief description
tags:
  - python
  - web
published: true
date: 2024-01-15
---

Your markdown content here...
```

### Projects

Create markdown files in `content/projects/`:

```markdown
---
title: Project Name
description: What it does
tags:
  - fastapi
  - python
github_url: https://github.com/user/repo
live_url: https://example.com
order: 1
---

Project details in markdown...
```

## Admin Panel

Access the admin panel at `/admin`. Default password is `changeme123` (change this in production!).

From the admin panel you can:
- Create, edit, and delete posts
- Create, edit, and delete projects
- Upload images
- Save posts as drafts

## License

MIT
