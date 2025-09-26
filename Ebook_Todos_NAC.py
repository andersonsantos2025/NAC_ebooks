import streamlit as st
import pandas as pd
from pathlib import Path
import base64, re, io, requests

st.set_page_config(page_title="E-books do NAC", layout="wide")
st.title("📚 E-books do NAC")

# ====== CONFIG: indique sua URL RAW do GitHub para a planilha ======
# Exemplo: "https://raw.githubusercontent.com/SEU_USER/nac-ebooks/main/listagem.xlsx"
LISTAGEM_URL = st.secrets.get("LISTAGEM_URL", "")  # opcional via Secrets
# Se preferir fixo no código, descomente a linha abaixo:
# LISTAGEM_URL = "https://raw.githubusercontent.com/SEU_USER/nac-ebooks/main/listagem.xlsx"

def is_url(s: str) -> bool:
    return isinstance(s, str) and s.strip().lower().startswith(("http://", "https://"))

def local_to_data_uri(path_like: str) -> str:
    """Converte imagem local em data URI; tenta extensões comuns se a passada não existir."""
    p = Path(path_like)
    if not p.exists():
        folder = p.parent if str(p.parent) not in ("", ".") else Path("img")
        stem = p.stem if p.stem else Path(path_like).stem
        for ext in [".png", ".jpg", ".jpeg", ".webp", ".PNG", ".JPG", ".JPEG", ".WEBP"]:
            cand = folder / f"{stem}{ext}"
            if cand.exists():
                p = cand
                break
    if not p.exists():
        return ""
    mime = {
        ".png": "image/png", ".PNG": "image/png",
        ".jpg": "image/jpeg", ".JPG": "image/jpeg",
        ".jpeg": "image/jpeg", ".JPEG": "image/jpeg",
        ".webp": "image/webp", ".WEBP": "image/webp",
    }.get(p.suffix, "image/png")
    b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"

def normalize_cover_value(val: str) -> str:
    """
    Normaliza a 3ª coluna (capa):
    - Se for URL -> retorna a própria URL.
    - Se for caminho absoluto (Windows/Linux) -> transforma para 'img/<arquivo>'.
    - Caso contrário -> retorna o que veio (esperado 'img/<arquivo>').
    """
    if not isinstance(val, str):
        return ""
    v = val.strip()
    if not v or v.lower() in ("nan", "none", "null"):
        return ""
    if is_url(v):
        return v
    # Caminho absoluto Windows (C:\...) ou Linux (/home/...)
    if re.match(r"^[a-zA-Z]:\\", v) or v.startswith("/"):
        filename = Path(v).name
        return f"img/{filename}"
    return v  # relativo já

def cover_src(capa_val: str) -> str:
    """Retorna src para <img>: se URL -> a URL; se caminho local -> data URI."""
    if not capa_val:
        return ""
    return capa_val if is_url(capa_val) else local_to_data_uri(capa_val)

# ====== 1) Carregar a planilha: local -> GitHub RAW -> uploader ======
df = None
for cand in (Path("listagem.xlsx"), Path("data/listagem.xlsx")):
    if cand.exists():
        df = pd.read_excel(cand, header=None)
        break

if df is None and LISTAGEM_URL:
    try:
        r = requests.get(LISTAGEM_URL, timeout=20)
        r.raise_for_status()
        df = pd.read_excel(io.BytesIO(r.content), header=None)
    except Exception as e:
        st.warning(f"Falha ao baixar a planilha do GitHub: {e}")

if df is None:
    up = st.file_uploader("Envie listagem.xlsx (colunas: índice | link | capa)", type=["xlsx"])
    if up:
        df = pd.read_excel(up, header=None)

if df is None:
    st.error("Não consegui carregar `listagem.xlsx` (local, GitHub ou upload).")
    st.stop()

# Garantir 3 colunas
while df.shape[1] < 3:
    df[df.shape[1]] = ""

# ====== 2) Extrair/normalizar ======
links = df[1].astype(str).apply(lambda x: x.strip()).tolist()
raw_covers = df[2].astype(str).tolist()
covers = [normalize_cover_value(x) for x in raw_covers]

# Validar: cada capa precisa resolver (URL ok ou arquivo local existente)
errors = []
srcs = []
for i, (lk, cp) in enumerate(zip(links, covers), start=1):
    if not lk:
        errors.append(f"Linha {i}: link vazio")
        srcs.append("")
        continue
    src = cover_src(cp)
    if not src:
        errors.append(f"Linha {i}: capa não encontrada -> '{cp}' (use URL ou 'img/<arquivo>')")
    srcs.append(src)

if errors:
    st.error("Há itens sem capa/arquivo. Corrija antes de publicar:")
    for m in errors:
        st.write("• ", m)
    st.info("Dica: na planilha, use 'img/nome.png' (arquivo dentro do repo) ou uma URL de imagem pública.")
    if LISTAGEM_URL:
        st.caption(f"Lendo planilha de: {LISTAGEM_URL}")
    st.stop()

# ====== 3) Render (4 por linha) ======
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
