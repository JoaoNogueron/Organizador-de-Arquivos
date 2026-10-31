
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import os
import threading
import queue

import customtkinter as ctk
import organizador


class OrganizadorApp:

    def __init__(self, janela):

        self.janela = janela

        self.janela.title("Organizador de Arquivos - Versão 3.0")
        self.janela.geometry("1100x800")
        self.janela.minsize(950, 680)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.pasta_selecionada = None

        self.incluir_subpastas = tk.BooleanVar(value=False)
        self.filtro_selecionado = tk.StringVar(value="Todos")

        self.evento_cancelamento = None
        self.fila = queue.Queue()
        self.operacao_em_andamento = False

        self.criar_interface()

    # =================================================
    # INTERFACE
    # =================================================

    def criar_interface(self):

        self.janela.configure(fg_color="#17212F")

        ctk.CTkLabel(
            self.janela,
            text="ORGANIZADOR DE ARQUIVOS NOGUERON",
            font=("Arial", 25, "bold"),
            text_color="white"
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self.janela,
            text="Gerencie e organize seus arquivos automaticamente",
            font=("Arial", 12),
            text_color="#AABBD0"
        ).pack(pady=(0, 18))

        # Seleção da pasta

        painel_pasta = ctk.CTkFrame(
            self.janela,
            fg_color="#263548",
            corner_radius=14
        )

        painel_pasta.pack(
            fill="x",
            padx=22,
            pady=5
        )

        painel_pasta.grid_columnconfigure(1, weight=1)

        self.botao_selecionar = ctk.CTkButton(
            painel_pasta,
            text="Selecionar pasta",
            command=self.selecionar_pasta,
            width=170,
            height=40,
            corner_radius=12,
            fg_color="#2878C7",
            hover_color="#1C5F9F",
            text_color="white",
            font=("Arial", 12, "bold")
        )

        self.botao_selecionar.grid(
            row=0,
            column=0,
            padx=12,
            pady=12
        )

        self.label_pasta = ctk.CTkLabel(
            painel_pasta,
            text="Nenhuma pasta selecionada",
            text_color="#C6D4E3",
            anchor="w"
        )

        self.label_pasta.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=10
        )

        # Opções

        painel_opcoes = ctk.CTkFrame(
            self.janela,
            fg_color="transparent"
        )

        painel_opcoes.pack(
            fill="x",
            padx=25,
            pady=12
        )

        self.check_subpastas = ctk.CTkCheckBox(
            painel_opcoes,
            text="Incluir arquivos de subpastas",
            variable=self.incluir_subpastas,
            text_color="white",
            checkbox_width=20,
            checkbox_height=20
        )

        self.check_subpastas.pack(
            side="left",
            padx=(0, 25)
        )

        ctk.CTkLabel(
            painel_opcoes,
            text="Filtrar por:",
            text_color="white"
        ).pack(side="left", padx=(0, 10))

        filtros = ["Todos", "Outros"]

        for categoria, extensoes in organizador.CATEGORIAS.items():

            filtros.append(categoria)

            for extensao in extensoes:

                if extensao not in filtros:
                    filtros.append(extensao)

        self.combo_filtro = ctk.CTkComboBox(
            painel_opcoes,
            variable=self.filtro_selecionado,
            values=filtros,
            width=200,
            height=35,
            corner_radius=10,
            state="readonly"
        )

        self.combo_filtro.pack(side="left")

        # Botões

        painel_botoes = ctk.CTkFrame(
            self.janela,
            fg_color="transparent"
        )

        painel_botoes.pack(pady=12)

        self.botao_simular = ctk.CTkButton(
            painel_botoes,
            text="SIMULAR",
            command=self.simular,
            width=155,
            height=45,
            corner_radius=14,
            fg_color="#2878C7",
            hover_color="#1C5F9F",
            text_color="white",
            font=("Arial", 12, "bold")
        )

        self.botao_simular.pack(side="left", padx=5)

        self.botao_organizar = ctk.CTkButton(
            painel_botoes,
            text="ORGANIZAR",
            command=self.organizar,
            width=155,
            height=45,
            corner_radius=14,
            fg_color="#218838",
            hover_color="#176B2B",
            text_color="white",
            font=("Arial", 12, "bold")
        )

        self.botao_organizar.pack(side="left", padx=5)

        self.botao_desfazer = ctk.CTkButton(
            painel_botoes,
            text="DESFAZER",
            command=self.desfazer,
            width=135,
            height=45,
            corner_radius=14,
            fg_color="#B7791F",
            hover_color="#925E15",
            text_color="white",
            font=("Arial", 12, "bold")
        )

        self.botao_desfazer.pack(side="left", padx=5)

        self.botao_destino = ctk.CTkButton(
            painel_botoes,
            text="ABRIR DESTINO",
            command=self.abrir_destino,
            width=145,
            height=45,
            corner_radius=14,
            fg_color="#455A75",
            hover_color="#34465D",
            text_color="white",
            font=("Arial", 12, "bold")
        )

        self.botao_destino.pack(side="left", padx=5)

        self.botao_relatorios = ctk.CTkButton(
            painel_botoes,
            text="RELATÓRIOS",
            command=self.abrir_relatorios,
            width=125,
            height=45,
            corner_radius=14,
            fg_color="#455A75",
            hover_color="#34465D",
            text_color="white",
            font=("Arial", 12, "bold")
        )

        self.botao_relatorios.pack(side="left", padx=5)

        # Cancelar

        self.botao_cancelar = ctk.CTkButton(
            self.janela,
            text="CANCELAR OPERAÇÃO",
            command=self.cancelar,
            width=220,
            height=42,
            corner_radius=14,
            fg_color="#C53030",
            hover_color="#922B2B",
            text_color="white",
            state="disabled",
            font=("Arial", 12, "bold")
        )

        self.botao_cancelar.pack(pady=(0, 12))

        # Estatísticas

        painel_stats = ctk.CTkFrame(
            self.janela,
            fg_color="transparent"
        )

        painel_stats.pack(
            fill="x",
            padx=20,
            pady=8
        )

        self.estatisticas = {}

        indicadores = [
            ("Encontrados", "encontrados"),
            ("Processados", "processados"),
            ("Ignorados", "ignorados"),
            ("Erros", "erros")
        ]

        for titulo, chave in indicadores:

            quadro = ctk.CTkFrame(
                painel_stats,
                fg_color="#263548",
                corner_radius=14
            )

            quadro.pack(
                side="left",
                fill="x",
                expand=True,
                padx=5
            )

            ctk.CTkLabel(
                quadro,
                text=titulo,
                text_color="#AABBD0",
                font=("Arial", 11)
            ).pack(pady=(9, 0))

            valor = ctk.CTkLabel(
                quadro,
                text="0",
                text_color="white",
                font=("Arial", 23, "bold")
            )

            valor.pack(pady=(0, 9))

            self.estatisticas[chave] = valor

        # Progresso

        painel_progresso = ctk.CTkFrame(
            self.janela,
            fg_color="transparent"
        )

        painel_progresso.pack(
            fill="x",
            padx=28,
            pady=10
        )

        self.label_progresso = ctk.CTkLabel(
            painel_progresso,
            text="Aguardando operação...",
            text_color="white",
            anchor="w"
        )

        self.label_progresso.pack(
            anchor="w",
            pady=(0, 6)
        )

        self.progresso = ctk.CTkProgressBar(
            painel_progresso,
            height=15,
            corner_radius=10,
            progress_color="#218838",
            fg_color="#35465B"
        )

        self.progresso.pack(fill="x")
        self.progresso.set(0)

        # Tabela

        ctk.CTkLabel(
            self.janela,
            text="ARQUIVOS ENCONTRADOS",
            font=("Arial", 14, "bold"),
            text_color="white"
        ).pack(
            anchor="w",
            padx=25,
            pady=(12, 6)
        )

        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure(
            "Treeview",
            background="#FFFFFF",
            foreground="#202936",
            rowheight=29,
            fieldbackground="#FFFFFF",
            font=("Arial", 9)
        )

        estilo.configure(
            "Treeview.Heading",
            font=("Arial", 10, "bold")
        )

        tabela_frame = ctk.CTkFrame(
            self.janela,
            fg_color="#263548",
            corner_radius=12
        )

        tabela_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 15)
        )

        colunas = (
            "nome",
            "extensao",
            "categoria",
            "situacao"
        )

        self.tabela = ttk.Treeview(
            tabela_frame,
            columns=colunas,
            show="headings"
        )

        self.tabela.heading("nome", text="Nome / Caminho relativo")
        self.tabela.heading("extensao", text="Extensão")
        self.tabela.heading("categoria", text="Categoria")
        self.tabela.heading("situacao", text="Situação")

        self.tabela.column("nome", width=450)
        self.tabela.column("extensao", width=100, anchor="center")
        self.tabela.column("categoria", width=170, anchor="center")
        self.tabela.column("situacao", width=150, anchor="center")

        barra_vertical = ttk.Scrollbar(
            tabela_frame,
            orient="vertical",
            command=self.tabela.yview
        )

        self.tabela.configure(
            yscrollcommand=barra_vertical.set
        )

        self.tabela.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(8, 0),
            pady=8
        )

        barra_vertical.pack(
            side="right",
            fill="y",
            padx=5,
            pady=8
        )

        self.tabela.tag_configure("sucesso", foreground="#218838")
        self.tabela.tag_configure("ignorado", foreground="#B7791F")
        self.tabela.tag_configure("erro", foreground="#C53030")

    # =================================================
    # ESTATÍSTICAS
    # =================================================

    def atualizar_estatisticas(
        self,
        encontrados,
        processados,
        ignorados,
        erros
    ):

        valores = {
            "encontrados": encontrados,
            "processados": processados,
            "ignorados": ignorados,
            "erros": erros
        }

        for chave, valor in valores.items():
            self.estatisticas[chave].configure(text=str(valor))

    # =================================================
    # LIMPAR TELA
    # =================================================

    def limpar_tela(self):

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        self.atualizar_estatisticas(0, 0, 0, 0)

        self.progresso.stop()
        self.progresso.configure(mode="determinate")
        self.progresso.set(0)

    # =================================================
    # SELECIONAR PASTA
    # =================================================

    def selecionar_pasta(self):

        if self.operacao_em_andamento:
            return

        pasta = filedialog.askdirectory(
            title="Selecione a pasta que deseja organizar"
        )

        if pasta:

            self.pasta_selecionada = Path(pasta)

            self.label_pasta.configure(
                text=str(self.pasta_selecionada)
            )

            self.limpar_tela()

            self.label_progresso.configure(
                text="Pasta selecionada. Pronto para começar."
            )

    # =================================================
    # CONTROLE DOS BOTÕES
    # =================================================

    def definir_estado_botoes(self, ocupado):

        estado = "disabled" if ocupado else "normal"

        self.botao_simular.configure(state=estado)
        self.botao_organizar.configure(state=estado)
        self.botao_desfazer.configure(state=estado)
        self.botao_destino.configure(state=estado)
        self.botao_relatorios.configure(state=estado)
        self.botao_selecionar.configure(state=estado)

        self.combo_filtro.configure(
            state="disabled" if ocupado else "readonly"
        )

        self.check_subpastas.configure(state=estado)

        self.botao_cancelar.configure(
            state="normal" if ocupado else "disabled"
        )

    # =================================================
    # INICIAR OPERAÇÃO
    # =================================================

    def executar(self, simular=False):

        if self.operacao_em_andamento:
            return

        if not self.pasta_selecionada:

            messagebox.showwarning(
                "Atenção",
                "Selecione uma pasta primeiro."
            )

            return

        origem = self.pasta_selecionada
        incluir_subpastas = self.incluir_subpastas.get()
        filtro = self.filtro_selecionado.get()

        try:

            organizador.validar_pastas(origem)

        except (ValueError, OSError) as erro:

            messagebox.showerror("Erro", str(erro))
            return

        if not simular:

            confirmar = messagebox.askyesno(
                "Confirmar organização",

                f"Pasta que será organizada:\n{origem}\n\n"
                f"Filtro: {filtro}\n"
                f"Incluir subpastas: {'Sim' if incluir_subpastas else 'Não'}\n\n"
                "ATENÇÃO: os arquivos serão MOVIDOS.\n"
                "Não serão criadas cópias.\n"
                "As pastas das categorias serão criadas dentro da pasta selecionada.\n\n"
                "Deseja continuar?"
            )

            if not confirmar:
                return

        self.limpar_tela()

        self.evento_cancelamento = threading.Event()
        self.operacao_em_andamento = True

        self.definir_estado_botoes(True)

        self.label_progresso.configure(
            text="Preparando operação..."
        )

        self.progresso.configure(mode="indeterminate")
        self.progresso.start()

        thread = threading.Thread(
            target=self.trabalhador,
            args=(
                origem,
                incluir_subpastas,
                filtro,
                simular,
                self.evento_cancelamento
            ),
            daemon=True
        )

        thread.start()

        self.janela.after(100, self.processar_fila)

    # =================================================
    # TRABALHADOR
    # =================================================

    def trabalhador(
        self,
        origem,
        incluir_subpastas,
        filtro,
        simular,
        evento
    ):

        def progresso_callback(fase, atual, total, nome):

            self.fila.put((
                "progresso",
                fase,
                atual,
                total,
                nome
            ))

        try:

            resultado = organizador.executar_organizacao(
                origem,
                incluir_subpastas=incluir_subpastas,
                filtro=filtro,
                simular=simular,
                evento_cancelamento=evento,
                callback_progresso=progresso_callback
            )

            self.fila.put(("resultado", resultado))

        except Exception as erro:

            self.fila.put(("erro", str(erro)))

    # =================================================
    # ATUALIZAR INTERFACE
    # =================================================

    def processar_fila(self):

        try:

            while True:

                mensagem = self.fila.get_nowait()

                tipo = mensagem[0]

                if tipo == "progresso":

                    _, fase, atual, total, nome = mensagem

                    if fase == "listando":

                        self.progresso.configure(mode="indeterminate")
                        self.progresso.start()

                        self.label_progresso.configure(
                            text=f"Analisando pasta... {atual} itens verificados. {nome}"
                        )

                    elif fase == "listagem_finalizada":

                        self.progresso.stop()

                        self.label_progresso.configure(
                            text=f"Listagem concluída: {atual} itens encontrados."
                        )

                    elif fase == "filtrando":

                        self.label_progresso.configure(
                            text=f"Aplicando filtros: {atual} de {total}"
                        )

                    elif fase == "processando":

                        self.progresso.stop()
                        self.progresso.configure(mode="determinate")

                        percentual = (
                            atual / total if total else 0
                        )

                        self.progresso.set(percentual)

                        self.label_progresso.configure(
                            text=f"Processando: {atual} de {total} — {nome}"
                        )

                elif tipo == "resultado":

                    self.progresso.stop()

                    self.finalizar_operacao(mensagem[1])

                    return

                elif tipo == "erro":

                    self.progresso.stop()

                    self.operacao_em_andamento = False
                    self.definir_estado_botoes(False)

                    self.botao_cancelar.configure(
                        text="CANCELAR OPERAÇÃO"
                    )

                    self.label_progresso.configure(
                        text="A operação não pôde ser concluída."
                    )

                    messagebox.showerror(
                        "Erro na operação",
                        mensagem[1]
                    )

                    return

        except queue.Empty:
            pass

        if self.operacao_em_andamento:
            self.janela.after(100, self.processar_fila)

    # =================================================
    # CANCELAR
    # =================================================

    def cancelar(self):

        if not self.operacao_em_andamento:
            return

        if self.evento_cancelamento:
            self.evento_cancelamento.set()

        self.botao_cancelar.configure(
            state="disabled",
            text="CANCELANDO..."
        )

        self.label_progresso.configure(
            text="Solicitação de cancelamento enviada. Aguarde..."
        )

    # =================================================
    # FINALIZAR
    # =================================================

    def finalizar_operacao(self, resultado):

        self.operacao_em_andamento = False

        self.definir_estado_botoes(False)

        self.botao_cancelar.configure(
            text="CANCELAR OPERAÇÃO"
        )

        encontrados = resultado["encontrados"]
        processados = resultado["processados"]
        ignorados = resultado["ignorados"]
        erros = resultado["erros"]

        self.atualizar_estatisticas(
            encontrados,
            processados,
            ignorados,
            erros
        )

        registros = resultado["registros"]

        for arquivo in resultado["arquivos"]:

            categoria = organizador.identificar_categoria(arquivo)
            extensao = arquivo.suffix.lower() or "Sem extensão"

            try:

                nome_exibido = str(
                    arquivo.relative_to(self.pasta_selecionada.resolve())
                )

            except ValueError:

                nome_exibido = arquivo.name

            situacao = "NÃO PROCESSADO"
            tag = "ignorado"

            for registro in registros:

                if registro.startswith(f"[SIMULAÇÃO] {arquivo} ->"):

                    situacao = "SIMULAÇÃO"
                    tag = "sucesso"
                    break

                elif registro.startswith(f"[MOVIDO] {arquivo} ->"):

                    situacao = "MOVIDO"
                    tag = "sucesso"
                    break

                elif registro.startswith(
                    f"[IGNORADO - NOME JÁ EXISTENTE] {arquivo}"
                ):

                    situacao = "JÁ EXISTE"
                    tag = "ignorado"
                    break

                elif registro.startswith(
                    f"[IGNORADO - JÁ ORGANIZADO] {arquivo}"
                ):

                    situacao = "JÁ ORGANIZADO"
                    tag = "ignorado"
                    break

                elif registro.startswith(f"[ERRO] {arquivo}:"):

                    situacao = "ERRO"
                    tag = "erro"
                    break

            self.tabela.insert(
                "",
                "end",
                values=(
                    nome_exibido,
                    extensao,
                    categoria,
                    situacao
                ),
                tags=(tag,)
            )

        self.progresso.configure(mode="determinate")
        self.progresso.set(1 if encontrados else 0)

        modo = resultado["modo"]

        if resultado["cancelado"]:

            self.label_progresso.configure(
                text=f"{modo} cancelada. {processados} arquivo(s) processado(s)."
            )

            titulo = "Operação cancelada"

        else:

            self.label_progresso.configure(
                text=f"{modo} concluída. {encontrados} arquivo(s) encontrado(s)."
            )

            titulo = "Operação concluída"

        resumo = (
            f"Operação: {modo}\n\n"
            f"Encontrados: {encontrados}\n"
            f"Processados: {processados}\n"
            f"Ignorados: {ignorados}\n"
            f"Erros: {erros}\n\n"
        )

        if resultado["cancelado"]:
            resumo += "A operação foi cancelada pelo usuário.\n\n"

        resumo += "CATEGORIAS:\n"

        for categoria, quantidade in sorted(
            resultado["categorias"].items()
        ):

            resumo += f"{categoria}: {quantidade}\n"

        resumo += f"\nRelatório salvo em:\n{resultado['relatorio']}"

        if resultado["cancelado"]:
            messagebox.showwarning(titulo, resumo)

        else:
            messagebox.showinfo(titulo, resumo)

    # =================================================
    # SIMULAR E ORGANIZAR
    # =================================================

    def simular(self):
        self.executar(simular=True)

    def organizar(self):
        self.executar(simular=False)

    # =================================================
    # DESFAZER
    # =================================================

    def desfazer(self):

        if self.operacao_em_andamento:
            return

        try:

            historico = organizador.carregar_historico()

        except RuntimeError as erro:

            messagebox.showerror("Erro no histórico", str(erro))
            return

        if not historico:

            messagebox.showinfo(
                "Histórico",
                "Não existe nenhuma organização para desfazer."
            )

            return

        ultima = historico[-1]
        quantidade = len(ultima.get("arquivos", []))

        confirmar = messagebox.askyesno(
            "Confirmar desfazer",

            "Deseja reverter a última operação?\n\n"
            f"Data: {ultima.get('data', 'Não informada')}\n"
            f"Arquivos registrados: {quantidade}\n\n"
            "Os arquivos movimentados serão devolvidos "
            "aos seus locais originais.\n\n"
            "Arquivos alterados ou com conflitos serão preservados."
        )

        if not confirmar:
            return

        try:

            resultado = organizador.desfazer_ultima_organizacao()

        except (RuntimeError, OSError, KeyError, ValueError) as erro:

            messagebox.showerror("Erro ao desfazer", str(erro))
            return

        self.atualizar_estatisticas(
            quantidade,
            resultado["removidos"],
            resultado["ignorados"],
            0
        )

        self.label_progresso.configure(
            text="Operação de desfazer concluída."
        )

        detalhes = resultado.get("detalhes", [])
        texto_detalhes = "\n".join(detalhes[:15])

        if len(detalhes) > 15:

            texto_detalhes += (
                f"\n... e mais {len(detalhes) - 15} registro(s)."
            )

        mensagem = (
            f"{resultado['mensagem']}\n\n"
            f"Devolvidos ou removidos: {resultado['removidos']}\n"
            f"Ignorados: {resultado['ignorados']}\n\n"
            f"DETALHES:\n{texto_detalhes}"
        )

        if resultado["ignorados"] > 0:

            messagebox.showwarning(
                "Desfazer com pendências",
                mensagem
            )

        else:

            messagebox.showinfo(
                "Desfazer concluído",
                mensagem
            )

    # =================================================
    # ABRIR DESTINO
    # =================================================

    def abrir_destino(self):

        if not self.pasta_selecionada:

            messagebox.showwarning(
                "Atenção",
                "Selecione uma pasta primeiro."
            )

            return

        destino = self.pasta_selecionada

        if not destino.exists():

            messagebox.showerror(
                "Erro",
                "A pasta selecionada não existe mais."
            )

            return

        try:

            os.startfile(str(destino))

        except OSError as erro:

            messagebox.showerror(
                "Erro",
                f"Não foi possível abrir a pasta:\n{erro}"
            )

    # =================================================
    # RELATÓRIOS
    # =================================================

       # =================================================
    # RELATÓRIOS
    # =================================================

    def abrir_relatorios(self):

        pasta = organizador.PASTA_RELATORIOS
        pasta.mkdir(parents=True, exist_ok=True)

        janela_relatorios = ctk.CTkToplevel(self.janela)

        janela_relatorios.transient(self.janela)
        janela_relatorios.lift()
        janela_relatorios.focus_force()
        janela_relatorios.attributes("-topmost", True)

        janela_relatorios.after(
            300,
            lambda: janela_relatorios.attributes("-topmost", False)
            if janela_relatorios.winfo_exists()
            else None
        )

        janela_relatorios.title("Histórico de Relatórios")
        janela_relatorios.geometry("900x580")
        janela_relatorios.configure(fg_color="#17212F")

        ctk.CTkLabel(
            janela_relatorios,
            text="HISTÓRICO DE RELATÓRIOS",
            font=("Arial", 20, "bold"),
            text_color="white"
        ).pack(pady=15)

        painel = ctk.CTkFrame(
            janela_relatorios,
            fg_color="#263548",
            corner_radius=14
        )

        painel.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        lista_frame = ctk.CTkFrame(
            painel,
            fg_color="transparent"
        )

        lista_frame.pack(
            side="left",
            fill="y",
            padx=10,
            pady=10
        )

        ctk.CTkLabel(
            lista_frame,
            text="Relatórios disponíveis",
            text_color="white"
        ).pack(pady=5)

        lista = tk.Listbox(
            lista_frame,
            width=35,
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#202936",
            selectbackground="#2878C7"
        )

        lista.pack(
            side="left",
            fill="y"
        )

        visualizacao = ctk.CTkFrame(
            painel,
            fg_color="transparent"
        )

        visualizacao.pack(
            side="right",
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        ctk.CTkLabel(
            visualizacao,
            text="Conteúdo do relatório",
            text_color="white"
        ).pack(pady=5)

        texto = tk.Text(
            visualizacao,
            wrap="word",
            font=("Consolas", 10),
            bg="white",
            fg="#202936",
            padx=10,
            pady=10
        )

        texto.pack(
            fill="both",
            expand=True
        )

        texto.config(state="disabled")

        # Carregar relatórios

        relatorios = sorted(
            pasta.glob("relatorio_*.txt"),
            key=lambda arquivo: arquivo.stat().st_mtime,
            reverse=True
        )

        for relatorio in relatorios:
            lista.insert("end", relatorio.name)

        # Mostrar relatório selecionado

        def mostrar_relatorio(event):

            selecao = lista.curselection()

            if not selecao:
                return

            indice = selecao[0]

            if indice >= len(relatorios):
                return

            arquivo = relatorios[indice]

            try:

                conteudo = arquivo.read_text(encoding="utf-8")

                texto.config(state="normal")
                texto.delete("1.0", "end")
                texto.insert("1.0", conteudo)
                texto.config(state="disabled")

            except OSError as erro:

                messagebox.showerror(
                    "Erro",
                    f"Não foi possível abrir o relatório:\n{erro}"
                )

        lista.bind("<<ListboxSelect>>", mostrar_relatorio)

        if not relatorios:
            lista.insert("end", "Nenhum relatório encontrado")

        # =============================================
        # COPIAR RELATÓRIO
        # =============================================

        def copiar_relatorio():

            selecao = lista.curselection()

            if not selecao:

                messagebox.showwarning(
                    "Atenção",
                    "Selecione um relatório antes de copiar."
                )

                return

            indice = selecao[0]

            if indice >= len(relatorios):
                return

            arquivo = relatorios[indice]

            try:

                conteudo = arquivo.read_text(encoding="utf-8")

                janela_relatorios.clipboard_clear()

                janela_relatorios.clipboard_append(conteudo)

                janela_relatorios.update()

                messagebox.showinfo(
                    "Relatório copiado",
                    "Relatório copiado para a área de transferência!\n\n"
                    "Agora você pode colar o conteúdo onde desejar."
                )

            except OSError as erro:

                messagebox.showerror(
                    "Erro",
                    f"Não foi possível copiar o relatório:\n{erro}"
                )

        # =============================================
        # PAINEL DE BOTÕES
        # =============================================

        painel_botoes = ctk.CTkFrame(
            janela_relatorios,
            fg_color="transparent"
        )

        painel_botoes.pack(pady=12)

        # Botão copiar

        ctk.CTkButton(
            painel_botoes,
            text="COPIAR RELATÓRIO",
            width=190,
            height=42,
            corner_radius=12,
            fg_color="#218838",
            hover_color="#176B2B",
            text_color="white",
            font=("Arial", 12, "bold"),
            command=copiar_relatorio
        ).pack(side="left", padx=8)

        # Botão fechar

        ctk.CTkButton(
            painel_botoes,
            text="FECHAR",
            width=150,
            height=42,
            corner_radius=12,
            fg_color="#455A75",
            hover_color="#34465D",
            text_color="white",
            font=("Arial", 12, "bold"),
            command=janela_relatorios.destroy
        ).pack(side="left", padx=8)

# =================================================
# INICIALIZAÇÃO
# =================================================

if __name__ == "__main__":

    janela = ctk.CTk()

    app = OrganizadorApp(janela)

    janela.mainloop()
