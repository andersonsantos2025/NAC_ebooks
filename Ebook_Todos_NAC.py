# app.py
import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="E-books do NAC", layout="wide")
st.title("📚 E-books do NAC")

# ------------------------------------------------------------------
# URLs da planilha no GitHub
# 1) RAW recomendado
PRIMARY_URL = "https://raw.githubusercontent.com/andersonsantos2025/NAC_ebooks/main/listagem.xls"
# 2) Fallback com ?raw=1 (aceita /blob/)
FALLBACK_URL = "https://github.com/andersonsantos2025/NAC_ebooks/blob/main/listagem.xls?raw=1"
# ------------------------------------------------------------------

@st.cache_data(ttl=300)
def fetch_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

def load_sheet_from(url: str) -> pd.DataFrame:
    data = fetch_bytes(url)
    lower = url.lower()
    # escolhe engine conforme extensão
    if lower.endswith(".xlsx"):
        return pd.read_excel(io.BytesIO(data), header=None, engine="openpyxl")
    elif lower.endswith(".xls"):
        return pd.read_excel(io.BytesIO(data), header=None, engine="xlrd")
    else:
        # tenta .xlsx, depois .xls
        try:
            return pd.read_excel(io.BytesIO(data), header=None, engine="openpyxl")
        except Exception:
            return pd.read_excel(io.BytesIO(data), header=None, engine="xlrd")

# Tenta carregar (RAW) -> fallback (?raw=1)
try:
    try:
        df = load_sheet_from(PRIMARY_URL)
        used_url = PRIMARY_URL
    except Exception:
        df = load_sheet_from(FALLBACK_URL)
        used_url = FALLBACK_URL
except Exception as e:
    st.error(f"Não consegui carregar a planilha do GitHub.\n\nDetalhe: {e}")
    st.write("URL testadas:")
    st.write("•", PRIMARY_URL)
    st.write("•", FALLBACK_URL)
    st.stop()

# Garante 3 colunas: A=índice (ignora), B=link do PDF, C=URL da capa (http/https)
while df.shape[1] < 3:
    df[df.shape[1]] = ""

links = df[1].astype(str).str.strip().tolist()
capas = df[2].astype(str).str.strip().tolist()

# Validação simples das capas
invalid = [
    f"Linha {i}: capa inválida → '{cp}'"
    for i, cp in enumerate(capas, start=1)
    if not (isinstance(cp, str) and cp.lower().startswith(("http://", "https://")))
]
if invalid:
    st.error("Há linhas sem URL de capa válida (coluna C) na planilha GitHub:")
    for msg in invalid:
        st.write("• ", msg)
    st.caption(f"Planilha lida de: {used_url}")
    st.stop()

# Renderização 4×N
for i in range(0, len(links), 4):
    cols = st.columns(4)
    for j in range(4):
        k = i + j
        if k >= len(links): break
        with cols[j]:
            st.markdown(
                f"""
                <a href="{links[k]}" target="_blank" rel="noopener">
                  <img src="{capas[k]}" width="180"
                       style="display:block;margin-bottom:10px;border-radius:12px;">
                </a>
                """,
                unsafe_allow_html=True,
            )

st.caption(f"Fonte da planilha: {used_url}")
