import io
import os
import unittest
import warnings
from contextlib import redirect_stderr

import flask_migrate
from sqlalchemy_utils import create_database, database_exists


if "TEST_DATABASE_URL" not in os.environ:
    raise RuntimeError(
        "TEST_DATABASE_URL environment variable must be set before running tests."
    )

os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

from tests.fixtures.models import make_models  # noqa: E402
from webapp.app import app, db  # noqa: E402


with app.app_context():
    if not database_exists(db.engine.url):
        create_database(db.engine.url)

warnings.filterwarnings(action="ignore", category=ResourceWarning)


class BaseTestCase(unittest.TestCase):
    db = db

    def setUp(self):
        app.testing = True
        self.context = app.app_context()
        self.context.push()
        self.db.drop_all()
        with redirect_stderr(io.StringIO()):
            flask_migrate.stamp(revision="base")
        with redirect_stderr(io.StringIO()):
            flask_migrate.upgrade()
        self.models = make_models()
        self.db.session.add(self.models["product"])
        self.db.session.add(self.models["deployment"])
        self.db.session.add(self.models["version"])
        self.db.session.commit()
        self.client = app.test_client()
        return super().setUp()

    def tearDown(self):
        self.db.session.close()
        self.context.pop()
        return super().tearDown()