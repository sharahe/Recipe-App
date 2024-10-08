import sqlite3
import os
from flask import g
from flask import Flask, request, redirect, flash, send_from_directory, url_for
from flask import render_template
from werkzeug.utils import secure_filename
import datetime
from openai import OpenAI
import json
import random
import shutil
import math
import requests

client = OpenAI()


UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/index/", methods=["POST", "GET"])
def hello_index():
    if request.method == "POST":
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


@app.route("/")
def recipes():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM recipes WHERE deleted=0")
    rows = cur.fetchall()
    return render_template("recipes.html", rows=rows)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/add/", methods=["POST", "GET"])
def recipes_add():
    if request.method == "POST":
        filename = ""
        if "add-image" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["add-image"]
        prompt_prefix = ""
        if len(request.form["name"]) == 0:
            prompt_prefix = "waves"
        else:
            prompt_prefix = request.form["name"]

        if file.filename == "":
            response = client.images.generate(
                model="dall-e-2",
                prompt=prompt_prefix + " high quality photography using Canon EOS R3.",
                size="256x256",
                quality="standard",
                n=1,
            )
            gen_img = response.data[0].url
            rand = math.floor(random.random() * 1000)
            filename = secure_filename(request.form["name"] + str(rand) + ".png")

            response = requests.get(gen_img, stream=True)
            with open(
                os.path.join(app.config["UPLOAD_FOLDER"], filename), "wb"
            ) as out_file:
                shutil.copyfileobj(response.raw, out_file)
            del response

        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

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
            "INSERT INTO recipes ( recipe_name, cuisine, serving_size, prep_time, cook_time, total_time, instructions, additional_notes, img_str_file, recipe_search_id, url, video_tips) values (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                request.form["name"],
                request.form["cuisine"],
                request.form["serving-size"],
                request.form["prep-time"],
                request.form["cook-time"],
                (
                    (
                        float(request.form["prep-time"])
                        + float(request.form["cook-time"])
                    )
                    if len(request.form["prep-time"]) > 0
                    and len(request.form["cook-time"]) > 0
                    else ""
                ),
                request.form["instructions"],
                request.form["notes"],
                filename,
                cur.lastrowid,
                request.form["recipe-url"],
                request.form["video-tips"],
            ),
        )

        recipe_id = cur.lastrowid

        # print("INGREDIENT_NUMBER", type(request.form["ingredient-number"]))
        for i in range(int(request.form["ingredient-number"])):

            # for every ingredient, check if it exists in the ingredients table. otherwise add to ingredients
            # add row to ingredients recipe table
            cur.execute(
                "SELECT id from ingredients WHERE name = ?",
                (request.form["ingredients-" + str(i)],),
            )

            ingred_exist = cur.fetchone()
            ingredient_id = None
            if ingred_exist is None:
                cur.execute(
                    "INSERT INTO ingredients  (name) values (?) ",
                    (request.form["ingredients-" + str(i)],),
                )
                conn.commit()
                ingredient_id = cur.lastrowid
            else:
                ingredient_id = ingred_exist[0]

            cur.execute(
                "INSERT INTO recipe_to_ingredients (recipe_id, ingredient_id, quantity, unit) values (?, ?, ?, ?)",
                (
                    recipe_id,
                    ingredient_id,
                    request.form["quantity-" + str(i)],
                    request.form["unit-" + str(i)],
                ),
            )

        conn.commit()

        return redirect("/" + str(recipe_id))
    return render_template("add_recipe.html")


@app.route("/uploads/<name>")
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route("/<int:recipe_id>")
def recipe(recipe_id):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM recipes WHERE recipe_id = ? AND deleted=0", (recipe_id,))
    rows = cur.fetchall()

    cur.execute(
        "SELECT * FROM recipe_to_ingredients r INNER JOIN ingredients i ON r.recipe_id = ? AND r.ingredient_id = i.id",
        (recipe_id,),
    )
    ingredients = cur.fetchall()
    return render_template("recipe.html", rows=rows, ingredients=ingredients)


@app.route("/<int:recipe_id>/ingredients")
def recipe_ingredient_json(recipe_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM recipe_to_ingredients r INNER JOIN ingredients i ON r.recipe_id = ? AND r.ingredient_id = i.id",
        (recipe_id,),
    )
    ingredients = cur.fetchall()

    ingredients_ls = []
    for i in ingredients:

        ingredients_ls.append(
            {"name": i["name"], "quantity": i["quantity"], "unit": i["unit"]}
        )

    return {"ingredients": ingredients_ls}


@app.route("/<int:recipe_id>/edit", methods=["POST", "GET"])
def recipe_edit(recipe_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes WHERE recipe_id = ? AND deleted=0", (recipe_id,))
    rows = cur.fetchall()
    if request.method == "POST":

        print("INGREDIENT_NUMBER", type(request.form["ingredient-number"]))

        cur.execute(
            "SELECT * FROM recipe_to_ingredients r INNER JOIN ingredients i ON r.ingredient_id = i.id WHERE r.recipe_id = ? ",
            (recipe_id,),
        )
        ingredients = cur.fetchall()

        for i in range(int(request.form["ingredient-number"])):

            q = request.form["quantity-" + str(i)]
            u = request.form["unit-" + str(i)]
            n = request.form["ingredients-" + str(i)]
            # if ingredient name dne in recipe to ingredients table, insert to table
            exists_in_table = False
            ingredient_id = 0
            for j in ingredients:
                if n == j["name"]:
                    exists_in_table = True
                    ingredient_id = j["id"]

            if exists_in_table:

                cur.execute(
                    "UPDATE recipe_to_ingredients SET quantity = ?, unit = ? WHERE recipe_id = ? AND ingredient_id = ? ",
                    (q, u, recipe_id, ingredient_id),
                )
                conn.commit()
            else:

                cur.execute(
                    "SELECT id from ingredients WHERE name = ?",
                    (n,),
                )

                ingred_exist = cur.fetchone()
                ingredient_id = None
                if ingred_exist is None:
                    cur.execute(
                        "INSERT INTO ingredients  (name) values (?) ",
                        (n,),
                    )
                    conn.commit()
                    ingredient_id = cur.lastrowid
                else:
                    ingredient_id = ingred_exist[0]

                cur.execute(
                    "INSERT INTO recipe_to_ingredients (recipe_id, ingredient_id, quantity, unit) values (?, ?, ?, ?)",
                    (
                        recipe_id,
                        ingredient_id,
                        q,
                        u,
                    ),
                )
                conn.commit()

            # if ingred dne in ingredients table, insert to ingredients
            # if ingredient name is in recipe to ingr table, update row
        for j in ingredients:
            exists_in_input = False
            for i in range(int(request.form["ingredient-number"])):

                q = request.form["quantity-" + str(i)]
                u = request.form["unit-" + str(i)]
                n = request.form["ingredients-" + str(i)]

                if n == j["name"]:
                    exists_in_input = True

            if not exists_in_input:
                print("DELETE", j["id"], recipe_id)
                cur.execute(
                    "DELETE FROM recipe_to_ingredients where ingredient_id = ? AND recipe_id = ?",
                    (j["id"], recipe_id),
                )
                conn.commit()

        # for ingred in recipe to ing:
        # if ing dne in input_ing, del row in recip to ing

        filename = ""
        # rows[0]["img_str_file"]

        file = request.files["add-image"]

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

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
                "UPDATE recipes SET recipe_name = ?, cuisine = ?, serving_size = ?, prep_time = ?, cook_time = ?, total_time = ?, instructions = ?, additional_notes = ?, url=?, video_tips = ? WHERE recipe_id = ? AND deleted=0",
                (
                    request.form["name"],
                    request.form["cuisine"],
                    request.form["serving-size"],
                    request.form["prep-time"],
                    request.form["cook-time"],
                    (
                        (
                            float(request.form["prep-time"])
                            + float(request.form["cook-time"])
                        )
                        if len(request.form["prep-time"]) > 0
                        and len(request.form["cook-time"]) > 0
                        else ""
                    ),
                    request.form["instructions"],
                    request.form["notes"],
                    request.form["recipe-url"],
                    request.form["video-tips"],
                    recipe_id,
                ),
            )
        else:
            cur.execute(
                "UPDATE recipes SET recipe_name = ?, cuisine = ?, serving_size = ?, prep_time = ?, cook_time = ?, total_time = ?, instructions = ?, additional_notes = ?, url=?, video_tips = ?, img_str_file= ? WHERE recipe_id = ? AND deleted=0",
                (
                    request.form["name"],
                    request.form["cuisine"],
                    request.form["serving-size"],
                    request.form["prep-time"],
                    request.form["cook-time"],
                    (
                        (
                            float(request.form["prep-time"])
                            + float(request.form["cook-time"])
                        )
                        if len(request.form["prep-time"]) > 0
                        and len(request.form["cook-time"]) > 0
                        else ""
                    ),
                    request.form["instructions"],
                    request.form["notes"],
                    request.form["recipe-url"],
                    request.form["video-tips"],
                    filename,
                    recipe_id,
                ),
            )
        conn.commit()
        return redirect("/" + str(recipe_id))
    return render_template("edit_recipe.html", rows=rows)


@app.route("/<int:recipe_id>/delete")
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
    return redirect("/")


@app.route("/pantry/add", methods=["POST", "GET"])
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

        return redirect("/pantry")
    return render_template("add_ingredient.html")


@app.route("/pantry/<int:ingredient_id>/edit", methods=["POST", "GET"])
def ingred_edit(ingredient_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ingredients WHERE id = ?", (ingredient_id,))
    rows = cur.fetchall()
    if request.method == "POST":

        cur.execute(
            "UPDATE  ingredients SET  name=?, category =? , quantity=?, unit=?, perishable=?, last_updated=? WHERE id=?",
            (
                request.form["name"],
                request.form["category"],
                request.form["quantity"],
                request.form["unit"],
                request.form["perishable"],
                datetime.datetime.now(datetime.timezone.utc),
                ingredient_id,
            ),
        )
        conn.commit()

        return redirect("/pantry")
    return render_template("edit_ingredient.html", row=rows[0])


@app.route("/pantry")
def ingred():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM ingredients WHERE quantity IS NOT NULL")
    rows = cur.fetchall()

    return render_template("ingredients.html", rows=rows)


@app.route("/pantry/recipe")
def ingred_from_recipe():
    cur = get_db().cursor()

    cur.execute("SELECT * FROM ingredients WHERE quantity IS NULL ORDER BY name")
    rows = cur.fetchall()

    return render_template("ingredients.html", rows=rows)


@app.route("/suggest")
def suggest():
    cur = get_db().cursor()
    cur.execute("SELECT name FROM ingredients WHERE quantity IS NOT NULL")
    rows = cur.fetchall()

    ingredient_str = ""

    for i in rows:
        ingredient_str = ingredient_str + "- " + i["name"] + "\n"

    cur.execute("SELECT recipe_id, recipe_name FROM recipes WHERE deleted = 0")
    rows = cur.fetchall()

    recipe_str = ""

    for i, x in enumerate(rows):
        recipe_str = recipe_str + str(x["recipe_id"]) + ". " + x["recipe_name"] + "\n"

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

Tell me which of the recipes I have provided is a good match for the ingredients I have.  There can be up to 3 matches, but don't include the recipe if we don't have most of the ingredients needed. Rank the recipes by how many of the ingredients are used. Reference the recipe by its number listed above. Do not list out the recipe steps, just the number. Do not start the reasoning with the recipe name.""".format(
                    recipe_str, ingredient_str
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "ingredient_reasoning",
                "schema": {
                    "type": "object",
                    "properties": {
                        "recipes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "number"},
                                    "reasoning": {"type": "string"},
                                },
                                "required": ["id", "reasoning"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["recipes"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
    )
    print(recipe_str, ingredient_str)
    print(completion.choices[0].message)

    output = json.loads(completion.choices[0].message.content)
    top_recipes = []
    for i in output["recipes"]:

        recipe_id = i["id"]
        recipe_reasoning = i["reasoning"]
        print(recipe_id, type(recipe_id))
        cur = get_db().cursor()
        cur.execute(
            "SELECT * FROM recipes WHERE deleted = 0 and recipe_id = ?",
            (recipe_id,),
        )
        recipe_details = cur.fetchone()
        top_recipes.append(recipe_details)
        # print(recipe_details["recipe_name"])

    return render_template(
        "suggest.html", rows=rows, chat=output, top_recipes=top_recipes
    )


@app.route("/search")
def search_recipe():
    keyword = request.args.get("keyword")

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

    return render_template("recipes.html", rows=rows, keyword=keyword)


@app.route("/import_search")
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
    return redirect("/")


@app.route("/<int:recipe_id>/favorite")
def favorite_recipe(recipe_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT favorite from recipes where recipe_id = ?", (recipe_id,))
    fave = cur.fetchone()

    cur.execute(
        "UPDATE recipes SET favorite = ? WHERE recipe_id = ?",
        ((fave["favorite"] + 1) % 2, recipe_id),
    )
    conn.commit()

    return redirect(request.referrer)


@app.route("/favorites")
def favorites():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM recipes WHERE deleted=0 and favorite=1")
    rows = cur.fetchall()

    return render_template("recipes.html", rows=rows)


@app.route("/reset")
def reset():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DROP TABLE items")
    cur.execute("DROP TABLE locations")
    cur.execute("DROP TABLE recipes")
    cur.execute("DROP TABLE ingredients")
    cur.execute("DROP TABLE recipe_to_ingredients")
    cur.execute("DROP TABLE recipe_search")
    cur.execute("DROP TABLE migration_log")
    conn.commit()
    with app.open_resource("dump.sql", mode="r") as f:
        conn.cursor().executescript(f.read())
    conn.commit()
    return redirect("/")


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
    "ALTER TABLE recipes ADD COLUMN url TEXT",
    "ALTER TABLE recipes ADD COLUMN video_tips TEXT",
]


with app.app_context():

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


import generate_tips
