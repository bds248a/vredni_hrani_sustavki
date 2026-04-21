import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import re

# Инициализиране на EasyOCR четеца (правим го веднъж, за да не се бави)
@st.cache_resource
def load_reader():
    # Зареждаме български и английски език
    return easyocr.Reader(['bg', 'en'], gpu=False) # Сложи gpu=True, ако имаш NVIDIA карта

reader = load_reader()

# База данни с опасни добавки
HARMFUL_ADDITIVES = {
    "E102": "Тартразин (силно алергенен)",
    "E110": "Сънсет жълто (опасно за деца)",
    "E123": "Амарант (забранен в САЩ)",
    "E211": "Натриев бензоат (консервант)",
    "E250": "Натриев нитрит (риск от канцерогенност)",
    "E621": "Мононатриев глутамат (възможни алергии)",
    "E951": "Аспартам (подсладител)"
}

bad_ingredients = [ "Хидрогенирани мазнини", "Частично хидрогенирани растителни масла", "Палмово масло", "Натриев нитрит ", "Натриев нитрат", 
"Глюкозо-фруктозен сироп", "Аспартам ", "Ацесулфам K", "Мононатриев глутамат", "BHA" , "BHT" , "Титанов диоксид", "Тартразин", "Сънсет жълто", "Алура червено"
"E310", "E311", "E312", "E320", "E321", "E407", "E430", "E431", "E432", "E433", "E434", "E435", "E436", "E450", "E451", "E452", "E466", "E620", "E621", "E622",
"E623", "E624", "E625", "E627", "E631", "E635", "E950", "E951", "E952", "E954", "E962", "E965"]

def process_image(image):
    # Превръщаме PIL изображението в numpy array за EasyOCR
    image_np = np.array(image)
    results = reader.readtext(image_np, detail=0) # detail=0 връща само текста
    return " ".join(results)

def extract_e_numbers(text):
    # Регулярен израз за намиране на Е-та (кирилица 'Е' или латиница 'E')
    pattern = r'[EeЕе]\s?\d{3,4}'
    matches = re.findall(pattern, text)
    
    found = {}
    for m in matches:
        # Стандартизираме към формат 'E123'
        clean_code = m.replace(" ", "").upper().replace("Е", "E")
        if clean_code in HARMFUL_ADDITIVES:
            found[clean_code] = HARMFUL_ADDITIVES[clean_code]
        else:
            found[clean_code] = "Няма информация в базата, но бъдете внимателни."
    return found

# --- Streamlit Интерфейс ---
st.set_page_config(page_title="EasyOCR Скенер", page_icon="🧪")
st.title("🧪 Анализ на съставки с EasyOCR")
st.write("Качете снимка на етикет, за да проверим за вредни добавки.")

uploaded_file = st.file_uploader("Прикачи снимка...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Качено изображение", use_container_width=True)
    
    with st.spinner("Извличане на текст..."):
        full_text = process_image(image)
        detected_e_numbers = extract_e_numbers(full_text)
        
        st.divider()
        
        if detected_e_numbers:
            st.subheader("⚠️ Открити добавки:")
            for code, info in detected_e_numbers.items():
                with st.expander(f"Резултат за {code}"):
                    st.write(f"**Информация:** {info}")
        else:
            st.success("Не бяха открити рискови Е-номера.")

        with st.expander("Виж целия разпознат текст"):
            st.write(full_text)
