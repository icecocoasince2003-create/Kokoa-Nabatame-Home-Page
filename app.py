from flask import Flask, render_template
from collections import defaultdict
from data.loader import (
    get_achievements, 
    get_societies, 
    get_qualifications,
    get_recent_records
)

app = Flask(__name__)

def sort_records(records):
    return sorted(records, key=lambda x: x["date"],reverse=True)

def group_records_by_year(records):
    grouped=defaultdict(list)
    for record in records:
        year = record["date"][:4]
        grouped[year].append(record)
    
    # 年の新しい順に並べる
    grouped_sorted = dict(sorted(grouped.items(), reverse=True))
    return grouped_sorted

@app.route("/")
def home():
    recent_records = sort_records(get_recent_records())[:5] #最新の5件を表示
    return render_template("index.html", recent_records=recent_records)

@app.route("/resume")
def resume():
    qualifications = get_qualifications()
    return render_template("resume.html", qualifications=qualifications)

@app.route("/activity")
def activity():
    achievements = get_achievements()
    societies = get_societies()

    all_records = sort_records(get_recent_records())
    grouped_records = group_records_by_year(all_records)

    return render_template(
        "activity.html", 
        achievements=achievements, 
        societies=societies,
        grouped_records=grouped_records,
        page="activity"
    )

if __name__ == "__main__":
    app.run(debug=True)