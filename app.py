from flask import Flask, render_template, request
from datetime import datetime, timezone
from functions import (
    get_coordinates_from_city,
    get_weather_for_event,
    search_events_by_city,
    classify_event
)

app = Flask(__name__)

def process_events(data, lat, lon):

    if not data or "_embedded" not in data:
        return [], [], "No events found."

    events = data["_embedded"]["events"]
    filtered_events = []
    backup_events = []

    for event in events:
        name = event.get("name", "No name")
        raw_date = event.get("dates", {}).get("start", {}).get("localDate", "")
        venue_data = event.get("_embedded", {}).get("venues", [{}])[0]
        venue = venue_data.get("name", "No venue")
        url = event.get("url", "#")

        ev_lat = float(venue_data.get("location", {}).get("latitude", lat))
        ev_lon = float(venue_data.get("location", {}).get("longitude", lon))

        try:
            parsed_date = datetime.strptime(raw_date, "%Y-%m-%d")
            date_str = parsed_date.strftime("%Y-%m-%d")
            pretty_date = parsed_date.strftime("%B %-d, %Y")
        except ValueError:
            continue

        forecast = get_weather_for_event(date_str, ev_lat, ev_lon)
        if not forecast:
            continue

        weather_code = forecast["weather_code"]
        temp_f = forecast["temp_f"]
        is_bad_weather = (temp_f < 60 or weather_code in [61, 63, 65, 80, 81, 82])
        event_type = classify_event(event)

        event_info = {
            "name": name,
            "venue": venue,
            "date": pretty_date,
            "url": url,
            "type": event_type,
        }

        if (is_bad_weather and event_type == "indoor") or (not is_bad_weather and event_type == "outdoor"):
            filtered_events.append(event_info)
        elif event_type in ["indoor", "outdoor"]:
            backup_events.append(event_info)

    return filtered_events, backup_events, None

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        city = request.form.get("city")
        if not city:
            return render_template("base.html", error="Please enter a city.")

        lat, lon = get_coordinates_from_city(city)
        if lat is None or lon is None:
            return render_template("base.html", error="City not found.")

        now = datetime.now(timezone.utc)
        start_date = now.strftime('%Y-%m-%dT00:00:00Z')
        end_date = now.strftime('%Y-%m-%dT23:59:59Z')
        today_str = now.strftime('%Y-%m-%d')

        forecast = get_weather_for_event(today_str, lat, lon)
        events_data = search_events_by_city(city, start_date, end_date)

        filtered, backup, error = process_events(events_data, lat, lon)

        return render_template(
            "results.html",
            city=city,
            forecast=forecast,
            filtered_events=filtered,
            backup_events=backup,
            error=error
        )

    return render_template("base.html")

if __name__ == "__main__":
    app.run(debug=True)
