from pathlib import Path

from playwright.sync_api import sync_playwright

AUTH_FILE = Path('auth.json')


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto('https://www.icesi.edu.co/moodle/login/index.php?loginredirect=1')
        input('Log in, open the Registry page, then press Enter here...')
        ctx.storage_state(path=str(AUTH_FILE))
        browser.close()
    print(f'Session saved to {AUTH_FILE.resolve()}')
