from pathlib import Path
from html.parser import HTMLParser
import html
import json
import re
import unicodedata
from urllib.parse import quote, urlparse

REPO_ZIP_RE = re.compile(r"vkkodi\.repo-(\d+(?:\.\d+)*)\.zip$", re.IGNORECASE)
README_NAME = "README.md"
KODI_BLOCK_COMMENT = "<!-- REPOSITORIO KODI (FORA DO HTML) -->"
TOPO_BADGE = "📦 Repositório Kodi • GitHub Pages"


# Utils
def extrair_versao(nome: str):
    """Extrai a versão de arquivos no padrão vkkodi.repo-X.Y.Z.zip."""
    m = REPO_ZIP_RE.search(nome)
    return tuple(map(int, m.group(1).split("."))) if m else ()


def remover_acentos(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    ).lower()


def caminho_relativo(child: Path, parent: Path) -> bool:
    """Compatibilidade segura para conferir se child está dentro de parent."""
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def caminho_publicavel(path: Path, raiz: Path) -> bool:
    """
    Evita varrer/publicar arquivos dentro de pastas ocultas, principalmente .git.
    Mantém o índice focado somente no que deve ir para o GitHub Pages.
    """
    try:
        partes = path.relative_to(raiz).parts
    except ValueError:
        return False
    return not any(parte.startswith(".") for parte in partes)


def pasta_tem_zip(pasta: Path, pastas_com_zip: set[Path]) -> bool:
    return any(caminho_relativo(pasta_zip, pasta) for pasta_zip in pastas_com_zip)


def href_nome(nome: str) -> str:
    """Escapa nomes de arquivo/pasta para uso seguro em href local."""
    return quote(nome, safe="")


def href_relativo(path: Path, raiz: Path) -> str:
    return quote(path.relative_to(raiz).as_posix(), safe="/")


# README.md da raiz exibido somente na página inicial.
def url_segura(url: str) -> bool:
    """Permite links relativos, âncoras e URLs http/https/mailto/tel."""
    url = url.strip()
    if not url:
        return False
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme.lower() not in {"http", "https", "mailto", "tel"}:
        return False
    lowered = url.lower().replace("\x00", "")
    return not lowered.startswith(("javascript:", "data:", "vbscript:"))


class SanitizadorHTML(HTMLParser):
    """
    Sanitizador simples e conservador para permitir HTML básico no README.md.
    Evita script/style/atributos perigosos, mas preserva ul/li/strong/code usados no README.
    """
    TAGS_BLOCO = {"p", "ul", "ol", "li", "blockquote", "pre", "h1", "h2", "h3", "h4", "h5", "h6", "br"}
    TAGS_INLINE = {"strong", "b", "em", "i", "code", "a", "span"}
    TAGS_PERMITIDAS = TAGS_BLOCO | TAGS_INLINE
    TAGS_DESCARTAR_CONTEUDO = {"script", "style", "iframe", "object", "embed"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes = []
        self.descartar_ate = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.TAGS_DESCARTAR_CONTEUDO:
            self.descartar_ate = tag
            return
        if self.descartar_ate or tag not in self.TAGS_PERMITIDAS:
            return
        if tag == "a":
            href = ""
            for nome, valor in attrs:
                if nome.lower() == "href" and valor and url_segura(valor):
                    href = valor.strip()
                    break
            if href:
                self.partes.append(f'<a href="{html.escape(href, quote=True)}">')
            else:
                self.partes.append("<a>")
            return
        if tag == "br":
            self.partes.append("<br>")
            return
        # Mantém tags sem atributos para evitar evento JS/style inline.
        self.partes.append(f"<{tag}>")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.descartar_ate:
            if tag == self.descartar_ate:
                self.descartar_ate = None
            return
        if tag in self.TAGS_PERMITIDAS and tag != "br":
            self.partes.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.descartar_ate:
            self.partes.append(html.escape(data, quote=False))

    def get_html(self) -> str:
        return "".join(self.partes)


def sanitizar_html_fragmento(fragmento: str) -> str:
    parser = SanitizadorHTML()
    parser.feed(fragmento)
    parser.close()
    return parser.get_html()


def markdown_links_para_html(texto: str) -> str:
    def repl(match):
        rotulo = html.escape(match.group(1), quote=False)
        url = match.group(2).strip()
        if not url_segura(url):
            return rotulo
        return f'<a href="{html.escape(url, quote=True)}">{rotulo}</a>'
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, texto)


def markdown_inline(texto: str) -> str:
    """Renderização segura de Markdown inline + HTML básico permitido."""
    texto = markdown_links_para_html(texto)
    texto = sanitizar_html_fragmento(texto)
    texto = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", texto)
    texto = re.sub(r"`([^`]+)`", r"<code>\1</code>", texto)
    return texto


def fechar_lista(saida, tipo_lista) -> None:
    if tipo_lista:
        saida.append(f"</{tipo_lista}>")


def linha_html_segura(stripped: str) -> bool:
    return bool(re.match(r"^</?(p|ul|ol|li|strong|b|em|i|code|pre|br|blockquote|h[1-6]|a)(\s|>|/)", stripped, re.IGNORECASE))


def renderizar_readme_markdown(caminho: Path) -> str:
    """
    Renderizador Markdown básico, sem dependências externas.
    Suporta títulos, parágrafos, listas, blocos de código, links e HTML básico seguro.
    """
    texto = caminho.read_text(encoding="utf-8", errors="replace")
    linhas = texto.splitlines()
    saida = []
    tipo_lista = None
    em_codigo = False
    codigo = []

    for linha in linhas:
        raw = linha.rstrip("\n")
        stripped = raw.strip()

        if stripped.startswith("```"):
            if em_codigo:
                saida.append("<pre><code>" + html.escape("\n".join(codigo), quote=False) + "</code></pre>")
                codigo = []
                em_codigo = False
            else:
                fechar_lista(saida, tipo_lista)
                tipo_lista = None
                em_codigo = True
            continue

        if em_codigo:
            codigo.append(raw)
            continue

        if not stripped:
            fechar_lista(saida, tipo_lista)
            tipo_lista = None
            continue

        # Ignora wrappers visuais comuns do README do GitHub, como <p align="left">
        # quando usados apenas para envolver listas. Isso evita HTML inválido <p><ul>...</ul></p>.
        if re.match(r"^<p\b[^>]*>\s*$", stripped, re.IGNORECASE) or re.match(r"^</p>\s*$", stripped, re.IGNORECASE):
            fechar_lista(saida, tipo_lista)
            tipo_lista = None
            continue

        # HTML básico seguro no README: evita aparecer &lt;ul&gt; / &lt;li&gt; na página.
        if linha_html_segura(stripped):
            fechar_lista(saida, tipo_lista)
            tipo_lista = None
            seguro = sanitizar_html_fragmento(stripped)
            if seguro:
                saida.append(seguro)
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            fechar_lista(saida, tipo_lista)
            tipo_lista = None
            nivel = len(heading.group(1))
            conteudo = markdown_inline(heading.group(2).strip())
            saida.append(f"<h{nivel}>{conteudo}</h{nivel}>")
            continue

        bullet = re.match(r"^[-*+]\s+(.+)$", stripped)
        if bullet:
            if tipo_lista != "ul":
                fechar_lista(saida, tipo_lista)
                tipo_lista = "ul"
                saida.append("<ul>")
            saida.append(f"<li>{markdown_inline(bullet.group(1).strip())}</li>")
            continue

        numero = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if numero:
            if tipo_lista != "ol":
                fechar_lista(saida, tipo_lista)
                tipo_lista = "ol"
                saida.append("<ol>")
            saida.append(f"<li>{markdown_inline(numero.group(1).strip())}</li>")
            continue

        fechar_lista(saida, tipo_lista)
        tipo_lista = None
        saida.append(f"<p>{markdown_inline(stripped)}</p>")

    if em_codigo:
        saida.append("<pre><code>" + html.escape("\n".join(codigo), quote=False) + "</code></pre>")

    fechar_lista(saida, tipo_lista)
    return "\n".join(saida).strip()



def texto_limpo_para_titulo(texto: str) -> str:
    """Remove HTML/Markdown simples para usar conteúdo do README como <title>."""
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = html.unescape(texto)
    texto = re.sub(r"[`*_]+", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def extrair_titulo_readme(raiz: Path) -> str:
    """
    Usa o primeiro título do README.md como título do site.
    Nada do nome exibido fica fixo no código: alterou o README, alterou o título gerado.
    """
    readme = raiz / README_NAME
    if not readme.is_file():
        return ""

    texto = readme.read_text(encoding="utf-8", errors="replace")

    # Prioriza título Markdown: # Meu Repositório
    for linha in texto.splitlines():
        m = re.match(r"^\s*#\s+(.+?)\s*$", linha)
        if m:
            titulo = texto_limpo_para_titulo(m.group(1))
            if titulo:
                return titulo

    # Também aceita README escrito com HTML: <h1>Meu Repositório</h1>
    m = re.search(r"<h1\b[^>]*>(.*?)</h1>", texto, flags=re.IGNORECASE | re.DOTALL)
    if m:
        titulo = texto_limpo_para_titulo(m.group(1))
        if titulo:
            return titulo

    return ""


def titulo_site(raiz: Path) -> str:
    """Título genérico com fallback neutro; nome do projeto vem do README.md quando existir."""
    return extrair_titulo_readme(raiz) or "Repositório"

def bloco_readme_raiz(raiz: Path) -> list[str]:
    readme = raiz / README_NAME
    if not readme.is_file():
        return []

    conteudo = renderizar_readme_markdown(readme)
    if not conteudo:
        return []

    return [
        "<!-- README.md (PAGINA INICIAL) -->",
        '<section class="readme-card">',
        conteudo,
        "</section>",
    ]


# Scan único (performance)
def scan_geral(raiz: Path):
    pastas_com_zip = set()
    todos_zips = []
    repos_one = []

    for p in raiz.rglob("*"):
        if not p.is_file():
            continue
        if not caminho_publicavel(p, raiz):
            continue
        if p.suffix.lower() != ".zip":
            continue

        todos_zips.append(p)
        pastas_com_zip.add(p.parent)

        v = extrair_versao(p.name)
        if v:
            repos_one.append((v, p))

    return pastas_com_zip, todos_zips, repos_one


# vkkodi.repo mais recente
def encontrar_repos_mais_recentes(repos_one):
    if not repos_one:
        return []
    maior = max(v for v, _ in repos_one)
    return sorted((p for v, p in repos_one if v == maior), key=lambda x: x.as_posix().lower())


def itens_da_pasta(pasta: Path, pastas_com_zip: set[Path]) -> list[tuple[str, Path]]:
    itens = []
    for item in sorted(pasta.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if item.name.startswith(".") or item.name == "index.html":
            continue
        if item.is_dir() and pasta_tem_zip(item, pastas_com_zip):
            itens.append(("dir", item))
        elif item.is_file() and item.suffix.lower() == ".zip":
            itens.append(("zip", item))
    return itens


def bloco_repositorio_kodi(raiz: Path, repos_recentes: list[Path]) -> str:
    if not repos_recentes:
        return ""

    bloco = [
        "",
        KODI_BLOCK_COMMENT,
        '<div id="Repositorio-KODI" style="display:none">',
        "<table>",
    ]
    for repo in repos_recentes:
        rel = repo.relative_to(raiz).as_posix()
        rel_html = html.escape(rel, quote=True)
        rel_href = quote(rel, safe="/")
        bloco.append(f'<tr><td><a href="{rel_href}">{rel_html}</a></td></tr>')
    bloco += ["</table>", "</div>"]
    return "\n".join(bloco)


def css_base() -> list[str]:
    return [
        "* { box-sizing:border-box; }",
        "body { margin:0; font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#f4f6f8; color:#1f2937; }",
        "a { color:#0066cc; text-decoration:none; font-weight:600; }",
        "a:hover { text-decoration:underline; }",
        "h1,h2,h3 { color:#111827; }",
    ]


def gerar_index_raiz(raiz: Path, pastas_com_zip: set[Path], todos_zips: list[Path], repos_recentes: list[Path]) -> str:
    itens = itens_da_pasta(raiz, pastas_com_zip)
    total_pastas = sum(1 for tipo, _ in itens if tipo == "dir")
    total_zips_raiz = sum(1 for tipo, _ in itens if tipo == "zip")
    total_zips_geral = len(todos_zips)
    titulo = titulo_site(raiz)

    css = css_base() + [
        "body { min-height:100vh; background:linear-gradient(135deg,#07111f 0%,#13263b 42%,#f4f6f8 42%,#f4f6f8 100%); }",
        ".page-shell { width:min(1180px, calc(100% - 32px)); margin:0 auto; padding:32px 0 44px; }",
        ".top-badge { display:inline-flex; align-items:center; gap:8px; margin:0 0 18px; padding:7px 12px; border:1px solid rgba(255,255,255,.24); border-radius:999px; background:rgba(255,255,255,.08); color:#fff; font-size:13px; letter-spacing:.02em; }",
        ".hero { color:#fff; padding:30px 0 26px; }",
        ".badge { display:inline-flex; align-items:center; gap:8px; padding:7px 12px; border:1px solid rgba(255,255,255,.24); border-radius:999px; background:rgba(255,255,255,.08); font-size:13px; letter-spacing:.02em; }",
        ".hero h1 { color:#fff; margin:16px 0 8px; font-size:clamp(30px, 5vw, 52px); line-height:1.03; }",
        ".hero p { max-width:760px; margin:0; color:#dce8f7; font-size:17px; line-height:1.6; }",
        ".layout { display:grid; grid-template-columns:minmax(0, 1.05fr) minmax(300px, .95fr); gap:22px; align-items:start; }",
        ".card { background:#fff; border:1px solid #e5e7eb; border-radius:18px; box-shadow:0 18px 44px rgba(15,23,42,.12); }",
        ".readme-card { padding:24px; }",
        ".readme-card h1 { margin:0 0 12px; font-size:28px; }",
        ".readme-card h2 { margin:22px 0 8px; font-size:21px; }",
        ".readme-card h3 { margin:18px 0 8px; }",
        ".readme-card p { margin:0 0 13px; line-height:1.68; color:#374151; }",
        ".readme-card ul,.readme-card ol { margin:12px 0 14px; padding-left:22px; line-height:1.68; color:#374151; }",
        ".readme-card li { margin:8px 0; }",
        ".readme-card code { background:#eef6ff; color:#075985; padding:3px 6px; border-radius:6px; font-weight:700; }",
        ".readme-card strong { color:#111827; }",
        ".panel { padding:20px; }",
        ".panel-head { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:16px; }",
        ".panel-head h2 { margin:0; font-size:22px; }",
        ".panel-head p { margin:5px 0 0; color:#6b7280; font-size:14px; }",
        ".stats { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:10px; margin-bottom:16px; }",
        ".stat { background:#f8fafc; border:1px solid #e5e7eb; border-radius:14px; padding:12px; }",
        ".stat strong { display:block; font-size:22px; color:#111827; }",
        ".stat span { font-size:12px; color:#6b7280; }",
        ".search-wrap { position:relative; margin-bottom:14px; }",
        "#search { width:100%; padding:12px 14px; border:1px solid #d1d5db; border-radius:12px; outline:none; font-size:15px; background:#fff; }",
        "#search:focus { border-color:#2563eb; box-shadow:0 0 0 4px rgba(37,99,235,.12); }",
        ".listing-grid { display:grid; grid-template-columns:1fr; gap:9px; max-height:680px; overflow:auto; padding-right:4px; }",
        ".entry { display:flex; align-items:center; gap:12px; padding:12px 13px; border:1px solid #e5e7eb; border-radius:14px; background:#fff; color:#111827; transition:.15s ease; }",
        ".entry:hover { transform:translateY(-1px); box-shadow:0 8px 22px rgba(15,23,42,.08); text-decoration:none; border-color:#bfdbfe; }",
        ".entry-icon { width:34px; height:34px; display:grid; place-items:center; border-radius:10px; background:#eff6ff; flex:0 0 auto; }",
        ".entry strong { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:100%; }",
        ".entry small { display:block; margin-top:2px; color:#6b7280; font-weight:500; }",
        ".empty { padding:18px; text-align:center; color:#6b7280; border:1px dashed #d1d5db; border-radius:14px; background:#f9fafb; }",
        ".footer-note { margin-top:18px; color:#6b7280; font-size:12px; text-align:center; }",
        "@media (max-width:900px) { body { background:#f4f6f8; } .top-badge,.badge { color:#1f2937; border-color:#d1d5db; background:#fff; } .layout { grid-template-columns:1fr; } }",
        "@media (max-width:560px) { .page-shell { width:min(100% - 20px, 1180px); padding-top:18px; } .readme-card,.panel { padding:16px; border-radius:14px; } .stats { grid-template-columns:1fr; } }",
    ]

    linhas = [
        "<!DOCTYPE html>",
        "<html lang='pt-BR'>",
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{html.escape(titulo, quote=False)}</title>",
        "<style>",
        *css,
        "</style>",
        "</head>",
        "<body>",
        '<main class="page-shell">',
        f'<div class="top-badge">{html.escape(TOPO_BADGE, quote=False)}</div>',
        '<section class="layout">',
        '<div class="card">',
    ]

    readme = bloco_readme_raiz(raiz)
    if readme:
        linhas.extend(readme)
    else:
        linhas.extend([
            '<section class="readme-card">',
            "<h1>Repositório disponível</h1>",
            "<p>Adicione um arquivo README.md na raiz para exibir instruções nesta área.</p>",
            "</section>",
        ])

    linhas.extend([
        "</div>",
        '<aside class="card panel">',
        '<div class="panel-head">',
        "<div>",
        "<h2>Arquivos disponíveis</h2>",
        "<p>Pastas e pacotes ZIP encontrados no repositório.</p>",
        "</div>",
        "</div>",
        '<div class="stats">',
        f'<div class="stat"><strong>{total_pastas}</strong><span>pastas</span></div>',
        f'<div class="stat"><strong>{total_zips_raiz}</strong><span>ZIPs na raiz</span></div>',
        f'<div class="stat"><strong>{total_zips_geral}</strong><span>ZIPs no total</span></div>',
        "</div>",
        '<div class="search-wrap"><input type="text" id="search" placeholder="Pesquisar arquivos ou pastas..."></div>',
        '<div id="listing" class="listing-grid">',
    ])

    itens_js = []
    for tipo, item in itens:
        nome_html = html.escape(item.name, quote=True)
        nome_norm = remover_acentos(item.name)
        if tipo == "dir":
            href = f'./{href_nome(item.name)}/index.html'
            card = (
                f'<a class="entry folder" href="{href}">'
                f'<span class="entry-icon">📁</span>'
                f'<span><strong>{nome_html}/</strong><small>Pasta com arquivos ZIP</small></span>'
                f'</a>'
            )
        else:
            href = f'./{href_nome(item.name)}'
            card = (
                f'<a class="entry zip" href="{href}">'
                f'<span class="entry-icon">📦</span>'
                f'<span><strong>{nome_html}</strong><small>Arquivo ZIP</small></span>'
                f'</a>'
            )
        linhas.append(card)
        itens_js.append([nome_norm, card])

    linhas.extend([
        "</div>",
        '<div class="footer-note">Página gerada automaticamente pelo GitHub Actions.</div>',
        "</aside>",
        "</section>",
        "</main>",
        "<script>",
        f"const items = {json.dumps(itens_js, ensure_ascii=False)};",
        "const input = document.getElementById('search');",
        "const listing = document.getElementById('listing');",
        "const empty = '<div class=\"empty\">Nenhum resultado encontrado.</div>';",
        "input.addEventListener('input', () => {",
        "  const t = input.value.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase();",
        "  const result = items.filter(i => i[0].includes(t)).map(i => i[1]).join('');",
        "  listing.innerHTML = result || empty;",
        "});",
        "</script>",
        "</body>",
        "</html>",
    ])

    content = "\n".join(linhas)
    bloco = bloco_repositorio_kodi(raiz, repos_recentes)
    if bloco:
        content += "\n" + bloco
    return content


def gerar_index_subpasta(pasta: Path, raiz: Path, pastas_com_zip: set[Path]) -> str:
    """
    Gera subpastas com visual semelhante à página inicial, mas sem README.md.
    Mantém a função principal: listar pastas com ZIP e arquivos .zip, com busca local.
    """
    itens = itens_da_pasta(pasta, pastas_com_zip)
    total_pastas = sum(1 for tipo, _ in itens if tipo == "dir")
    total_zips = sum(1 for tipo, _ in itens if tipo == "zip")
    rel = pasta.relative_to(raiz).as_posix()
    titulo_pasta = pasta.name if pasta != raiz else "Início"
    titulo = titulo_site(raiz)

    css = css_base() + [
        "body { min-height:100vh; background:linear-gradient(135deg,#07111f 0%,#13263b 38%,#f4f6f8 38%,#f4f6f8 100%); }",
        ".page-shell { width:min(1120px, calc(100% - 32px)); margin:0 auto; padding:30px 0 42px; }",
        ".hero { color:#fff; padding:24px 0 22px; }",
        ".badge { display:inline-flex; align-items:center; gap:8px; padding:7px 12px; border:1px solid rgba(255,255,255,.24); border-radius:999px; background:rgba(255,255,255,.08); font-size:13px; letter-spacing:.02em; }",
        ".hero h1 { color:#fff; margin:14px 0 8px; font-size:clamp(28px,4vw,44px); line-height:1.05; }",
        ".hero p { max-width:760px; margin:0; color:#dce8f7; font-size:16px; line-height:1.6; }",
        ".card { background:#fff; border:1px solid #e5e7eb; border-radius:18px; box-shadow:0 18px 44px rgba(15,23,42,.12); }",
        ".panel { padding:22px; }",
        ".topbar { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:18px; flex-wrap:wrap; }",
        ".title-wrap h2 { margin:0; font-size:24px; color:#111827; }",
        ".title-wrap p { margin:6px 0 0; color:#6b7280; font-size:14px; word-break:break-word; }",
        ".actions { display:flex; gap:10px; flex-wrap:wrap; }",
        ".btn { display:inline-flex; align-items:center; justify-content:center; gap:8px; padding:9px 14px; border-radius:999px; border:1px solid #2563eb; color:#2563eb; background:#fff; font-weight:700; font-size:14px; transition:.15s ease; }",
        ".btn:hover { background:#2563eb; color:#fff; text-decoration:none; transform:translateY(-1px); }",
        ".stats { display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:10px; margin-bottom:16px; }",
        ".stat { background:#f8fafc; border:1px solid #e5e7eb; border-radius:14px; padding:12px; }",
        ".stat strong { display:block; font-size:22px; color:#111827; }",
        ".stat span { font-size:12px; color:#6b7280; }",
        ".search-wrap { position:relative; margin-bottom:16px; }",
        "#search { width:100%; padding:12px 14px; border:1px solid #d1d5db; border-radius:12px; outline:none; font-size:15px; background:#fff; }",
        "#search:focus { border-color:#2563eb; box-shadow:0 0 0 4px rgba(37,99,235,.12); }",
        ".listing-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(250px,1fr)); gap:10px; }",
        ".entry { display:flex; align-items:center; gap:12px; min-width:0; padding:13px; border:1px solid #e5e7eb; border-radius:14px; background:#fff; color:#111827; transition:.15s ease; }",
        ".entry:hover { transform:translateY(-1px); box-shadow:0 8px 22px rgba(15,23,42,.08); text-decoration:none; border-color:#bfdbfe; }",
        ".entry-icon { width:36px; height:36px; display:grid; place-items:center; border-radius:11px; background:#eff6ff; flex:0 0 auto; }",
        ".entry.zip .entry-icon { background:#ecfdf5; }",
        ".entry span:last-child { min-width:0; }",
        ".entry strong { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:100%; }",
        ".entry small { display:block; margin-top:2px; color:#6b7280; font-weight:500; }",
        ".empty { grid-column:1/-1; padding:18px; text-align:center; color:#6b7280; border:1px dashed #d1d5db; border-radius:14px; background:#f9fafb; }",
        ".footer-note { margin-top:18px; color:#6b7280; font-size:12px; text-align:center; }",
        "@media (max-width:760px) { body { background:#f4f6f8; } .hero { color:#111827; padding-top:18px; } .hero h1 { color:#111827; } .hero p { color:#4b5563; } .badge { color:#1f2937; border-color:#d1d5db; background:#fff; } .page-shell { width:min(100% - 20px, 1120px); padding-top:16px; } .panel { padding:16px; border-radius:14px; } .stats { grid-template-columns:1fr; } .listing-grid { grid-template-columns:1fr; } }",
    ]

    linhas = [
        "<!DOCTYPE html>",
        "<html lang='pt-BR'>",
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{html.escape(titulo_pasta, quote=False)} • {html.escape(titulo, quote=False)}</title>",
        "<style>",
        *css,
        "</style>",
        "</head>",
        "<body>",
        '<main class="page-shell">',
        '<section class="hero">',
        f'<div class="badge">{html.escape(TOPO_BADGE, quote=False)}</div>',
        f"<h1>{html.escape(titulo_pasta, quote=False)}</h1>",
        "<p>Arquivos desta pasta organizados para instalação e download. Use a busca para localizar rapidamente o pacote desejado.</p>",
        "</section>",
        '<section class="card panel">',
        '<div class="topbar">',
        '<div class="title-wrap">',
        "<h2>Arquivos disponíveis</h2>",
        f"<p>{html.escape(rel, quote=False)}</p>",
        "</div>",
        '<div class="actions">',
        '<a class="btn" href="../index.html">← Voltar</a>',
        "</div>",
        "</div>",
        '<div class="stats">',
        f'<div class="stat"><strong>{total_pastas}</strong><span>pastas</span></div>',
        f'<div class="stat"><strong>{total_zips}</strong><span>arquivos ZIP</span></div>',
        "</div>",
        '<div class="search-wrap"><input type="text" id="search" placeholder="Pesquisar arquivos ou pastas..."></div>',
        '<div id="listing" class="listing-grid">',
    ]

    itens_js = []
    for tipo, item in itens:
        nome_html = html.escape(item.name, quote=True)
        nome_norm = remover_acentos(item.name)
        if tipo == "dir":
            href = f'./{href_nome(item.name)}/index.html'
            card = (
                f'<a class="entry folder" href="{href}">'
                f'<span class="entry-icon">📁</span>'
                f'<span><strong>{nome_html}/</strong><small>Pasta com arquivos ZIP</small></span>'
                f'</a>'
            )
        else:
            href = f'./{href_nome(item.name)}'
            card = (
                f'<a class="entry zip" href="{href}">'
                f'<span class="entry-icon">📦</span>'
                f'<span><strong>{nome_html}</strong><small>Arquivo ZIP</small></span>'
                f'</a>'
            )
        linhas.append(card)
        itens_js.append([nome_norm, card])

    if not itens:
        linhas.append('<div class="empty">Nenhum arquivo disponível nesta pasta.</div>')

    linhas.extend([
        "</div>",
        '<div class="footer-note">Página gerada automaticamente pelo GitHub Actions.</div>',
        "</section>",
        "</main>",
        "<script>",
        f"const items = {json.dumps(itens_js, ensure_ascii=False)};",
        "const input = document.getElementById('search');",
        "const listing = document.getElementById('listing');",
        "const empty = '<div class=\"empty\">Nenhum resultado encontrado.</div>';",
        "input.addEventListener('input', () => {",
        "  const t = input.value.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase();",
        "  const result = items.filter(i => i[0].includes(t)).map(i => i[1]).join('');",
        "  listing.innerHTML = result || empty;",
        "});",
        "</script>",
        "</body>",
        "</html>",
    ])
    return "\n".join(linhas)


# Index handling
def gerar_ou_remover_index(
    pasta: Path,
    raiz: Path,
    pastas_com_zip: set[Path],
    todos_zips: list[Path],
    tem_zip_geral: bool,
    repos_recentes: list[Path]
):
    index = pasta / "index.html"
    tem_zip_na_pasta = pasta_tem_zip(pasta, pastas_com_zip)

    # Remove index de subpastas sem zip na própria pasta ou em subpastas.
    if pasta != raiz and not tem_zip_na_pasta:
        if index.exists():
            index.unlink()
            print(f"🧹 removido: {index.relative_to(raiz)}")
        return

    # Remove index da raiz se não houver nenhum .zip no repositório.
    if pasta == raiz and not tem_zip_geral:
        if index.exists():
            index.unlink()
            print(f"🧹 removido: {index.relative_to(raiz)}")
        return

    if pasta == raiz:
        content = gerar_index_raiz(raiz, pastas_com_zip, todos_zips, repos_recentes)
    else:
        content = gerar_index_subpasta(pasta, raiz, pastas_com_zip)

    index.write_text(content, encoding="utf-8", newline="\n")
    print(f"✔ index atualizado: {index.relative_to(raiz)}")


# Bottom-up
def varrer_bottom_up(pasta: Path, raiz: Path, *args):
    for sub in sorted(pasta.iterdir(), key=lambda x: x.name.lower()):
        if sub.is_dir() and not sub.name.startswith("."):
            varrer_bottom_up(sub, raiz, *args)
    gerar_ou_remover_index(pasta, raiz, *args)


# Main
if __name__ == "__main__":
    raiz = Path(".").resolve()
    pastas_com_zip, todos_zips, repos_one = scan_geral(raiz)
    repos_recentes = encontrar_repos_mais_recentes(repos_one)
    tem_zip_geral = bool(todos_zips)

    varrer_bottom_up(
        raiz,
        raiz,
        pastas_com_zip,
        todos_zips,
        tem_zip_geral,
        repos_recentes,
    )
