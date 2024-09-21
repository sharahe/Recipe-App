import sqlite3
import os
from flask import g
from flask import Flask, request, redirect, flash, send_from_directory
from flask import render_template
from werkzeug.utils import secure_filename
import datetime


UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def index():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM items")
    print(cur.fetchall())
    return "<p>Hello, World!!! Main Page</p>"


@app.route("/index/", methods=["POST", "GET"])
def hello_index():
    if request.method == "POST":
        print(request.form["Name"])
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO items (name, category, quantity, notes) values (?,?,?,?)",
            (
                request.form["Name"],
                request.form["Category"],
                request.form["Quantity"],
                request.form["Notes"],
            ),
        )
        conn.commit()
    cur = get_db().cursor()
    cur.execute("SELECT * FROM items")
    rows = cur.fetchall()
    return render_template("index.html", rows=rows)


@app.route("/recipes/")
def recipes():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM recipes WHERE deleted=0")
    rows = cur.fetchall()
    print(rows)
    return render_template("recipes.html", rows=rows)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/recipes/add/", methods=["POST", "GET"])
def recipes_add():
    if request.method == "POST":
        filename = ""
        if "add-image" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["add-image"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        print(request.form["name"])

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO recipes ( recipe_name, cuisine, serving_size, prep_time, cook_time, total_time, instructions, additional_notes, img_str_file) values (?,?,?,?,?,?,?,?,?)",
            (
                # request.form["recipe_id"], # autoincrements on its own?
                request.form["name"],
                request.form["cuisine"],
                request.form["serving-size"],
                request.form["prep-time"],
                request.form["cook-time"],
                float(request.form["prep-time"]) + float(request.form["cook-time"]),
                request.form["instructions"],
                request.form["notes"],
                filename,
            ),
        )
        conn.commit()
        print(file)

        return redirect("/recipes/" + str(cur.lastrowid))
    return render_template("add_recipe.html")


@app.route("/uploads/<name>")
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route("/recipes/<int:recipe_id>")
def recipe(recipe_id):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM recipes WHERE recipe_id = ? AND deleted=0", (recipe_id,))
    rows = cur.fetchall()
    print(rows)
    return render_template("recipe.html", rows=rows)


@app.route("/recipes/<int:recipe_id>/edit", methods=["POST", "GET"])
def recipe_edit(recipe_id):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM recipes WHERE recipe_id = ? AND deleted=0", (recipe_id,))
    rows = cur.fetchall()
    if request.method == "POST":
        filename = ""
        # rows[0]["img_str_file"]

        file = request.files["add-image"]

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        print(request.form["name"])
        conn = get_db()
        cur = conn.cursor()
        if filename == "":
            cur.execute(
                "UPDATE recipes SET recipe_name = ?, cuisine = ?, serving_size = ?, prep_time = ?, cook_time = ?, total_time = ?, instructions = ?, additional_notes = ? WHERE recipe_id = ? AND deleted=0",
                (
                    request.form["name"],
                    request.form["cuisine"],
                    request.form["serving-size"],
                    request.form["prep-time"],
                    request.form["cook-time"],
                    float(request.form["prep-time"]) + float(request.form["cook-time"]),
                    request.form["instructions"],
                    request.form["notes"],
                    recipe_id,
                ),
            )
        else:
            cur.execute(
                "UPDATE recipes SET recipe_name = ?, cuisine = ?, serving_size = ?, prep_time = ?, cook_time = ?, total_time = ?, instructions = ?, additional_notes = ?, img_str_file= ? WHERE recipe_id = ? AND deleted=0",
                (
                    request.form["name"],
                    request.form["cuisine"],
                    request.form["serving-size"],
                    request.form["prep-time"],
                    request.form["cook-time"],
                    float(request.form["prep-time"]) + float(request.form["cook-time"]),
                    request.form["instructions"],
                    request.form["notes"],
                    filename,
                    recipe_id,
                ),
            )
        conn.commit()
        return redirect("/recipes/" + str(recipe_id))
    return render_template("edit_recipe.html", rows=rows)


@app.route("/recipes/<int:recipe_id>/delete")
def recipe_delete(recipe_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE recipes SET deleted=TRUE WHERE recipe_id = ?", (recipe_id,))
    conn.commit()
    return redirect("/recipes/")


# def get_records():
#     with conn:
#         cur.execute("SELECT * FROM items")
#         print(curr.fetchall())

DATABASE = "database.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
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


migrations = [
    "CREATE TABLE IF NOT EXISTS locations (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,room TEXT);",
    "CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT,location_id INTEGER,name TEXT,category TEXT,quantity FLOAT,notes TEXT);",
    "CREATE TABLE IF NOT EXISTS recipes (recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,recipe_name TEXT,cuisine TEXT,serving_size INTEGER,prep_time INTEGER,cook_time INTEGER,total_time INTEGER,instructions TEXT,additional_notes TEXT,img_str_file TEXT,deleted BOOLEAN DEFAULT FALSE);",
    "CREATE TABLE IF NOT EXISTS recipe_to_ingredients (recipe_id INTEGER,ingredient_id INTEGER,quantity FLOAT,unit TEXT);",
    "CREATE TABLE IF NOT EXISTS ingredients (ingredient_id INTEGER,ingredient_name TEXT,ingredient_category TEXT);",
    """CREATE VIRTUAL TABLE recipe_search USING FTS5(recipe_name, instructions, additional_notes, cuisine);""",
]

with app.app_context():
    print("initializing")
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS migration_log (id INTEGER PRIMARY KEY, version INTEGER, created_at TEXT )"
    )
    cur.execute("SELECT MAX(version) as v from migration_log")
    rows = cur.fetchall()

    max_version = rows[0]["v"]
    if max_version < len(migrations):
        for i, x in enumerate(migrations[max_version:]):
            cur.execute(x)
            print("Running Migration ", x)
            n = datetime.datetime.now(datetime.timezone.utc)

            cur.execute(
                "INSERT INTO migration_log (version,created_at) values (?,?)",
                (i + max_version + 1, n.isoformat()),
            )
            db.commit()
