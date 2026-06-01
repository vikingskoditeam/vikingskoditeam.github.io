from pathlib import Path
import html
import json
import re
import unicodedata
from urllib.parse import quote

REPO_ZIP_RE = re.compile(r"vkkodi\.repo-(\d+(?:\.\d+)*)\.zip$", re.IGNORECASE)


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


def pasta_tem_zip(pasta: Path, pastas_com_zip: set[Path]) -> bool:
    return any(caminho_relativo(pasta_zip, pasta) for pasta_zip in pastas_com_zip)


def href_nome(nome: str) -> str:
    """Escapa nomes de arquivo/pasta para uso seguro em href local."""
    return quote(nome, safe="")


# Index handling
def gerar_ou_remover_index(
    pasta: Path,
    raiz: Path,
    pastas_com_zip: set[Path],
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

    linhas_html = [
        "<!DOCTYPE html>",
        "<html lang='pt-BR'>",
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Directory listing</title>",
        "<style>",
        "body { font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; background:#f4f6f8; color:#222; padding:24px; }",
        "h1 { margin-bottom:8px; }",
        "hr { border:0; border-top:1px solid #ddd; margin:12px 0 20px; }",
        "pre { background:#fff; padding:14px; border-radius:10px; box-shadow:0 4px 14px rgba(0,0,0,.08); line-height:1.6; overflow:auto; }",
        "a { color:#0066cc; text-decoration:none; font-weight:500; }",
        "a:hover { text-decoration:underline; }",
        "#search { padding:8px 12px; width:min(320px, 100%); border-radius:6px; border:1px solid #ccc; margin-bottom:16px; box-sizing:border-box; }",
        ".voltar { display:inline-block; margin-bottom:16px; padding:6px 14px; border-radius:999px; border:1px solid #0066cc; color:#0066cc; transition:.2s; }",
        ".voltar:hover { background:#0066cc; color:#fff; text-decoration:none; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Directory listing</h1>",
        "<hr/>",
    ]

    if pasta != raiz:
        linhas_html.append('<a class="voltar" href="../index.html">← Voltar</a>')

    linhas_html.append('<input type="text" id="search" placeholder="Pesquisar arquivos ou pastas...">')
    linhas_html.append("<pre id='listing'>")

    itens = []
    for item in sorted(pasta.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if item.name.startswith(".") or item.name == "index.html":
            continue

        nome_html = html.escape(item.name, quote=True)
        nome_href = href_nome(item.name)

        if item.is_dir() and pasta_tem_zip(item, pastas_com_zip):
            linha = f'📁 <a href="./{nome_href}/index.html">{nome_html}/</a>'
        elif item.is_file() and item.suffix.lower() == ".zip":
            linha = f'📦 <a href="./{nome_href}">{nome_html}</a>'
        else:
            continue

        linhas_html.append(linha)
        itens.append([remover_acentos(item.name), linha])

    linhas_html.extend([
        "</pre>",
        "<script>",
        f"const items = {json.dumps(itens, ensure_ascii=False)};",
        "const input = document.getElementById('search');",
        "const listing = document.getElementById('listing');",
        "input.addEventListener('input', () => {",
        "  const t = input.value.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase();",
        "  listing.innerHTML = items.filter(i => i[0].includes(t)).map(i => i[1]).join('\\n');",
        "});",
        "</script>",
        "</body>",
        "</html>",
    ])

    content = "\n".join(linhas_html)

    # Bloco externo usado pelo Kodi/cliente para localizar o vkkodi.repo mais recente.
    # Fica fora do HTML por compatibilidade com o comportamento anterior.
    if pasta == raiz and repos_recentes:
        bloco = [
            "",
            "<!-- REPOSITORIO KODI (FORA DO HTML) -->",
            '<div id="Repositorio-KODI" style="display:none">',
            "<table>",
        ]
        for repo in repos_recentes:
            rel = repo.relative_to(raiz).as_posix()
            rel_html = html.escape(rel, quote=True)
            rel_href = quote(rel, safe="/")
            bloco.append(f'<tr><td><a href="{rel_href}">{rel_html}</a></td></tr>')
        bloco += ["</table>", "</div>"]
        content += "\n" + "\n".join(bloco)

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
        tem_zip_geral,
        repos_recentes,
    )
