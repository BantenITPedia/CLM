from pathlib import Path
import re
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BASE_URL = "http://localhost"
BASE_HOST_HEADER = "localhost"
USERNAME = "manual_user"
PASSWORD = "ManualPass2026Safe"
OUT_DIR = Path("/opt/clm/manual-images")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_click_continue(page):
    # Try common submit/next controls in this project.
    selectors = [
        "button:has-text('Continue')",
        "button:has-text('Next')",
        "button[type='submit']",
        "input[type='submit']",
    ]
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count() > 0:
            try:
                loc.first.click(timeout=2000)
                return True
            except Exception:
                continue
    return False


def try_fill_step1(page):
    # Try to pick first option from selects/radios/checkboxes so wizard can proceed.
    for sel in ["select", "select[name*='entity']", "select[name*='type']"]:
        loc = page.locator(sel)
        if loc.count() > 0:
            for i in range(loc.count()):
                try:
                    opts = loc.nth(i).locator("option")
                    if opts.count() > 1:
                        value = opts.nth(1).get_attribute("value")
                        if value:
                            loc.nth(i).select_option(value=value)
                            return True
                except Exception:
                    pass

    radios = page.locator("input[type='radio']")
    if radios.count() > 0:
        try:
            radios.first.check(force=True)
            return True
        except Exception:
            pass

    checks = page.locator("input[type='checkbox']")
    if checks.count() > 0:
        try:
            checks.first.check(force=True)
            return True
        except Exception:
            pass

    return False


def shot(page, name, selector=None):
    target = OUT_DIR / name
    if selector:
        loc = page.locator(selector)
        if loc.count() > 0:
            loc.first.scroll_into_view_if_needed(timeout=3000)
            loc.first.screenshot(path=str(target))
            return
    page.screenshot(path=str(target), full_page=True)


def goto(page, path):
    page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")


def login(page):
    goto(page, "/")
    shot(page, "img-01-login.png")
    if page.locator("#username").count() > 0:
        page.fill("#username", USERNAME)
    else:
        page.fill("input[name='username']", USERNAME)

    if page.locator("#password").count() > 0:
        page.fill("#password", PASSWORD)
    else:
        page.fill("input[name='password']", PASSWORD)
    page.locator("button[type='submit']").first.click()
    page.wait_for_load_state("domcontentloaded")
    try:
        page.wait_for_url(re.compile(r".*/dashboard/?$"), timeout=8000)
    except PWTimeout:
        # If login redirects to another first page, continue anyway.
        pass


def capture_all(page):
    shot(page, "img-02-dashboard.png")

    goto(page, "/contracts/")
    shot(page, "img-03-contract-list.png")

    # Wizard step 1
    goto(page, "/contracts/create/step-1/")
    shot(page, "img-04-wizard-step-1.png")

    # Try to move to step 2 from step 1.
    try_fill_step1(page)
    safe_click_continue(page)
    page.wait_for_load_state("domcontentloaded")
    shot(page, "img-05-wizard-step-2.png")

    # Attempt to open step 3 and step 4 directly (if guarded, app may redirect).
    goto(page, "/contracts/create/step-3/")
    shot(page, "img-06-wizard-step-3.png")

    goto(page, "/contracts/create/step-4/")
    shot(page, "img-07-wizard-step-4.png")

    # Contract detail and section-focused screenshots using first existing contract.
    goto(page, "/contracts/1/")
    shot(page, "img-08-contract-detail.png")

    shot(page, "img-09-participant-section.png", "h5:has-text('Participants')")

    # Documents area may vary; fallback to full page if selector missing.
    shot(page, "img-10-document-upload.png", "h5:has-text('Documents')")

    shot(page, "img-11-comment-section.png", "h5:has-text('Comments')")

    goto(page, "/contracts/expiring/")
    shot(page, "img-12-expiring-soon.png")

    # Admin panel view.
    goto(page, "/admin/")
    shot(page, "img-13-admin-panel.png")


if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()
        if BASE_HOST_HEADER:
            page.set_extra_http_headers({"Host": BASE_HOST_HEADER})
        login(page)
        capture_all(page)
        context.close()
        browser.close()
    print("Screenshots generated in", OUT_DIR)
