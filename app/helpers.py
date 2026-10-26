import os
import re
import subprocess
import sys
from xml.sax.saxutils import escape

from app.config import CONTROL_CHARACTER_PATTERN, SOURCE_ENCODING_LIST


def resourcePath(relativePath):
    """Caminho de um recurso (assets/...), tanto rodando o script quanto no .exe do PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        baseDirectory = sys._MEIPASS
    else:
        baseDirectory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(baseDirectory, relativePath)


def naturalSortKey(text):
    """Ordem natural: ex2.c vem antes de ex10.c."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def moveItems(itemList, selectedIndexList, direction):
    """Move os itens selecionados uma posição (-1 = acima, +1 = abaixo).

    Altera itemList no lugar e devolve os novos índices dos itens movidos.
    """
    selectedSet = set(selectedIndexList)
    newIndexList = []
    for index in sorted(selectedIndexList, reverse=direction > 0):
        target = index + direction
        if 0 <= target < len(itemList) and target not in selectedSet:
            itemList[index], itemList[target] = itemList[target], itemList[index]
            selectedSet.remove(index)
            selectedSet.add(target)
            newIndexList.append(target)
        else:
            newIndexList.append(index)
    return sorted(newIndexList)


def readSourceText(sourcePath):
    """Lê o arquivo tentando UTF-8 e, se falhar, o ANSI (Windows-1252)."""
    with open(sourcePath, "rb") as sourceFile:
        rawBytes = sourceFile.read()
    for encodingName in SOURCE_ENCODING_LIST:
        try:
            return rawBytes.decode(encodingName)
        except UnicodeDecodeError:
            continue
    return rawBytes.decode("latin-1", errors="replace")


def sanitizeText(text, supportsUnicode):
    text = CONTROL_CHARACTER_PATTERN.sub("?", text)
    if not supportsUnicode:
        text = text.encode("cp1252", errors="replace").decode("cp1252")
    return text


def cleanParagraphText(text):
    """Texto seguro para Paragraph (fonte Helvetica, XML escapado)."""
    return escape(sanitizeText(text, supportsUnicode=False))


def openFile(filePath):
    if sys.platform.startswith("win"):
        os.startfile(filePath)
    elif sys.platform == "darwin":
        subprocess.run(["open", filePath], check=False)
    else:
        subprocess.run(["xdg-open", filePath], check=False)
