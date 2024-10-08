# Recipe-App

<h3>Hi, I'm Shara!</h3>
  <p>
    I love eating food and trying new recipes. Who doesn't? After cooking a lot
    of recipes, I was facing 3 main problems:
  </p>
  <ol>
    <li>
      I was having trouble with figuring out what new and creative recipes I
      could make with a given set of ingredients at home.
    </li>
    <li>It was becoming hard to keep track of the modifications I made.</li>
    <li>
      My job was increasingly using LLMs and I wanted to improve my skills
      through hands-on experience with them.
    </li>
  </ol>
  <p>
    So, I created Recipe-App. It's intended to solve those problems, and serve
    as an AI teaching tool for learning how to integrate LLMs into a product.
  </p>
  <p>It has 3 main features:</p>
  <ol>
    <li>Storing and searching recipes</li>
    <li>Tracking pantry inventory</li>
    <li>Helpful AI features to save time like suggestion or generation</li>
  </ol>
  AI Features:
  <ul>
    <li>
      Suggest Recipe: Suggests available recipes to make given the ingredients
      in your pantry
    </li>
    <li>
      Upload Image with Dall-E: If no image is uploaded upon adding a new
      recipe, an image will be generated as a placeholder based on the recipe
      name
    </li>
    <li>
      Summarize Video Tutorial Tips: Generates top three tips from related
      YouTube tutorial using video transcript summarization
    </li>
  </ul>

  <p>
    This is a temporary public deployment for GHC 2024. Feel free to add and
    modify recipes, test out the AI features, or give these recipes a try!
  </p>
  <p>To get started, visit the <a href="https://recipes.sharahe.com/">Recipes page</a>.</p>

  <h3>Technical Tools used:</h3>
  <p>
    HTML, CSS, sqlite3, Jinja, Preact, Javascript, Python, Flask, OpenAI API
  </p>

  <p>
    Learn more about my technical experience
    <a
      href="https://bit.ly/4dH8nt4"
      >here</a
    >. Feel free to find me on
    <a href="https://www.linkedin.com/in/sharahe">Linkedin</a>.

# Technical

Using https://github.com/astral-sh/uv for package management.

To setup virtual environment:
`uv venv`

To activate virtual environment:
`source .venv/bin/activate`

To install dependencies from requirements.txt:
`uv pip sync requirements.txt`

To install/uninstall a new dependency, add package name to requirements.in, then compile and sync
`uv pip compile requirements.in -o requirements.txt`
`uv pip sync requirements.txt`

To run locally:
`flask run --debug`

To dump sql db
`sqlite3 database.db  .dump > dump.sql`
