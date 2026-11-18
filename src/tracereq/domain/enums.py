from enum import StrEnum


class RequirementType(StrEnum):
    """Типы требований"""

    BUSINESS = 'Бизнес-требование'
    FUNCTIONAL = 'Функциональное требование'
    NON_FUNCTIONAL = 'Нефункциональное требование'
    USER = 'Пользовательское требование'
    INTERFACE = 'Требование к интерфейсу'


class RequirementStatus(StrEnum):
    """Статусы требований"""

    DRAFT = 'Черновик'
    IN_PROGRESS = 'В работе'
    REVIEW = 'На проверке'
    APPROVED = 'Утверждено'
    REJECTED = 'Отклонено'


class Priority(StrEnum):
    """Приоритеты требований"""

    LOW = 'Низкий'
    MEDIUM = 'Средний'
    HIGH = 'Высокий'
    CRITICAL = 'Критический'


class LinkType(StrEnum):
    """Типы связей между требованиями"""

    IMPLEMENTS = 'Реализует'
    DEPENDS_ON = 'Зависит от'
    CONTRADICTS = 'Противоречит'
