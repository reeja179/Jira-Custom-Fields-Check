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
            return response.json()
        else:
            print(f"✗ API Error: Status {response.status_code}")
            print(f"  Response: {response.text}")
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


def evaluate_status(count):
    """Determine PASS/FAIL status based on threshold"""
    if count <= THRESHOLD:
        return "PASS ✓"
    else:
        return "FAIL ✗"


def print_results(custom_fields):
    """Print formatted results"""
    count = len(custom_fields)
    status = evaluate_status(count)

    print("\n" + "=" * 70)
    print("📊 JIRA CUSTOM FIELDS VALIDATION REPORT")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Jira Instance: {JIRA_URL}")
    print(f"Threshold: {THRESHOLD} fields")
    print("-" * 70)
    print(f"Total Custom Fields: {count}")
    print(f"Status: {status}")
    print("-" * 70)

    if count > THRESHOLD:
        print(f"⚠️  WARNING: Instance exceeds threshold by {count - THRESHOLD} fields!")
    else:
        print(f"✓ Safe: {THRESHOLD - count} fields remaining before threshold")

    print("\nDetailed field list:")
    for f in custom_fields:
        print(f"  - {f['id']}: {f['name']} ({f['type']})")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Custom Fields Count: {count}/{THRESHOLD}")
    print(f"Overall Status: {status}")
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

    print_results(custom_fields)

    count = len(custom_fields)
    if count > THRESHOLD:
        exit(1)  # FAIL
    else:
        exit(0)  # PASS


if __name__ == "__main__":
    main()
