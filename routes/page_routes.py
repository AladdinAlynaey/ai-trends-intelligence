"""
Page routes — serves HTML pages.
"""
from flask import Blueprint, render_template, g, request, redirect, url_for

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    return render_template("index.html")


@pages_bp.route("/login")
def login_page():
    return render_template("login.html")


@pages_bp.route("/register")
def register_page():
    return render_template("register.html")


@pages_bp.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@pages_bp.route("/trends")
def trends_page():
    return render_template("trends.html")


@pages_bp.route("/articles")
def articles_page():
    return render_template("articles.html")


@pages_bp.route("/search")
def search_page():
    return render_template("search.html")


@pages_bp.route("/publish")
def publish_page():
    return render_template("publish.html")


@pages_bp.route("/admin")
def admin_page():
    return render_template("admin.html")


@pages_bp.route("/settings")
def settings_page():
    return render_template("settings.html")
