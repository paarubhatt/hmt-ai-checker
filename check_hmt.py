"""HMT stock checker: Playwright loads the store, Claude reads the page,
and you get an email when new watches are in stock."""
import os, sys, json, re, smtplib
from email.message import EmailMessage

import anthropic
from playwright.sync_api import sync_playwright

SHOP_URL = "https://www.hmtwatches.store/"
STATE_FILE = "seen.json"
MODEL = "claude-haiku-5-5"
# Set NOTIFY_ALL=true (in the workflow) to get the full list on every run
NOTIFY_ALL = os.environ.get("NOTIFY_ALL", "false").lower() == "true"

PROMPT = (
    "Below is the text of the HMT online watch store's All Products page. "
    "List ONLY watches that can be bought right now. Exclude any showing "
    "'Sold out', 'Out of stock', 'Notify me' or similar. Each watch name "
    "starts with 'HMT' (for example 'HMT Sangam MGSS 05'). Use the LINKS "
    "section to find each watch's URL. Reply with ONLY a JSON array, no "
    'other text: [{"name": "", "price": "", "url": ""}]. '
    "If none are available, reply [].\n\n"
)


def get_page_text():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(SHOP_URL, wait_until="networkidle", timeout=90000)

        # Go to the full catalogue
        try:
            page.get_by_role("link", name="All Products").first.click()
            page.wait_for_load_state("networkidle")
        except Exception:
            print("Could not click 'All Products'; using homepage instead")

        # Scroll so every product loads
        for _ in range(15):
            page.mouse.wheel(0, 4000)
            page.wait_for_timeout(1000)

        text = page.inner_text("body")
        links = page.eval_on_selector_all(
            "a",
            "els => els.map(e => e.innerText.trim().replace(/\\n/g,' ') + ' -> ' + e.href)",
        )
        browser.close()

    if len(text) < 300:
        sys.exit("Page text is nearly empty - the site may be blocking the bot.")
    return text[:60000] + "\n\nLINKS:\n" + "\n".join(links)[:30000]


def ask_claude(page_text):
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": PROMPT + page_text}],
    )
    out = resp.content[0].text
    start, end = out.find("["), out.rfind("]")
    if start == -1 or end == -1:
        sys.exit(f"Claude did not return JSON:\n{out}")
    return json.loads(out[start : end + 1])


def send_email(subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ["GMAIL_USER"]
    msg["To"] = os.environ["TO_EMAIL"]
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(os.environ["GMAIL_USER"], os.environ["GMAIL_APP_PASSWORD"])
        s.send_message(msg)


def fmt(w):
    return f"- {w.get('name')} | {w.get('price')} | {w.get('url')}"


def main():
    watches = ask_claude(get_page_text())
    print(f"Claude found {len(watches)} watch(es) in stock")

    old = []
    if os.path.exists(STATE_FILE):
        try:
            old = json.load(open(STATE_FILE))
        except Exception:
            old = []
    old_names = {w.get("name") for w in old}
    new = [w for w in watches if w.get("name") not in old_names]

    if new or (NOTIFY_ALL and watches):
        body = ""
        if new:
            body += "NEW IN STOCK:\n" + "\n".join(fmt(w) for w in new) + "\n\n"
        body += "ALL AVAILABLE NOW:\n" + "\n".join(fmt(w) for w in watches)
        subject = (
            f"HMT: {len(new)} new watch(es) in stock!" if new
            else f"HMT: {len(watches)} watch(es) available"
        )
        send_email(subject, body)
        print("Email sent")
    else:
        print("Nothing new, no email sent")

    json.dump(watches, open(STATE_FILE, "w"), indent=2)


if __name__ == "__main__":
    main()
