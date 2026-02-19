from dataclasses import dataclass
from io import BytesIO
import logging
import re

from docx import Document

from services.text_normalizer import normalize_text

HEADING_MARKER = "heading"
BULLET_STYLE_MARKERS = ("list bullet", "маркирован", "bullet")
NUMBERED_STYLE_MARKERS = ("list number", "нумер", "numbered")

BULLET_PREFIX_RE = re.compile(r"^[\-•*–—]\s*(.+)$")
NUMBERED_POINT_RE = re.compile(r"^(?P<number>\d+(?:\.\d+)+)[\.)]?\s*(?P<body>.*)$")
NUMBER_IN_TEXT_RE = re.compile(r"(?P<number>\d+(?:\.\d+)+)")
HEADING_PREFIX_RE = re.compile(r"^\d+(?:\.\d+)*[\.)]?\s*(?P<body>.+)$")


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

    def __init__(self, logger=None):
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
    """
    Импорт требований из .docx.

    Ожидаемая структура:
    - Заголовок секции (тип требований): "Бизнес-требования" / "Пользовательские требования" / ...
      Заголовок может быть:
        * со стилем Heading
        * с номером "1. Бизнес-требования"
        * без номера "Бизнес-требования"
    - Далее требования:
        * нумерованные пункты "6.2.4 ..."
        * маркированные пункты "- ..."
        * ИЛИ обычные абзацы (важно для документов, где требования идут строками без списков)
    """

    def __init__(self, aliases=None, reader=None, logger=None):
        self._logger = logger or logging.getLogger(__name__)
        self._aliases = self._normalize_aliases(aliases or {})
        self._reader = reader or DocxReader(logger=self._logger)

    def parse(self, file_bytes: bytes):
        paragraphs = self._reader.read_paragraphs(file_bytes)
        drafts = []

        current_type = None
        current_parent = None
        child_index = 0

        # Для "плоских" абзацев (без нумерации/буллетов) - автонумерация внутри типа
        plain_index_by_type: dict[str, int] = {}

        for p in paragraphs:
            #Пытаемся распознать секцию типа требований
            resolved_heading_type = self._resolve_requirement_type(p)
            if resolved_heading_type:
                current_type = resolved_heading_type
                current_parent = None
                child_index = 0
                plain_index_by_type.setdefault(current_type, 0)
                continue

            # Пока не встретили секцию типа - ничего не импортируем
            if not current_type:
                continue

            # Нумерованные пункты вида x.x.x Текст"
            numbered = self._parse_numbered(p.text)
            if numbered:
                number, body = numbered
                current_parent = number
                child_index = 0
                if body:
                    drafts.append(self._make_draft(number, body, current_type))
                continue

            #Буллеты (по стилю/префиксу)
            bullet_text = self._parse_bullet_text(p)
            if bullet_text:
                explicit_number = NUMBER_IN_TEXT_RE.search(bullet_text)
                if explicit_number:
                    number = explicit_number.group("number")
                    body = normalize_text(
                        bullet_text.replace(number, "", 1).strip(" .:-"),
                        lower=False,
                    )
                    if body:
                        drafts.append(self._make_draft(number, body, current_type))
                        child_index = self._sync_child_index(current_parent, number, child_index)
                    continue

                if current_parent:
                    child_index += 1
                    drafts.append(self._make_draft(f"{current_parent}.{child_index}", bullet_text, current_type))
                else:
                    # Буллет без родителя
                    plain_index_by_type[current_type] += 1
                    drafts.append(self._make_plain_draft(plain_index_by_type[current_type], bullet_text, current_type))
                continue

            # Обычный абзац под текущим типом требований
            text = normalize_text(p.text, lower=False)
            if not text:
                continue
            # Отсекаем “заголовкообразные”/мусорные строки внутри секций
            if self._looks_like_noise(text):
                continue

            plain_index_by_type[current_type] += 1
            drafts.append(self._make_plain_draft(plain_index_by_type[current_type], text, current_type))

        if not drafts:
            self._logger.warning("Не найдено требований для импорта")
            raise ValueError("Не найдено требований для импорта. Используйте заголовки с типом требований.")

        self._logger.info("Импортировано требований: %s", len(drafts))
        return drafts

    @staticmethod
    def _normalize_aliases(aliases):
        # aliases: {"бизнес-требования": "BUSINESS", ...}
        return {normalize_text(k): v for k, v in aliases.items() if normalize_text(k) and v}

    @staticmethod
    def _is_heading_style(style_name: str) -> bool:
        return HEADING_MARKER in normalize_text(style_name)

    @staticmethod
    def _is_numbered_style(style_name: str) -> bool:
        s = normalize_text(style_name)
        return any(m in s for m in NUMBERED_STYLE_MARKERS)

    def _resolve_requirement_type(self, paragraph: DocxParagraph):
        """
        Возвращает requirement_type если абзац — заголовок секции типа требований.
        Поддерживает:
        - прямое совпадение по aliases (с номером или без)
        - заголовки со стилем Heading
        - строки вида "1. Бизнес-требования"
        """
        raw = normalize_text(paragraph.text, lower=False)
        if not raw:
            return None

        normalized_full = normalize_text(raw)
        direct_match = self._aliases.get(normalized_full)
        if direct_match:
            return direct_match

        # Если строка начинается с "1. ..." - попробуем алиас по “body”
        m = HEADING_PREFIX_RE.match(raw)
        if m:
            body_norm = normalize_text(m.group("body"))
            aliased = self._aliases.get(body_norm)
            if aliased:
                return aliased

        # Если это Heading-стиль - часто заголовки типа требований не нумеруются
        if self._is_heading_style(paragraph.style_name):
            # попробуем алиас по тексту как есть
            return self._aliases.get(normalized_full)

        return None

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
    def _make_plain_draft(index: int, body: str, requirement_type: str) -> RequirementDraft:
        # “Плоские” требования: чтобы не терять структуру, добавляем локальный номер.
        title = normalize_text(f"{index}. {body}", lower=False)
        return RequirementDraft(title=title, requirement_type=requirement_type)

    @staticmethod
    def _sync_child_index(parent, number: str, current_index: int) -> int:
        if not parent or not number.startswith(f"{parent}."):
            return current_index
        suffix = number[len(parent) + 1 :]
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

    @staticmethod
    def _looks_like_noise(text: str) -> bool:
        """
        Минимальная защита от мусора внутри секций:
        """
        t = normalize_text(text)
        if t in {"оглавление", "глоссарий", "определение", "описание"}:
            return True
        return False
