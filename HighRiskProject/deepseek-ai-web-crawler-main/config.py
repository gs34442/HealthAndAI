# config.py

BASE_URL = "https://findahealthcenter.hrsa.gov/?zip=80126%252C%2BLittleton%252C%2BCO%252C%2BUSA&radius=10"
CSS_SELECTOR = "[class^='.resultHealthCenter']"
REQUIRED_KEYS = [
    "locationName",
    "operated",
    "address-street",
    "address-city",
    "tel",
    "distance",
    "website",
    "directions"
]
