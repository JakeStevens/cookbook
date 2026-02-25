import os
import sqlite3
import json
import pytest
import sys
from unittest.mock import MagicMock

# Ensure dotenv is mocked before build is imported
if "dotenv" not in sys.modules:
    mock_dotenv = MagicMock()
    sys.modules["dotenv"] = mock_dotenv

import build

@pytest.fixture
def malicious_db(tmp_path):
    db_path = tmp_path / "malicious.db"
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE recipes (name TEXT, uid TEXT, data TEXT)')

    # Malicious payload: traverse up to root and create exploit.html
    # output_path = os.path.join(output_dir, 'recipe', f"{recipe['id']}.html")
    # If output_dir is 'dist', path is 'dist/recipe/../../exploit.html' -> 'exploit.html' (sibling of dist)
    malicious_uid = '../../exploit'

    conn.execute('INSERT INTO recipes (name, uid, data) VALUES (?, ?, ?)',
                 ('Malicious Recipe', malicious_uid, json.dumps({})))

    conn.commit()
    conn.close()
    return str(db_path)

@pytest.fixture
def temp_output(tmp_path):
    return tmp_path / "dist"

def test_path_traversal(malicious_db, temp_output, monkeypatch, tmp_path):
    monkeypatch.setattr(build, "DB_PATH", malicious_db)
    monkeypatch.setattr(build, "OUTPUT_DIR", str(temp_output))

    # Ensure static directory exists for copying
    if not os.path.exists('static'):
        os.makedirs('static')

    # Run build
    build.build()

    # Check if exploit.html exists in the traversed location
    # It should be at tmp_path / 'exploit.html' because 'dist/recipe/../../' lands at tmp_path
    traversed_file = tmp_path / 'exploit.html'

    if traversed_file.exists():
        # Clean up
        os.remove(traversed_file)
        pytest.fail("Path traversal vulnerability exploited! File found outside output directory.")

    # Verify that the file was created SAFELY inside dist/recipe/
    # If we sanitize properly (e.g. using os.path.basename), it should be 'exploit.html'
    safe_exploit = temp_output / 'recipe' / 'exploit.html'
    assert safe_exploit.exists(), "Sanitized file not found in expected location (dist/recipe/exploit.html)."
