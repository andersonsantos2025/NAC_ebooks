import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="E-books do NAC", layout="wide")
st.title("📚 E-books do NAC")

# URL RAW da planilha (.xlsx)
LISTAGEM_URL = "https://raw.githubusercontent.com/andersonsantos2025/NAC_ebooks/main/listagem.xlsx"

# ---------- utils ----------
def to_raw_github(url: str) -> str:
    if not isinstance(url, str):
        return ""
    u = url.strip()
    if "github.com" in u and "/blob/" in u:
        u = u.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/")
    return u

def url_sanitize(u: str) -> str:
    return u.strip().replace(" ", "%20")

def normalize_image_url(u: str) -> str:
    if not isinstance(u, str) or not u.strip():
        return ""
    return url_sanitize(to_raw_github(u))

def looks_like_image(content_type: str) -> bool:
    return isinstance(content_type, str) and content_type.lower().startswith("image/")

@st.cache_data(ttl=300)
def load_sheet(url: str) -> pd.DataFrame:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), header=None, engine="openpyxl")

def check_image(url: str) -> bool:
    try:
        h = requests.head(url, allow_redirects=True, timeout=15)
        if h.status_code >= 400:
            return False
        return looks_like_image(h.headers.get("Content-Type", ""))
    except Exception:
        return False

# ---------- carregar planilha ----------
try:
    df = load_sheet(LISTAGEM_URL)
except Exception as e:
    st.error(f"Não consegui carregar a planilha do GitHub.\n\nDetalhe: {e}")
    st.stop()

# Esperado: A=índice, B=link PDF, C=URL da capa
while df.shape[1] < 3:
    df[df.shape[1]] = ""

links = df[1].astype(str).str.strip().tolist()
raw_covers = df[2].astype(str).tolist()
covers = [normalize_image_url(c) for c in raw_covers]

# Validar capas para evitar imagens quebradas
broken = []
for i, u in enumerate(covers, start=1):
    ok = isinstance(u, str) and u.lower().startswith(("http://", "https://")) and check_image(u)
    if not ok:
        broken.append((i, raw_covers[i-1], u))

if broken:
    st.error("Algumas capas não estão acessíveis como imagem. Corrija a coluna C na planilha.")
    with st.expander("Ver detalhes (linha | valor na planilha | após normalização)"):
        for lin, original, normal in broken:
            st.write(f"• Linha {lin}:")
            st.write("  - planilha:", original)
            st.write("  - normalizado:", normal)
            st.write("---")
    st.stop()

# ---------- render (4 por linha) ----------
for i in range(0, len(links), 4):
    cols = st.columns(4)
    for j in range(4):
        k = i + j
        if k >= len(links): break
        with cols[j]:
            st.markdown(
                f"""
                <a href="{links[k]}" target="_blank" rel="noopener">
                  <img src="{covers[k]}" width="180"
                       style="display:block;margin-bottom:10px;border-radius:12px;">
                </a>
                """,
                unsafe_allow_html=True,
            )
