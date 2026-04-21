import streamlit as st
import requests
from PIL import Image

API_KEY = "helloworld"

BAD_INGREDIENTS_BG = [
"аспартам",
"сукралоза",
"ацесулфам",
"натриев бензоат",
"сорбинова киселина",
"кофеин",
"таурин",
]

st.title("OCR Ingredient Checker")

uploaded_file = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])

def extract_text(file):
url = "https://api.ocr.space/parse/image"
r = requests.post(
url,
files={"file": file},
data={"apikey": API_KEY, "language": "bul"}
)
result = r.json()
try:
return result["ParsedResults"][0]["ParsedText"]
except:
return ""

if uploaded_file:
image = Image.open(uploaded_file)
st.image(image)

text = extract_text(uploaded_file).lower()

st.text_area("Extracted text", text)

found = [i for i in BAD_INGREDIENTS_BG if i in text]

if found:
for i in found:
st.write(f"❌ {i}")
else:
st.write("✅ Nothing found")
