import streamlit as st
import pandas as pd
import requests, io, re

st.set_page_config(page_title="E-books do NAC", layout="wide")
st.title("📚 E-books do NAC")

# >>> Troque pela SUA URL RAW do GitHub (ou defina em Secrets)
LISTAGEM_URL = st.secrets.get(
    "LISTAGEM_URL",
    "https://github.com/andersonsantos2025/NAC_ebooks/raw/refs/heads/main/listagem.xlsx"  # <-- edite aqui
)

def is_raw_github(url: str) -> bool:
    return "raw.githubusercontent.com" in url or url.endswith("?raw=1")

@st.cache_data(ttl=300)
def load_table(url: str) -> pd.DataFrame:
    # baixa o conteúdo
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    content = r.content

    # decide pelo sufixo
    lower = url.lower()
    if lower.endswith(".xlsx") or "application/vnd.openxmlformats" in r.headers.get("Content-Type",""):
        # força engine openpyxl
        return pd.read_excel(io.BytesIO(content), header=None, engine="openpyxl")
    elif lower.endswith(".csv") or "text/csv" in r.headers.get("Content-Type",""):
        # caso você opte por CSV no futuro
        return pd.read_csv(io.BytesIO(content), header=None)
    else:
        # tenta Excel mesmo sem extensão correta
        try:
            return pd.read_excel(io.BytesIO(content), header=None, engine="openpyxl")
        except Exception as e:
            raise RuntimeError(
                "O conteúdo baixado não parece um .xlsx válido. "
                "Confirme que a URL é RAW do GitHub e o arquivo é .xlsx."
            ) from e

# Validação da URL RAW
if not is_raw_github(LISTAGEM_URL):
    st.error("A URL da planilha não é RAW do GitHub. Use o formato:\n"
             "`https://raw.githubusercontent.com/<user>/<repo>/<branch>/listagem.xlsx`")
    st.stop()

# Carrega a planilha
try:
    df = load_table(LISTAGEM_URL)
except Exception as e:
    st.error(f"Não consegui carregar a planilha do GitHub.\n\nDetalhe: {e}")
    st.caption(f"URL usada: {LISTAGEM_URL}")
    st.stop()

# Garante 3 colunas (A=idx, B=link PDF, C=URL capa)
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
    for msg in invalid: st.write("• ", msg)
    st.caption(f"Planilha lida de: {LISTAGEM_URL}")
    st.stop()

# Render 4 por linha
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
