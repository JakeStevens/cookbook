import sqlite3
import os
import json
import shutil
import concurrent.futures
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

# Configuration
DB_PATH = os.getenv('DB_PATH', 'paprika.sqlite')
OUTPUT_DIR = 'dist'
TEMPLATE_DIR = 'templates'
STATIC_DIR = 'static'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

_template_recipe = None

def init_worker(template_dir):
    global _template_recipe
    env = Environment(loader=FileSystemLoader(template_dir))
    _template_recipe = env.get_template('recipe.html')

def process_recipe_task(recipe, output_dir):
    output_path = os.path.join(output_dir, 'recipe', f"{recipe['id']}.html")
    with open(output_path, 'w') as f:
        f.write(_template_recipe.render(recipe=recipe, root_path='../'))

def process_batch_task(recipes_batch, output_dir):
    for recipe in recipes_batch:
        process_recipe_task(recipe, output_dir)

def build():
    # 1. Setup Output Directory
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(os.path.join(OUTPUT_DIR, 'recipe'))
    
    # 2. Copy Static Assets
    shutil.copytree(STATIC_DIR, os.path.join(OUTPUT_DIR, 'static'))
    
    # 3. Setup Jinja2
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    
    # 4. Fetch Data
    conn = get_db_connection()
    # Using the schema from paprika-downloader/recipes.db
    recipes_query = conn.execute('SELECT name, uid, data FROM recipes').fetchall()
    conn.close()
    
    # Transform data for templates
    recipes = []
    for row in recipes_query:
        try:
            data = json.loads(row['data'])
        except (ValueError, TypeError):
            data = {}
        
        recipes.append({
            'id': row['uid'],
            'name': row['name'] or 'Untitled Recipe',
            'description': data.get('description', ''),
            'prep_time': data.get('prep_time', ''),
            'cook_time': data.get('cook_time', ''),
            'total_time': data.get('total_time', ''),
            'servings': data.get('servings', ''),
            'ingredients': data.get('ingredients', ''),
            'directions': data.get('directions', '')
        })

    # 5. Render Index
    template_index = env.get_template('index.html')
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(template_index.render(recipes=recipes, root_path=''))
        
    # 6. Render Individual Recipes
    # Use ProcessPoolExecutor for CPU-bound rendering (Jinja2)
    # ThreadPoolExecutor was tested and found slower due to GIL contention.
    batch_size = 100
    with concurrent.futures.ProcessPoolExecutor(initializer=init_worker, initargs=(TEMPLATE_DIR,)) as executor:
        futures = [
            executor.submit(process_batch_task, recipes[i:i + batch_size], OUTPUT_DIR)
            for i in range(0, len(recipes), batch_size)
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()
            
    # 7. Generate Search Index
    search_index = [
        {'id': r['id'], 'title': r['name'], 'total_time': r['total_time']} 
        for r in recipes
    ]
    with open(os.path.join(OUTPUT_DIR, 'search.json'), 'w') as f:
        json.dump(search_index, f)
        
    print(f"Successfully generated site in '{OUTPUT_DIR}' with {len(recipes)} recipes.")

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"Error: Database '{DB_PATH}' not found. Run seed_db.py first.")
    else:
        build()
