import os
from canonicalwebteam.flask_base.app import FlaskBase
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_apispec import FlaskApiSpec

app = FlaskBase(__name__, "products-api")

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# API Documentation
app.config.update(
    {
        "APISPEC_TITLE": "Products API",
        "APISPEC_VERSION": "v1",
        "APISPEC_OPENAPI_VERSION": "3.0.2",
        "APISPEC_URL_PREFIX": "/v1",
        "APISPEC_SWAGGER_URL": "/swagger",
        "APISPEC_SWAGGER_UI_URL": "/swagger-ui",
    }
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
docs = FlaskApiSpec(app)


@app.route("/v1/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8040, debug=True)
