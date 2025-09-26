import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="E-books do NAC", layout="wide")
st.title("📚 E-books do NAC")

# URL RAW da planilha (troque aqui se mudar o caminho/branch)
LISTAGEM_URL = "https://raw.githubusercontent.com/andersonsantos2025/NAC_ebooks/main/listagem.xlsx"

@st.cache_data(ttl=300)
def load_sheet(url: str) -> pd.DataFrame:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    # .xlsx -> engine openpyxl
    return pd.read_excel(io.BytesIO(r.content), header=None, engine="openpyxl")

try:
    df = load_sheet(LISTAGEM_URL)
except Exception as e:
    st.error(f"Não consegui carregar a planilha do GitHub.\n\nDetalhe: {e}")
    st.caption(f"URL usada: {LISTAGEM_URL}")
    st.stop()

# Esperado: A = índice (ignorar), B = link do PDF, C = URL da capa (RAW GitHub)
while df.shape[1] < 3:
    df[df.shape[1]] = ""

links = df[1].astype(str).str.strip().tolist()
capas = df[2].astype(str).str.strip().tolist()

# Validação: capa precisa ser URL http(s)
invalid = [
    f"Linha {i}: capa inválida → '{cp}'"
    for i, cp in enumerate(capas, start=1)
    if not (isinstance(cp, str) and cp.lower().startswith(("http://", "https://")))
]
if invalid:
    st.error("Há linhas sem URL de capa válida (coluna C). Corrija a planilha:")
    for msg in invalid:
        st.write("• ", msg)
    st.caption(f"Planilha lida de: {LISTAGEM_URL}")
    st.stop()

# Render: 4 por linha, capa clicável
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

st.caption(f"Fonte da planilha: {LISTAGEM_URL}")
