from flask import Flask, render_template, request
from functions import process_events_for_next_3_days

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    events = []
    error = None
    if request.method == "POST":
        city = request.form["city"]
        events, error = process_events_for_next_3_days(city)
    return render_template("index.html", events=events, error=error)

if __name__ == "__main__":
    app.run(debug=True)