from datetime import timedelta

DOMAIN = "cloudflare_tunnel_monitor"

# Constants for user data keys
CONF_ACCOUNT_ID = "account_id"
CONF_API_KEY = "api_key"


# Constants for labels displayed in the user interface
LABEL_ACCOUNT_ID = "Account ID"
LABEL_API_KEY = "API Token"

# Constants for placeholders or suggested values
PLACEHOLDER_API_KEY = "api-token"
PLACEHOLDER_ACCOUNT_ID = "your-account-id"
CONF_METRICS_URL = "metrics_url"
LABEL_METRICS_URL = "Metrics URL"
PLACEHOLDER_METRICS_URL = "http://10.0.30.5:20241/metrics"

# Update intervals for the slower tunnel details
DETAILS_UPDATE_INTERVAL = timedelta(minutes=10)
LATEST_VERSION_UPDATE_INTERVAL = timedelta(hours=6)

# Options
CONF_REPAIR_ISSUES = "repair_issues"
DEFAULT_REPAIR_ISSUES = False
