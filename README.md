# Magelatório: Gerador de Relatório de Atividades

Essa ferramenta foi criada para gerar relatórios de atividades práticas das matérias de programação especificamente para o CEFET-MG, mas, na prática, pode ser usado para qualquer relatório que precise do código-fonte e/ou fotos dos resultados. A ferramenta gera um PDF com o **código-fonte** (numerado) de cada atividade e os **prints do console** que você fornecer, quantos quiser por atividade. 

Aceita C, C++, Java, Python, entre várias outras linguagens. A lista completa de extensões aceitas está em `SOURCE_FILE_EXTENSION_LIST`, em `app/config.py`. Mesmo assim, qualquer outro arquivo de texto pode ser escolhido em "Todos os arquivos", porém a formatação pode não funcionar.

## Manual de Uso

1. Preencha o título da atividade, o nome do aluno, a disciplina, o nome do professor (opcionais) e adicione os arquivos de código. A ordem alfanumérica é aplicada, mas pode ser alterada com os botões *'Subir'*/*'Descer'*.
2. Após prosseguir, o programa passará por cada um dos arquivos de código adicionados, dando a opção de anexar fotos/prints do output relacionadas ao código.
   - *'Adicionar imagens…'* escolhe arquivos de imagem;
   - *'Colar da área de transferência'* (ou Ctrl+V) cola uma imagem da área de transferência.
   O usuário pode também pular essa etapa, deixando a parte de imagens no relatório em branco.
3. Após adicionar fotos em todos os códigos, você pode gerar o PDF em seu diretório de preferência. (Caso haja algum código sem imagens anexadas, o programa irá avisar o usuário, mas esse aviso pode ser ignorado.)
4. Pronto! Seu relatório está pronto para ser enviado.

[**Relatório de Exemplo**](https://github.com/user-attachments/files/34148341/relatorio_codigos.pdf)


## Instalação

Requer Python 3.9 ou mais novo. O Tkinter já vem com o Python no Windows e no macOS.

```
pip install -r requirements.txt
```

O Tkinter precisa ser instalado manualmente em sistemas **Linux** com esse comando:

```
sudo apt install python3-tk
```

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
```

## Observações

- A geração do PDF (`app/pdf_report.py`) não depende da interface e pode ser usada por outros scripts: `buildReport(reportInfo, activityList, outputPath)`.
- No Linux, colar da área de transferência exige `xclip` ou `wl-clipboard` instalado; *Adicionar imagens…* funciona sempre.
- A fonte DejaVu Sans Mono segue a licença em `assets/DejaVuSansMono-LICENSE.txt`.
