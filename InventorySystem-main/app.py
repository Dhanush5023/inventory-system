import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, session

from .models import db, Sellers, Products, Orders, OrderItems




# ==============================
# LOAD ENV
# ==============================

load_dotenv()

import os

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

# ==============================
# FLASK SETUP
# ==============================

app = Flask(__name__)

app.config.update(
    SQLALCHEMY_DATABASE_URI=DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret"),
    SQLALCHEMY_ENGINE_OPTIONS={
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
)

db.init_app(app)

# ==============================
# HOME
# ==============================

@app.route('/')
def home():
    if session.get("seller_id"):
        return redirect(url_for("products"))
    return render_template("home.html")

# ==============================
# SIGNUP
# ==============================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None

    if request.method == 'POST':
        name = request.form['name'].strip()
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not name or not username or not password:
            error = "All fields required"

        elif Sellers.query.filter_by(username=username).first():
            error = "Username already exists"

        else:
            user = Sellers(name=name, username=username, password=password)
            db.session.add(user)
            db.session.commit()

            session["seller_id"] = user.id
            return redirect(url_for('products'))

    return render_template('signup.html', error=error)

# ==============================
# LOGIN
# ==============================

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        user = Sellers.query.filter_by(username=username, password=password).first()

        if user:
            session["seller_id"] = user.id
            return redirect(url_for('products'))

        error = "Invalid credentials"

    return render_template("login.html", error=error)

# ==============================
# LOGOUT
# ==============================

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ==============================
# PRODUCTS
# ==============================

@app.route('/products')
def products():
    if "seller_id" not in session:
        return redirect(url_for("login"))

    products_list = Products.query.filter_by(
        seller_id=session["seller_id"]
    ).all()

    return render_template(
        "products.html",
        products=products_list,
        status=request.args.get("status"),
        error=request.args.get("error")
    )

# ==============================
# ADD PRODUCT
# ==============================

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if "seller_id" not in session:
        return redirect(url_for("login"))

    error = None

    if request.method == 'POST':
        try:
            expiry = request.form['expiry']
            expiry_val = datetime.strptime(expiry, "%Y-%m-%d") if expiry else None

            product = Products(
                name=request.form['name'],
                price=float(request.form['price']),
                quantity=int(request.form['quantity']),
                category=request.form['category'],
                expiry=expiry_val,
                seller_id=session["seller_id"]
            )

            db.session.add(product)
            db.session.commit()

            return redirect(url_for("products", status="Product added"))

        except Exception as e:
            error = str(e)

    return render_template("add_product.html", error=error)

# ==============================
# PRODUCT DETAIL
# ==============================

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    if "seller_id" not in session:
        return redirect(url_for("login"))

    product = Products.query.filter_by(
        id=product_id,
        seller_id=session["seller_id"]
    ).first()

    if not product:
        return redirect(url_for("products", error="Product not found"))

    return render_template("product_detail.html", product=product)

# ==============================
# UPDATE PRODUCT
# ==============================

@app.route('/products/update/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    if "seller_id" not in session:
        return redirect(url_for("login"))

    product = Products.query.filter_by(
        id=product_id,
        seller_id=session["seller_id"]
    ).first_or_404()

    if request.method == 'POST':
        expiry = request.form['expiry']

        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.quantity = int(request.form['quantity'])
        product.category = request.form['category']
        product.expiry = datetime.strptime(expiry, "%Y-%m-%d") if expiry else None

        db.session.commit()

        return redirect(url_for("products", status="Updated"))

    return render_template("update_product.html", product=product)

# ==============================
# DELETE PRODUCT (FIXED)
# ==============================

@app.route('/products/delete/<int:product_id>', methods=['GET', 'POST'])
def delete_product(product_id):

    if "seller_id" not in session:
        return redirect(url_for("login"))

    product = Products.query.filter_by(
        id=product_id,
        seller_id=session["seller_id"]
    ).first_or_404()

    if request.method == "POST":
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for("products", status="Deleted"))

    return render_template("delete_product.html", product=product)

# ==============================
# ORDERS
# ==============================

@app.route('/orders')
def orders():
    if "seller_id" not in session:
        return redirect(url_for("login"))

    orders_list = Orders.query.filter_by(
        seller_id=session["seller_id"]
    ).all()

    return render_template("orders.html", orders=orders_list)

# ==============================
# CREATE ORDER
# ==============================

@app.route('/order/create')
def create_order():
    if "seller_id" not in session:
        return redirect(url_for("login"))

    products_list = Products.query.filter_by(
        seller_id=session["seller_id"]
    ).all()

    return render_template(
        "create_order.html",
        products=products_list,
        order_items=session.get("order_items", [])
    )

@app.route('/order/add-item', methods=['POST'])
def add_order_item():

    pid = request.form.get("product_id")

    # prevent empty or invalid ID
    if not pid or not pid.isdigit():
        return redirect(url_for("create_order"))

    product = Products.query.get_or_404(int(pid))

    items = session.get("order_items", [])

    items.append({
        "product_id": product.id,
        "name": product.name,
        "quantity": int(request.form["quantity"]),
        "price": float(product.price)
    })

    session["order_items"] = items
    session.modified = True

    return redirect(url_for("create_order"))


@app.route('/order/submit', methods=['POST'])
def submit_order():

    items = session.get("order_items", [])
    order_type = request.form["order_type"]

    if not items:
        return redirect(url_for("create_order"))

    order = Orders(
        seller_id=session["seller_id"],
        type=order_type,
        total_price=0
    )

    db.session.add(order)
    db.session.commit()

    total = 0

    for i in items:
        product = Products.query.get(i["product_id"])

        db.session.add(OrderItems(
            order_id=order.id,
            product_id=product.id,
            quantity=i["quantity"],
            price=i["price"]
        ))

        if order_type == "Incoming":
            product.quantity += i["quantity"]
        else:
            product.quantity -= i["quantity"]

        total += i["quantity"] * i["price"]

    order.total_price = total
    db.session.commit()

    session.pop("order_items", None)

    return redirect(url_for("orders"))

# ==============================
# ORDER DETAIL
# ==============================

@app.route('/order/<int:order_id>')
def order_detail(order_id):

    if "seller_id" not in session:
        return redirect(url_for("login"))

    order = Orders.query.filter_by(
        id=order_id,
        seller_id=session["seller_id"]
    ).first()

    if not order:
        return redirect(url_for("orders"))

    items = OrderItems.query.filter_by(order_id=order.id).all()

    details = []

    for item in items:
        product = Products.query.get(item.product_id)

        details.append({
            "id": item.id,
            "product_name": product.name if product else "Deleted",
            "quantity": item.quantity,
            "price": item.price,
            "total": item.price * item.quantity
        })

    return render_template("order_detail.html", order=order, order_items=details)

# ==============================
# RUN
# ==============================

import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

