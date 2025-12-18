from pathlib import Path
import re


def extrair_versao(nome: str):
    m = re.search(r"vkkodi\.repo-(\d+(?:\.\d+)*)\.zip", nome)
    if not m:
        return ()
    return tuple(map(int, m.group(1).split(".")))


def encontrar_repos_mais_recentes(raiz: Path) -> list[Path]:
    encontrados: list[tuple[tuple[int, ...], Path]] = []

    for item in raiz.rglob("vkkodi.repo-*.zip"):
        versao = extrair_versao(item.name)
        if versao:
            encontrados.append((versao, item))

    if not encontrados:
        return []

    maior_versao = max(v for v, _ in encontrados)
    return [item for v, item in encontrados if v == maior_versao]


def gerar_index_em_pasta(pasta: Path, raiz: Path, repos_recentes: list[Path]):
    itens = sorted(
        pasta.iterdir(),
        key=lambda x: (not x.is_dir(), x.name.lower())
    )

    linhas = [
        "<!DOCTYPE html>",
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
                f'<a href="./{item.name}/index.html">{item.name}/</a>'
            )
        elif item.is_file() and item.suffix.lower() == ".zip":
            linhas.append(
                f'<a href="./{item.name}">{item.name}</a>'
            )

    linhas.extend([
        "</pre>",
        "</body>",
        "</html>",
    ])

    # 🔥 TABELA OCULTA FORA DO HTML (SÓ NA RAIZ)
    if pasta == raiz and repos_recentes:
        linhas.append('<div id="Repositorio-KODI" style="display:none">')
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

    print(f"✔ index gerado em: {pasta.resolve()}")


def varrer_recursivo(pasta: Path, raiz: Path, repos_recentes: list[Path]):
    gerar_index_em_pasta(pasta, raiz, repos_recentes)

    for item in pasta.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            varrer_recursivo(item, raiz, repos_recentes)


if __name__ == "__main__":
    raiz = Path(".")

    repos_recentes = encontrar_repos_mais_recentes(raiz)

    if not repos_recentes:
        print("⚠ Nenhum .zip encontrado. Nenhuma tabela oculta será gerada.")

    varrer_recursivo(raiz, raiz, repos_recentes)
