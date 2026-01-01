from pathlib import Path
import re
import unicodedata

# Utils
def extrair_versao(nome: str):
    m = re.search(r"vkkodi\.repo-(\d+(?:\.\d+)*)\.zip", nome)
    return tuple(map(int, m.group(1).split("."))) if m else ()
def pasta_tem_zip_recursivo(pasta: Path) -> bool:
    return any(p.suffix.lower() == ".zip" for p in pasta.rglob("*.zip"))
def remover_acentos(texto: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

# Repositórios mais recentes
def encontrar_repos_mais_recentes(raiz: Path) -> list[Path]:
    encontrados = []
    for item in raiz.rglob("vkkodi.repo-*.zip"):
        versao = extrair_versao(item.name)
        if versao:
            encontrados.append((versao, item))
    if not encontrados:
        return []
    maior = max(v for v, _ in encontrados)
    return [p for v, p in encontrados if v == maior]

# Index handling
def gerar_ou_remover_index(pasta: Path, raiz: Path):
    index = pasta / "index.html"
    tem_zip = pasta_tem_zip_recursivo(pasta)
    # Se não é raiz e não tem zip → remove index
    if pasta != raiz and not tem_zip:
        if index.exists():
            index.unlink()
            print(f"🧹 removido: {index}")
        return
    # Verifica qualquer zip geral na raiz para decidir manter index na raiz
    tem_zip_geral = pasta_tem_zip_recursivo(raiz)
    if pasta == raiz and not tem_zip_geral:
        if index.exists():
            index.unlink()
            print(f"🧹 removido: {index}")
        return
    # Repositórios oficiais para o bloco Kodi (vkkodi.repo-*.zip)
    repos_recentes = encontrar_repos_mais_recentes(raiz)
        # Gerar conteúdo HTML
        linhas_html = [
        "<!DOCTYPE html>",
        "<html lang='pt-BR'>",
        "<head>",
        '<meta charset="utf-8">',
        "<title>Directory listing</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; background:#f9f9f9; color:#333; padding:20px; }",
        "h1 { color:#222; }",
        "hr { border:0; border-top:1px solid #ccc; margin:10px 0; }",
        "pre { background:#fff; padding:10px; border-radius:8px; box-shadow:0 0 5px rgba(0,0,0,0.1); }",
        "a { text-decoration:none; color:#0066cc; }",
        "a:hover { text-decoration:underline; }",
        "table { border-collapse:collapse; margin-top:10px; }",
        "td { padding:5px 10px; border:1px solid #ddd; }",
        "#search { padding:6px 10px; width:300px; margin-bottom:12px; border-radius:4px; border:1px solid #ccc; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Directory listing</h1>",
        "<hr/>",
    ]
    # Botão Voltar
    if pasta != raiz:
        linhas_html.append(
            '<a href="../index.html" style="display:inline-flex; align-items:center; gap:6px; '
            'padding:6px 16px; border:1px solid #0066cc; color:#0066cc; '
            'border-radius:999px; margin-bottom:12px; text-decoration:none; '
            'font-weight:600; background:#fff; transition:0.2s;">'
            '← Voltar</a>'
            '<style>'
            'a[href="../index.html"]:hover { background:#0066cc; color:#fff; }'
            '</style>'
        )
    # Campo pesquisa
    linhas_html.append('<input type="text" id="search" placeholder="Pesquisar arquivos ou pastas...">')
    linhas_html.append("<pre id='listing'>")
    # Listagem geral
    itens = []
    for item in sorted(pasta.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if item.name.startswith(".") or item.name == "index.html":
            continue
        if item.is_dir() and pasta_tem_zip_recursivo(item):
            linha_html = f'📁 <a href="./{item.name}/index.html">{item.name}/</a>'
        elif item.suffix.lower() == ".zip":
            linha_html = f'📦 <a href="./{item.name}">{item.name}</a>'
        else:
            continue
        linhas_html.append(linha_html)
        itens.append([remover_acentos(item.name), linha_html])
    linhas_html.extend([
        "</pre>",
        "<script>",
        "const searchInput = document.getElementById('search');",
        "const listing = document.getElementById('listing');",
        f"const items = {str(itens)};",
        "function removerAcentos(str) {",
        "  return str.normalize('NFD').replace(/\\p{Diacritic}/gu, '').toLowerCase();",
        "}",
        "searchInput.addEventListener('input', () => {",
        "  const term = removerAcentos(searchInput.value);",
        "  listing.innerHTML = items",
        "    .filter(i => i[0].includes(term))",
        "    .map(i => i[1])",
        "    .join('\\n');",
        "});",
        "</script>",
        "</body>",
        "</html>",
    ])
    index.write_text("\n".join(linhas_html), encoding="utf-8")
    print(f"✔ index atualizado: {pasta}")
        # Bloco externo Kodi (apenas vkkodi.repo-*.zip)
        if pasta == raiz:
        if repos_recentes:  # só lista se houver vkkodi.repo-*.zip
            kodi_block = [
                "",
                "<!-- REPOSITORIO KODI (FORA DO HTML) -->",
                '<div id="Repositorio-KODI" style="display:none">',
                "<table>",
            ]
            for repo in repos_recentes:
                rel = repo.relative_to(raiz).as_posix()
                kodi_block.append(f'<tr><td><a href="{rel}">{rel}</a></td></tr>')
            kodi_block.extend([
                "</table>",
                "</div>"
            ])
            with index.open("a", encoding="utf-8") as f:
                f.write("\n".join(kodi_block))
            print(f"✔ bloco externo Kodi adicionado: {index}")

# Varredura bottom-up
def varrer_bottom_up(pasta: Path, raiz: Path):
    for sub in pasta.iterdir():
        if sub.is_dir() and not sub.name.startswith("."):
            varrer_bottom_up(sub, raiz)
    gerar_ou_remover_index(pasta, raiz)

# Main
if __name__ == "__main__":
    raiz = Path(".")
    varrer_bottom_up(raiz, raiz)
    gerar_ou_remover_index(raiz, raiz)