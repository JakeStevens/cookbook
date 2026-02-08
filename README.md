# Cookbook Static Site Generator

A minimalist static site generator for creating a searchable cookbook website from a Paprika Recipe Manager SQLite database.

## Features

- **Static Generation**: Converts your SQLite recipe database into a collection of fast, lightweight HTML files.
- **Client-Side Search**: A functional search bar that filters recipes instantly using a JSON index.
- **Minimalist Design**: Clean, responsive CSS with zero heavy frameworks.
- **Integration**: Designed to work seamlessly with the `paprika-downloader` project.

## Prerequisites

- Python 3.10+
- A `recipes.db` file (compatible with the `paprika-downloader` schema)

## Setup

1. **Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Linux/macOS
   pip install -r requirements.txt
   ```

2. **Configuration**:
   Create a `.env` file in the root directory and point it to your database:
   ```env
   DB_PATH=/path/to/your/paprika-downloader/recipes.db
   ```

## Usage

### Generate the Site
Run the build script to parse the database and generate the static files:
```bash
python3 build.py
```
The output will be located in the `dist/` directory.

### Preview the Site
Serve the generated site locally:
```bash
python3 -m http.server -d dist -b 0.0.0.0 8000
```
Then navigate to `http://localhost:8000` in your browser.

## Project Structure

- `build.py`: The main generation script.
- `templates/`: Jinja2 HTML templates for the layout and recipe pages.
- `static/`: CSS and JavaScript for styling and search functionality.
- `dist/`: The generated static website (created after running `build.py`).
