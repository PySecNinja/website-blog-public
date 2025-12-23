from pathlib import Path
from typing import Optional
from datetime import datetime, date
import re
import frontmatter
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension


def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Calculate estimated reading time in minutes."""
    words = len(re.findall(r'\w+', text))
    minutes = max(1, round(words / words_per_minute))
    return minutes


def generate_toc(html_content: str) -> tuple[list[dict], str]:
    """Extract headings from HTML and generate table of contents.

    Returns a tuple of (toc_list, modified_html_with_ids).
    """
    toc = []
    heading_pattern = re.compile(r'<(h[23])>(.*?)</\1>', re.IGNORECASE)

    def make_id(text: str) -> str:
        # Remove HTML tags, lowercase, replace spaces with hyphens
        clean = re.sub(r'<[^>]+>', '', text)
        slug = re.sub(r'[^\w\s-]', '', clean.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        return slug

    def replace_heading(match):
        tag = match.group(1).lower()
        text = match.group(2)
        heading_id = make_id(text)
        level = int(tag[1])
        toc.append({"id": heading_id, "text": re.sub(r'<[^>]+>', '', text), "level": level})
        return f'<{tag} id="{heading_id}">{text}</{tag}>'

    modified_html = heading_pattern.sub(replace_heading, html_content)
    return toc, modified_html


def parse_markdown_file(file_path: Path) -> Optional[dict]:
    """Parse a markdown file with frontmatter and return structured data."""
    if not file_path.exists():
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        post = frontmatter.load(f)

    md = markdown.Markdown(
        extensions=[
            CodeHiliteExtension(css_class="highlight", linenums=False),
            FencedCodeExtension(),
            TableExtension(),
            "nl2br",
        ]
    )

    html_content = md.convert(post.content)

    # Generate table of contents and add IDs to headings
    toc, html_with_ids = generate_toc(html_content)

    metadata = dict(post.metadata)
    metadata["content"] = html_with_ids
    metadata["raw_content"] = post.content
    metadata["slug"] = file_path.stem
    metadata["reading_time"] = calculate_reading_time(post.content)
    metadata["toc"] = toc

    if "date" in metadata:
        if isinstance(metadata["date"], str):
            metadata["date"] = datetime.fromisoformat(metadata["date"])
        elif isinstance(metadata["date"], date) and not isinstance(metadata["date"], datetime):
            # Convert date to datetime for consistent sorting
            metadata["date"] = datetime.combine(metadata["date"], datetime.min.time())
    else:
        metadata["date"] = datetime.fromtimestamp(file_path.stat().st_mtime)

    if "tags" not in metadata:
        metadata["tags"] = []

    if "title" not in metadata:
        metadata["title"] = file_path.stem.replace("-", " ").title()

    if "published" not in metadata:
        metadata["published"] = True

    return metadata


def get_all_posts(posts_dir: Path, include_drafts: bool = False) -> list[dict]:
    """Get all posts sorted by date (newest first)."""
    posts = []
    if not posts_dir.exists():
        return posts

    for file_path in posts_dir.glob("*.md"):
        post = parse_markdown_file(file_path)
        if post:
            if include_drafts or post.get("published", True):
                posts.append(post)

    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


def get_all_projects(projects_dir: Path) -> list[dict]:
    """Get all projects sorted by date (newest first)."""
    projects = []
    if not projects_dir.exists():
        return projects

    for file_path in projects_dir.glob("*.md"):
        project = parse_markdown_file(file_path)
        if project:
            projects.append(project)

    projects.sort(key=lambda x: x.get("order", 0))
    return projects


def save_markdown_file(file_path: Path, title: str, content: str, **metadata) -> None:
    """Save content as a markdown file with frontmatter."""
    post = frontmatter.Post(content)
    post["title"] = title
    post["date"] = datetime.now().isoformat()

    for key, value in metadata.items():
        post[key] = value

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))


def delete_content_file(file_path: Path) -> bool:
    """Delete a content file."""
    if file_path.exists():
        file_path.unlink()
        return True
    return False
