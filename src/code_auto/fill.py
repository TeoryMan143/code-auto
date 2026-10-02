import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

# project root (where pyproject.toml is)
ROOT = Path(__file__).resolve().parents[2]
RESOURCES = ROOT / 'resources'
ERROR_DIR = RESOURCES / 'error'
DRY_DIR = RESOURCES / 'dry'
CODES_FILE = RESOURCES / 'codes.csv'
RESULTS_FILE = RESOURCES / 'results.csv'
AUTH_FILE = Path('auth.json')

EDIT_URL = 'https://www.icesi.edu.co/moodle/mod/data/edit.php?d=27'


# Used for every row unless the CSV has a column with the same name
DEFAULTS = {
    'monitor': 'Jonathan David Cortés Castaño',
    # exact text, en dash included
    'activity': 'Acompañamiento a estudiantes – Grammar/Vocabulary',
    'other_activity': '',
    'modality': 'Apoyo a profesores',
    'course': '',
    'other_course': '',
    'teacher': '',
    'date': '',  # YYYY-MM-DD
    'start': '',  # 24h
    'end': '',
    'comment': '',
}


class SessionExpired(Exception):
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description='Fill the Moodle form for every code in resources/codes.csv.'
    )
    parser.add_argument(
        '--submit', action='store_true', help='save the forms instead of taking screenshots'
    )
    for name, default in DEFAULTS.items():
        parser.add_argument(f'--{name.replace("_", "-")}', default=default)
    return parser.parse_args()


def process(page, e, submit, dialogs):
    dialogs.clear()
    page.goto(EDIT_URL)
    if 'login' in page.url:
        raise SessionExpired()

    # 1. Search
    page.fill('#codigo_estudiante', e['code'])
    page.click('#button_codigo')
    try:
        page.wait_for_function(
            "document.querySelector('#field_347').value.trim() !== ''",
            timeout=10_000,
        )
    except PWTimeout as pw:
        raise LookupError(f'not found ({dialogs[-1] if dialogs else "no message"})') from pw

    # 2. Fill the form
    if e['course']:
        page.select_option('#field_357', label=e['course'], timeout=10_000)
    if e['other_course']:
        page.fill('#field_374', e['other_course'])
    if e['teacher']:
        page.select_option('#field_363', label=e['teacher'], timeout=10_000)

    page.select_option('#field_367', label=e['monitor'])
    page.select_option('#field_365', label=e['activity'])
    if e['other_activity']:
        page.fill('#field_366', e['other_activity'])

    d = datetime.strptime(e['date'], '%Y-%m-%d')
    page.select_option('select[name=field_373_day]', value=str(d.day))
    page.select_option('select[name=field_373_month]', value=str(d.month))
    page.select_option('select[name=field_373_year]', value=str(d.year))

    page.fill('#field_371', e['start'])
    page.fill('#field_372', e['end'])

    if e['comment']:
        page.frame_locator('#field_370_ifr').locator('body').fill(e['comment'])

    page.select_option('#field_3978', label=e['modality'])

    # 3. Save
    if not submit:
        page.screenshot(path=DRY_DIR / f'{e["code"]}.png', full_page=True)
        return

    with page.expect_navigation():
        page.click('input[name="saveandadd"]')

    alert = page.locator('.alert-danger, .alert-warning')
    if alert.count():
        raise RuntimeError(alert.first.inner_text()[:120])


def main():
    ERROR_DIR.mkdir(parents=True, exist_ok=True)
    DRY_DIR.mkdir(parents=True, exist_ok=True)
    args = parse_args()
    values = vars(args)
    submit = values.pop('submit')
    if not AUTH_FILE.exists():
        sys.exit('auth.json not found. Run `uv run login` first.')

    # Skip entries already saved in a previous run
    done = set()
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r['status'] == 'ok':
                    done.add(r['key'])

    print('SUBMIT mode' if submit else 'DRY RUN (nothing is saved). Use --submit to save.')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=150)
        ctx = browser.new_context(storage_state=str(AUTH_FILE))
        page = ctx.new_page()
        page.set_default_timeout(15_000)

        dialogs = []

        def on_dialog(dlg):
            dialogs.append(dlg.message)
            dlg.accept()

        page.on('dialog', on_dialog)

        new_file = not RESULTS_FILE.exists()
        with (
            open(CODES_FILE, newline='', encoding='utf-8-sig') as f,
            open(RESULTS_FILE, 'a', newline='', encoding='utf-8') as out,
        ):
            w = csv.writer(out)
            if new_file:
                w.writerow(['key', 'code', 'status'])

            for row in csv.DictReader(f):
                e = {**values, 'code': row['code'].strip()}
                key = f'{e["code"]}|{e["date"]}|{e["start"]}'
                if key in done:
                    print(f'skip {key} (already ok)')
                    continue
                try:
                    process(page, e, submit, dialogs)
                    status = 'ok'
                except SessionExpired:
                    print('Session expired. Run `uv run login` again.')
                    break
                except Exception as ex:
                    page.screenshot(path=ERROR_DIR / f'{e["code"]}.png')
                    status = f'error: {str(ex).splitlines()[0]}'
                print(f'{e["code"]}: {status}')
                if submit:
                    w.writerow([key, e['code'], status])
                    out.flush()
        browser.close()
