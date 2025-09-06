
from __future__ import annotations
import os
from datetime import datetime
from typing import List, Dict, Any

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# -----------------------------
# App + Config
# -----------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev_secret_key_change_me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///ecofinds.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

CATEGORIES = ["Home", "Fashion", "Electronics", "Outdoors", "Beauty", "Other"]

# -----------------------------
# Models
# -----------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    products = db.relationship("Product", backref="seller", lazy=True)
    orders = db.relationship("Order", backref="buyer", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.Float, nullable=False, default=0.0)
    category = db.Column(db.String(50), default="Other")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    total = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("OrderItem", backref="order", lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False, default=0.0)
    product = db.relationship("Product")

# -----------------------------
# Auth helpers
# -----------------------------
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Create tables at startup (Flask 3.x-safe)
with app.app_context():
    db.create_all()

# Seed minimal data if empty
    if not User.query.first():
        demo = User(email="demo@ecofinds.local", name="Demo User")
        demo.set_password("demo1234")
        db.session.add(demo)
        db.session.commit()
    if not Product.query.first():
        demo = User.query.first()
        seed = [
            Product(name="Bamboo Toothbrush", description="Eco-friendly bamboo toothbrush.", price=3.99, category="Beauty", seller_id=demo.id),
            Product(name="Reusable Water Bottle", description="Stainless steel bottle, 750ml.", price=14.50, category="Outdoors", seller_id=demo.id),
            Product(name="Organic Cotton Tote", description="Durable tote bag for daily use.", price=9.99, category="Fashion", seller_id=demo.id),
        ]
        db.session.add_all(seed)
        db.session.commit()

# -----------------------------
# Utilities
# -----------------------------
def get_cart() -> List[Dict[str, Any]]:
    return session.get("cart", [])

def save_cart(cart: List[Dict[str, Any]]) -> None:
    session["cart"] = cart

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    query = Product.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Product.name.ilike(like), Product.description.ilike(like)))
    if category:
        query = query.filter_by(category=category)

    products = query.order_by(Product.created_at.desc()).all()
    return render_template("index.html", products=products, q=q, category=category, categories=CATEGORIES)

@app.route("/product/<int:product_id>")
def product_detail(product_id: int):
    product = db.session.get(Product, product_id) or abort(404)
    return render_template("product_detail.html", product=product)

@app.route("/product/new", methods=["GET", "POST"])
@login_required
def product_form():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = float(request.form.get("price") or 0)
        category = request.form.get("category", "Other")
        if not name:
            flash("Product name is required.", "error")
            return redirect(url_for("product_form"))
        p = Product(name=name, description=description, price=price, category=category, seller_id=current_user.id)
        db.session.add(p)
        db.session.commit()
        flash("Product created.", "success")
        return redirect(url_for("my_listings"))
    return render_template("product_form.html", categories=CATEGORIES)

@app.route("/my-listings")
@login_required
def my_listings():
    listings = Product.query.filter_by(seller_id=current_user.id).order_by(Product.created_at.desc()).all()
    return render_template("my_listings.html", listings=listings)

@app.route("/dashboard")
@login_required
def dashboard():
    listings_count = Product.query.filter_by(seller_id=current_user.id).count()
    orders_count = Order.query.filter_by(user_id=current_user.id).count()
    cart_count = sum(item.get("quantity", 1) for item in get_cart())
    return render_template("dashboard.html", listings_count=listings_count, orders_count=orders_count, cart_count=cart_count)

# ------------- Auth -------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))
        login_user(user)
        flash("Welcome back!", "success")
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("signup"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for("signup"))
        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Account created. Welcome!", "success")
        return redirect(url_for("index"))
    return render_template("signup.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

# ------------- Cart -------------
@app.route("/cart")
def cart():
    cart_items = get_cart()
    total = sum(item["price"] * item.get("quantity", 1) for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total=total)

@app.route("/cart/add/<int:product_id>", methods=["POST", "GET"])
def add_to_cart(product_id: int):
    product = db.session.get(Product, product_id) or abort(404)
    cart = get_cart()
    # Try to merge quantities if already present
    for item in cart:
        if item["id"] == product.id:
            item["quantity"] = item.get("quantity", 1) + 1
            break
    else:
        cart.append({"id": product.id, "name": product.name, "price": product.price, "quantity": 1})
    save_cart(cart)
    flash("Added to cart.", "success")
    return redirect(url_for("cart"))

@app.route("/cart/remove/<int:product_id>", methods=["POST", "GET"])
def remove_from_cart(product_id: int):
    cart = [item for item in get_cart() if item["id"] != product_id]
    save_cart(cart)
    flash("Removed from cart.", "success")
    return redirect(url_for("cart"))

# ------------- Orders / Checkout -------------
@app.route("/checkout", methods=["POST", "GET"])
@login_required
def checkout():
    cart = get_cart()
    if not cart:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart"))
    total = sum(item["price"] * item.get("quantity", 1) for item in cart)
    order = Order(user_id=current_user.id, total=total)
    db.session.add(order)
    db.session.flush()  # get order.id
    for item in cart:
        db.session.add(OrderItem(order_id=order.id, product_id=item["id"], quantity=item.get("quantity",1), price=item["price"]))
    db.session.commit()
    save_cart([])
    flash(f"Order #{order.id} placed successfully!", "success")
    return redirect(url_for("orders"))

@app.route("/orders")
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders)

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
