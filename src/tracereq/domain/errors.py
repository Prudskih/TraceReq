"""Ошибки приложения, не зависящие от HTTP и конкретной базы данных."""


class ApplicationError(Exception):
    """Ожидаемая ошибка выполнения пользовательской операции."""


class NotFound(ApplicationError):
    pass


class InvalidInput(ApplicationError):
    pass


class Conflict(ApplicationError):
    pass
