# HMT AI Stock Checker

Checks https://www.hmtwatches.store/ on a schedule. Playwright loads the page,
Claude reads it and lists the watches in stock, and you get an email when
something new appears. Runs free on GitHub Actions, even when your PC is off.

## Setup

1. **Claude API key**: console.anthropic.com -> add a few dollars of credit -> API Keys -> Create Key.
2. **Gmail app password**: Google Account -> Security -> turn on 2-Step Verification -> App passwords -> create "HMT checker" -> copy the 16-character code.
3. **Create a private GitHub repo** and upload all files in this folder
   (including the hidden `.github` folder).
4. In the repo: Settings -> Secrets and variables -> Actions -> New repository secret. Add:
   - `ANTHROPIC_API_KEY`
   - `GMAIL_USER` (your Gmail address)
   - `GMAIL_APP_PASSWORD` (the 16-character code, no spaces)
   - `TO_EMAIL` (where alerts should go; can be the same Gmail)
5. Settings -> Actions -> General -> Workflow permissions -> select **Read and write permissions** -> Save.
6. Go to the **Actions** tab -> "HMT AI check" -> **Run workflow**.

## Testing

- Open the run logs. You should see "Claude found N watch(es) in stock".
- Compare the list with the website. A sold-out watch must not appear.
- The first run emails you everything in stock because `seen.json` starts empty.

## Customising

- **Frequency**: edit the `cron` line in `.github/workflows/check.yml`.
  Avoid going below every 30-60 minutes.
- **Full list every run**: set `NOTIFY_ALL: "true"` in the workflow.
- **Wrong stock detection**: edit `PROMPT` in `check_hmt.py` with the exact
  wording the site uses for sold-out items.

## Notes

- GitHub cron is in UTC (IST = UTC + 5:30), and runs can be delayed a few minutes.
- Keep the checks light and personal, and respect the site's terms of use.
