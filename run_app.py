import os
import subprocess
import venv


def get_venv_python(venv_dir: str) -> str:
    if os.name == "nt":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    return os.path.join(venv_dir, "bin", "python")


def ensure_venv(venv_dir: str) -> str:
    python_path = get_venv_python(venv_dir)
    if os.path.exists(python_path):
        return python_path

    builder = venv.EnvBuilder(with_pip=True)
    builder.create(venv_dir)
    return python_path


def install_requirements(python_path: str) -> None:
    subprocess.check_call([python_path, "-m", "pip", "install", "-r", "requirements.txt"])


def run_app(python_path: str) -> None:
    subprocess.check_call([python_path, "app.py"])


def main() -> None:
    venv_dir = os.path.join(os.path.dirname(__file__), ".venv")
    python_path = ensure_venv(venv_dir)
    install_requirements(python_path)
    run_app(python_path)


if __name__ == "__main__":
    main()