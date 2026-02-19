
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
                bullet_text = self._parse_bullet_text(paragraph)
                if not bullet_text:
                    continue

                explicit_number = NUMBER_IN_TEXT_RE.search(bullet_text)
                if explicit_number:
                    number = explicit_number.group("number")
                    body = normalize_text(bullet_text.replace(number, "", 1).strip(" .:-"), lower=False)
                    if body:
                        drafts.append(self._make_draft(number, body, current_type))
                        child_index = self._sync_child_index(current_parent, number, child_index)
                    continue

                if current_parent:
                    child_index += 1
                    drafts.append(self._make_draft(f"{current_parent}.{child_index}", bullet_text, current_type))

            if not drafts:
                self._logger.warning("Не найдено требований для импорта")
                raise ValueError(
                    "Не найдено требований для импорта. Используйте заголовки с типом требований, пункты 4.1/4.1.1 и маркированные подпункты."
                )

            self._logger.info("Импортировано требований: %s", len(drafts))
            return drafts

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

    @staticmethod
    def _sync_child_index(parent, number: str, current_index: int) -> int:
        if not parent or not number.startswith(f"{parent}."):
            return current_index
        suffix = number[len(parent) + 1:]
        if suffix.isdigit():
            return max(current_index, int(suffix))
        return current_index

    @staticmethod
    def _parse_bullet_text(paragraph: DocxParagraph):
        style = normalize_text(paragraph.style_name)
        text = normalize_text(paragraph.text, lower=False)
        if not text:
            return None

        is_bullet_style = any(marker in style for marker in BULLET_STYLE_MARKERS)
        match = BULLET_PREFIX_RE.match(text)
        if not is_bullet_style and not match:
            return None

        cleaned = match.group(1) if match else text
        return normalize_text(cleaned, lower=False)

