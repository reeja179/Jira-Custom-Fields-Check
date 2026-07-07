# Jira Custom Fields Check

GitHub Actions workflow that checks whether a Jira instance exceeds 100 custom fields.

## What it does
- Queries `GET /rest/api/2/field` on the configured Jira instance
- Filters fields to count only custom fields (IDs starting with `customfield_`)
- Compares the count against a threshold of 100
- Outputs PASS (≤100) or FAIL (>100) in the workflow logs

## Setup
1. Generate a Jira API token: https://id.atlassian.com/manage-profile/security/api-tokens
2. In this repo, go to **Settings → Secrets and variables → Actions** and add:
   - `JIRA_URL` — e.g. `https://your-domain.atlassian.net` (no trailing slash)
   - `JIRA_EMAIL` — your Atlassian account email
   - `JIRA_API_TOKEN` — the API token from step 1
3. Go to the **Actions** tab, select **Jira Custom Fields Check**, and click **Run workflow**

## Files
- `.github/workflows/jira-fields-check.yml` — the GitHub Actions workflow
- `Jiracustomfieldscheck.py` — script that queries Jira and evaluates the threshold
