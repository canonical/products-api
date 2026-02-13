from webapp.app import db


class Product(db.Model):
    """Product model - maps to products table."""

    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)


class Deployment(db.Model):
    """Deployment model - maps to deployments table."""

    __tablename__ = "deployments"
    id = db.Column(db.Integer, primary_key=True)


class Version(db.Model):
    """Version model - maps to versions table."""

    __tablename__ = "versions"
    id = db.Column(db.Integer, primary_key=True)
