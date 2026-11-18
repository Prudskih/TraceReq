import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from io import BytesIO
from typing import Protocol

from docx import Document
from docx.text.paragraph import Paragraph

from tracereq.domain.entities import RequirementDraft
from tracereq.domain.enums import RequirementType
from tracereq.domain.errors import InvalidInput
from tracereq.infrastructure.documents.text_normalizer import normalize_text

BULLET_STYLE_MARKERS = ('list bullet', 'маркирован', 'bullet')
NUMBERED_STYLE_MARKERS = ('list number', 'нумер', 'numbered')

BULLET_PREFIX_RE = re.compile(r'^[\-•*–—]\s*(.+)$')
NUMBERED_POINT_RE = re.compile(r'^\d+(?:\.\d+)*[\.)]?\s+.+$')
GROUP_HEADING_RE = re.compile(r'^<\s*(?P<body>[^<>]+?)\s*>$')
END_MARKER = 'end'


@dataclass(frozen=True, slots=True)
class DocxParagraph:
    text: str
    style_name: str
    is_list_item: bool


class ParagraphReader(Protocol):
    def read_paragraphs(self, file_bytes: bytes) -> list[DocxParagraph]: ...


class DocxReader:
    """Слой чтения из .docx."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def read_paragraphs(self, file_bytes: bytes) -> list[DocxParagraph]:
        try:
            document = Document(BytesIO(file_bytes))
        except Exception as exc:
            self._logger.exception('Ошибка чтения .docx')
            raise InvalidInput('Некорректный .docx файл') from exc

        paragraphs = []
        for paragraph in document.paragraphs:
            text = normalize_text(paragraph.text, lower=False)
            if not text:
                continue
            style_name = (paragraph.style.name or '') if paragraph.style else ''
            paragraphs.append(
                DocxParagraph(
                    text=text,
                    style_name=style_name,
                    is_list_item=self._is_list_item(paragraph, text, style_name),
                )
            )
        return paragraphs

    @staticmethod
    def _is_list_item(paragraph: Paragraph, text: str, style_name: str) -> bool:
        style = normalize_text(style_name)
        if any(marker in style for marker in (*BULLET_STYLE_MARKERS, *NUMBERED_STYLE_MARKERS)):
            return True

        p_pr = paragraph._p.pPr
        if p_pr is not None and p_pr.numPr is not None:
            return True

        if BULLET_PREFIX_RE.match(text):
            return True
        return bool(NUMBERED_POINT_RE.match(text))


class DocxImportService:
    """Импорт требований из .docx по секциям формата <...> и пунктам списков."""

    def __init__(
        self,
        aliases: Mapping[str, str] | None = None,
        reader: ParagraphReader | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._aliases = self._normalize_aliases(aliases or {})
        self._reader: ParagraphReader = (
            reader if reader is not None else DocxReader(logger=self._logger)
        )

    def parse(self, file_bytes: bytes) -> list[RequirementDraft]:
        paragraphs = self._reader.read_paragraphs(file_bytes)
        drafts = []

        current_type = None
        index_by_type: dict[str, int] = {}

        for p in paragraphs:
            marker = self._resolve_group_marker(p)
            if marker == END_MARKER:
                current_type = None
                continue
            if marker:
                current_type = marker
                index_by_type.setdefault(current_type, 0)
                continue

            if not current_type or not p.is_list_item:
                continue

            text = normalize_text(p.text, lower=False)
            if not text:
                continue

            index_by_type[current_type] += 1
            drafts.append(self._make_draft(index_by_type[current_type], text, current_type))

        if not drafts:
            self._logger.warning('Не найдено требований для импорта')
            raise InvalidInput(
                'Не найдено требований для импорта. Используйте секции в формате <...> и списки.'
            )

        self._logger.info('Разобрано требований из документа: %s', len(drafts))
        return drafts

    @staticmethod
    def _normalize_aliases(aliases: Mapping[str, str]) -> dict[str, str]:
        normalized = {normalize_text(k): v for k, v in aliases.items() if normalize_text(k) and v}
        normalized.update({normalize_text(v): v for v in aliases.values() if normalize_text(v)})
        return normalized

    def _resolve_group_marker(self, paragraph: DocxParagraph) -> str | None:
        raw = normalize_text(paragraph.text, lower=False)
        if not raw:
            return None

        group_match = GROUP_HEADING_RE.match(raw)
        if not group_match:
            return None

        marker_value = normalize_text(group_match.group('body'))
        if marker_value in {END_MARKER, 'конец'}:
            return END_MARKER
        return self._aliases.get(marker_value)

    @staticmethod
    def _make_draft(index: int, body: str, requirement_type: str) -> RequirementDraft:
        title = normalize_text(f'{requirement_type} {index}', lower=False)
        return RequirementDraft(
            title=title, requirement_type=RequirementType(requirement_type), description=body
        )
