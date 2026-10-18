from collections import defaultdict
from datetime import date

from flask import Flask, abort, render_template

from data.loader import get_post, get_posts, get_profile, get_researchmap

# public/ の中身（画像・CSS）を /style.css のようなURLで配信（ローカル確認用。Vercel でも同じ）
app = Flask(__name__, static_folder="public", static_url_path="")


@app.context_processor
def common():
    """すべてのページで使う情報（プロフィール・researchmap・今年）。"""
    return {"profile": get_profile(), "rm": get_researchmap(), "this_year": date.today().year}


@app.template_filter("ym")
def ym(value):
    """'2026-08-25' → '2026.08'"""
    value = str(value or "")
    return value[:7].replace("-", ".")


@app.template_filter("ymd")
def ymd(value):
    """'2026-05-27' → '2026年5月27日'"""
    parts = str(value or "").split("-")
    labels = ["年", "月", "日"]
    return "".join(f"{int(x)}{labels[i]}" for i, x in enumerate(parts[:3]) if x.isdigit())


# 業績ページでの種類の並び順
ACHIEVEMENT_ORDER = [("論文", "論文"), ("著作", "その他の著作"), ("発表", "学会発表"), ("受賞", "受賞")]


def by_year(items, key):
    grouped = defaultdict(list)
    for item in items:
        grouped[str(item[key])[:4]].append(item)
    return dict(sorted(grouped.items(), reverse=True))


@app.route("/")
def home():
    return render_template("index.html", page="home", recent_posts=get_posts()[:3])


@app.route("/resume")
def resume():
    return render_template("resume.html", page="resume")


@app.route("/activity")
def activity():
    achievements = get_researchmap()["achievements"]
    groups = [(label, [a for a in achievements if a["type"] == t]) for t, label in ACHIEVEMENT_ORDER]
    return render_template("activity.html", page="activity",
                           achievement_groups=[(label, items) for label, items in groups if items])


@app.route("/blog")
def blog():
    return render_template("blog.html", page="blog", grouped_posts=by_year(get_posts(), "date"))


@app.route("/blog/<slug>")
def blog_post(slug):
    post = get_post(slug)
    if post is None:
        abort(404)
    return render_template("post.html", page="blog", post=post)


if __name__ == "__main__":
    app.run(debug=True)
