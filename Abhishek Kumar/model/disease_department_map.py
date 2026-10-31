"""
disease_department_map.py
--------------------------
The real-world dataset we use (see model/data/Training.csv) labels every
row with a specific DISEASE (e.g. "Migraine", "Hypertension"), not a
hospital department. A hospital doesn't have a "Migraine department" —
so this file maps each of the 41 diseases in the dataset to the hospital
department that would actually treat it.

This mapping is what turns a disease-prediction dataset into a
DEPARTMENT-prediction dataset for our use case.

Feel free to edit this mapping to match your own hospital's structure.
"""

DISEASE_TO_DEPARTMENT = {
    "Fungal infection": "Dermatology",
    "Allergy": "General Medicine",
    "GERD": "Gastroenterology",
    "Chronic cholestasis": "Gastroenterology",
    "Drug Reaction": "Dermatology",
    "Peptic ulcer diseae": "Gastroenterology",
    "AIDS": "General Medicine",
    "Diabetes ": "General Medicine",
    "Gastroenteritis": "Gastroenterology",
    "Bronchial Asthma": "General Medicine",
    "Hypertension ": "Cardiology",
    "Migraine": "Neurology",
    "Cervical spondylosis": "Orthopedic",
    "Paralysis (brain hemorrhage)": "Neurology",
    "Jaundice": "Gastroenterology",
    "Malaria": "General Medicine",
    "Chicken pox": "Dermatology",
    "Dengue": "General Medicine",
    "Typhoid": "General Medicine",
    "hepatitis A": "Gastroenterology",
    "Hepatitis B": "Gastroenterology",
    "Hepatitis C": "Gastroenterology",
    "Hepatitis D": "Gastroenterology",
    "Hepatitis E": "Gastroenterology",
    "Alcoholic hepatitis": "Gastroenterology",
    "Tuberculosis": "General Medicine",
    "Common Cold": "General Medicine",
    "Pneumonia": "General Medicine",
    "Dimorphic hemmorhoids(piles)": "Gastroenterology",
    "Heart attack": "Cardiology",
    "Varicose veins": "Cardiology",
    "Hypothyroidism": "General Medicine",
    "Hyperthyroidism": "General Medicine",
    "Hypoglycemia": "General Medicine",
    "Osteoarthristis": "Orthopedic",
    "Arthritis": "Orthopedic",
    "(vertigo) Paroymsal  Positional Vertigo": "ENT",
    "Acne": "Dermatology",
    "Urinary tract infection": "Urology",
    "Psoriasis": "Dermatology",
    "Impetigo": "Dermatology",
}

# Departments that exist on the hospital map but aren't produced by this
# particular disease dataset (kept here so the graph/map still shows them
# and so you know which departments to add more training data for).
DEPARTMENTS_WITHOUT_TRAINING_DATA = ["Psychiatry", "Pediatrics", "Ophthalmology"]
