from dataclasses import dataclass, field

from PIL import Image

from app.config import REPORT_DEFAULT_TITLE


@dataclass
class Screenshot:
    label: str
    image: Image.Image


@dataclass
class Activity:
    sourcePath: str
    screenshotList: list = field(default_factory=list)


@dataclass
class ReportInfo:
    reportTitle: str = REPORT_DEFAULT_TITLE
    reportStudent: str = ""
    reportCourse: str = ""
    reportTeacher: str = ""
