from flask import Flask, render_template, request, redirect, url_for
from functions import process_events_for_next_3_days

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        city = request.form.get("city_name")
        if city:
            return redirect(url_for("results", city_name=city))
    return render_template("index.html")

@app.route("/results")
def results():
    city = request.args.get("city_name", None)
    if city:
        events, error = process_events_for_next_3_days(city)
    else:
        events, error = [], "No city specified."

    return render_template("results.html", result=events, error=error)


if __name__ == "__main__":
    app.run(debug=True)