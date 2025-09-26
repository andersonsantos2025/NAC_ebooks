# app.py
import streamlit as st
import pandas as pd
import requests, io

st.set_page_config(page_title="E-books do NAC", layout="wide")
st.title("📚 E-books do NAC")

# ------------------------------------------------------------------
# 1) Endereço RAW da planilha no GitHub
#    - você pode setar em st.secrets["LISTAGEM_URL"]
#    - ou preencher diretamente a variável abaixo.
# ------------------------------------------------------------------
LISTAGEM_URL = st.secrets.get(
    "LISTAGEM_URL",
    "https://raw.githubusercontent.com/SEU_USER/SEU_REPO/main/listagem.xlsx"  # <-- troque para o seu repo
)

# ------------------------------------------------------------------
# 2) Baixar e ler a planilha
#    Estrutura esperada:   Coluna A = índice (ignorado)
#                          Coluna B = link do PDF
#                          Coluna C = URL da capa (https://raw.githubusercontent.com/.../img/xxx.png)
# ------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_sheet(url: str) -> pd.DataFrame:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), header=None)

try:
    df = load_sheet(LISTAGEM_URL)
except Exception as e:
    st.error(f"Não consegui carregar a planilha do GitHub.\n\nDetalhe: {e}")
    st.stop()

# Garante ao menos 3 colunas
while df.shape[1] < 3:
    df[df.shape[1]] = ""

links = df[1].astype(str).str.strip().tolist()   # PDFs
capas = df[2].astype(str).str.strip().tolist()   # URLs de imagem (RAW GitHub)

# Validação simples: capa deve ser URL http(s)
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

# ------------------------------------------------------------------
# 3) Renderização: 4 capas por linha, clicáveis (target=_blank)
# ------------------------------------------------------------------
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

# Rodapé opcional
st.caption(f"Fonte da planilha: {LISTAGEM_URL}")
