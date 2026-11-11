"""Chromium smoke QA against an already-running SENTINEL server."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS = ROOT / 'docs' / 'images'
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
ROUTES = ['/', '/assistant', '/maintenance', '/recovery', '/opportunities', '/approvals', '/research', '/reports', '/earnings', '/audit', '/settings']
errors = []
results = []
with sync_playwright() as playwright:
    import os
    launch_options = {'headless': True}
    if os.environ.get('SENTINEL_CHROMIUM_PATH'):
        launch_options['executable_path'] = os.environ['SENTINEL_CHROMIUM_PATH']
    browser = playwright.chromium.launch(**launch_options)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    page.on('console', lambda message: errors.append(f'console:{message.type}:{message.text}') if message.type == 'error' else None)
    page.on('pageerror', lambda error: errors.append(f'page:{error}'))
    for route in ROUTES:
        response = page.goto('http://127.0.0.1:8000' + route, wait_until='networkidle')
        assert response and response.status == 200, (route, response.status if response else None)
        assert 'LIN4CRE' in page.title()
        assert page.locator('main').count() == 1
        results.append({'route': route, 'status': response.status, 'title': page.locator('h1').first.text_content()})
    for route, name in [('/assistant', 'assistant'), ('/maintenance', 'maintenance'), ('/recovery', 'recovery')]:
        page.goto('http://127.0.0.1:8000' + route, wait_until='networkidle')
        page.screenshot(path=str(SCREENSHOTS / f'{name}.png'), full_page=True)
    page.goto('http://127.0.0.1:8000/assistant', wait_until='networkidle')
    box = page.get_by_placeholder('Ask SENTINEL to check, install, repair, update, back up, restore or explain…')
    box.fill('Explain what you are doing')
    box.press('Enter')
    page.get_by_text('I translate ordinary-language requests into registered operations', exact=False).wait_for(timeout=15000)
    box.fill('How much did I make?')
    box.press('Enter')
    page.get_by_text('No Data Available — no paid bounty records exist.', exact=False).wait_for(timeout=15000)
    page.screenshot(path=str(SCREENSHOTS / 'assistant-conversation.png'), full_page=True)
    page.set_viewport_size({'width': 390, 'height': 844})
    for route in ['/', '/assistant', '/maintenance', '/recovery']:
        page.goto('http://127.0.0.1:8000' + route, wait_until='networkidle')
        dimensions = page.evaluate('({width: document.documentElement.scrollWidth, viewport: window.innerWidth})')
        assert dimensions['width'] <= dimensions['viewport'] + 1, (route, dimensions)
        results.append({'route': route, 'mobile': True, **dimensions})
    page.goto('http://127.0.0.1:8000/assistant', wait_until='networkidle')
    page.screenshot(path=str(SCREENSHOTS / 'assistant-mobile.png'), full_page=True)
    browser.close()
assert not errors, errors
print(json.dumps({'passed': True, 'routes': results, 'console_errors': errors}, indent=2))
