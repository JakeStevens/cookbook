import sqlite3
import json
import os
import shutil
import subprocess
import sys

# Setup test environment
TEST_DB = 'test_reproduce.sqlite'
OUTPUT_DIR = 'dist'

def setup_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    conn = sqlite3.connect(TEST_DB)
    conn.execute('CREATE TABLE IF NOT EXISTS recipes (uid TEXT PRIMARY KEY, name TEXT, data TEXT)')

    # Insert malicious payload
    payload = '<script>alert("XSS")</script>'
    data = {
        'description': 'Malicious Description',
        'ingredients': '1 cup of exploit',
        'directions': 'Mix well and ' + payload
    }

    conn.execute(
        'INSERT INTO recipes (uid, name, data) VALUES (?, ?, ?)',
        ('test-xss', 'Test Recipe', json.dumps(data))
    )
    conn.commit()
    conn.close()
    print(f"Created test database: {TEST_DB}")

def run_build():
    env = os.environ.copy()
    env['DB_PATH'] = TEST_DB
    result = subprocess.run([sys.executable, 'build.py'], env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print("Build failed:")
        print(result.stderr)
        return False
    return True

def check_output():
    recipe_path = os.path.join(OUTPUT_DIR, 'recipe', 'test-xss.html')
    if not os.path.exists(recipe_path):
        print(f"Error: Output file {recipe_path} not found")
        return False

    with open(recipe_path, 'r') as f:
        content = f.read()
        print(f"Checking {recipe_path}...")

        payload = '<script>alert("XSS")</script>'
        if payload in content:
            print("[FAIL] Found unescaped script in recipe page!")
            return False

        # Jinja2 escapes " as &#34;
        escaped_payload = '&lt;script&gt;alert(&#34;XSS&#34;)&lt;/script&gt;'
        if escaped_payload in content:
             print("[PASS] Script is properly escaped.")
             return True
        else:
             print("[WARNING] Script is NOT escaped (or format is different).")
             # This means it might be stripped or encoded differently.
             # If strict escaping is on, it should be HTML escaped.
             return False

if __name__ == "__main__":
    success = False
    try:
        setup_db()
        # We need to ensure static directory exists because build.py tries to copy it
        if not os.path.exists('static'):
            os.makedirs('static')

        if run_build():
            success = check_output()
    except Exception as e:
        print(f"An error occurred: {e}")
        success = False
    finally:
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)
