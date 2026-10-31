
from pathlib import Path
from datetime import datetime
import shutil
import json
import os


# =====================================================
# CONFIGURAÇÕES
# =====================================================

PASTA_BASE = Path(__file__).parent

PASTA_ORGANIZADA = PASTA_BASE / "arquivos_organizados"

PASTA_RELATORIOS = PASTA_BASE / "relatorios"

ARQUIVO_HISTORICO = PASTA_BASE / "historico_operacoes.json"


# =====================================================
# CATEGORIAS
# =====================================================

CATEGORIAS = {
    "Imagens": [
        ".jpg", ".jpeg", ".png", ".gif", ".webp",
        ".bmp", ".tiff", ".tif", ".svg", ".ico", ".heic"
    ],
    "Documentos": [
        ".doc", ".docx", ".odt", ".txt", ".rtf",
        ".odf", ".pages"
    ],
    "PDFs": [".pdf"],
    "Planilhas": [
        ".xls", ".xlsx", ".xlsm", ".csv", ".ods", ".tsv"
    ],
    "Apresentacoes": [
        ".ppt", ".pptx", ".odp", ".key"
    ],
    "Compactados": [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"
    ],
    "Videos": [
        ".mp4", ".avi", ".mkv", ".mov", ".wmv",
        ".webm", ".mpeg", ".mpg", ".m4v"
    ],
    "Audios": [
        ".mp3", ".wav", ".ogg", ".flac", ".aac",
        ".m4a", ".wma", ".opus"
    ],
    "Codigos": [
        ".py", ".cs", ".html", ".css", ".js",
        ".ts", ".java", ".cpp", ".c", ".h",
        ".php", ".json", ".xml", ".sql", ".bat",
        ".ps1", ".sh", ".jsx", ".tsx"
    ],
    "Executaveis": [
        ".exe", ".msi", ".app", ".deb", ".rpm"
    ],
    "Aplicativos": [
        ".apk", ".appx", ".msix"
    ],
    "Extensoes": [".vsix"],
    "Torrents": [".torrent"],
}


# =====================================================
# CANCELAMENTO
# =====================================================

def cancelamento_solicitado(evento):

    return evento is not None and evento.is_set()


def informar_progresso(callback, fase, atual, total=0, nome=""):

    if callback:
        callback(fase, atual, total, nome)


# =====================================================
# IDENTIFICAÇÃO
# =====================================================

def arquivo_temporario(arquivo):

    nome = arquivo.name.lower()

    if nome.startswith("~$"):
        return True

    extensoes_temporarias = [
        ".tmp", ".temp", ".parts", ".crdownload", ".part"
    ]

    return arquivo.suffix.lower() in extensoes_temporarias


def identificar_categoria(arquivo):

    extensao = arquivo.suffix.lower()

    for categoria, extensoes in CATEGORIAS.items():

        if extensao in extensoes:
            return categoria

    return "Outros"


# =====================================================
# CONTROLE DE NOMES E CONFLITOS
# =====================================================

def chave_caminho(caminho):

    return os.path.normcase(
        str(Path(caminho).resolve())
    )


def gerar_destino_livre(
    destino_original,
    reservados=None,
    nomes_originais=None
):

    if reservados is None:
        reservados = set()

    if nomes_originais is None:
        nomes_originais = set()

    destino_original = Path(destino_original)

    # Primeiro tenta manter o nome original.

    chave = chave_caminho(destino_original)

    if (
        not destino_original.exists()
        and chave not in reservados
    ):

        reservados.add(chave)

        return destino_original

    # Se já existir, procura outro nome.

    contador = 1

    while True:

        novo_nome = (
            f"{destino_original.stem}_{contador}"
            f"{destino_original.suffix}"
        )

        novo_destino = (
            destino_original.parent / novo_nome
        )

        chave = chave_caminho(novo_destino)

        if (
            not novo_destino.exists()
            and chave not in reservados
            and chave not in nomes_originais
        ):

            reservados.add(chave)

            return novo_destino

        contador += 1


def planejar_destinos(arquivos, origem):

    """
    Define antecipadamente os destinos de todos os arquivos.

    Evita que arquivos com nomes iguais sejam direcionados
    para o mesmo caminho.

    Exemplo:
    foto.jpg
    foto_1.jpg
    foto_2.jpg
    """

    destinos = {}

    reservados = set()
    nomes_originais = set()

    # Primeiro registra todos os destinos naturais.
    # Assim, um arquivo chamado foto_1.jpg não perde
    # seu nome para outro arquivo chamado foto.jpg.

    for arquivo in arquivos:

        categoria = identificar_categoria(arquivo)

        destino_original = (
            origem / categoria / arquivo.name
        )

        nomes_originais.add(
            chave_caminho(destino_original)
        )

    # Agora define um destino exclusivo para cada arquivo.

    for arquivo in arquivos:

        categoria = identificar_categoria(arquivo)

        destino_original = (
            origem / categoria / arquivo.name
        )

        chave = chave_caminho(destino_original)

        if (
            not destino_original.exists()
            and chave not in reservados
        ):

            destinos[arquivo] = destino_original

            reservados.add(chave)

        else:

            destinos[arquivo] = gerar_destino_livre(
                destino_original,
                reservados,
                nomes_originais
            )

    return destinos


# =====================================================
# LISTAR ARQUIVOS
# =====================================================

def listar_arquivos(
    origem,
    incluir_subpastas=False,
    evento_cancelamento=None,
    callback_progresso=None
):

    origem = Path(origem).resolve()

    if incluir_subpastas:
        arquivos = origem.rglob("*")
    else:
        arquivos = origem.iterdir()

    resultado = []
    analisados = 0

    categorias_existentes = set(CATEGORIAS.keys())
    categorias_existentes.add("Outros")

    for arquivo in arquivos:

        if cancelamento_solicitado(evento_cancelamento):
            break

        analisados += 1

        if analisados % 25 == 0:

            informar_progresso(
                callback_progresso,
                "listando",
                analisados,
                0,
                arquivo.name
            )

        try:

            if not arquivo.is_file():
                continue

            if arquivo.is_symlink():
                continue

            caminho = arquivo.resolve()

            relativo = caminho.relative_to(origem)

            # Não reprocessar arquivos já organizados.

            if (
                len(relativo.parts) > 1
                and relativo.parts[0] in categorias_existentes
            ):
                continue

            resultado.append(arquivo)

        except (OSError, ValueError):
            continue

    informar_progresso(
        callback_progresso,
        "listagem_finalizada",
        analisados,
        analisados,
        ""
    )

    return sorted(
        resultado,
        key=lambda arquivo: str(arquivo).lower()
    )


# =====================================================
# FILTROS
# =====================================================

def corresponde_filtro(arquivo, categoria, filtro="Todos"):

    filtro = str(filtro).strip()

    if filtro.lower() == "todos":
        return True

    if filtro in CATEGORIAS or filtro == "Outros":
        return categoria == filtro

    extensao = filtro.lower()

    if not extensao.startswith("."):
        extensao = "." + extensao

    return arquivo.suffix.lower() == extensao


# =====================================================
# VALIDAR PASTAS
# =====================================================

def validar_pastas(origem):

    origem = Path(origem).expanduser().resolve()

    if not origem.exists():
        raise ValueError("A pasta de origem não existe.")

    if not origem.is_dir():
        raise ValueError("O caminho informado não é uma pasta.")

    return origem, origem


# =====================================================
# HISTÓRICO
# =====================================================

def carregar_historico():

    if not ARQUIVO_HISTORICO.exists():
        return []

    try:

        dados = json.loads(
            ARQUIVO_HISTORICO.read_text(encoding="utf-8")
        )

        if not isinstance(dados, list):
            raise ValueError("Formato de histórico inválido.")

        return dados

    except (OSError, json.JSONDecodeError, ValueError) as erro:

        raise RuntimeError(
            f"Não foi possível ler o histórico: {erro}"
        )


def salvar_historico(historico):

    temporario = ARQUIVO_HISTORICO.with_suffix(".tmp")

    try:

        temporario.write_text(
            json.dumps(
                historico,
                ensure_ascii=False,
                indent=4
            ),
            encoding="utf-8"
        )

        temporario.replace(ARQUIVO_HISTORICO)

    except OSError:

        if temporario.exists():
            temporario.unlink()

        raise


# =====================================================
# REGISTRAR ARQUIVO MOVIDO
# =====================================================

def registrar_movimentacao(operacao, origem, destino):

    informacoes = destino.stat()

    registro = {
        "origem": str(origem.resolve()),
        "caminho": str(destino.resolve()),
        "tamanho": informacoes.st_size,
        "modificado_ns": informacoes.st_mtime_ns
    }

    historico = carregar_historico()

    indice = next(
        (
            i for i, item in enumerate(historico)
            if item.get("id") == operacao["id"]
        ),
        None
    )

    if indice is None:

        nova_operacao = {
            "id": operacao["id"],
            "data": operacao["data"],
            "origem": operacao["origem"],
            "tipo": "movimentacao",
            "arquivos": [registro]
        }

        historico.append(nova_operacao)

    else:

        historico[indice]["arquivos"].append(registro)

    try:

        salvar_historico(historico)

    except Exception:

        # Tenta devolver o arquivo se não conseguir
        # registrar a movimentação no histórico.

        try:

            origem.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            destino.rename(origem)

        except OSError:
            pass

        raise


# =====================================================
# RELATÓRIO
# =====================================================

def salvar_relatorio(
    origem,
    modo,
    registros,
    processados,
    ignorados,
    erros
):

    PASTA_RELATORIOS.mkdir(parents=True, exist_ok=True)

    data = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    caminho = PASTA_RELATORIOS / f"relatorio_{data}.txt"

    contador = 1

    while caminho.exists():

        caminho = (
            PASTA_RELATORIOS /
            f"relatorio_{data}_{contador}.txt"
        )

        contador += 1

    linhas = [
        "RELATORIO DO ORGANIZADOR DE ARQUIVOS",
        "=" * 40,
        f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"Modo: {modo}",
        f"Pasta organizada: {origem}",
        "",
        "DETALHES",
        "-" * 40,
    ]

    linhas.extend(registros)

    linhas.extend([
        "",
        "RESUMO",
        "-" * 40,
        f"Processados: {processados}",
        f"Ignorados: {ignorados}",
        f"Erros: {erros}",
    ])

    caminho.write_text(
        "\n".join(linhas),
        encoding="utf-8"
    )

    return caminho


# =====================================================
# EXECUTAR ORGANIZAÇÃO
# =====================================================

def executar_organizacao(
    origem,
    incluir_subpastas=False,
    filtro="Todos",
    simular=False,
    evento_cancelamento=None,
    callback_progresso=None
):

    origem, destino = validar_pastas(origem)

    resultado = {
        "encontrados": 0,
        "processados": 0,
        "ignorados": 0,
        "erros": 0,
        "categorias": {},
        "registros": [],
        "arquivos": [],
        "cancelado": False,
        "modo": "Simulação" if simular else "Movimentação"
    }

    # Listagem.

    arquivos = listar_arquivos(
        origem,
        incluir_subpastas,
        evento_cancelamento,
        callback_progresso
    )

    if cancelamento_solicitado(evento_cancelamento):
        resultado["cancelado"] = True

    # Aplicar filtro.

    for indice, arquivo in enumerate(arquivos, start=1):

        if cancelamento_solicitado(evento_cancelamento):

            resultado["cancelado"] = True
            break

        if arquivo_temporario(arquivo):
            continue

        categoria = identificar_categoria(arquivo)

        if corresponde_filtro(arquivo, categoria, filtro):
            resultado["arquivos"].append(arquivo)

        if indice % 50 == 0:

            informar_progresso(
                callback_progresso,
                "filtrando",
                indice,
                len(arquivos),
                arquivo.name
            )

    resultado["encontrados"] = len(resultado["arquivos"])

    if not resultado["cancelado"] and not simular:
        carregar_historico()

    # Planejar destinos únicos antes de movimentar.
    # A simulação usa exatamente o mesmo planejamento.

    destinos_planejados = planejar_destinos(
        resultado["arquivos"],
        origem
    )

    # Identificador da operação.

    operacao = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "data": datetime.now().isoformat(timespec="seconds"),
        "origem": str(origem),
        "arquivos": []
    }

    total = resultado["encontrados"]

    # Processamento.

    for indice, arquivo in enumerate(
        resultado["arquivos"],
        start=1
    ):

        if cancelamento_solicitado(evento_cancelamento):

            resultado["cancelado"] = True
            break

        categoria = identificar_categoria(arquivo)

        destino_arquivo = destinos_planejados[arquivo]

        informar_progresso(
            callback_progresso,
            "processando",
            indice,
            total,
            arquivo.name
        )

        # Simulação.

        if simular:

            resultado["processados"] += 1

            resultado["registros"].append(
                f"[SIMULAÇÃO] {arquivo} -> {destino_arquivo}"
            )

            resultado["categorias"][categoria] = (
                resultado["categorias"].get(categoria, 0) + 1
            )

            continue

        # Evitar mover o arquivo para ele mesmo.

        try:

            if arquivo.resolve() == destino_arquivo.resolve():

                resultado["ignorados"] += 1

                resultado["registros"].append(
                    f"[IGNORADO - JÁ ORGANIZADO] {arquivo}"
                )

                continue

        except OSError:
            pass

        try:

            destino_arquivo.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            # Verificação adicional imediatamente antes
            # da movimentação.

            if destino_arquivo.exists():

                destino_arquivo = gerar_destino_livre(
                    destino_arquivo
                )

            # rename movimenta sem criar cópia.

            arquivo.rename(destino_arquivo)

            registrar_movimentacao(
                operacao,
                arquivo,
                destino_arquivo
            )

            resultado["processados"] += 1

            resultado["registros"].append(
                f"[MOVIDO] {arquivo} -> {destino_arquivo}"
            )

            if destino_arquivo.name != arquivo.name:

                resultado["registros"].append(
                    f"[NOME AJUSTADO] "
                    f"{arquivo.name} -> {destino_arquivo.name}"
                )

            resultado["categorias"][categoria] = (
                resultado["categorias"].get(categoria, 0) + 1
            )

        except (OSError, RuntimeError) as erro:

            resultado["erros"] += 1

            resultado["registros"].append(
                f"[ERRO] {arquivo}: {erro}"
            )

    if cancelamento_solicitado(evento_cancelamento):
        resultado["cancelado"] = True

    # Relatório.

    modo_relatorio = resultado["modo"]

    if resultado["cancelado"]:
        modo_relatorio += " cancelada"

    resultado["relatorio"] = salvar_relatorio(
        origem,
        modo_relatorio,
        resultado["registros"],
        resultado["processados"],
        resultado["ignorados"],
        resultado["erros"]
    )

    informar_progresso(
        callback_progresso,
        "concluido",
        resultado["processados"],
        total,
        ""
    )

    return resultado


# =====================================================
# DESFAZER ÚLTIMA ORGANIZAÇÃO
# =====================================================


def desfazer_ultima_organizacao():

    historico = carregar_historico()

    if not historico:

        return {
            "sucesso": False,
            "mensagem": "Não existe nenhuma organização para desfazer.",
            "removidos": 0,
            "ignorados": 0,
            "detalhes": []
        }

    operacao = historico[-1]

    removidos = 0
    ignorados = 0

    detalhes = []
    pendentes = []

    for registro in reversed(operacao["arquivos"]):

        arquivo = Path(registro["caminho"])

        # Novo formato: devolver ao local original.

        if registro.get("origem"):

            original = Path(registro["origem"])

            try:

                if not arquivo.exists():

                    detalhes.append(
                        f"[JÁ AUSENTE] {arquivo}"
                    )

                    continue

                if original.exists():

                    ignorados += 1
                    pendentes.append(registro)

                    detalhes.append(
                        f"[IGNORADO - ORIGINAL JÁ EXISTE] {original}"
                    )

                    continue

                informacoes = arquivo.stat()

                # Verifica somente o tamanho.
                # A validação por data foi removida.

                if informacoes.st_size != registro["tamanho"]:

                    ignorados += 1
                    pendentes.append(registro)

                    detalhes.append(
                        f"[IGNORADO - TAMANHO ALTERADO] {arquivo}"
                    )

                    continue

                original.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                arquivo.rename(original)

                removidos += 1

                detalhes.append(
                    f"[DEVOLVIDO AO LOCAL ORIGINAL] {original}"
                )

                pasta = arquivo.parent

                try:
                    pasta.rmdir()
                except OSError:
                    pass

            except OSError as erro:

                ignorados += 1
                pendentes.append(registro)

                detalhes.append(
                    f"[ERRO AO DEVOLVER] {arquivo}: {erro}"
                )

            continue

        # Compatibilidade com histórico antigo.

        try:

            destino_base = PASTA_ORGANIZADA.resolve()
            caminho = arquivo.resolve()

            if (
                caminho == destino_base
                or destino_base not in caminho.parents
            ):

                ignorados += 1
                pendentes.append(registro)

                detalhes.append(
                    f"[IGNORADO - CAMINHO INVÁLIDO] {arquivo}"
                )

                continue

            if not arquivo.exists():

                detalhes.append(
                    f"[JÁ AUSENTE] {arquivo}"
                )

                continue

            informacoes = arquivo.stat()

            # Também removida a validação por data
            # do formato antigo.

            if informacoes.st_size != registro["tamanho"]:

                ignorados += 1
                pendentes.append(registro)

                detalhes.append(
                    f"[IGNORADO - TAMANHO ALTERADO] {arquivo}"
                )

                continue

            arquivo.unlink()

            removidos += 1

            detalhes.append(
                f"[CÓPIA ANTIGA REMOVIDA] {arquivo}"
            )

            pasta = arquivo.parent

            while pasta != destino_base:

                try:
                    pasta.rmdir()
                    pasta = pasta.parent
                except OSError:
                    break

        except OSError as erro:

            ignorados += 1
            pendentes.append(registro)

            detalhes.append(
                f"[ERRO] {arquivo}: {erro}"
            )

    operacao["arquivos"] = list(reversed(pendentes))

    if not operacao["arquivos"]:
        historico.pop()

    salvar_historico(historico)

    return {
        "sucesso": True,
        "mensagem": "Operação de desfazer concluída.",
        "removidos": removidos,
        "ignorados": ignorados,
        "detalhes": detalhes
    }


# =====================================================
# EXECUÇÃO PELO TERMINAL
# =====================================================

def organizar_arquivos():

    print("\nORGANIZADOR DE ARQUIVOS - VERSÃO 3.1")
    print("-" * 45)

    entrada = input(
        "Digite o caminho da pasta que deseja organizar: "
    ).strip().strip('"')

    origem = Path(entrada).expanduser()

    try:

        validar_pastas(origem)

    except ValueError as erro:

        print(f"Erro: {erro}")
        return

    print("\n1 - Simular organização")
    print("2 - Mover arquivos")

    opcao = input("Escolha uma opção: ").strip()

    if opcao not in ("1", "2"):

        print("Opção inválida.")
        return

    subpastas = input(
        "\nIncluir subpastas? (s/n): "
    ).strip().lower() == "s"

    print("\nCATEGORIAS DISPONÍVEIS")
    print("-" * 30)

    print("Todos")

    for categoria in CATEGORIAS:
        print(categoria)

    print("Outros")

    filtro = input(
        "\nDigite a categoria ou extensão desejada: "
    ).strip() or "Todos"

    try:

        resultado = executar_organizacao(
            origem,
            incluir_subpastas=subpastas,
            filtro=filtro,
            simular=(opcao == "1")
        )

    except (ValueError, RuntimeError, OSError) as erro:

        print(f"Erro: {erro}")
        return

    for registro in resultado["registros"]:
        print(registro)

    print("\nRESUMO")
    print("-" * 40)

    print(f"Encontrados: {resultado['encontrados']}")
    print(f"Processados: {resultado['processados']}")
    print(f"Ignorados: {resultado['ignorados']}")
    print(f"Erros: {resultado['erros']}")

    if resultado["cancelado"]:
        print("Operação cancelada.")

    print("\nCATEGORIAS")

    for categoria, quantidade in sorted(
        resultado["categorias"].items()
    ):

        print(f"{categoria}: {quantidade}")

    print(f"\nRelatório: {resultado['relatorio']}")


if __name__ == "__main__":
    organizar_arquivos()
