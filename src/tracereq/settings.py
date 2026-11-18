"""Настройки читаются при создании приложения, а не при импорте модулей."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from tracereq.domain.enums import RequirementType


def default_instance_dir() -> Path:
    source_root = Path(__file__).resolve().parents[2]
    base = source_root if (source_root / 'pyproject.toml').is_file() else Path.cwd()
    return base / 'instance'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    database_url: str = 'sqlite:///requirements_trace.db'
    instance_dir: Path = Field(default_factory=default_instance_dir)
    host: str = '127.0.0.1'
    port: int = Field(default=5000, ge=1, le=65535)
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    requirement_type_aliases: dict[str, RequirementType] = Field(
        default_factory=lambda: {
            'бизнес-требования': RequirementType.BUSINESS,
            'функциональные требования': RequirementType.FUNCTIONAL,
            'нефункциональные требования': RequirementType.NON_FUNCTIONAL,
            'пользовательские требования': RequirementType.USER,
            'требования к интерфейсу': RequirementType.INTERFACE,
        }
    )
