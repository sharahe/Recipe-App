# README

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
