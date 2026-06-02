```python
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
# OCR LOADER
# ==========================================
@st.cache_resource
def load_reader():
    return easyocr.Reader(
        ['bg', 'en'],
        gpu=False,
        verbose=False
    )

try:
    reader = load_reader()
except Exception as e:
    st.error(f"Failed to load OCR engine: {e}")
    st.stop()

# ==========================================
# DATABASE
# ==========================================
INGREDIENT_DATABASE = {
    "E950": {
        "en": "Acesulfame K",
        "bg": "Ацесулфам К",
        "risk": 3,
        "category": "Sweetener",
        "info": "Artificial sweetener",
        "aliases": ["e950", "acesulfame k", "ацесулфам", "ацесулфам к"]
    },
    "E951": {
        "en": "Aspartame",
        "bg": "Аспартам",
        "risk": 3,
        "category": "Sweetener",
        "info": "Artificial sweetener",
        "aliases": ["e951", "aspartame", "аспартам"]
    },
    "E955": {
        "en": "Sucralose",
        "bg": "Сукралоза",
        "risk": 3,
        "category": "Sweetener",
        "info": "Artificial sweetener",
        "aliases": ["e955", "sucralose", "сукралоза"]
    },
    "E621": {
        "en": "Monosodium Glutamate",
        "bg": "Мононатриев глутамат",
        "risk": 2,
        "category": "Flavor Enhancer",
        "info": "Flavor enhancer",
        "aliases": ["e621", "msg", "monosodium glutamate", "мононатриев глутамат"]
    },
    "E210": {
        "en": "Benzoic Acid",
        "bg": "Бензоена киселина",
        "risk": 2,
        "category": "Preservative",
        "info": "May cause allergic reactions",
        "aliases": ["e210", "benzoic acid", "бензоена киселина"]
    },
    "E220": {
        "en": "Sulfur Dioxide",
        "bg": "Серен диоксид",
        "risk": 3,
        "category": "Preservative",
        "info": "May trigger asthma reactions",
        "aliases": ["e220", "sulfur dioxide", "серен диоксид"]
    },
    "E250": {
        "en": "Sodium Nitrite",
        "bg": "Натриев нитрит",
        "risk": 3,
        "category": "Preservative",
        "info": "Linked to cancer risk",
        "aliases": ["e250", "sodium nitrite", "натриев нитрит"]
    },
    "E320": {
        "en": "BHA",
        "bg": "BHA",
        "risk": 3,
        "category": "Antioxidant",
        "info": "Possible carcinogen",
        "aliases": ["e320", "bha"]
    },
    "E321": {
        "en": "BHT",
        "bg": "BHT",
        "risk": 3,
        "category": "Antioxidant",
        "info": "Linked to hormonal issues",
        "aliases": ["e321", "bht"]
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

ALLERGENS = [
    "milk", "мляко",
    "gluten", "глутен",
    "soy", "соя",
    "eggs", "яйца",
    "peanuts", "фъстъци",
    "nuts", "ядки",
    "fish", "риба"
]

# ==========================================
# IMAGE PROCESSING
# ==========================================
def preprocess_image(image):
    image = image.convert("RGB")

    img = np.array(image)

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    gray = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    blur = cv2.GaussianBlur(gray, (3, 3), 0)

    return blur

# ==========================================
# TEXT HELPERS
# ==========================================
def normalize_text(text):
    text = text.lower()

    replacements = {
        "0": "o",
        "1": "i",
        "|": "i"
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    return text

def normalize_e_number(e):
    e = e.upper()
    e = e.replace(" ", "")
    e = e.replace("-", "")
    e = e.replace(".", "")
    e = e.replace(":", "")

    e = e.replace("Е", "E")
    e = e.replace("O", "0")
    e = e.replace("I", "1")
    e = e.replace("Z", "2")

    return e

# ==========================================
# DETECTION
# ==========================================
def detect_e_numbers(text):
    found = set()

    e_matches = re.findall(
        r'[EeЕе][\s\-\.:]*\d{3}',
        text
    )

    for e in e_matches:
        e_clean = normalize_e_number(e)

        if e_clean in INGREDIENT_DATABASE:
            found.add(e_clean)

    return list(found)

def detect_ingredients(text):
    normalized = normalize_text(text)

    words = [
        w.strip()
        for w in re.split(r'[,;\n()]', normalized)
        if w.strip()
    ]

    found = set()

    for item in detect_e_numbers(text):
        found.add(item)

    for code, data in INGREDIENT_DATABASE.items():

        for alias in data["aliases"]:

            alias = alias.lower()

            for word in words:

                if (
                    alias in word
                    or fuzz.ratio(alias, word) > 85
                ):
                    found.add(code)
                    break

    return list(found)

def detect_harmful(text):
    normalized = normalize_text(text)

    words = [
        w.strip()
        for w in re.split(r'[,;\n()]', normalized)
        if w.strip()
    ]

    found = set()

    for ingredient in HARMFUL_INGREDIENTS:

        ing = ingredient.lower()

        for word in words:

            if (
                ing in word
                or fuzz.ratio(ing, word) > 85
            ):
                found.add(ingredient)
                break

    return list(found)

def detect_allergens(text):
    normalized = normalize_text(text)

    words = [
        w.strip()
        for w in re.split(r'[,;\n()]', normalized)
        if w.strip()
    ]

    found = set()

    for allergen in ALLERGENS:

        allergen = allergen.lower()

        for word in words:

            if (
                allergen in word
                or fuzz.ratio(allergen, word) > 85
            ):
                found.add(allergen)
                break

    return list(found)

# ==========================================
# SCORING
# ==========================================
def calculate_score(found_items, harmful_items):

    total = 0

    for item in found_items:
        total += INGREDIENT_DATABASE.get(
            item,
            {}
        ).get(
            "risk",
            0
        )

    for item in harmful_items:
        total += HARMFUL_INGREDIENTS.get(
            item,
            {}
        ).get(
            "risk",
            0
        )

    return total

def get_health_label(score):

    if score == 0:
        return "🟢 Healthy"

    if score <= 4:
        return "🟡 Moderate"

    return "🔴 Unhealthy"

def risk_color(risk):

    if risk == 1:
        return "🟢"

    if risk == 2:
        return "🟡"

    return "🔴"

# ==========================================
# UI
# ==========================================
st.title("🧪 AI Ingredient Scanner")

st.markdown("""
Upload a food label image to detect:

- Harmful ingredients
- E-numbers
- Allergens
- Artificial sweeteners
""")

uploaded_file = st.file_uploader(
    "📤 Upload image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:

    try:
        image = Image.open(uploaded_file).convert("RGB")
    except Exception:
        st.error("Invalid image file.")
        st.stop()

    st.image(
        image,
        caption="Uploaded Image",
        use_container_width=True
    )

    st.write("🔍 Processing image...")

    processed = preprocess_image(image)

    try:
        results = reader.readtext(
            processed,
            detail=0,
            paragraph=True
        )

    except Exception as e:
        st.error(f"OCR Error: {e}")
        st.stop()

    extracted_text = " ".join(results)

    st.subheader("📄 Extracted Text")

    st.text_area(
        "OCR Result",
        extracted_text,
        height=220
    )

    found_ingredients = detect_ingredients(extracted_text)
    harmful_found = detect_harmful(extracted_text)
    allergens_found = detect_allergens(extracted_text)

    score = calculate_score(
        found_ingredients,
        harmful_found
    )

    label = get_health_label(score)

    st.subheader("🧪 Analysis")

    st.markdown(f"## {label}")
    st.markdown(f"### Health Score: {score}")

    if found_ingredients:

        st.subheader("⚠️ Detected Additives")

        for item in sorted(found_ingredients):

            data = INGREDIENT_DATABASE.get(item)

            if not data:
                continue

            color = risk_color(data["risk"])

            st.markdown(
f"""
{color} **{item} — {data['en']}**

- 🇧🇬 {data['bg']}
- Category: {data['category']}
- Risk Level: {data['risk']}/3
- ℹ️ {data['info']}
"""
            )

    if harmful_found:

        st.subheader("🚨 Harmful Ingredients")

        for item in sorted(harmful_found):

            data = HARMFUL_INGREDIENTS.get(item)

            if not data:
                continue

            color = risk_color(data["risk"])

            st.markdown(
f"""
{color} **{item.title()}**

- Risk Level: {data['risk']}/3
- ℹ️ {data['info']}
"""
            )

    if allergens_found:

        st.subheader("🥜 Allergens")

        for allergen in sorted(allergens_found):
            st.warning(f"⚠️ {allergen}")

    if (
        not found_ingredients
        and not harmful_found
        and not allergens_found
    ):
        st.success(
            "✅ No dangerous ingredients detected."
        )

st.markdown("---")
st.caption(
    "AI Ingredient Scanner • BG + EN OCR"
)
```
