import os
import sqlite3
import json
import shutil
import pytest
import sys
from unittest.mock import MagicMock

# Mock dotenv before importing build
mock_dotenv = MagicMock()
sys.modules["dotenv"] = mock_dotenv

import build

@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test_recipes.db"
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE recipes (name TEXT, uid TEXT, data TEXT)')

    # Sample recipe data
    recipe1_data = {
        "description": "Test Recipe 1 Description",
        "prep_time": "10m",
        "cook_time": "20m",
        "total_time": "30m",
        "servings": "2",
        "ingredients": "Ingredient 1\nIngredient 2",
        "directions": "Step 1\nStep 2"
    }
    conn.execute('INSERT INTO recipes (name, uid, data) VALUES (?, ?, ?)',
                 ("Test Recipe 1", "recipe-1", json.dumps(recipe1_data)))

    # Recipe with malformed data
    conn.execute('INSERT INTO recipes (name, uid, data) VALUES (?, ?, ?)',
                 ("Malformed Recipe", "malformed", "not a json"))

    # Recipe with missing data (null)
    conn.execute('INSERT INTO recipes (name, uid, data) VALUES (?, ?, ?)',
                 ("Empty Recipe", "empty", None))

    conn.commit()
    conn.close()
    return str(db_path)

@pytest.fixture
def temp_output(tmp_path):
    return tmp_path / "dist"

def test_get_db_connection(test_db, monkeypatch):
    monkeypatch.setattr(build, "DB_PATH", test_db)
    conn = build.get_db_connection()
    assert isinstance(conn, sqlite3.Connection)
    assert conn.row_factory == sqlite3.Row
    conn.close()

def test_build(test_db, temp_output, monkeypatch, tmp_path):
    # Setup mocks
    monkeypatch.setattr(build, "DB_PATH", test_db)
    monkeypatch.setattr(build, "OUTPUT_DIR", str(temp_output))

    # We use real templates and static files from the project root
    # assuming pytest is run from the project root.

    # Run build
    build.build()

    # Verify directory structure
    assert temp_output.exists()
    assert (temp_output / "recipe").exists()
    assert (temp_output / "static").exists()

    # Verify index.html
    index_path = temp_output / "index.html"
    assert index_path.exists()
    with open(index_path, 'r') as f:
        content = f.read()
        assert "Test Recipe 1" in content
        assert "Malformed Recipe" in content
        assert "Empty Recipe" in content
        assert "recipe/recipe-1.html" in content
        assert "recipe/malformed.html" in content
        assert "recipe/empty.html" in content

    # Verify individual recipe page
    recipe_path = temp_output / "recipe" / "recipe-1.html"
    assert recipe_path.exists()
    with open(recipe_path, 'r') as f:
        content = f.read()
        assert "Test Recipe 1" in content
        assert "Test Recipe 1 Description" in content
        assert "Ingredient 1" in content
        assert "Step 1" in content

    # Verify malformed recipe page (should handle it gracefully)
    malformed_path = temp_output / "recipe" / "malformed.html"
    assert malformed_path.exists()
    with open(malformed_path, 'r') as f:
        content = f.read()
        assert "Malformed Recipe" in content

    # Verify search.json
    search_path = temp_output / "search.json"
    assert search_path.exists()
    with open(search_path, 'r') as f:
        data = json.load(f)
        assert len(data) == 3
        assert data[0]['title'] == "Test Recipe 1"
        assert data[0]['id'] == "recipe-1"

    # Verify static files copied
    assert (temp_output / "static" / "style.css").exists()
    assert (temp_output / "static" / "search.js").exists()

def test_build_empty_db(tmp_path, monkeypatch):
    # Setup empty DB
    db_path = tmp_path / "empty_recipes.db"
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE recipes (name TEXT, uid TEXT, data TEXT)')
    conn.commit()
    conn.close()

    temp_output = tmp_path / "dist_empty"

    monkeypatch.setattr(build, "DB_PATH", str(db_path))
    monkeypatch.setattr(build, "OUTPUT_DIR", str(temp_output))

    build.build()

    assert temp_output.exists()
    assert (temp_output / "index.html").exists()
    with open(temp_output / "search.json", 'r') as f:
        data = json.load(f)
        assert data == []
