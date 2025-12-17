from pathlib import Path


def coletar_zips_recursivo(pasta: Path, base: Path):
    zips = []

    for item in pasta.iterdir():
        if item.name.startswith("."):
            continue

        if item.is_file() and item.suffix.lower() == ".zip":
            zips.append(item.relative_to(base).as_posix())

        elif item.is_dir():
            zips.extend(coletar_zips_recursivo(item, base))

    return zips


def gerar_index_em_pasta(pasta: Path, raiz: Path):
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

    # 🔥 TABELA OCULTA FORA DO HTML (GAMBIARRA INTENCIONAL PRO KODI)
    if pasta == raiz:
        zips = coletar_zips_recursivo(raiz, raiz)

        linhas.append('<div id="div" style="display:none">')
        linhas.append("<table>")

        for zip_path in zips:
            linhas.append(
                f'<tr><td><a href="{zip_path}">{zip_path}</a></td></tr>'
            )

        linhas.append("</table>")
        linhas.append("</div>")

    (pasta / "index.html").write_text(
        "\n".join(linhas),
        encoding="utf-8"
    )

    print(f"✔ index gerado em: {pasta}")


def varrer_recursivo(pasta: Path, raiz: Path):
    gerar_index_em_pasta(pasta, raiz)

    for item in pasta.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            varrer_recursivo(item, raiz)


if __name__ == "__main__":
    raiz = Path(".")
    varrer_recursivo(raiz, raiz)
