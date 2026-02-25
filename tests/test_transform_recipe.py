import pytest
import json
import sys
from unittest.mock import MagicMock

# Mock dotenv before importing build
mock_dotenv = MagicMock()
sys.modules["dotenv"] = mock_dotenv

from build import transform_recipe

def test_transform_recipe_happy_path():
    data = {
        "description": "Tasty",
        "prep_time": "10m",
        "cook_time": "20m",
        "total_time": "30m",
        "servings": "4",
        "ingredients": "Ing1\nIng2",
        "directions": "Step1\nStep2"
    }
    row = {
        "uid": "123",
        "name": "My Recipe",
        "data": json.dumps(data)
    }
    result = transform_recipe(row)

    assert result['id'] == "123"
    assert result['name'] == "My Recipe"
    assert result['description'] == "Tasty"
    assert result['prep_time'] == "10m"
    assert result['cook_time'] == "20m"
    assert result['total_time'] == "30m"
    assert result['servings'] == "4"
    assert result['ingredients'] == "Ing1\nIng2"
    assert result['directions'] == "Step1\nStep2"

def test_transform_recipe_missing_fields():
    data = {
        "description": "Tasty"
        # Other fields missing
    }
    row = {
        "uid": "123",
        "name": "My Recipe",
        "data": json.dumps(data)
    }
    result = transform_recipe(row)

    assert result['description'] == "Tasty"
    assert result['prep_time'] == ""
    assert result['cook_time'] == ""

def test_transform_recipe_malformed_data():
    row = {
        "uid": "123",
        "name": "My Recipe",
        "data": "not valid json"
    }
    result = transform_recipe(row)

    # Should return empty fields for data-derived values
    assert result['description'] == ""
    assert result['ingredients'] == ""

def test_transform_recipe_none_data():
    row = {
        "uid": "123",
        "name": "My Recipe",
        "data": None
    }
    # json.loads(None) raises TypeError which is caught
    result = transform_recipe(row)

    assert result['description'] == ""

def test_transform_recipe_none_name():
    data = {}
    row = {
        "uid": "123",
        "name": None,
        "data": json.dumps(data)
    }
    result = transform_recipe(row)

    assert result['name'] == "Untitled Recipe"

def test_transform_recipe_empty_name():
    data = {}
    row = {
        "uid": "123",
        "name": "",
        "data": json.dumps(data)
    }
    result = transform_recipe(row)

    assert result['name'] == "Untitled Recipe"
