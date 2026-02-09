from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# =====================
# SELLERS
# =====================

class Sellers(db.Model):
    __tablename__ = "sellers"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


# =====================
# PRODUCTS
# =====================

class Products(db.Model):
    __tablename__ = "products"

    id = db.Column(db.BigInteger, primary_key=True)
    seller_id = db.Column(db.BigInteger, db.ForeignKey("sellers.id"))
    name = db.Column(db.String(100))
    price = db.Column(db.Numeric(10, 2))
    quantity = db.Column(db.Integer)
    category = db.Column(db.String(50))
    expiry = db.Column(db.Date)


# =====================
# ORDERS
# =====================

class Orders(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.BigInteger, primary_key=True)
    seller_id = db.Column(db.BigInteger, db.ForeignKey("sellers.id"))
    type = db.Column(db.String(20))
    total_price = db.Column(db.Numeric(10, 2))


# =====================
# ORDER ITEMS
# =====================

class OrderItems(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.BigInteger, primary_key=True)
    order_id = db.Column(db.BigInteger, db.ForeignKey("orders.id"))
    product_id = db.Column(db.BigInteger, db.ForeignKey("products.id"))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Numeric(10, 2))
