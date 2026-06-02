import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import pandas as pd

st.set_page_config(
    page_title="Анализ на етикети",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Анализ на етикети за потенциално вредни съставки")

st.write(
    "Качи снимка на продуктов етикет. "
    "Системата ще извлече текста и ще провери за известни спорни съставки."
)

# Списък с потенциално вредни/спорни съставки
HARMFUL_INGREDIENTS = {
    "aspartame": "Изкуствен подсладител.",
    "sodium nitrite": "Консервант, използван в месни продукти.",
    "nitrite": "Консервант в месни продукти.",
    "nitrites": "Консерванти.",
    "msg": "Мононатриев глутамат.",
    "monosodium glutamate": "Подобрител на вкуса.",
    "high fructose corn syrup": "Царевичен сироп с високо съдържание на фруктоза.",
    "hfcs": "Царевичен сироп с високо съдържание на фруктоза.",
    "sodium benzoate": "Консервант.",
    "potassium sorbate": "Консервант.",
    "bht": "Антиоксидант и консервант.",
    "bha": "Антиоксидант и консервант.",
    "tartrazine": "Оцветител E102.",
    "e102": "Тартразин.",
    "e110": "Жълт оцветител.",
    "e124": "Понсо 4R.",
    "e129": "Allura Red.",
    "e211": "Натриев бензоат.",
    "e621": "Мононатриев глутамат.",
    "palm oil": "Палмово масло.",
    "hydrogenated oil": "Хидрогенирани мазнини.",
    "trans fat": "Транс мазнини."
}


@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en', 'bg'], gpu=False)


def extract_text(image):
    reader = load_ocr()

    results = reader.readtext(
        np.array(image),
        detail=0,
        paragraph=True
    )

    return "\n".join(results)


def analyze_ingredients(text):
    found = []

    text_lower = text.lower()

    for ingredient, description in HARMFUL_INGREDIENTS.items():
        if ingredient in text_lower:
            found.append({
                "Съставка": ingredient,
                "Описание": description
            })

    return found


uploaded_file = st.file_uploader(
    "Качи снимка",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:

    image = Image.open(uploaded_file)

    col1, col2 = st.columns(2)

    with col1:
        st.image(image, caption="Качена снимка", use_container_width=True)

    with st.spinner("OCR анализ..."):
        text = extract_text(image)

    with col2:
        st.subheader("Извлечен текст")
        st.text_area(
            "OCR резултат",
            text,
            height=400
        )

    st.divider()

    st.subheader("Анализ на съставките")

    findings = analyze_ingredients(text)

    if findings:
        st.warning(
            f"Открити са {len(findings)} потенциално спорни съставки."
        )

        df = pd.DataFrame(findings)
        st.dataframe(df, use_container_width=True)

    else:
        st.success(
            "Не са открити съставки от зададения списък."
        )

    st.info(
        "Този инструмент е само информативен и не представлява медицински съвет."
    )
