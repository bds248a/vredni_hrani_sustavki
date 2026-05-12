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
    return easyocr.Reader(['bg', 'en'])

reader = load_reader()

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
        "aliases": [
            "acesulfame k",
            "ацесулфам",
            "ацесулфам к"
        ]
    },

    "E951": {
        "en": "Aspartame",
        "bg": "Аспартам",
        "risk": 3,
        "category": "Sweetener",
        "info": "Artificial sweetener",
        "aliases": [
            "aspartame",
            "аспартам"
        ]
    },

    "E955": {
        "en": "Sucralose",
        "bg": "Сукралоза",
        "risk": 3,
        "category": "Sweetener",
        "info": "Artificial sweetener",
        "aliases": [
            "sucralose",
            "сукралоза"
        ]
    },

    "E621": {
        "en": "Monosodium Glutamate",
        "bg": "Мононатриев глутамат",
        "risk": 2,
        "category": "Flavor Enhancer",
        "info": "Flavor enhancer",
        "aliases": [
            "msg",
            "monosodium glutamate",
            "мононатриев глутамат"
        ]
    },

    "E210": {
        "en": "Benzoic Acid",
        "bg": "Бензоена киселина",
        "risk": 2,
        "category": "Preservative",
        "info": "May cause allergic reactions",
        "aliases": [
            "benzoic acid",
            "бензоена киселина"
        ]
    },

    "E220": {
        "en": "Sulfur Dioxide",
        "bg": "Серен диоксид",
        "risk": 3,
        "category": "Preservative",
        "info": "May trigger asthma reactions",
        "aliases": [
            "sulfur dioxide",
            "серен диоксид"
        ]
    },

    "E250": {
        "en": "Sodium Nitrite",
        "bg": "Натриев нитрит",
        "risk": 3,
        "category": "Preservative",
        "info": "Linked to cancer risk",
        "aliases": [
            "sodium nitrite",
            "натриев нитрит"
        ]
    },

    "E320": {
        "en": "BHA",
        "bg": "BHA",
        "risk": 3,
        "category": "Antioxidant",
        "info": "Possible carcinogen",
        "aliases": [
            "bha"
        ]
    },

    "E321": {
        "en": "BHT",
        "bg": "BHT",
        "risk": 3,
        "category": "Antioxidant",
        "info": "Linked to hormonal issues",
        "aliases": [
            "bht"
        ]
    }
}

# ==========================================
# HARMFUL INGREDIENTS
# ==========================================

HARMFUL_INGREDIENTS = {

    "sugar": {
        "risk": 3,
        "info": "High sugar intake may lead to obesity and diabetes"
    },

    "захар": {
        "risk": 3,
        "info": "Високият прием може да доведе до диабет"
    },

    "palm oil": {
        "risk": 2,
        "info": "May increase LDL cholesterol"
    },

    "палмово масло": {
        "risk": 2,
        "info": "Повишава LDL холестерола"
    },

    "glucose-fructose syrup": {
        "risk": 3,
        "info": "May disrupt metabolism"
    },

    "глюкозо-фруктозен сироп": {
        "risk": 3,
        "info": "Нарушава метаболизма"
    }
}

# ==========================================
# ALLERGENS
# ==========================================

ALLERGENS = [
    "milk",
    "мляко",
    "gluten",
    "глутен",
    "soy",
    "соя",
    "eggs",
    "яйца",
    "peanuts",
    "фъстъци",
    "nuts",
    "ядки",
    "fish",
    "риба"
]

# ==========================================
# IMAGE PREPROCESSING
# ==========================================

def preprocess_image(image):

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

    thresh = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return thresh

# ==========================================
# NORMALIZE TEXT
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

# ==========================================
# NORMALIZE E-NUMBERS
# ==========================================

def normalize_e_number(e):

    e = e.upper()

    e = e.replace(" ", "")
    e = e.replace("-", "")
    e = e.replace(".", "")

    e = e.replace("O", "0")
    e = e.replace("I", "1")
    e = e.replace("Z", "2")

    return e

# ==========================================
# DETECT E-NUMBERS
# ==========================================

def detect_e_numbers(text):

    found = []

    e_matches = re.findall(
        r'[Ee][\s\-\.]?\d{3}',
        text
    )

    for e in e_matches:

        e_clean = normalize_e_number(e)

        if e_clean in INGREDIENT_DATABASE:
            found.append(e_clean)

    return found

# ==========================================
# DETECT INGREDIENTS
# ==========================================

def detect_ingredients(text):

    text = normalize_text(text)

    found = []

    found.extend(detect_e_numbers(text))

    for code, data in INGREDIENT_DATABASE.items():

        for alias in data["aliases"]:

            score = fuzz.partial_ratio(
                alias.lower(),
                text
            )

            if score > 85:
                found.append(code)
                break

    return list(set(found))

# ==========================================
# DETECT HARMFUL INGREDIENTS
# ==========================================

def detect_harmful(text):

    text = normalize_text(text)

    found = []

    for ingredient in HARMFUL_INGREDIENTS:

        score = fuzz.partial_ratio(
            ingredient,
            text
        )

        if score > 85:
            found.append(ingredient)

    return list(set(found))

# ==========================================
# DETECT ALLERGENS
# ==========================================

def detect_allergens(text):

    text = normalize_text(text)

    found = []

    for allergen in ALLERGENS:

        score = fuzz.partial_ratio(
            allergen,
            text
        )

        if score > 85:
            found.append(allergen)

    return list(set(found))

# ==========================================
# CALCULATE SCORE
# ==========================================

def calculate_score(found_items, harmful_items):

    total = 0

    for item in found_items:
        total += INGREDIENT_DATABASE[item]["risk"]

    for item in harmful_items:
        total += HARMFUL_INGREDIENTS[item]["risk"]

    return total

# ==========================================
# HEALTH LABEL
# ==========================================

def get_health_label(score):

    if score == 0:
        return "🟢 Healthy"

    elif score <= 4:
        return "🟡 Moderate"

    return "🔴 Unhealthy"

# ==========================================
# RISK COLOR
# ==========================================

def risk_color(risk):

    if risk == 1:
        return "🟢"

    elif risk == 2:
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

# ==========================================
# PROCESS IMAGE
# ==========================================

if uploaded_file:

    image = Image.open(uploaded_file)

    st.image(
        image,
        caption="Uploaded Image",
        use_container_width=True
    )

    st.write("🔍 Processing image...")

    processed = preprocess_image(image)

    # ======================================
    # OCR (FIXED VERSION)
    # ======================================

    results = reader.readtext(
        processed,
        detail=0,
        paragraph=True
    )

    extracted_text = " ".join(results)

    # ======================================
    # SHOW EXTRACTED TEXT
    # ======================================

    st.subheader("📄 Extracted Text")

    st.text_area(
        "OCR Result",
        extracted_text,
        height=200
    )

    # ======================================
    # DETECTION
    # ======================================

    found_ingredients = detect_ingredients(extracted_text)

    harmful_found = detect_harmful(extracted_text)

    allergens_found = detect_allergens(extracted_text)

    # ======================================
    # SCORE
    # ======================================

    score = calculate_score(
        found_ingredients,
        harmful_found
    )

    label = get_health_label(score)

    # ======================================
    # RESULTS
    # ======================================

    st.subheader("🧪 Analysis")

    st.markdown(f"## {label}")
    st.markdown(f"### Health Score: {score}")

    # ======================================
    # ADDITIVES
    # ======================================

    if found_ingredients:

        st.subheader("⚠️ Detected Additives")

        for item in found_ingredients:

            data = INGREDIENT_DATABASE[item]

            color = risk_color(data["risk"])

            st.markdown(f"""
{color} **{item} — {data['en']}**
- 🇧🇬 {data['bg']}
- Category: {data['category']}
- Risk Level: {data['risk']}/3
- ℹ️ {data['info']}
""")

    # ======================================
    # HARMFUL INGREDIENTS
    # ======================================

    if harmful_found:

        st.subheader("🚨 Harmful Ingredients")

        for item in harmful_found:

            data = HARMFUL_INGREDIENTS[item]

            color = risk_color(data["risk"])

            st.markdown(f"""
{color} **{item.title()}**
- Risk Level: {data['risk']}/3
- ℹ️ {data['info']}
""")

    # ======================================
    # ALLERGENS
    # ======================================

    if allergens_found:

        st.subheader("🥜 Allergens")

        for allergen in allergens_found:

            st.warning(f"⚠️ {allergen}")

    # ======================================
    # SAFE RESULT
    # ======================================

    if (
        not found_ingredients and
        not harmful_found and
        not allergens_found
    ):

        st.success("✅ No dangerous ingredients detected.")

# ==========================================
# FOOTER
# ==========================================

st.markdown("---")
st.caption("AI Ingredient Scanner • BG + EN OCR")
