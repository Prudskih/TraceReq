
from dataclasses import dataclass
from io import BytesIO
import logging
import re
from services.text_normalizer import normalize_text
from docx import Document

HEADING_MARKER = "heading"
BULLET_STYLE_MARKERS = ("list bullet", "маркирован")
BULLET_PREFIX_RE = re.compile(r"^[\-•*–—]\s*(.+)$")
NUMBERED_POINT_RE = re.compile(r"^(?P<number>\d+(?:\.\d+)+)[\.)]?\s*(?P<body>.*)$")
NUMBER_IN_TEXT_RE = re.compile(r"(?P<number>\d+(?:\.\d+)+)")


@dataclass(frozen=True)
class DocxParagraph:
    text: str
    style_name: str


@dataclass(frozen=True)
class RequirementDraft:
    title: str
    requirement_type: str
    description: str = ""

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "requirement_type": self.requirement_type,
        }

class DocxReader:
    """Слой чтения абзацев из .docx."""

    def __init__(self, logger = None):
        self._logger = logger or logging.getLogger(__name__)

    def read_paragraphs(self, file_bytes: bytes):
        try:
            document = Document(BytesIO(file_bytes))
        except Exception as exc:
            self._logger.exception("Ошибка чтения .docx")
            raise ValueError("Некорректный .docx файл") from exc

        paragraphs = []
        for paragraph in document.paragraphs:
            text = normalize_text(paragraph.text, lower=False)
            if not text:
                continue
            style_name = paragraph.style.name if paragraph.style else ""
            paragraphs.append(DocxParagraph(text=text, style_name=style_name))
        return paragraphs


class DocxImportService:
    """Ипорта требований из .docx."""

    def __init__(self, aliases = None, reader = None, logger = None):
        self._logger = logger or logging.getLogger(__name__)
        self._aliases = self._normalize_aliases(aliases or {})
        self._reader = reader or DocxReader(logger=self._logger)

    def parse(self, file_bytes: bytes):
        paragraphs = self._reader.read_paragraphs(file_bytes)
        drafts= []

        current_type = None
        current_parent= None
        child_index = 0

        for paragraph in paragraphs:
            if self._is_heading(paragraph.style_name):
                current_type = self._resolve_requirement_type(paragraph.text)
                current_parent = None
                child_index = 0
                continue

            if not current_type:
                continue

            numbered = self._parse_numbered(paragraph.text)
            if numbered:
                current_parent = numbered[0]
                child_index = 0
                if numbered[1]:
                    drafts.append(self._make_draft(numbered[0], numbered[1], current_type))
                continue
        #Обработку иерархий  дописать

        self._logger.info("Импортировано требований: %s", len(drafts))
        return drafts

    @staticmethod
    def _normalize_aliases(aliases):
        return {normalize_text(key): value for key, value in aliases.items() if normalize_text(key) and value}

    @staticmethod
    def _is_heading(style_name: str) -> bool:
        return HEADING_MARKER in normalize_text(style_name)

    def _resolve_requirement_type(self, heading_text: str):
        return self._aliases.get(normalize_text(heading_text))

    @staticmethod
    def _parse_numbered(text: str):
        match = NUMBERED_POINT_RE.match(normalize_text(text, lower=False))
        if not match:
            return None
        return match.group("number"), normalize_text(match.group("body"), lower=False)


    @staticmethod
    def _make_draft(number: str, body: str, requirement_type: str) -> RequirementDraft:
        title = normalize_text(f"{number} {body}", lower=False)
        return RequirementDraft(title=title, requirement_type=requirement_type)

