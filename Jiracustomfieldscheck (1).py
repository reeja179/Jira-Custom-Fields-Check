#!/usr/bin/env python3
"""
Jira Custom Fields Validator
Check if Jira instance exceeds 100 custom fields
"""

import os
import requests
import base64
from datetime import datetime

# ============================================================================
# CONFIGURATION - loaded from environment variables (set as GitHub Secrets)
# ============================================================================

JIRA_URL = os.environ.get("JIRA_URL")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")

THRESHOLD = 100  # Maximum allowed custom fields


def validate_config():
    """Make sure required env vars are set before doing anything else"""
    missing = [name for name, val in
               [("JIRA_URL", JIRA_URL), ("JIRA_EMAIL", JIRA_EMAIL), ("JIRA_API_TOKEN", JIRA_API_TOKEN)]
               if not val]
    if missing:
        print(f"✗ Missing required environment variables: {', '.join(missing)}")
        exit(1)


def create_auth_header():
    """Create Basic Auth header for Jira API"""
    auth_string = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()
    return {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }


def get_jira_fields():
    """Query Jira API to retrieve all fields"""
    print(f"🔍 Querying Jira API: {JIRA_URL}/rest/api/2/field")
    print("-" * 70)

    headers = create_auth_header()

    try:
        response = requests.get(
            f"{JIRA_URL}/rest/api/2/field",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            print("✓ API connection successful!")
            try:
                return response.json()
            except ValueError:
                print("✗ Response was not valid JSON. Raw response below:")
                print(f"  Content-Type: {response.headers.get('Content-Type')}")
                print(f"  First 300 chars: {response.text[:300]!r}")
                return None
        else:
            print(f"✗ API Error: Status {response.status_code}")
            print(f"  Response: {response.text[:300]}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"✗ Connection Error: {e}")
        return None


def filter_custom_fields(fields):
    """Filter and count only custom fields (exclude system fields)"""
    custom_fields = []

    for field in fields:
        field_id = field.get("id", "")

        if field_id.startswith("customfield_"):
            custom_fields.append({
                "id": field_id,
                "name": field.get("name"),
                "type": field.get("schema", {}).get("type", "unknown"),
                "custom": field.get("custom", True)
            })

    return custom_fields


def find_duplicate_fields(custom_fields):
    """
    Group custom fields by name (case-insensitive) to find duplicates.
    Since the Jira field API doesn't expose a created-date, we use the
    numeric suffix in the field ID (e.g. customfield_10023) as a proxy
    for recency -- higher number = created more recently.
    Returns:
        duplicate_groups: dict of name -> list of fields (sorted oldest -> newest)
        dedup_fields: list of custom_fields with only the newest field kept
                      per duplicate name (older duplicates dropped)
    """
    groups = {}
    for field in custom_fields:
        key = (field.get("name") or "").strip().lower()
        groups.setdefault(key, []).append(field)

    def field_number(field):
        # Extract the numeric part of customfield_10023 -> 10023
        try:
            return int(field["id"].split("_")[-1])
        except (ValueError, IndexError):
            return 0

    duplicate_groups = {}
    dedup_fields = []

    for key, fields in groups.items():
        if len(fields) > 1:
            fields_sorted = sorted(fields, key=field_number)  # oldest -> newest
            duplicate_groups[key] = fields_sorted
            dedup_fields.append(fields_sorted[-1])  # keep only the newest
        else:
            dedup_fields.append(fields[0])

    return duplicate_groups, dedup_fields


def print_duplicate_report(duplicate_groups):
    """Print details of duplicate-named custom fields and merge suggestion"""
    if not duplicate_groups:
        print("\n✓ No duplicate-named custom fields found.")
        return

    print("\n" + "=" * 70)
    print(f"⚠️  DUPLICATE FIELD NAMES FOUND: {len(duplicate_groups)} name(s)")
    print("=" * 70)

    for name, fields in duplicate_groups.items():
        keeper = fields[-1]
        older = fields[:-1]
        print(f"\n  Name: \"{fields[0]['name']}\"  ({len(fields)} fields share this name)")
        for f in older:
            print(f"    - {f['id']} ({f['type']})  -> older, candidate to merge/remove")
        print(f"    - {keeper['id']} ({keeper['type']})  -> newest, recommended to KEEP")

    print("\n  Suggestion: review the older fields above -- if they hold the same")
    print("  kind of data (e.g. two 'Summary' fields, one rich text), migrate any")
    print("  needed values into the newest field and archive/remove the rest.")


def evaluate_status(count):
    """Determine PASS/FAIL status based on threshold"""
    if count <= THRESHOLD:
        return "PASS ✓"
    else:
        return "FAIL ✗"


def print_results(custom_fields, duplicate_groups, dedup_fields):
    """Print formatted results, including raw vs deduplicated counts"""
    raw_count = len(custom_fields)
    dedup_count = len(dedup_fields)
    raw_status = evaluate_status(raw_count)
    dedup_status = evaluate_status(dedup_count)

    print("\n" + "=" * 70)
    print("📊 JIRA CUSTOM FIELDS VALIDATION REPORT")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Jira Instance: {JIRA_URL}")
    print(f"Threshold: {THRESHOLD} fields")
    print("-" * 70)
    print(f"Raw Custom Fields Count:          {raw_count}  -> Status: {raw_status}")
    print(f"Deduplicated Custom Fields Count: {dedup_count}  -> Status: {dedup_status}")
    print("-" * 70)

    if raw_count > THRESHOLD:
        print(f"⚠️  WARNING (raw): Instance exceeds threshold by {raw_count - THRESHOLD} fields!")
    else:
        print(f"✓ Safe (raw): {THRESHOLD - raw_count} fields remaining before threshold")

    if dedup_count != raw_count:
        if dedup_count > THRESHOLD:
            print(f"⚠️  WARNING (deduplicated): still exceeds threshold by {dedup_count - THRESHOLD} fields!")
        else:
            print(f"✓ Safe (deduplicated): {THRESHOLD - dedup_count} fields remaining before threshold")

    print_duplicate_report(duplicate_groups)

    print("\nDetailed field list (all custom fields):")
    for f in custom_fields:
        print(f"  - {f['id']}: {f['name']} ({f['type']})")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Raw Count:          {raw_count}/{THRESHOLD}  -> {raw_status}")
    print(f"Deduplicated Count: {dedup_count}/{THRESHOLD}  -> {dedup_status}")
    print(f"Duplicate names found: {len(duplicate_groups)}")
    print("=" * 70)


def main():
    """Main execution function"""
    print("\n🚀 JIRA CUSTOM FIELDS CHECKER")
    print("=" * 70)

    validate_config()

    fields = get_jira_fields()

    if fields is None:
        print("\n✗ Failed to retrieve fields from Jira")
        exit(1)

    print(f"\n✓ Retrieved {len(fields)} total fields")
    custom_fields = filter_custom_fields(fields)
    duplicate_groups, dedup_fields = find_duplicate_fields(custom_fields)

    print_results(custom_fields, duplicate_groups, dedup_fields)

    # Overall PASS/FAIL is based on the raw count (matches the original task spec).
    # The deduplicated count is reported alongside for visibility, in case
    # cleaning up duplicate-named fields would bring the instance under threshold.
    count = len(custom_fields)
    if count > THRESHOLD:
        exit(1)  # FAIL
    else:
        exit(0)  # PASS


if __name__ == "__main__":
    main()
