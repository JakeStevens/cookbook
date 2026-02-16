import http.server
import socketserver
import threading
import pytest
import os
import time
from playwright.sync_api import Page, expect

PORT = 8001

@pytest.fixture(scope="module")
def test_server():
    # Serve the current directory
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

    # Allow reuse of address
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", PORT), Handler)

    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Create the repro file
    repro_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>XSS Repro</title>
    </head>
    <body>
        <div id="search-container">
            <input type="text" id="search-input" placeholder="Search recipes...">
        </div>
        <ul class="recipe-list" id="recipe-list"></ul>
        <script src="static/search.js"></script>
    </body>
    </html>
    """
    with open("repro_test.html", "w") as f:
        f.write(repro_html)

    yield httpd

    httpd.shutdown()
    httpd.server_close()

    if os.path.exists("repro_test.html"):
        os.remove("repro_test.html")

def test_search_xss_fix(page: Page, test_server):
    # Intercept search.json
    def handle_route(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body='''[
                {"id": "1", "title": "<img src=x onerror=console.log(\'XSS\') id=\'xss-trigger\'>", "total_time": "10 mins"},
                {"id": "2", "title": "Valid Recipe", "total_time": "20 mins"}
            ]'''
        )

    page.route("**/search.json", handle_route)

    page.goto(f"http://localhost:{PORT}/repro_test.html")

    # Test 1: Malicious Input
    # Type in search box to trigger the rendering
    page.fill("#search-input", "img")

    # Check if the XSS element exists in the DOM
    # We expect it NOT to exist as an element, but as text
    # The vulnerability was that the img tag was created and executed
    # If fixed, the locator will fail to find it as an element
    expect(page.locator("#xss-trigger")).to_have_count(0)

    # Check if the text content contains the HTML tag (escaped)
    # Use expect to wait for the debounced rendering
    expect(page.locator("#recipe-list")).to_contain_text("<img")

    # Test 2: Valid Input
    page.fill("#search-input", "Valid")

    valid_recipe = page.get_by_text("Valid Recipe")
    expect(valid_recipe).to_be_visible()

    # Check structure
    h3 = page.locator("li.recipe-card > a > h3", has_text="Valid Recipe")
    expect(h3).to_be_visible()
