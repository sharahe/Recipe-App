import sqlite3
from flask import g
from flask import Flask, request, redirect
from flask import render_template

app = Flask(__name__)


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


@app.route("/recipes/add/", methods=["POST", "GET"])
def recipes_add():
    if request.method == "POST":
        print(request.form["name"])

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO recipes ( recipe_name, cuisine, serving_size, prep_time, cook_time, total_time, instructions, additional_notes) values (?,?,?,?,?,?,?,?)",
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
                # request.form["img_str_file"],
            ),
        )
        conn.commit()
        return redirect("/recipes/" + str(cur.lastrowid))
    return render_template("add_recipe.html")


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
        print(request.form["name"])
        conn = get_db()
        cur = conn.cursor()
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
