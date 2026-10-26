# Gerador de Relatório de Atividades

Gera um PDF com o **código-fonte** (numerado) de cada atividade e os **prints do console** que você fornecer, quantos quiser por atividade. Aceita C, C++, Java, Python e outras linguagens (a lista de extensões está em `SOURCE_FILE_EXTENSION_LIST`, em `app/config.py`; qualquer outro arquivo de texto pode ser escolhido em "Todos os arquivos").

## Instalação

Requer Python 3.9 ou mais novo.

```
pip install -r requirements.txt
```

O tkinter já vem com o Python no Windows e no macOS. No Linux: `sudo apt install python3-tk`.

## Uso

```
python main.py
```

1. **Passo 1** – preencha título, aluno, disciplina e professor (opcionais) e adicione os arquivos de código. A ordem natural é aplicada (`ex2` antes de `ex10`); use *Subir*/*Descer* para reordenar.
2. **Um passo por atividade** – o programa mostra o código e pede os prints:
   - *Adicionar imagens…* escolhe arquivos de imagem;
   - *Colar da área de transferência* (ou Ctrl+V) cola um recorte de tela. No Windows, Win+Shift+S copia um recorte; no macOS, Cmd+Ctrl+Shift+4.
3. **Último passo** – *Gerar PDF*, escolha onde salvar.

Atividades sem print são avisadas antes de gerar. Arquivos de código em UTF-8 ou ANSI (Windows-1252) são lidos corretamente.

## Gerar um .exe único (Windows)

```
pip install pyinstaller
build_exe.bat
```

O resultado fica em `dist\RelatorioAtividades.exe`: um arquivo só, sem janela de console, com a fonte do código embutida (`assets/`). A primeira abertura é um pouco lenta porque o PyInstaller descompacta o programa em uma pasta temporária. Alguns antivírus desconfiam de executáveis `--onefile`; se isso acontecer, gere sem essa opção (troque `--onefile` por `--onedir` no `build_exe.bat`).

## Estrutura

```
main.py            ponto de entrada
app/
  config.py        constantes (margens, fontes, cores, limites)
  models.py        Screenshot, Activity, ReportInfo
  helpers.py       utilidades puras (leitura de arquivo, ordenação, recursos)
  pdf_report.py    geração do PDF (sem tkinter)
  gui.py           interface tkinter (assistente passo a passo)
assets/            fonte DejaVu Sans Mono embutida (e sua licença)
build_exe.bat      empacotamento com PyInstaller
```

## Observações

- A geração do PDF (`app/pdf_report.py`) não depende da interface e pode ser usada por outros scripts: `buildReport(reportInfo, activityList, outputPath)`.
- No Linux, colar da área de transferência exige `xclip` ou `wl-clipboard` instalado; *Adicionar imagens…* funciona sempre.
- A fonte DejaVu Sans Mono segue a licença em `assets/DejaVuSansMono-LICENSE.txt`.
