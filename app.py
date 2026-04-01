from flask import Flask, render_template
from data.loader import get_achievements, get_societies, get_qualifications

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/resume")
def resume():
    qualifications = get_qualifications()
    return render_template("resume.html", qualifications=qualifications)

@app.route("/activity")
def activity():
    achievements = get_achievements()
    societies = get_societies()
    return render_template("activity.html", achievements=achievements, societies=societies)

if __name__ == "__main__":
    app.run(debug=True)