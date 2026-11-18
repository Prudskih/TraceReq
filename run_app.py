"""Создание окружения, установка пакета и запуск из любого рабочего каталога."""

import os
import subprocess
import sys
import venv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def main() -> None:
    if sys.version_info < (3, 11):
        raise SystemExit('TraceReq requires Python 3.11 or newer')
    environment = BASE_DIR / '.venv'
    executable = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not executable.is_file():
        venv.EnvBuilder(with_pip=True).create(environment)
    subprocess.run(
        [str(executable), '-m', 'pip', 'install', '-e', str(BASE_DIR)],
        cwd=BASE_DIR,
        check=True,
    )
    subprocess.run([str(executable), '-m', 'tracereq'], cwd=BASE_DIR, check=True)


if __name__ == '__main__':
    main()
