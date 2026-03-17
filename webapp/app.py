from canonicalwebteam.flask_base.app import FlaskBase
from canonicalwebteam.flask_base.env import get_flask_env
from flask import jsonify
from flask_apispec import FlaskApiSpec
from webapp.database import db, migrate
import webapp.views as views

app = FlaskBase(__name__, "products-api")

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = get_flask_env("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# API Documentation
app.config.update(
    {
        "APISPEC_TITLE": "Products API",
        "APISPEC_VERSION": "v1",
        "APISPEC_OPENAPI_VERSION": "3.0.2",
        "APISPEC_SWAGGER_URL": "/swagger",
        "APISPEC_SWAGGER_UI_URL": "/swagger-ui",
    }
)

db.init_app(app)
migrate.init_app(app, db)
docs = FlaskApiSpec(app)

app.add_url_rule("/products", view_func=views.get_products, methods=["GET"])
app.add_url_rule(
    "/products/<string:product_slug>",
    view_func=views.get_product,
    methods=["GET"],
)
app.add_url_rule(
    "/products/<string:product_slug>/<string:deployment_slug>",
    view_func=views.get_product_deployment,
    methods=["GET"],
)


@app.errorhandler(422)
def handle_validation_error(error):
    messages = error.data.get("messages", {})

    return (
        jsonify(
            {
                "error": {
                    "message": "Invalid request.",
                    "details": messages.get("query", messages),
                }
            }
        ),
        400,
    )


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8040, debug=True)
