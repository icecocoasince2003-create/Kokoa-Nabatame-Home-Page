from flask import Flask, render_template
from data.loader import get_achievements, get_societies, get_qualifications

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html', page='index')


@app.route('/resume')
def resume():
    return render_template(
        'resume.html',
        page='resume',
        qualifications=get_qualifications(),
    )


@app.route('/activity')
def activity():
    return render_template(
        'activity.html',
        page='activity',
        achievements=get_achievements(),
        societies=get_societies(),
    )


if __name__ == '__main__':
    app.run(debug=True)
