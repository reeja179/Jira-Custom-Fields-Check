#!/usr/bin/env python3
"""
Jira Custom Fields Validator
Check if Jira instance exceeds 100 custom fields
"""

import requests
import base64
import json
from datetime import datetime

# ============================================================================
# CONFIGURATION - UPDATE THESE WITH YOUR VALUES
# ============================================================================

JIRA_URL = "https://techdatatoronto.atlassian.net"
JIRA_EMAIL = "reeja4009@gmail.com"
JIRA_API_TOKEN = "ATATT3xFfGF0PCWk7ZgM0LZjLMo17zqVvQVex_HLxBu8CN89s3Ye9i4MvdJPNF33CieLZkLJ5cqwLmJqFvd-hRd637knmRPx-hl3jBYhfdZ0oge0HHZAMbiUkMfy1OKTEDLaM4koSR0jLf3pSJlNsi8GnLoykgDHDwo7speSSPSsrO4gjAAto-s=97F3E380"

THRESHOLD = 100  # Maximum allowed custom fields

# ============================================================================
# SCRIPT LOGIC
# ============================================================================

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
    
    # API v2 returns a list of field objects
    for field in fields:
        # In Jira API v2, custom fields have IDs like "customfield_10000"
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
    
    # Step 1: Get fields from Jira
    fields = get_jira_fields()
    
    if fields is None:
        print("\n✗ Failed to retrieve fields from Jira")
        exit(1)
    
    # Step 2: Filter custom fields only
    print(f"\n✓ Retrieved {len(fields)} total fields")
    custom_fields = filter_custom_fields(fields)
    
    # Step 3: Print results
    print_results(custom_fields)
    
    # Step 4: Exit with appropriate code
    count = len(custom_fields)
    if count > THRESHOLD:
        exit(1)  # FAIL
    else:
        exit(0)  # PASS


if __name__ == "__main__":
    main()