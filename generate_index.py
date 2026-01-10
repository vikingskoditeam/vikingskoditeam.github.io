from pathlib import Path
import re
import unicodedata

# Utils
def extrair_versao(nome: str):
    m = re.search(r"vkkodi\.repo-(\d+(?:\.\d+)*)\.zip", nome)
    return tuple(map(int, m.group(1).split("."))) if m else ()
def remover_acentos(texto: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

# Scan único (performance)
def scan_geral(raiz: Path):
    pastas_com_zip = set()
    todos_zips = []
    repos_one = []
    for p in raiz.rglob("*"):
        if not p.is_file():
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
    return [p for v, p in repos_one if v == maior]

# Index handling
def gerar_ou_remover_index(
    pasta: Path,
    raiz: Path,
    pastas_com_zip: set,
    tem_zip_geral: bool,
    repos_recentes: list[Path]
):
    index = pasta / "index.html"
    tem_zip_na_pasta = (
        pasta in pastas_com_zip or
        any(p.is_relative_to(pasta) for p in pastas_com_zip)
    )
    # Remove index de subpastas sem zip
    if pasta != raiz and not tem_zip_na_pasta:
        if index.exists():
            index.unlink()
            print(f"🧹 removido: {index}")
        return
    # Remove index da raiz se não houver zip nenhum
    if pasta == raiz and not tem_zip_geral:
        if index.exists():
            index.unlink()
            print(f"🧹 removido: {index}")
        return
        # HTML (estiloso + leve)
    linhas_html = [
        "<!DOCTYPE html>",
        "<html lang='pt-BR'>",
        "<head>",
        '<meta charset="utf-8">',
        "<title>Directory listing</title>",
        "<style>",
        "body { font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; background:#f4f6f8; color:#222; padding:24px; }",
        "h1 { margin-bottom:8px; }",
        "hr { border:0; border-top:1px solid #ddd; margin:12px 0 20px; }",
        "pre { background:#fff; padding:14px; border-radius:10px; box-shadow:0 4px 14px rgba(0,0,0,.08); line-height:1.6; }",
        "a { color:#0066cc; text-decoration:none; font-weight:500; }",
        "a:hover { text-decoration:underline; }",
        "#search { padding:8px 12px; width:320px; border-radius:6px; border:1px solid #ccc; margin-bottom:16px; }",
        ".voltar { display:inline-block; margin-bottom:16px; padding:6px 14px; border-radius:999px; border:1px solid #0066cc; color:#0066cc; transition:.2s; }",
        ".voltar:hover { background:#0066cc; color:#fff; text-decoration: none;}",
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
        if item.is_dir() and any(p.is_relative_to(item) for p in pastas_com_zip):
            linha = f'📁 <a href="./{item.name}/index.html">{item.name}/</a>'
        elif item.suffix.lower() == ".zip":
            linha = f'📦 <a href="./{item.name}">{item.name}</a>'
        else:
            continue
        linhas_html.append(linha)
        itens.append([remover_acentos(item.name), linha])
    linhas_html.extend([
        "</pre>",
        "<script>",
        f"const items = {itens};",
        "const input = document.getElementById('search');",
        "const listing = document.getElementById('listing');",
        "input.addEventListener('input', () => {",
        " const t = input.value.normalize('NFD').replace(/\\p{Diacritic}/gu,'').toLowerCase();",
        " listing.innerHTML = items.filter(i=>i[0].includes(t)).map(i=>i[1]).join('\\n');",
        "});",
        "</script>",
        "</body>",
        "</html>",
    ])
    index.write_text("\n".join(linhas_html), encoding="utf-8")
    print(f"✔ index atualizado: {pasta}")

        # Bloco externo Kodi
    if pasta == raiz:
        content = index.read_text(encoding="utf-8")
        content = re.sub(
            r'<!-- REPOSITORIO KODI \(FORA DO HTML\) -->.*?</div>',
            '',
            content,
            flags=re.DOTALL
        )
        if repos_recentes:
            bloco = [
                "",
                "<!-- REPOSITORIO KODI (FORA DO HTML) -->",
                '<div id="Repositorio-KODI" style="display:none">',
                "<table>",
            ]
            for repo in repos_recentes:
                rel = repo.relative_to(raiz).as_posix()
                bloco.append(f'<tr><td><a href="{rel}">{rel}</a></td></tr>')
            bloco += ["</table>", "</div>"]
            content += "\n" + "\n".join(bloco)
        index.write_text(content, encoding="utf-8")

# Bottom-up
def varrer_bottom_up(pasta, raiz, *args):
    for sub in pasta.iterdir():
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
        repos_recentes
    )
