from pathlib import Path
import re


def extrair_versao(nome: str):
    m = re.search(r"vkkodi\.repo-(\d+(?:\.\d+)*)\.zip", nome)
    if not m:
        return ()
    return tuple(map(int, m.group(1).split(".")))


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


def pasta_tem_zip_recursivo(pasta: Path) -> bool:
    return any(
        f.is_file() and f.suffix.lower() == ".zip"
        for f in pasta.rglob("*.zip")
    )


def remover_index_se_existe(pasta: Path):
    index = pasta / "index.html"
    if index.exists():
        index.unlink()
        print(f"🧹 removido: {index}")


def gerar_index(pasta: Path, raiz: Path, repos_recentes: list[Path]):
    tem_zip_em_qualquer_nivel = pasta_tem_zip_recursivo(pasta)

    # ❌ remove index se não houver zip nem abaixo (exceto raiz)
    if pasta != raiz and not tem_zip_em_qualquer_nivel:
        remover_index_se_existe(pasta)
        return

    # ❌ remove index da raiz se não existir zip nenhum no repo
    if pasta == raiz and not repos_recentes:
        remover_index_se_existe(pasta)
        return

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

    for item in sorted(pasta.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if item.name.startswith(".") or item.name == "index.html":
            continue

        if item.is_dir():
            linhas.append(
                f'<a href="./{item.name}/index.html">{item.name}/</a>'
            )

        elif item.is_file() and item.suffix.lower() == ".zip":
            linhas.append(f'<a href="./{item.name}">{item.name}</a>')

    linhas.extend([
        "</pre>",
        "</body>",
        "</html>",
    ])

    # 🔥 tabela oculta apenas na raiz
    if pasta == raiz and repos_recentes:
        linhas.append("")
        linhas.append('<div id="Repositorio-KODI" style="display:none">')
        linhas.append("<table>")
        for repo in repos_recentes:
            rel = repo.relative_to(raiz).as_posix()
            linhas.append(f'<tr><td><a href="{rel}">{rel}</a></td></tr>')
        linhas.append("</table>")
        linhas.append("</div>")

    (pasta / "index.html").write_text("\n".join(linhas), encoding="utf-8")
    print(f"✔ index atualizado: {pasta}")


def varrer(pasta: Path, raiz: Path, repos_recentes: list[Path]):
    for sub in pasta.iterdir():
        if sub.is_dir() and not sub.name.startswith("."):
            varrer(sub, raiz, repos_recentes)

    gerar_index(pasta, raiz, repos_recentes)


if __name__ == "__main__":
    raiz = Path(".")

    repos_recentes = encontrar_repos_mais_recentes(raiz)

    varrer(raiz, raiz, repos_recentes)

    # 🔁 garante que a raiz reflita o estado final
    repos_recentes = encontrar_repos_mais_recentes(raiz)
    gerar_index(raiz, raiz, repos_recentes)
