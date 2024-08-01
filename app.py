import sqlite3
from flask import g
from flask import Flask

from flask import render_template

app = Flask(__name__)


@app.route("/")
def index():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM items")
    print(cur.fetchall())
    return "<p>Hello, World????! Hi Shara</p>"


@app.route("/index/")
@app.route("/index/<name>")
def hello(name=None):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM items")
    rows = cur.fetchall()
    return render_template("index.html", person=name, rows=rows)


# def get_records():
#     with conn:
#         cur.execute("SELECT * FROM items")
#         print(curr.fetchall())

DATABASE = "database.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource("schema.sql", mode="r") as f:
            db.cursor().executescript(f.read())
        db.commit()
