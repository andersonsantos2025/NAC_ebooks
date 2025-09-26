import streamlit as st
import pandas as pd
from pathlib import Path
import base64

st.set_page_config(page_title="E-books NAC", layout="wide")
st.title("📚 E-books do NAC")

# ---------- helpers ----------
def is_url(s: str) -> bool:
    return isinstance(s, str) and s.strip().lower().startswith(("http://", "https://"))

def local_to_data_uri(path_like: str) -> str:
    """Converte imagem local (png/jpg/jpeg/webp) para data URI. Tenta extensões comuns."""
    p = Path(path_like)
    if not p.exists():
        # se veio só 'img/nome' sem extensão, tentar extensões conhecidas
        folder = p.parent if str(p.parent) not in ("", ".") else Path("img")
        stem = p.stem if p.stem else Path(path_like).stem
        for ext in [".png", ".jpg", ".jpeg", ".webp", ".PNG", ".JPG", ".JPEG", ".WEBP"]:
            cand = folder / f"{stem}{ext}"
            if cand.exists():
                p = cand
                break
    if not p.exists():
        return ""  # não achou
    mime = {
        ".png": "image/png", ".PNG": "image/png",
        ".jpg": "image/jpeg", ".JPG": "image/jpeg",
        ".jpeg": "image/jpeg", ".JPEG": "image/jpeg",
        ".webp": "image/webp", ".WEBP": "image/webp",
    }.get(p.suffix, "image/png")
    b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"

def cover_src(capa_val: str) -> str:
    """Retorna src para <img>: URL direta ou data URI se for caminho local."""
    if not isinstance(capa_val, str):
        return ""
    v = capa_val.strip()
    if not v or v.lower() in ("nan", "none", "null"):
        return ""
    return v if is_url(v) else local_to_data_uri(v)

# ---------- carregar a planilha ----------
df = None
for cand in (Path("listagem.xlsx"), Path("data/listagem.xlsx")):
    if cand.exists():
        df = pd.read_excel(cand, header=None)
        break
if df is None:
    up = st.file_uploader(
        "Envie listagem.xlsx (colunas: índice | link | capa)", type=["xlsx"]
    )
    if up:
        df = pd.read_excel(up, header=None)
if df is None:
    st.stop()

# garantir 3 colunas
while df.shape[1] < 3:
    df[df.shape[1]] = ""

# extrair dados
links = df[1].astype(str).apply(lambda x: x.strip()).tolist()
capas = df[2].astype(str).tolist()

# validações: 27 linhas e todas com capa resolvida
missing = []
srcs = []
for i, (lk, cp) in enumerate(zip(links, capas), start=1):
    if not lk:
        missing.append(f"Linha {i}: link vazio")
        srcs.append("")
        continue
    src = cover_src(cp)
    if not src:
        missing.append(f"Linha {i}: capa não encontrada -> '{cp}'")
    srcs.append(src)

if missing:
    st.error("Há itens sem capa/arquivo. Corrija a planilha antes de publicar:")
    for m in missing:
        st.write("• ", m)
    st.stop()

# ---------- render: 4 por linha, capa clicável ----------
for i in range(0, len(links), 4):
    cols = st.columns(4)
    for j in range(4):
        k = i + j
        if k >= len(links):
            break
        with cols[j]:
            st.markdown(
                f"""
                <a href="{links[k]}" target="_blank" rel="noopener">
                  <img src="{srcs[k]}" width="180"
                       style="display:block;margin-bottom:8px;border-radius:12px;">
                </a>
                """,
                unsafe_allow_html=True,
            )
