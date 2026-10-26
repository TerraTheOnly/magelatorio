import io
import os
from datetime import date

from PIL import Image, ImageOps
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus import Image as PdfImage

from app.config import (
    BUNDLED_FONT_RELATIVE_PATH,
    CODE_BORDER_COLOR,
    CODE_CELL_PADDING,
    CODE_FONT_FALLBACK,
    CODE_FONT_NAME,
    CODE_FONT_SIZE,
    CODE_LINE_HEIGHT,
    CODE_NUMBER_BACKGROUND,
    CODE_NUMBER_COLOR,
    CODE_TEXT_BACKGROUND,
    FOOTER_BASELINE,
    IMAGE_MAX_PIXEL_WIDTH,
    IMAGE_MAX_UPSCALE,
    IMAGE_PIXEL_TO_POINT,
    IMAGE_RESERVED_HEIGHT,
    PAGE_MARGIN_BOTTOM,
    PAGE_MARGIN_HORIZONTAL,
    PAGE_MARGIN_TOP,
    PAGE_SIZE,
    SYSTEM_FONT_PATH_LIST,
    TAB_WIDTH,
)
from app.helpers import cleanParagraphText, readSourceText, resourcePath, sanitizeText


def registerCodeFont():
    """Registra uma fonte monoespaçada com acentos. Devolve (nome, suportaUnicode)."""
    for fontPath in (resourcePath(BUNDLED_FONT_RELATIVE_PATH), *SYSTEM_FONT_PATH_LIST):
        if os.path.isfile(fontPath):
            try:
                pdfmetrics.registerFont(TTFont(CODE_FONT_NAME, fontPath))
                return CODE_FONT_NAME, True
            except Exception:
                continue
    return CODE_FONT_FALLBACK, False


def buildStyleMap():
    baseStyle = getSampleStyleSheet()["Normal"]
    return {
        "title": ParagraphStyle("ReportTitle", parent=baseStyle, fontName="Helvetica-Bold", fontSize=20, leading=25, spaceAfter=8),
        "info": ParagraphStyle("ReportInfoLine", parent=baseStyle, fontSize=11, leading=15),
        "activityHeading": ParagraphStyle("ActivityHeading", parent=baseStyle, fontName="Helvetica-Bold", fontSize=15, leading=19, spaceAfter=4),
        "sectionHeading": ParagraphStyle("SectionHeading", parent=baseStyle, fontName="Helvetica-Bold", fontSize=11, leading=14, spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#333333")),
        "caption": ParagraphStyle("FigureCaption", parent=baseStyle, fontName="Helvetica-Oblique", fontSize=8.5, leading=11, alignment=1, textColor=colors.HexColor("#555555"), spaceBefore=3),
        "note": ParagraphStyle("EmptyNote", parent=baseStyle, fontName="Helvetica-Oblique", fontSize=9.5, textColor=colors.HexColor("#777777")),
    }


def buildHeaderStory(reportInfo, styleMap):
    story = [Paragraph(cleanParagraphText(reportInfo.reportTitle), styleMap["title"])]
    lineList = (
        ("Aluno", reportInfo.reportStudent),
        ("Disciplina", reportInfo.reportCourse),
        ("Professor", reportInfo.reportTeacher),
        ("Data", date.today().strftime("%d/%m/%Y")),
    )
    for labelText, valueText in lineList:
        if valueText:
            story.append(Paragraph(f"<b>{labelText}:</b> {cleanParagraphText(valueText)}", styleMap["info"]))
    story.extend([Spacer(1, 6), HRFlowable(width="100%", thickness=0.8, color=colors.grey), Spacer(1, 10)])
    return story


def buildCodeTable(sourceText, codeFontName, supportsUnicode, tableWidth):
    """Código numerado em tabela (quebra automática de linhas longas)."""
    lineList = sourceText.expandtabs(TAB_WIDTH).splitlines() or [""]
    numberDigits = len(str(len(lineList)))
    characterWidth = pdfmetrics.stringWidth("M", codeFontName, CODE_FONT_SIZE)
    numberColumnWidth = characterWidth * numberDigits + 2 * CODE_CELL_PADDING
    codeColumnWidth = tableWidth - numberColumnWidth
    maxCharacterCount = max(10, int((codeColumnWidth - 2 * CODE_CELL_PADDING) // characterWidth))

    rowList = []
    for lineNumber, lineText in enumerate(lineList, start=1):
        lineText = sanitizeText(lineText.rstrip(), supportsUnicode)
        segmentList = [lineText[start:start + maxCharacterCount] for start in range(0, len(lineText), maxCharacterCount)] or [""]
        for segmentIndex, segmentText in enumerate(segmentList):
            rowList.append([str(lineNumber) if segmentIndex == 0 else "", segmentText])

    table = Table(rowList, colWidths=[numberColumnWidth, codeColumnWidth], rowHeights=CODE_LINE_HEIGHT)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), codeFontName),
        ("FONTSIZE", (0, 0), (-1, -1), CODE_FONT_SIZE),
        ("LEADING", (0, 0), (-1, -1), CODE_LINE_HEIGHT),
        ("TEXTCOLOR", (0, 0), (0, -1), CODE_NUMBER_COLOR),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (0, -1), CODE_NUMBER_BACKGROUND),
        ("BACKGROUND", (1, 0), (1, -1), CODE_TEXT_BACKGROUND),
        ("LEFTPADDING", (0, 0), (-1, -1), CODE_CELL_PADDING),
        ("RIGHTPADDING", (0, 0), (-1, -1), CODE_CELL_PADDING),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("BOX", (0, 0), (-1, -1), 0.5, CODE_BORDER_COLOR),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, CODE_BORDER_COLOR),
    ]))
    return table


def prepareImage(image):
    """Normaliza orientação/transparência e reduz prints gigantes."""
    image = ImageOps.exif_transpose(image)
    hasTransparency = image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info)
    if hasTransparency:
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, "white")
        background.paste(image, mask=image.getchannel("A"))
        image = background
    else:
        image = image.convert("RGB")
    if image.width > IMAGE_MAX_PIXEL_WIDTH:
        scale = IMAGE_MAX_PIXEL_WIDTH / image.width
        image = image.resize((IMAGE_MAX_PIXEL_WIDTH, max(1, round(image.height * scale))), Image.LANCZOS)
    return image


def buildImageFlowable(image, maxWidth, maxHeight):
    image = prepareImage(image)
    naturalWidth = image.width * IMAGE_PIXEL_TO_POINT
    naturalHeight = image.height * IMAGE_PIXEL_TO_POINT
    scale = min(maxWidth / naturalWidth, maxHeight / naturalHeight, IMAGE_MAX_UPSCALE)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return PdfImage(buffer, width=naturalWidth * scale, height=naturalHeight * scale)


def buildActivityStory(activityNumber, activity, styleMap, codeFontName, supportsUnicode, frameWidth, frameHeight):
    fileName = os.path.basename(activity.sourcePath)
    story = [
        CondPageBreak(4 * cm),
        Paragraph(f"Atividade {activityNumber} — {cleanParagraphText(fileName)}", styleMap["activityHeading"]),
        Paragraph("Código-fonte", styleMap["sectionHeading"]),
        buildCodeTable(readSourceText(activity.sourcePath), codeFontName, supportsUnicode, frameWidth),
        Spacer(1, 10),
    ]

    sectionHeading = Paragraph("Saída do console", styleMap["sectionHeading"])
    if not activity.screenshotList:
        story.append(KeepTogether([sectionHeading, Paragraph("(nenhum print anexado)", styleMap["note"])]))
        return story

    maxImageHeight = frameHeight - IMAGE_RESERVED_HEIGHT
    screenshotCount = len(activity.screenshotList)
    for screenshotIndex, screenshot in enumerate(activity.screenshotList, start=1):
        figureBlock = [
            buildImageFlowable(screenshot.image, frameWidth, maxImageHeight),
            Paragraph(f"Saída do console — atividade {activityNumber} ({screenshotIndex}/{screenshotCount})", styleMap["caption"]),
        ]
        if screenshotIndex == 1:
            figureBlock.insert(0, sectionHeading)
        story.append(KeepTogether(figureBlock))
        story.append(Spacer(1, 10))
    return story


def buildReport(reportInfo, activityList, outputPath):
    """Gera o PDF em outputPath."""
    codeFontName, supportsUnicode = registerCodeFont()
    styleMap = buildStyleMap()

    pageWidth, pageHeight = PAGE_SIZE
    frameWidth = pageWidth - 2 * PAGE_MARGIN_HORIZONTAL
    frameHeight = pageHeight - PAGE_MARGIN_TOP - PAGE_MARGIN_BOTTOM

    footerText = " — ".join(part for part in (reportInfo.reportStudent, reportInfo.reportCourse) if part)
    footerText = sanitizeText(footerText, supportsUnicode=False)

    def drawFooter(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(PAGE_MARGIN_HORIZONTAL, FOOTER_BASELINE, footerText)
        canvas.drawRightString(pageWidth - PAGE_MARGIN_HORIZONTAL, FOOTER_BASELINE, f"Página {document.page}")
        canvas.restoreState()

    document = BaseDocTemplate(
        outputPath,
        pagesize=PAGE_SIZE,
        title=reportInfo.reportTitle,
        author=reportInfo.reportStudent,
    )
    bodyFrame = Frame(
        PAGE_MARGIN_HORIZONTAL, PAGE_MARGIN_BOTTOM, frameWidth, frameHeight,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="body",
    )
    document.addPageTemplates([PageTemplate(id="main", frames=[bodyFrame], onPage=drawFooter)])

    story = buildHeaderStory(reportInfo, styleMap)
    for activityIndex, activity in enumerate(activityList, start=1):
        if activityIndex > 1:
            story.append(PageBreak())
        story.extend(buildActivityStory(activityIndex, activity, styleMap, codeFontName, supportsUnicode, frameWidth, frameHeight))
    document.build(story)
