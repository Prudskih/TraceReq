"""Запуск через python -m tracereq или команду tracereq."""

import argparse
import logging

import uvicorn

from tracereq.infrastructure.persistence.initialization import initialize_database
from tracereq.settings import Settings
from tracereq.web.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description='TraceReq server and database setup')
    parser.add_argument('command', nargs='?', choices=['serve', 'init-db'], default='serve')
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s'
    )
    settings = Settings()
    if args.command == 'init-db':
        try:
            path = initialize_database(settings)
        except (FileExistsError, ValueError) as exc:
            parser.exit(1, f'Database initialization refused: {exc}\n')
        print(f'Database created: {path}')
        return
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port)


if __name__ == '__main__':
    main()
