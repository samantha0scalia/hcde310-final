import requests
from datetime import datetime, timedelta

TICKET_MASTER_API_KEY = "rn0c8lpspqcfdqyvDRKxr7lCm7R7lx4C"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

def get_weather_description(code):
    code_map = {
        0: "Clear sky ☀️",
        1: "Mainly clear 🌤️",
        2: "Partly cloudy ⛅",
        3: "Overcast ☁️",
        45: "Fog 🌫️",
        48: "Rime fog 🌫️❄️",
        51: "Light drizzle 🌦️",
        53: "Moderate drizzle 🌦️",
        55: "Dense drizzle 🌧️",
        56: "Freezing drizzle ❄️🌧️",
        57: "Freezing drizzle (dense) ❄️🌧️",
        61: "Slight rain 🌧️",
        63: "Moderate rain 🌧️",
        65: "Heavy rain 🌧️⛈️",
        66: "Freezing rain (light) ❄️🌧️",
        67: "Freezing rain (heavy) ❄️🌧️",
        71: "Slight snow 🌨️",
        73: "Moderate snow 🌨️",
        75: "Heavy snow ❄️🌨️",
        77: "Snow grains ❄️",
        80: "Slight rain showers 🌦️",
        81: "Moderate rain showers 🌧️",
        82: "Violent rain showers 🌧️⛈️",
        85: "Slight snow showers 🌨️",
        86: "Heavy snow showers ❄️🌨️",
        95: "Thunderstorm ⛈️⚡",
        96: "Thunderstorm w/ slight hail ⛈️🌨️",
        99: "Thunderstorm w/ heavy hail ⛈️🌨️❄️"
    }
    return code_map.get(code, "Unknown 🌈")

def get_coordinates_from_city(city_name):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1"
    response = requests.get(url)
    if response.status_code != 200:
        return None, None
    data = response.json()
    if "results" not in data or not data["results"]:
        return None, None
    lat = data["results"][0]["latitude"]
    lon = data["results"][0]["longitude"]
    return lat, lon

def get_weather_for_event(date_str, lat, lon):
    url = (f"{OPEN_METEO_BASE_URL}?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min"
           f"&temperature_unit=fahrenheit&timezone=auto&start_date={date_str}&end_date={date_str}")
    response = requests.get(url)
    if response.status_code != 200:
        return None

    data = response.json()
    try:
        weather_code = data["daily"]["weathercode"][0]
        temp_max = data["daily"]["temperature_2m_max"][0]
        temp_min = data["daily"]["temperature_2m_min"][0]
        avg_temp = (temp_max + temp_min) / 2
        return {"weather_code": weather_code, "temp_f": avg_temp}
    except (KeyError, IndexError):
        return None


def search_events_by_city(city, start_date, end_date):
    url = (f"https://app.ticketmaster.com/discovery/v2/events.json?apikey={TICKETMASTER_API_KEY}"
           f"&city={city}&startDateTime={start_date}&endDateTime={end_date}&size=20")
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

def classify_event(event):
    name = event.get("name", "").lower()
    classifications = event.get("classifications", [])
    segment = classifications[0]["segment"]["name"].lower() if classifications else ""

    keywords_indoor = ["theater", "ballet", "opera", "symphony", "indoor", "orchestra", "broadway"]
    keywords_outdoor = ["festival", "fair", "outdoor", "parade", "market", "race", "marathon"]

    if any(word in name for word in keywords_indoor) or "classical" in segment:
        return "indoor"
    elif any(word in name for word in keywords_outdoor):
        return "outdoor"
    else:
        return "indoor"

def process_events_for_next_3_days(city):
    lat, lon = get_coordinates_from_city(city)
    if lat is None or lon is None:
        return None, "Could not find coordinates for city."

    today = datetime.now()
    all_results = []

    for offset in range(3):
        target_date = today + timedelta(days=offset)
        date_str = target_date.strftime("%Y-%m-%d")

        forecast = get_weather_for_event(date_str, lat, lon)
        if not forecast:
            continue

        weather_code = forecast["weather_code"]
        temp_f = forecast["temp_f"]
        weather_desc = get_weather_description(weather_code)

        is_bad_weather = (temp_f < 60 or weather_code in [61, 63, 65, 80, 81, 82, 95, 96, 99])

        start_iso = target_date.strftime("%Y-%m-%dT00:00:00Z")
        end_iso = target_date.strftime("%Y-%m-%dT23:59:59Z")

        events_data = search_events_by_city(city, start_iso, end_iso)
        if not events_data or "_embedded" not in events_data:
            continue

        day_results = []

        for event in events_data["_embedded"]["events"]:
            name = event.get("name", "No name")
            url = event.get("url", "#")
            venue = event.get("_embedded", {}).get("venues", [{}])[0].get("name", "No venue")

            event_type = classify_event(event)

            if (is_bad_weather and event_type == "indoor") or (not is_bad_weather and event_type == "outdoor"):
                day_results.append({
                    "name": name,
                    "venue": venue,
                    "url": url
                })

            if len(day_results) >= 5:
                break

        all_results.append({
            "date": target_date.strftime("%A, %B %-d, %Y"),
            "weather": f"{int(temp_f)}°F, {weather_desc}",
            "events": day_results
        })

    return all_results, None