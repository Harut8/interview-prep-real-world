import requests

# This is a very poorly structured script.
# TASK:
# 1. Create a WeatherClient class.
# 2. Use an environment variable for the API KEY.
# 3. Add error handling for network timeouts and 4xx/5xx responses.
# 4. Add a cache (simple dict) to avoid redundant calls for the same city.
# 5. Write a mock test using `unittest.mock` or `pytest-mock`.

API_KEY = "12345-FIXME"  # Hardcoded! Bad!
URL = "https://api.weather-mock.com/v1/current"


def get_weather(city):
    params = {"q": city, "appid": API_KEY}
    resp = requests.get(URL, params=params)
    data = resp.json()
    print(f"City: {data['name']}, Temp: {data['main']['temp']}")


if __name__ == "__main__":
    get_weather("Moscow")
    get_weather("London")
