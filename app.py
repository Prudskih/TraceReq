"""Совместимая точка входа; реализация находится в пакете tracereq."""

from tracereq.web.app import create_app

if __name__ == '__main__':
    from tracereq.__main__ import main

    main()
else:
    app = create_app()
