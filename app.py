import os
import re
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for
)
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Blog, Admin


app = Flask(__name__)

# -----------------------
# Güvenlik
# -----------------------
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

# -----------------------
# Database
# -----------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# -----------------------
# Yardımcı fonksiyonlar
# -----------------------
def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "-", text.strip())


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


# -----------------------
# Public sayfalar
# -----------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# -----------------------
# Blog (ziyaretçi)
# -----------------------
@app.route("/blog")
def blog_list():
    blogs = Blog.query.order_by(Blog.created_at.desc()).all()
    return render_template("blog.html", blogs=blogs)


@app.route("/blog/<slug>")
def blog_detail(slug):
    blog = Blog.query.filter_by(slug=slug).first_or_404()
    return render_template("blog-detail.html", blog=blog)


# -----------------------
# Admin login / logout
# -----------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin = Admin.query.filter_by(
            username=request.form["username"]
        ).first()

        if admin and check_password_hash(
            admin.password,
            request.form["password"]
        ):
            session["admin"] = admin.id
            return redirect(url_for("admin_blogs"))

    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


# -----------------------
# Admin blog işlemleri
# -----------------------
@app.route("/admin/blogs")
@admin_required
def admin_blogs():
    blogs = Blog.query.order_by(Blog.created_at.desc()).all()
    return render_template("admin/blogs.html", blogs=blogs)


@app.route("/admin/blog/add", methods=["GET", "POST"])
@admin_required
def blog_add():
    if request.method == "POST":
        blog = Blog(
            title=request.form["title"],
            slug=slugify(request.form["title"]),
            meta_description=request.form.get("meta_description"),
            content=request.form["content"]
        )

        db.session.add(blog)
        db.session.commit()
        return redirect(url_for("admin_blogs"))

    return render_template("admin/blog-add.html")


@app.route("/admin/blog/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def blog_edit(id):
    blog = Blog.query.get_or_404(id)

    if request.method == "POST":
        blog.title = request.form["title"]
        blog.slug = slugify(blog.title)
        blog.meta_description = request.form.get("meta_description")
        blog.content = request.form["content"]

        db.session.commit()
        return redirect(url_for("admin_blogs"))

    return render_template("admin/blog-edit.html", blog=blog)


@app.route("/admin/blog/delete/<int:id>")
@admin_required
def blog_delete(id):
    blog = Blog.query.get_or_404(id)
    db.session.delete(blog)
    db.session.commit()
    return redirect(url_for("admin_blogs"))


# -----------------------
# Admin şifre değiştir
# -----------------------
@app.route("/admin/password", methods=["GET", "POST"])
@admin_required
def admin_change_password():
    admin = Admin.query.get(session["admin"])

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        new_password_confirm = request.form["new_password_confirm"]

        if not check_password_hash(admin.password, current_password):
            return render_template(
                "admin/change-password.html",
                error="Mevcut şifre yanlış"
            )

        if new_password != new_password_confirm:
            return render_template(
                "admin/change-password.html",
                error="Yeni şifreler eşleşmiyor"
            )

        admin.password = generate_password_hash(new_password)
        db.session.commit()

        return render_template(
            "admin/change-password.html",
            success="Şifre başarıyla güncellendi"
        )

    return render_template("admin/change-password.html")
