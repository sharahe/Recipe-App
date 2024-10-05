import sqlite3
import os
from flask import g
from flask import Flask, request, redirect, flash, send_from_directory
from flask import render_template
from werkzeug.utils import secure_filename
import datetime
from openai import OpenAI

client = OpenAI()


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
            "INSERT INTO recipe_search ( recipe_name, cuisine, instructions, additional_notes) values (?,?,?,?)",
            (
                request.form["name"],
                request.form["cuisine"],
                request.form["instructions"],
                request.form["notes"],
            ),
        )
        cur.execute(
            "INSERT INTO recipes ( recipe_name, cuisine, serving_size, prep_time, cook_time, total_time, instructions, additional_notes, img_str_file, recipe_search_id) values (?,?,?,?,?,?,?,?,?,?)",
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
                cur.lastrowid,
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
        cur.execute(
            "SELECT recipe_search_id from recipes where recipe_id = ?", (recipe_id,)
        )
        row = cur.fetchone()
        cur.execute(
            "UPDATE recipe_search SET recipe_name = ?, cuisine = ?, instructions = ?, additional_notes = ? WHERE rowid = ?",
            (
                request.form["name"],
                request.form["cuisine"],
                request.form["instructions"],
                request.form["notes"],
                row[0],
            ),
        )
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
    cur.execute(
        "SELECT recipe_search_id from recipes where recipe_id = ?", (recipe_id,)
    )
    row = cur.fetchone()
    cur.execute("DELETE FROM recipe_search where rowid = ?", (row[0],))
    cur.execute("UPDATE recipes SET deleted=TRUE WHERE recipe_id = ?", (recipe_id,))
    conn.commit()
    return redirect("/recipes/")


@app.route("/recipes/pantry/add", methods=["POST", "GET"])
def ingred_add():
    if request.method == "POST":

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO ingredients ( name, category, quantity, unit, perishable, last_updated) values (?,?,?,?,?,?)",
            (
                request.form["name"],
                request.form["category"],
                request.form["quantity"],
                request.form["unit"],
                request.form["perishable"],
                datetime.datetime.now(datetime.timezone.utc),
            ),
        )
        conn.commit()

        return redirect("/recipes/pantry")
    return render_template("add_ingredient.html")


@app.route("/recipes/pantry")
def ingred():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM ingredients")
    rows = cur.fetchall()
    print(rows)
    return render_template("ingredients.html", rows=rows)


@app.route("/recipes/suggest")
def suggest():
    cur = get_db().cursor()
    cur.execute("SELECT name FROM ingredients")
    rows = cur.fetchall()
    print(rows)
    ingredient_str = ""

    for i in rows:
        ingredient_str = ingredient_str + "- " + i["name"] + "\n"

    print(ingredient_str)
    cur.execute("SELECT recipe_name FROM recipes")
    rows = cur.fetchall()

    recipe_str = ""

    for i, x in enumerate(rows):
        recipe_str = recipe_str + str(i + 1) + ". " + x["recipe_name"] + "\n"
    print(recipe_str)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": """Here are the names of the recipes I have to choose from: 
{}

I have the following ingredients: 
{}

Tell me which of the recipes I have provided is a good match for the ingredients I have.  There can be up to 3 matches, but don't include the recipe if we don't have most of the ingredients needed. Rank the recipes by how many of the ingredients are used. Reference the recipe by its number listed above. Do not list out the recipe steps, just the number""".format(
                    recipe_str, ingredient_str
                ),
            },
        ],
    )

    print(completion.choices[0].message)
    return render_template(
        "suggest.html", rows=rows, chat=completion.choices[0].message.content
    )


@app.route("/recipes/search")
def search_recipe():
    keyword = request.args.get("keyword")
    print(keyword)
    cur = get_db().cursor()

    cur.execute(
        "SELECT rowid FROM recipe_search WHERE recipe_search MATCH ?", (keyword,)
    )
    rows = cur.fetchall()
    rowids = []
    for i in rows:
        rowids.append(i[0])
    cur.execute(
        f"SELECT * FROM recipes WHERE recipe_search_id in ({','.join(['?']*len(rowids))})",
        rowids,
    )
    rows = cur.fetchall()

    print(rows)
    return render_template("search_recipe.html", rows=rows, keyword=keyword)


@app.route("/recipes/import_search")
def import_recipe_search():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes WHERE recipe_search_id is NULL")
    rows = cur.fetchall()
    for i in rows:
        cur.execute(
            "INSERT INTO recipe_search ( recipe_name, cuisine, instructions, additional_notes) values (?,?,?,?)",
            (
                i["recipe_name"],
                i["cuisine"],
                i["instructions"],
                i["additional_notes"],
            ),
        )

        cur.execute(
            "UPDATE recipes SET recipe_search_id = ? WHERE recipe_id = ?",
            (cur.lastrowid, i["recipe_id"]),
        )
        conn.commit()
    return redirect("/recipes")


@app.route("/recipes/<int:recipe_id>/favorite")
def favorite_recipe(recipe_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT favorite from recipes where recipe_id = ?", (recipe_id,))
    fave = cur.fetchone()
    print(recipe_id, fave["favorite"])

    cur.execute(
        "UPDATE recipes SET favorite = ? WHERE recipe_id = ?",
        ((fave["favorite"] + 1) % 2, recipe_id),
    )
    conn.commit()

    return redirect(request.referrer)


@app.route("/recipes/favorites")
def favorites():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM recipes WHERE deleted=0 and favorite=1")
    rows = cur.fetchall()
    print(rows)
    return render_template("recipes.html", rows=rows)


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
    "DROP TABLE ingredients;",
    "CREATE TABLE IF NOT EXISTS ingredients (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,category TEXT,quantity FLOAT,unit TEXT,perishable TEXT,last_updated TEXT);",
    "ALTER TABLE recipes ADD COLUMN recipe_search_id INTEGER",
    "ALTER TABLE recipes ADD COLUMN favorite BOOLEAN DEFAULT FALSE",
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
    if max_version is None:
        max_version = 0
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
