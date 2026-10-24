"""Superset local dùng PostgreSQL metadata, secret qua env không commit."""

import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://superset:" + os.environ["POSTGRES_PASSWORD"] + "@postgres:5432/superset"
SQLALCHEMY_TRACK_MODIFICATIONS = False
WTF_CSRF_ENABLED = True
TALISMAN_ENABLED = False
FEATURE_FLAGS = {"ENABLE_TEMPLATE_PROCESSING": False}
MAPBOX_API_KEY = ""
