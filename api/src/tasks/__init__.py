"""Celery tasks package."""

from .training import train_online_model

__all__ = ["train_online_model"]
