"""Конфигурация приложения"""
import os
from models.requirement import RequirementType
import json

class Config:
    """Базовый класс конфигурации"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///requirements_trace.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REQUIREMENT_TYPE_ALIASES = {
        'бизнес-требования': RequirementType.BUSINESS.value,
        'функциональные требования': RequirementType.FUNCTIONAL.value,
        'нефункциональные требования': RequirementType.NON_FUNCTIONAL.value,
        'пользовательские требования': RequirementType.USER.value,
        'требования к интерфейсу': RequirementType.INTERFACE.value,
    }

