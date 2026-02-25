import sys
import pytest
from unittest.mock import MagicMock
from jinja2 import Template, exceptions

# Mock dotenv before importing build to avoid dependency on .env file
mock_dotenv = MagicMock()
sys.modules["dotenv"] = mock_dotenv

import build

def test_init_worker(tmp_path):
    # Setup: Create a temporary template directory and a dummy recipe.html
    # This ensures the test is isolated from the project's actual templates.
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    recipe_template = template_dir / "recipe.html"
    recipe_template.write_text("<html><body>{{ recipe.name }}</body></html>")

    # Ensure _template_recipe is None initially to verify it gets set
    build._template_recipe = None

    # Call init_worker with the temporary directory
    build.init_worker(str(template_dir))

    # Assert _template_recipe is set and is a Template object
    assert build._template_recipe is not None
    assert isinstance(build._template_recipe, Template)

    # Verify it can render (sanity check that it's the right template)
    rendered = build._template_recipe.render(recipe={'name': 'Test Recipe'})
    assert "Test Recipe" in rendered

def test_init_worker_invalid_dir(tmp_path):
    # Test with a directory that exists but does not contain recipe.html
    empty_dir = tmp_path / "empty_templates"
    empty_dir.mkdir()

    with pytest.raises(exceptions.TemplateNotFound):
        build.init_worker(str(empty_dir))
