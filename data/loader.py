import json5
import os

DATA_DIR = os.path.dirname(__file__)

def load_json(filename):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, encoding="utf-8") as f:
        return json5.load(f)

def get_achievements():
    return load_json("achievements.json5")

def get_societies():
    return load_json("societies.json5")

def get_qualifications():
    return load_json("qualifications.json5")

def get_recent_records():
    return load_json("recent_records.json5")