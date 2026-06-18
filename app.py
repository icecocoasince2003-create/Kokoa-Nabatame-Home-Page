from flask import Flask, render_template, abort
from collections import defaultdict
from data.loader import (
    get_achievements,
    get_societies,
    get_qualifications,
    get_posts,
    get_post,
)

app = Flask(__name__)


def group_posts_by_year(posts):
    grouped = defaultdict(list)
    for post in posts:
        year = post["date"][:4]
        grouped[year].append(post)

    # 年の新しい順に並べる
    return dict(sorted(grouped.items(), reverse=True))


@app.route("/")
def home():
    recent_posts = get_posts()[:5]  # 最新の5件を表示
    return render_template("index.html", recent_records=recent_posts, page="index")


@app.route("/blog")
def blog():
    grouped_records = group_posts_by_year(get_posts())
    return render_template("blog.html", grouped_records=grouped_records, page="blog")


@app.route("/blog/<slug>")
def blog_post(slug):
    post = get_post(slug)
    if post is None:
        abort(404)
    return render_template("post.html", post=post, page="blog")


@app.route("/resume")
def resume():
    qualifications = get_qualifications()
    return render_template("resume.html", qualifications=qualifications, page="resume")


@app.route("/activity")
def activity():
    achievements = get_achievements()
    societies = get_societies()

    return render_template(
        "activity.html",
        achievements=achievements,
        societies=societies,
        page="activity",
    )


if __name__ == "__main__":
    app.run(debug=True)
