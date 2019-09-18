from flask import render_template, request, Blueprint, redirect, url_for
from paywac import db

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home():
    return render_template('home.html')


@main.route("/about")
def about():
    return render_template('about.html', title='About')


@main.route('/create_db')
def create_db():
    db.create_all()
    return redirect(url_for('main.home'))