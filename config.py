"""Конфигурация приложения"""
import os

class Config:
    """Базовый класс конфигурации"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///requirements_trace.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
