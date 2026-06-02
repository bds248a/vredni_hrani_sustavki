import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import cv2
import re
from rapidfuzz import fuzz

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="AI Ingredient Scanner",
    page_icon="🧪",
    layout="centered"
)

# ==========================================
# LOAD OCR
# ==========================================
@st.cache_resource
def load_reader():
    # Kept cached so it only loads into memory once
    return easyocr.Reader(['bg', 'en'])

reader = load_reader()

# ==========================================
# DATABASE
# ==========================================
INGREDIENT_DATABASE = {
    "E950": {
        "en": "Acesulfame K", "bg": "Ацесулфам К", "risk": 3, "category": "Sweetener",
        "info": "Artificial sweetener", "aliases": ["e950", "acesulfame k", "ацесулфам", "ацесулфам к"]
    },
    "E951": {
        "en": "Aspartame", "bg": "Аспартам", "risk": 3, "category": "Sweetener",
        "info": "Artificial sweetener", "aliases": ["e951", "aspartame", "аспартам"]
    },
    "E955": {
        "en": "Sucralose", "bg": "Сукралоза", "risk": 3, "category": "Sweetener",
        "info": "Artificial sweetener", "aliases": ["e955", "sucralose", "сукралоза"]
    },
    "E621": {
        "en": "Monosodium Glutamate", "bg": "Мононатриев глутамат", "risk": 2, "category": "Flavor Enhancer",
        "info": "Flavor enhancer", "aliases": ["e621", "msg", "monosodium glutamate", "мононатриев глутамат"]
    },
    "E210": {
        "en": "Benzoic Acid", "bg": "Бензоена киселина", "risk": 2, "category": "Preservative",
        "info": "May cause allergic reactions", "aliases": ["e210", "benzoic acid", "бензоена киселина"]
    },
    "E220": {
        "en": "Sulfur Dioxide", "bg": "Серен диоксид", "risk": 3, "category": "Preservative",
        "info": "May trigger asthma reactions", "aliases": ["e220", "sulfur dioxide", "серен диоксид"]
    },
    "E250": {
        "en": "Sodium Nitrite", "bg": "Натриев нитрит", "risk": 3, "category": "Preservative",
        "info": "Linked to cancer risk", "aliases": ["e250", "sodium nitrite", "натриев нитрит"]
    },
    "E320": {
        "en": "BHA", "bg": "BHA", "risk": 3, "category": "Antioxidant",
        "info": "Possible carcinogen", "aliases": ["e320", "bha"]
    },
    "E321": {
        "en": "BHT", "bg": "BHT", "risk": 3, "category": "Antioxidant",
        "info": "Linked to hormonal issues", "aliases": ["e321", "bht"]
    }
}

HARMFUL_INGREDIENTS = {
    "sugar": {"risk": 3, "info": "High sugar intake may lead to obesity and diabetes"},
    "захар": {"risk": 3, "info": "Високият прием може да доведе до диабет"},
    "palm oil": {"risk": 2, "info": "May increase LDL cholesterol"},
    "палмово масло": {"risk": 2, "info": "Повишава LDL холестерола"},
    "glucose-fructose syrup": {"risk": 3, "info": "May disrupt metabolism"},
    "глюкозо-фруктозен сироп": {"risk": 3, "info": "Нарушава метаболизма"},
    "caffeine": {"risk": 2, "info": "High caffeine intake may affect sleep and heart rate"},
    "кофеин": {"risk": 2, "info": "Високият прием може да повлияе съня и сърдечния ритъм"},
    "taurine": {"risk": 1, "info": "Commonly found in energy drinks"},
    "таурин": {"risk": 1, "info": "Често се среща в енергийни напитки"}
}

ALLERGENS = ["milk", "мляко", "gluten", "глутен", "soy", "соя", "eggs", "яйца", "peanuts", "фъстъци", "nuts", "ядки", "fish", "риба"]

# ==========================================
# IMAGE PREPROCESSING
# ==========================================
def preprocess_image(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # Upscale for clearer character tracking
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # Mild blur to handle noise without destroying line profiles
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # REMOVED adaptiveThreshold because EasyOCR performs worse on raw binary text masks.
    return blur

# ==========================================
# TEXT NORMALIZATION
# ==========================================
def normalize_text(text):
    text = text.lower()
    replacements = {"0": "o", "1": "i", "|": "i"}
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)
    return text

def normalize_e_number(e):
    e = e.upper().replace(" ", "").replace("-", "").replace(".", "").replace(":", "")
    e = e.replace("O", "0").replace("I", "1").replace("Z", "2")
    return e

# ==========================================
# DETECTION ENGINES
# ==========================================
def detect_e_numbers(text):
    found = []
    e_matches = re.findall(r'[Ee][\s\-\.:]?\d{3}', text)
    for e in e_matches:
        e_clean = normalize_e_number(e)
        if e_clean in INGREDIENT_DATABASE:
            found.append(e_clean)
    return found

def detect_ingredients(text):
    normalized = normalize_text(text)
    found = []
    words = [w.strip() for w in re.split(r'[,;\n()]', normalized) if w.strip()]

    # 1. Direct Regex Lookup
    found.extend(detect_e_numbers(text))

    # 2. Alias Matches
    for code, data in INGREDIENT_DATABASE.items():
        for alias in data["aliases"]:
            alias_lower = alias.lower()
            for word in words:
                if alias_lower in word or fuzz.ratio(alias_lower, word) > 85:
                    found.append(code)
                    break
    return list(set(found))

def detect_harmful(text):
    normalized = normalize_text(text)
    found = []
    words = [w.strip() for w in re.split(r'[,;\n()]', normalized) if w.strip()]

    for ingredient in HARMFUL_INGREDIENTS:
        ing_lower = ingredient.lower()
        for word in words:
            if ing_lower in word or fuzz.ratio(ing_lower, word) > 85:
                found.append(ingredient)
                break
    return list(set(found))

def detect_allergens(text
