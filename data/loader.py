import json5
import os
import re
import markdown
import yaml

DATA_DIR = os.path.dirname(__file__)
POSTS_DIR = os.path.join(DATA_DIR, "..", "posts")

# ファイル先頭の --- ... --- で囲まれた部分（フロントマター）と本文を分ける
_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)

# 一覧カードに出す抜粋の最大文字数
_EXCERPT_LIMIT = 120


def load_json(filename):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, encoding="utf-8") as f:
        return json5.load(f)


def get_achievements():
    return load_json("achievements.json5")


def get_societies():
    return load_json("societies.json5")


def get_qualifications():
    return load_json("qualifications.json5")


def _parse_post(filepath):
    """1つの Markdown ファイルを読み込み、記事データの辞書を返す。"""
    slug = os.path.splitext(os.path.basename(filepath))[0]
    with open(filepath, encoding="utf-8") as f:
        raw = f.read()

    match = _FRONT_MATTER_RE.match(raw)
    if match:
        meta = yaml.safe_load(match.group(1)) or {}
        body_md = match.group(2)
    else:
        meta = {}
        body_md = raw

    html = markdown.markdown(body_md, extensions=["extra", "nl2br"])

    # 一覧カード用の抜粋（本文のタグを取り除いた素のテキストから生成）
    summary = meta.get("summary")
    if not summary:
        text = re.sub(r"<[^>]+>", "", html)
        summary = " ".join(text.split())
    if len(summary) > _EXCERPT_LIMIT:
        summary = summary[:_EXCERPT_LIMIT].rstrip() + "…"

    return {
        "slug": slug,
        "title": meta.get("title", slug),
        "date": str(meta.get("date", "")),
        "type": meta.get("type", "その他"),
        "place": meta.get("place", "") or "",
        "url": meta.get("url", "") or "",
        "summary": summary,
        "html": html,
    }


def _is_post_file(name):
    return name.endswith(".md") and name.lower() != "readme.md"


def get_posts():
    """posts/ 内のすべての記事を、日付の新しい順に並べて返す。"""
    if not os.path.isdir(POSTS_DIR):
        return []
    posts = [
        _parse_post(os.path.join(POSTS_DIR, name))
        for name in os.listdir(POSTS_DIR)
        if _is_post_file(name)
    ]
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def get_post(slug):
    """slug（ファイル名）に対応する記事を返す。無ければ None。"""
    filepath = os.path.join(POSTS_DIR, slug + ".md")
    if not os.path.isfile(filepath):
        return None
    return _parse_post(filepath)
