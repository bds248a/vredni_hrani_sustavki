import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import re

@st.cache_resource
def load_reader():
    return easyocr.Reader(['bg', 'en'], gpu=False)

reader = load_reader()

# Разширена база данни с вредни съставки
HARMFUL_SUBSTANCES = {
    # Е-номера
    "E102": "Тартразин - силен алерген, забранен в някои страни.",
    "E211": "Натриев бензоат - консервант, подозиран за връзка с хиперактивност.",
    "E250": "Натриев нитрит - използва се в колбаси, потенциално канцерогенен.",
    "E621": "Мононатриев глутамат - подобрител на вкуса, може да причини главоболие.",
    "E951": "Аспартам - изкуствен подсладител, спорен за здравето.",
    
    # Други съставки (ключови думи)
    "палмово масло": "Високо съдържание на наситени мазнини; екологичен проблем.",
    "палмова мазнина": "Високо съдържание на наситени мазнини.",
    "хидрогенирани": "Индикация за наличие на трансмазнини, вредни за сърцето.",
    "фруктозен сироп": "Високофруктозен сироп от царевица - свързва се със затлъстяване.",
    "глюкозо-фруктозен": "Силно преработена захар, повишава риска от диабет.",
    "аспартам": "Изкуствен подсладител с негативна репутация.",
    "оцветител": "Изкуствените оцветители често са източник на хиперактивност при деца.",
}

def process_image(image):
    image_np = np.array(image)
    results = reader.readtext(image_np, detail=0)
    return " ".join(results).lower() # Правим всичко в малки букви за по-лесно търсене

def analyze_ingredients(text):
    found_items = {}
    
    # 1. Търсене на Е-номера чрез Regex
    e_pattern = r'[eeее]\s?\d{3,4}'
    e_matches = re.findall(e_pattern, text)
    for m in e_matches:
        clean_code = m.replace(" ", "").upper().replace("Е", "E")
        found_items[clean_code] = HARMFUL_SUBSTANCES.get(clean_code, "Е-номер: Проверете за специфични странични ефекти.")

    # 2. Търсене на конкретни думи
    for ingredient, description in HARMFUL_SUBSTANCES.items():
        if not ingredient.startswith("E") and ingredient in text:
            found_items[ingredient.capitalize()] = description
            
    return found_items

# --- Streamlit UI ---
st.set_page_config(page_title="Health Scanner Pro", page_icon="🥗")
st.title("🥗 Скенер за вредни съставки")
st.write("Качете снимка на етикета (Съдържание), за да проверим за Е-та, палмово масло, трансмазнини и захари.")

uploaded_file = st.file_uploader("Прикачи снимка...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Качен етикет", use_container_width=True)
    
    with st.spinner("Анализиране на съдържанието..."):
        full_text = process_image(image)
        results = analyze_ingredients(full_text)
        
        st.divider()
        
        if results:
            st.error(f"Внимание! Открити са {len(results)} потенциално вредни съставки:")
            for item, info in results.items():
                with st.expander(f"🚩 {item}"):
                    st.write(info)
        else:
            st.success("Не са открити критични съставки от нашата база данни.")

        with st.expander("Технически детайли (разпознат текст)"):
            st.text(full_text)
