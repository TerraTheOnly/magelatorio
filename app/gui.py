import os
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageGrab, ImageTk

from app.config import (
    PREVIEW_MAX_HEIGHT,
    PREVIEW_MAX_WIDTH,
    REPORT_DEFAULT_TITLE,
    SOURCE_FILE_PATTERN,
    WINDOW_GEOMETRY,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_TITLE,
)
from app.helpers import moveItems, naturalSortKey, openFile, readSourceText
from app.models import Activity, ReportInfo, Screenshot
from app.pdf_report import buildReport


class ReportApp:
    """Assistente: passo 1 = dados e arquivos; passos seguintes = prints de cada atividade."""

    def __init__(self, root):
        self.root = root
        self.activityList = []
        self.stepIndex = 0
        self.clipboardCounter = 0
        self.previewPhoto = None

        root.title(WINDOW_TITLE)
        root.geometry(WINDOW_GEOMETRY)
        root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        root.report_callback_exception = self.handleCallbackError

        self.buildNavigationBar()
        self.frameContainer = ttk.Frame(root)
        self.frameContainer.pack(fill="both", expand=True)
        self.buildSetupFrame()
        self.buildActivityFrame()
        self.showStep()

    # ---- erros inesperados (no .exe não há console para ver o traceback)

    def handleCallbackError(self, errorType, errorValue, errorTraceback):
        details = "".join(traceback.format_exception(errorType, errorValue, errorTraceback))
        messagebox.showerror("Erro inesperado", details)

    # ---- construção da interface

    def buildNavigationBar(self):
        frameNavigation = ttk.Frame(self.root, padding=(12, 8))
        frameNavigation.pack(side="bottom", fill="x")
        self.labelStatus = ttk.Label(frameNavigation)
        self.labelStatus.pack(side="left")
        self.buttonNext = ttk.Button(frameNavigation, command=self.goNext)
        self.buttonNext.pack(side="right")
        self.buttonBack = ttk.Button(frameNavigation, text="← Voltar", command=self.goBack)
        self.buttonBack.pack(side="right", padx=(0, 8))

    def buildSetupFrame(self):
        self.frameSetup = ttk.Frame(self.frameContainer, padding=12)

        frameInfo = ttk.LabelFrame(self.frameSetup, text="Dados do relatório", padding=10)
        frameInfo.pack(fill="x")
        frameInfo.columnconfigure(1, weight=1)
        self.entryByField = {}
        fieldList = (
            ("title", "Título", REPORT_DEFAULT_TITLE),
            ("student", "Aluno", ""),
            ("course", "Disciplina", ""),
            ("teacher", "Professor", ""),
        )
        for rowIndex, (fieldKey, fieldLabel, fieldDefault) in enumerate(fieldList):
            ttk.Label(frameInfo, text=fieldLabel).grid(row=rowIndex, column=0, sticky="w", pady=3, padx=(0, 10))
            entry = ttk.Entry(frameInfo)
            entry.insert(0, fieldDefault)
            entry.grid(row=rowIndex, column=1, sticky="ew", pady=3)
            self.entryByField[fieldKey] = entry

        frameFiles = ttk.LabelFrame(self.frameSetup, text="Atividades (arquivos de código), na ordem em que aparecerão no relatório", padding=10)
        frameFiles.pack(fill="both", expand=True, pady=(12, 0))
        frameFiles.columnconfigure(0, weight=1)
        frameFiles.rowconfigure(0, weight=1)
        self.listboxActivities = tk.Listbox(frameFiles, selectmode="extended", activestyle="none")
        self.listboxActivities.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frameFiles, command=self.listboxActivities.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listboxActivities.configure(yscrollcommand=scrollbar.set)

        frameButtons = ttk.Frame(frameFiles)
        frameButtons.grid(row=0, column=2, sticky="n", padx=(10, 0))
        for buttonText, buttonCommand in (
            ("Adicionar arquivos…", self.addActivityFiles),
            ("Remover selecionados", self.removeActivityFiles),
            ("Subir", lambda: self.moveActivityFiles(-1)),
            ("Descer", lambda: self.moveActivityFiles(1)),
        ):
            ttk.Button(frameButtons, text=buttonText, command=buttonCommand).pack(fill="x", pady=2)

    def buildActivityFrame(self):
        self.frameActivity = ttk.Frame(self.frameContainer, padding=12)
        self.labelActivityTitle = ttk.Label(self.frameActivity, font=("TkDefaultFont", 13, "bold"))
        self.labelActivityTitle.pack(anchor="w", pady=(0, 8))

        panedBody = ttk.PanedWindow(self.frameActivity, orient="horizontal")
        panedBody.pack(fill="both", expand=True)

        frameCode = ttk.LabelFrame(panedBody, text="Código-fonte", padding=6)
        frameCode.rowconfigure(0, weight=1)
        frameCode.columnconfigure(0, weight=1)
        self.textCode = tk.Text(frameCode, wrap="none", state="disabled", font="TkFixedFont", width=40)
        self.textCode.grid(row=0, column=0, sticky="nsew")
        scrollbarVertical = ttk.Scrollbar(frameCode, command=self.textCode.yview)
        scrollbarVertical.grid(row=0, column=1, sticky="ns")
        scrollbarHorizontal = ttk.Scrollbar(frameCode, orient="horizontal", command=self.textCode.xview)
        scrollbarHorizontal.grid(row=1, column=0, sticky="ew")
        self.textCode.configure(yscrollcommand=scrollbarVertical.set, xscrollcommand=scrollbarHorizontal.set)
        panedBody.add(frameCode, weight=1)

        frameScreenshots = ttk.LabelFrame(panedBody, text="Prints do console (quantos quiser)", padding=6)
        frameScreenshots.columnconfigure(0, weight=1)
        frameScreenshots.rowconfigure(2, weight=1)
        self.listboxScreenshots = tk.Listbox(frameScreenshots, selectmode="extended", activestyle="none", height=6)
        self.listboxScreenshots.grid(row=0, column=0, sticky="ew")
        self.listboxScreenshots.bind("<<ListboxSelect>>", lambda event: self.showPreview())

        frameButtons = ttk.Frame(frameScreenshots)
        frameButtons.grid(row=1, column=0, sticky="ew", pady=6)
        for buttonText, buttonCommand in (
            ("Adicionar imagens…", self.addScreenshotFiles),
            ("Colar da área de transferência (Ctrl+V)", self.pasteScreenshot),
            ("Remover", self.removeScreenshots),
            ("↑", lambda: self.moveScreenshots(-1)),
            ("↓", lambda: self.moveScreenshots(1)),
        ):
            ttk.Button(frameButtons, text=buttonText, command=buttonCommand).pack(side="left", padx=(0, 4))

        self.labelPreview = ttk.Label(frameScreenshots, text="Selecione um print para visualizar", anchor="center")
        self.labelPreview.grid(row=2, column=0, sticky="nsew")
        panedBody.add(frameScreenshots, weight=1)

        for sequence in ("<Control-v>", "<Command-v>"):
            try:
                self.root.bind(sequence, lambda event: self.pasteScreenshot() if self.stepIndex > 0 else None)
            except tk.TclError:
                pass

    # ---- navegação

    def currentActivity(self):
        return self.activityList[self.stepIndex - 1]

    def showStep(self):
        stepCount = len(self.activityList) + 1
        self.frameSetup.pack_forget()
        self.frameActivity.pack_forget()
        if self.stepIndex == 0:
            self.frameSetup.pack(fill="both", expand=True)
        else:
            self.frameActivity.pack(fill="both", expand=True)
            self.loadActivityStep()
        self.labelStatus.configure(text=f"Passo {self.stepIndex + 1} de {stepCount}")
        self.buttonBack.configure(state="disabled" if self.stepIndex == 0 else "normal")
        isLastStep = self.stepIndex == len(self.activityList)
        self.buttonNext.configure(text="Gerar PDF" if isLastStep and self.stepIndex > 0 else "Avançar →")

    def goNext(self):
        if self.stepIndex == 0 and not self.activityList:
            messagebox.showwarning("Nenhuma atividade", "Adicione pelo menos um arquivo de código para continuar.")
            return
        if self.stepIndex == len(self.activityList):
            self.generateReport()
            return
        self.stepIndex += 1
        self.showStep()

    def goBack(self):
        if self.stepIndex > 0:
            self.stepIndex -= 1
            self.showStep()

    # ---- passo 1: arquivos

    def refreshActivityListbox(self, selectedIndexList=()):
        self.listboxActivities.delete(0, "end")
        for activity in self.activityList:
            self.listboxActivities.insert("end", os.path.basename(activity.sourcePath))
        for index in selectedIndexList:
            self.listboxActivities.selection_set(index)

    def addActivityFiles(self):
        pathList = filedialog.askopenfilenames(
            title="Escolha os arquivos das atividades",
            filetypes=[("Arquivos de código", SOURCE_FILE_PATTERN), ("Todos os arquivos", "*.*")],
        )
        knownPathSet = {os.path.abspath(activity.sourcePath) for activity in self.activityList}
        for path in sorted(pathList, key=lambda item: naturalSortKey(os.path.basename(item))):
            if os.path.abspath(path) not in knownPathSet:
                self.activityList.append(Activity(sourcePath=path))
        self.refreshActivityListbox()

    def removeActivityFiles(self):
        for index in sorted(self.listboxActivities.curselection(), reverse=True):
            del self.activityList[index]
        self.refreshActivityListbox()

    def moveActivityFiles(self, direction):
        newIndexList = moveItems(self.activityList, list(self.listboxActivities.curselection()), direction)
        self.refreshActivityListbox(newIndexList)

    # ---- passos 2..N: prints

    def loadActivityStep(self):
        activity = self.currentActivity()
        fileName = os.path.basename(activity.sourcePath)
        self.labelActivityTitle.configure(text=f"Atividade {self.stepIndex} de {len(self.activityList)} — {fileName}")
        try:
            sourceText = readSourceText(activity.sourcePath)
        except OSError as error:
            sourceText = f"Não foi possível ler o arquivo:\n{error}"
        self.textCode.configure(state="normal")
        self.textCode.delete("1.0", "end")
        self.textCode.insert("1.0", sourceText)
        self.textCode.configure(state="disabled")
        self.refreshScreenshotListbox()

    def refreshScreenshotListbox(self, selectedIndexList=()):
        activity = self.currentActivity()
        self.listboxScreenshots.delete(0, "end")
        for index, screenshot in enumerate(activity.screenshotList, start=1):
            self.listboxScreenshots.insert("end", f"{index}. {screenshot.label} ({screenshot.image.width}×{screenshot.image.height})")
        for index in selectedIndexList:
            self.listboxScreenshots.selection_set(index)
        self.showPreview()

    def showPreview(self):
        selectionList = self.listboxScreenshots.curselection()
        if not selectionList:
            self.previewPhoto = None
            self.labelPreview.configure(image="", text="Selecione um print para visualizar")
            return
        thumbnail = self.currentActivity().screenshotList[selectionList[0]].image.convert("RGB")
        thumbnail.thumbnail((PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT))
        self.previewPhoto = ImageTk.PhotoImage(thumbnail)
        self.labelPreview.configure(image=self.previewPhoto, text="")

    def addScreenshotFiles(self):
        pathList = filedialog.askopenfilenames(
            title="Escolha os prints do console",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Todos os arquivos", "*.*")],
        )
        failedList = []
        for path in sorted(pathList, key=lambda item: naturalSortKey(os.path.basename(item))):
            try:
                with Image.open(path) as openedImage:
                    openedImage.load()
                    image = openedImage.copy()
            except Exception:
                failedList.append(os.path.basename(path))
                continue
            self.currentActivity().screenshotList.append(Screenshot(os.path.basename(path), image))
        self.refreshScreenshotListbox()
        if failedList:
            messagebox.showerror("Imagem inválida", "Não foi possível abrir:\n" + "\n".join(failedList))

    def pasteScreenshot(self):
        try:
            clipboardContent = ImageGrab.grabclipboard()
        except Exception as error:
            messagebox.showerror("Área de transferência", f"Não foi possível ler a área de transferência:\n{error}")
            return
        if isinstance(clipboardContent, Image.Image):
            self.clipboardCounter += 1
            newScreenshotList = [Screenshot(f"colado {self.clipboardCounter}", clipboardContent)]
        elif isinstance(clipboardContent, list):
            newScreenshotList = []
            for path in clipboardContent:
                try:
                    with Image.open(path) as openedImage:
                        openedImage.load()
                        newScreenshotList.append(Screenshot(os.path.basename(path), openedImage.copy()))
                except Exception:
                    continue
        else:
            newScreenshotList = []
        if not newScreenshotList:
            messagebox.showinfo(
                "Nada para colar",
                "Não há imagem na área de transferência.\n\n"
                "Copie um recorte da tela (Windows: Win+Shift+S; macOS: Cmd+Ctrl+Shift+4) e tente de novo.",
            )
            return
        self.currentActivity().screenshotList.extend(newScreenshotList)
        self.refreshScreenshotListbox()

    def removeScreenshots(self):
        activity = self.currentActivity()
        for index in sorted(self.listboxScreenshots.curselection(), reverse=True):
            del activity.screenshotList[index]
        self.refreshScreenshotListbox()

    def moveScreenshots(self, direction):
        activity = self.currentActivity()
        newIndexList = moveItems(activity.screenshotList, list(self.listboxScreenshots.curselection()), direction)
        self.refreshScreenshotListbox(newIndexList)

    # ---- geração

    def readReportInfo(self):
        textByField = {key: entry.get().strip() for key, entry in self.entryByField.items()}
        return ReportInfo(
            reportTitle=textByField["title"] or REPORT_DEFAULT_TITLE,
            reportStudent=textByField["student"],
            reportCourse=textByField["course"],
            reportTeacher=textByField["teacher"],
        )

    def generateReport(self):
        missingNameList = [os.path.basename(activity.sourcePath) for activity in self.activityList if not activity.screenshotList]
        if missingNameList:
            shouldContinue = messagebox.askyesno(
                "Atividades sem print",
                "Estas atividades não têm nenhum print:\n\n" + "\n".join(missingNameList) + "\n\nGerar o PDF mesmo assim?",
            )
            if not shouldContinue:
                return

        outputPath = filedialog.asksaveasfilename(
            title="Salvar relatório",
            defaultextension=".pdf",
            initialdir=os.path.dirname(os.path.abspath(self.activityList[0].sourcePath)),
            initialfile="relatorio.pdf",
            filetypes=[("PDF", "*.pdf")],
        )
        if not outputPath:
            return

        self.root.configure(cursor="watch")
        self.root.update_idletasks()
        try:
            buildReport(self.readReportInfo(), self.activityList, outputPath)
        except Exception as error:
            self.root.configure(cursor="")
            messagebox.showerror("Erro ao gerar o PDF", f"{error}\n\nSe o PDF estiver aberto em outro programa, feche-o e tente de novo.")
            return
        self.root.configure(cursor="")
        if messagebox.askyesno("Relatório pronto", f"PDF salvo em:\n{outputPath}\n\nAbrir agora?"):
            openFile(outputPath)
