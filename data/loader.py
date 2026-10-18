"""data/ と posts/ のファイルを読み込む関数たち。"""

import os
import re

import markdown
import yaml

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(DATA_DIR, "..", "posts")

# ファイル先頭の --- ... --- で囲まれた部分（フロントマター）と本文を分ける
_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
_EXCERPT_LIMIT = 120  # 一覧カードに出す抜粋の最大文字数


def _load_yaml(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_profile():
    """手で書く情報（data/profile.yaml）。"""
    return _load_yaml("profile.yaml")


def get_researchmap():
    """researchmap から自動生成した情報（data/researchmap.yaml）。"""
    rm = _load_yaml("researchmap.yaml")
    for key in ("keywords", "fields", "achievements", "projects",
                "experience", "memberships", "outreach"):
        rm.setdefault(key, [])
    return rm


# ---------- ブログ記事 ----------

def _parse_post(filepath):
    slug = os.path.splitext(os.path.basename(filepath))[0]
    with open(filepath, encoding="utf-8") as f:
        raw = f.read()

    match = _FRONT_MATTER_RE.match(raw)
    meta, body_md = ({}, raw)
    if match:
        meta = yaml.safe_load(match.group(1)) or {}
        body_md = match.group(2)

    html = markdown.markdown(body_md, extensions=["extra", "nl2br"])

    summary = meta.get("summary")
    if not summary:
        summary = " ".join(re.sub(r"<[^>]+>", "", html).split())
    if len(summary) > _EXCERPT_LIMIT:
        summary = summary[:_EXCERPT_LIMIT].rstrip() + "…"

    return {
        "slug": slug,
        "title": meta.get("title", slug),
        "date": str(meta.get("date", "")),
        "type": meta.get("type") or "その他",
        "place": meta.get("place") or "",
        "url": meta.get("url") or "",
        "summary": summary,
        "html": html,
    }


def get_posts():
    """posts/ 内のすべての記事を、日付の新しい順に返す。"""
    if not os.path.isdir(POSTS_DIR):
        return []
    posts = [
        _parse_post(os.path.join(POSTS_DIR, name))
        for name in os.listdir(POSTS_DIR)
        if name.endswith(".md") and name.lower() != "readme.md"
    ]
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def get_post(slug):
    filepath = os.path.join(POSTS_DIR, slug + ".md")
    if "/" in slug or not os.path.isfile(filepath):
        return None
    return _parse_post(filepath)
