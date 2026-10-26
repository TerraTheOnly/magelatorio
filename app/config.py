import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

REPORT_DEFAULT_TITLE = "Relatório da Atividade"

# ---- página do PDF
PAGE_SIZE = A4
PAGE_MARGIN_HORIZONTAL = 2 * cm
PAGE_MARGIN_TOP = 2 * cm
PAGE_MARGIN_BOTTOM = 2.2 * cm
FOOTER_BASELINE = 1.1 * cm

# ---- bloco de código
CODE_FONT_NAME = "CodeFont"
CODE_FONT_FALLBACK = "Courier"
CODE_FONT_SIZE = 8.5
CODE_LINE_HEIGHT = 10.5
CODE_CELL_PADDING = 4
CODE_NUMBER_COLOR = colors.HexColor("#808080")
CODE_NUMBER_BACKGROUND = colors.HexColor("#ECECEC")
CODE_TEXT_BACKGROUND = colors.HexColor("#F7F7F7")
CODE_BORDER_COLOR = colors.HexColor("#C8C8C8")
TAB_WIDTH = 4

# ---- imagens (prints)
IMAGE_MAX_PIXEL_WIDTH = 1800
IMAGE_PIXEL_TO_POINT = 0.75  # 96 dpi -> 72 dpi
IMAGE_MAX_UPSCALE = 1.5
IMAGE_RESERVED_HEIGHT = 3 * cm  # espaço para título da seção, legenda e margens

# ---- arquivos de código aceitos no seletor (qualquer outro: "Todos os arquivos")
SOURCE_FILE_EXTENSION_LIST = (
    ".c", ".h",
    ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx",
    ".java",
    ".py",
    ".cs",
    ".js", ".mjs", ".ts", ".tsx", ".jsx",
    ".go",
    ".rs",
    ".kt",
    ".swift",
    ".php",
    ".rb",
    ".pas", ".pp",
    ".por", ".alg",
    ".sh", ".sql", ".r", ".R", ".m",
)
SOURCE_FILE_PATTERN = " ".join(f"*{extension}" for extension in SOURCE_FILE_EXTENSION_LIST)

# ---- leitura de texto
SOURCE_ENCODING_LIST = ("utf-8-sig", "cp1252")
CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

# ---- fontes monoespaçadas: a embutida (assets/) tem prioridade, depois as do sistema
BUNDLED_FONT_RELATIVE_PATH = "assets/DejaVuSansMono.ttf"
SYSTEM_FONT_PATH_LIST = (
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/cour.ttf",
    "/System/Library/Fonts/Supplemental/Courier New.ttf",
    "/Library/Fonts/Courier New.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
)

# ---- interface
WINDOW_TITLE = "Gerador de Relatório de Atividades"
WINDOW_GEOMETRY = "1060x700"
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600
PREVIEW_MAX_WIDTH = 440
PREVIEW_MAX_HEIGHT = 260
