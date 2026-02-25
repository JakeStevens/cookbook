import os
import sqlite3
import json
import pytest
import sys
from unittest.mock import MagicMock

# Mock dotenv before importing build
mock_dotenv = MagicMock()
sys.modules["dotenv"] = mock_dotenv

import build

@pytest.fixture
def xss_db(tmp_path):
    db_path = tmp_path / "xss_recipes.db"
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE recipes (name TEXT, uid TEXT, data TEXT)')

    # Insert malicious payload
    # Payload is inserted into 'directions' which is rendered in recipe.html
    payload = '<script>alert("XSS")</script>'
    data = {
        'description': 'Malicious Description',
        'ingredients': '1 cup of exploit',
        'directions': 'Mix well and ' + payload
    }

    conn.execute(
        'INSERT INTO recipes (name, uid, data) VALUES (?, ?, ?)',
        ('Test Recipe', 'test-xss', json.dumps(data))
    )
    conn.commit()
    conn.close()
    return str(db_path)

def test_xss_prevention(xss_db, tmp_path, monkeypatch):
    # Setup output directory
    output_dir = tmp_path / "dist"

    # Setup mocks
    monkeypatch.setattr(build, "DB_PATH", xss_db)
    monkeypatch.setattr(build, "OUTPUT_DIR", str(output_dir))

    # We use real templates and static files from the project root
    # assuming pytest is run from the project root.
    # We might need to adjust TEMPLATE_DIR if tests are run from a different location
    # but typically pytest is run from root.

    # Run build
    build.build()

    # Verify output file
    output_path = output_dir / "recipe" / "test-xss.html"
    assert output_path.exists(), f"Output file {output_path} does not exist"

    with open(output_path, 'r') as f:
        content = f.read()

        payload = '<script>alert("XSS")</script>'
        # Jinja2 escapes " as &#34;
        escaped_payload_1 = '&lt;script&gt;alert(&#34;XSS&#34;)&lt;/script&gt;'
        # Or possibly:
        escaped_payload_2 = '&lt;script&gt;alert("XSS")&lt;/script&gt;'
        # Or even:
        escaped_payload_3 = '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;'

        assert payload not in content, "Found unescaped script in recipe page!"

        # Check if either escaped version is present
        assert escaped_payload_1 in content or escaped_payload_2 in content or escaped_payload_3 in content, \
            f"Script is not properly escaped. Content snippet: {content[:500]}"
