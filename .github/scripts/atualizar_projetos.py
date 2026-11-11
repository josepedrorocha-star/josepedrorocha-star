"""
Atualiza a secção "Os meus projetos · My projects" do README.md.

- Projetos públicos: aparecem com nome, descrição, ligação e data.
- Projetos privados: aparece só o número total (sem nomes nem descrições).

Para contar os privados é preciso um token pessoal guardado no segredo
PROFILE_TOKEN. Sem ele, a lista dos públicos funciona na mesma e a linha
dos privados simplesmente não aparece.
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime

UTILIZADOR = "josepedrorocha-star"
README = "README.md"
INICIO = "<!-- PROJETOS:INICIO -->"
FIM = "<!-- PROJETOS:FIM -->"
# Repositórios que nunca aparecem na lista (a própria página de perfil).
IGNORAR = {UTILIZADOR.lower()}
MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]


def pedir(url, token):
    cabecalhos = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "atualizar-projetos",
    }
    if token:
        cabecalhos["Authorization"] = f"Bearer {token}"
    pedido = urllib.request.Request(url, headers=cabecalhos)
    with urllib.request.urlopen(pedido) as resposta:
        return json.load(resposta)


def obter_repos(token_pessoal):
    """Devolve a lista de repositórios e se os privados estão incluídos."""
    repos, pagina = [], 1
    if token_pessoal:
        base = ("https://api.github.com/user/repos"
                "?affiliation=owner&visibility=all&per_page=100&page={}")
    else:
        base = (f"https://api.github.com/users/{UTILIZADOR}/repos"
                "?type=owner&per_page=100&page={}")
    while True:
        lote = pedir(base.format(pagina), token_pessoal)
        if not lote:
            break
        repos.extend(lote)
        pagina += 1
    return repos, bool(token_pessoal)


def data_pt(iso):
    d = datetime.strptime(iso[:10], "%Y-%m-%d")
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def limpar(texto):
    return (texto or "").replace("|", "/").replace("\n", " ").strip()


def construir_secao(repos, inclui_privados):
    proprios = [r for r in repos
                if not r.get("fork")
                and r["name"].lower() not in IGNORAR
                and r["owner"]["login"].lower() == UTILIZADOR.lower()]
    publicos = [r for r in proprios if not r.get("private")]
    privados = [r for r in proprios if r.get("private")]
    publicos.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)

    linhas = []
    if publicos:
        linhas += [
            "| Projeto · Project | Descrição · Description | Atualizado · Updated |",
            "|---|---|---|",
        ]
        for r in publicos:
            nome = f"[**{r['name']}**]({r['html_url']})"
            site = (r.get("homepage") or "").strip()
            if site:
                nome += f"<br>[▶ Abrir · Open]({site})"
            descricao = limpar(r.get("description")) or "—"
            if r.get("archived"):
                descricao += " _(arquivado · archived)_"
            linhas.append(
                f"| {nome} | {descricao} | {data_pt(r['pushed_at'])} |")
    else:
        linhas.append("_Ainda não há projetos públicos · "
                      "No public projects yet._")

    if inclui_privados and privados:
        n = len(privados)
        pt = "projeto privado" if n == 1 else "projetos privados"
        en = "private project" if n == 1 else "private projects"
        linhas += [
            "",
            f"🔒 **+{n}** {pt} em desenvolvimento · "
            f"**+{n}** {en} in progress",
        ]
    return "\n".join(linhas)


def main():
    token_pessoal = os.environ.get("PROFILE_TOKEN", "").strip()
    if len(sys.argv) > 1:  # modo de teste: ler repositórios de um ficheiro
        with open(sys.argv[1], encoding="utf-8") as f:
            repos, inclui_privados = json.load(f), True
    else:
        repos, inclui_privados = obter_repos(token_pessoal)
        privados = sum(1 for r in repos if r.get("private"))
        print(f"Chave pessoal: {'sim' if token_pessoal else 'não'} | "
              f"repositórios vistos: {len(repos)} | privados: {privados}")

    secao = construir_secao(repos, inclui_privados)
    with open(README, encoding="utf-8") as f:
        conteudo = f.read()
    padrao = re.compile(re.escape(INICIO) + r".*?" + re.escape(FIM), re.S)
    if not padrao.search(conteudo):
        sys.exit("Não encontrei as marcas PROJETOS:INICIO / PROJETOS:FIM.")
    novo = padrao.sub(lambda _: f"{INICIO}\n{secao}\n{FIM}", conteudo)
    if novo != conteudo:
        with open(README, "w", encoding="utf-8") as f:
            f.write(novo)
        print("README atualizado.")
    else:
        print("Sem alterações.")


if __name__ == "__main__":
    main()
