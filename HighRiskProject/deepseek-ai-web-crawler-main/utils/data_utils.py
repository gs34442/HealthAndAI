import csv

from models.clinic import Clinic


def is_duplicate_clinic(clinic_name: str, seen_names: set) -> bool:
    return clinic_name in seen_names


def is_complete_clinic(clinic: dict, required_keys: list) -> bool:
    return all(key in clinic for key in required_keys)


def save_clinic_to_csv(clinics: list, filename: str):
    if not clinics:
        print("No clinics to save.")
        return

    # Use field names from the Venue model
    fieldnames = Clinic.model_fields.keys()

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clinics)
    print(f"Saved {len(clinics)} venues to '{filename}'.")

# from models.venue import Venue


# def is_duplicate_venue(venue_name: str, seen_names: set) -> bool:
#     return venue_name in seen_names


# def is_complete_venue(venue: dict, required_keys: list) -> bool:
#     return all(key in venue for key in required_keys)


# def save_venues_to_csv(venues: list, filename: str):
#     if not venues:
#         print("No venues to save.")
#         return

#     # Use field names from the Venue model
#     fieldnames = Venue.model_fields.keys()

#     with open(filename, mode="w", newline="", encoding="utf-8") as file:
#         writer = csv.DictWriter(file, fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(venues)
#     print(f"Saved {len(venues)} venues to '{filename}'.")
