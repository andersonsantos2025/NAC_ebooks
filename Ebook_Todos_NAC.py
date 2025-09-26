# app.py
import streamlit as st
import pandas as pd
import requests, io, urllib.parse

st.set_page_config(page_title="E-books do NAC", layout="wide")
st.title("📚 E-books do NAC")

# URL RAW da planilha (ajuste se mudar)
LISTAGEM_URL = "https://raw.githubusercontent.com/andersonsantos2025/NAC_ebooks/main/listagem.xlsx"

# ---------- utils ----------
def to_raw_github(url: str) -> str:
    """Converte github.com/.../blob/... em raw.githubusercontent.com/..."""
    if not isinstance(url, str):
        return ""
    u = url.strip()
    if "github.com" in u and "/blob/" in u:
        u = u.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/")
    return u

def url_sanitize(u: str) -> str:
    """Remove espaços extras e codifica espaços como %20."""
    u = u.strip()
    # codificar apenas espaços; manter restante como veio
    return u.replace(" ", "%20")

def normalize_image_url(u: str) -> str:
    if not isinstance(u, str) or not u.strip():
        return ""
    u = to_raw_github(u)
    u = url_sanitize(u)
    return u

def looks_like_image(content_type: str) -> bool:
    return isinstance(content_type, str) and content_type.lower().startswith("image/")

@st.cache_data(ttl=300)
def load_sheet(url: str) -> pd.DataFrame:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), header=None, engine="openpyxl")

def check_image(url: str) -> bool:
    """HEAD na URL; retorna True se for imagem acessível."""
    try:
        h = requests.head(url, allow_redirects=True, timeout=15)
        if h.status_code >= 400:
            return False
        ct = h.headers.get("Content-Type", "")
        return looks_like_image(ct)
    except Exception:
        return False

# ---------- carregar planilha ----------
try:
    df = load_sheet(LISTAGEM_URL)
except Exception as e:
    st.error(f"Não consegui carregar a planilha do GitHub.\n\nDetalhe: {e}")
    st.caption(f"URL usada: {LISTAGEM_URL}")
    st.stop()

# Esperado: A=índice, B=link PDF, C=URL da capa
while df.shape[1] < 3:
    df[df.shape[1]] = ""

links = df[1].astype(str).str.strip().tolist()
raw_covers = df[2].astype(str).tolist()
covers = [normalize_image_url(c) for c in raw_covers]

# Validar capas (evita imagem quebrada)
broken = []
for i, u in enumerate(covers, start=1):
    if not (isinstance(u, str) and u.lower().startswith(("http://", "https://")) and check_image(u)):
        broken.append((i, raw_covers[i-1], u))

if broken:
    st.error("Algumas capas não estão acessíveis como imagem. Corrija a coluna C na planilha.")
    with st.expander("Ver detalhes (linha | valor na planilha | após normalização)"):
        for lin, original, normal in broken:
            st.write(f"• Linha {lin}:")
            st.write(f"  - planilha: {
