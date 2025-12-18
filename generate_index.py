from pathlib import Path


def extrair_versao(nome: str):
    partes = nome.replace("vkkodi.repo-", "").replace(".zip", "")
    return tuple(int(p) for p in partes.split(".") if p.isdigit())


def encontrar_repos_mais_recentes(raiz: Path):
    encontrados = []

    for item in raiz.rglob("vkkodi.repo-*.zip"):
        versao = extrair_versao(item.name)
        if versao:
            encontrados.append((versao, item))

    if not encontrados:
        return []

    # descobre a maior versão
    maior_versao = max(v for v, _ in encontrados)

    # retorna TODOS os zips dessa versão
    return [item for v, item in encontrados if v == maior_versao]


def gerar_index_em_pasta(pasta: Path, raiz: Path, repos_recentes: list[Path]):
    itens = sorted(
        pasta.iterdir(),
        key=lambda x: (x.is_file(), x.name.lower())
    )

    linhas = [
        "<html>",
        "<head>",
        '<meta charset="utf-8">',
        "<title>Directory listing</title>",
        "</head>",
        "<body>",
        "<h1>Directory listing</h1>",
        "<hr/>",
        "<pre>",
    ]

    if pasta != raiz:
        linhas.append('<a href="../index.html">..</a>')

    for item in itens:
        if item.name.startswith(".") or item.name == "index.html":
            continue

        if item.is_dir():
            linhas.append(
                f'<a href="./{item.name}/index.html">{item.name}</a>'
            )

        elif item.is_file() and item.suffix.lower() == ".zip":
            linhas.append(
                f'<a href="./{item.name}">{item.name}</a>'
            )

    # FECHA HTML NORMAL
    linhas.append("</pre>")
    linhas.append("</body>")
    linhas.append("</html>")

    # 🔥 TABELA OCULTA FORA DO HTML (SÓ NA RAIZ)
    if pasta == raiz and repos_recentes:
        linhas.append('<div id="div" style="display:none">')
        linhas.append("<table>")

        for repo in repos_recentes:
            rel = repo.relative_to(raiz).as_posix()
            linhas.append(
                f'<tr><td><a href="{rel}">{rel}</a></td></tr>'
            )

        linhas.append("</table>")
        linhas.append("</div>")

    (pasta / "index.html").write_text(
        "\n".join(linhas),
        encoding="utf-8"
    )

    print(f"✔ index gerado em: {pasta}")


def varrer_recursivo(pasta: Path, raiz: Path, repos_recentes: list[Path]):
    gerar_index_em_pasta(pasta, raiz, repos_recentes)

    for item in pasta.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            varrer_recursivo(item, raiz, repos_recentes)


if __name__ == "__main__":
    raiz = Path(".")
    repos_recentes = encontrar_repos_mais_recentes(raiz)
    varrer_recursivo(raiz, raiz, repos_recentes)
