from __future__ import annotations
import os
from datetime import datetime
from typing import Optional

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

# -----------------------------
# App + Config
# -----------------------------
app = Flask(__name__, instance_relative_config=True)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, "ecofinds.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# -----------------------------
# Constants
# -----------------------------
CATEGORIES = [
    "Electronics",
    "Home & Kitchen",
    "Books",
    "Fashion",
    "Sports",
    "Toys",
    "Other"
]

# -----------------------------
# Models
# -----------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship("Product", backref="seller", lazy=True)
    cart_items = db.relationship("CartItem", backref="user", lazy=True)
    orders = db.relationship("Order", backref="user", lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)
    price_rupees = db.Column(db.Integer, nullable=False, default=0)
    image_url = db.Column(db.String(255), nullable=True)

    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    product = db.relationship("Product")


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    price_rupees = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    product = db.relationship("Product")

# -----------------------------
# Login manager
# -----------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------
# Helpers
# -----------------------------
def parse_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    query = Product.query.order_by(Product.created_at.desc())
    if q:
        query = query.filter(Product.title.ilike(f"%{q}%"))
    if category:
        query = query.filter(Product.category == category)

    products = query.all()
    return render_template("index.html", products=products, q=q, category=category, categories=CATEGORIES)

# ---------- Auth ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not email or not username or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("signup"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return redirect(url_for("signup"))

        user = User(email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Signup successful. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("index"))
        flash("Invalid email or password", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("index"))

# ---------- User Dashboard ----------
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            flash("Username cannot be empty.", "danger")
            return redirect(url_for("dashboard"))
        current_user.username = username
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("dashboard"))
    return render_template("dashboard.html")

# ---------- Product CRUD ----------
@app.route("/products/new", methods=["GET", "POST"])
@login_required
def product_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        price_rupees = parse_int(request.form.get("price", "0"), 0)
        image_url = request.form.get("image_url", "").strip()

        if not title or not category:
            flash("Title and category are required.", "danger")
            return redirect(url_for("product_new"))
        if category not in CATEGORIES:
            flash("Invalid category.", "danger")
            return redirect(url_for("product_new"))

        product = Product(
            title=title,
            description=description,
            category=category,
            price_rupees=price_rupees,
            image_url=image_url if image_url else None,
            seller_id=current_user.id,
        )
        db.session.add(product)
        db.session.commit()
        flash("Listing created.", "success")
        return redirect(url_for("my_listings"))
    return render_template("product_form.html", categories=CATEGORIES, mode="new")


@app.route("/products/<int:product_id>")
def product_detail(product_id: int):
    product = Product.query.get_or_404(product_id)
    return render_template("product_detail.html", product=product)


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def product_edit(product_id: int):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id:
        flash("You can only edit your own listings.", "danger")
        return redirect(url_for("index"))
    if request.method == "POST":
        product.title = request.form.get("title", "").strip()
        product.description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        if category not in CATEGORIES:
            flash("Invalid category.", "danger")
            return redirect(url_for("product_edit", product_id=product.id))
        product.category = category
        product.price_rupees = parse_int(request.form.get("price", "0"), 0)
        image_url = request.form.get("image_url", "").strip()
        product.image_url = image_url if image_url else None
        db.session.commit()
        flash("Listing updated.", "success")
        return redirect(url_for("my_listings"))
    return render_template("product_form.html", categories=CATEGORIES, mode="edit", product=product)


@app.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def product_delete(product_id: int):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id:
        flash("You can only delete your own listings.", "danger")
        return redirect(url_for("index"))
    db.session.delete(product)
    db.session.commit()
    flash("Listing deleted.", "info")
    return redirect(url_for("my_listings"))


@app.route("/my-listings")
@login_required
def my_listings():
    products = Product.query.filter_by(seller_id=current_user.id).order_by(Product.created_at.desc()).all()
    return render_template("my_listings.html", products=products)

# ---------- Cart & Checkout ----------
@app.route("/cart")
@login_required
def cart_view():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(i.product.price_rupees * i.quantity for i in items if i.product)
    return render_template("cart.html", items=items, total=total)


@app.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def cart_add(product_id: int):
    product = Product.query.get_or_404(product_id)
    item = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    if item:
        item.quantity += 1
    else:
        item = CartItem(user_id=current_user.id, product_id=product.id, quantity=1)
        db.session.add(item)
    db.session.commit()
    flash("Added to cart.", "success")
    return redirect(url_for("cart_view"))


@app.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def cart_remove(item_id: int):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash("Cannot modify another user's cart.", "danger")
        return redirect(url_for("cart_view"))
    db.session.delete(item)
    db.session.commit()
    flash("Removed from cart.", "info")
    return redirect(url_for("cart_view"))


@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart_view"))
    order = Order(user_id=current_user.id)
    db.session.add(order)
    db.session.flush()  # get order.id

    for item in items:
        if not item.product:
            continue
        oi = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            title=item.product.title,
            price_rupees=item.product.price_rupees,
            quantity=item.quantity,
        )
        db.session.add(oi)
        db.session.delete(item)  # clear cart

    db.session.commit()
    flash("Checkout complete! Order created.", "success")
    return redirect(url_for("orders"))

# ---------- Orders (Previous Purchases) ----------
@app.route("/orders")
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders)

# -----------------------------
# Initialize database and Run
# -----------------------------
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
