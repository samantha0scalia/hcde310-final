from flask import Flask, render_template, request
from functions import process_events_for_next_3_days

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        city = request.form.get("city")
        if not city:
            return render_template("base.html", error="Please enter a city.")

        results, error = process_events_for_next_3_days(city)

        if error:
            return render_template("base.html", error=error)

        return render_template("results.html", city=city, results=results)

    return render_template("base.html")

if __name__ == "__main__":
    app.run(debug=True)
