import os
from prometheus_client import Counter, Histogram, CollectorRegistry, multiprocess, make_asgi_app

# Ensure the directory for multiprocess metrics exists if configured
# This should match PROMETHEUS_MULTIPROC_DIR in .env and docker-compose volume
if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
    prom_dir = os.environ['PROMETHEUS_MULTIPROC_DIR']
    os.makedirs(prom_dir, exist_ok=True)
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
else:
    # Standard registry for single process or non-Uvicorn multiprocess setups
    registry = CollectorRegistry() # Use default registry if multiprocess is not needed/configured

# --- Define Metrics ---

# Example: Counter for scheduled posts
# Usage: POSTS_SCHEDULED.labels(platform='twitter').inc()
POSTS_SCHEDULED = Counter(
    'posts_scheduled_total',
    'Total number of posts scheduled',
    ['platform'], # Label to distinguish counts per platform
    registry=registry
)

# Example: Counter for successfully sent posts
# Usage: POSTS_SENT_SUCCESS.labels(platform='facebook').inc()
POSTS_SENT_SUCCESS = Counter(
    'posts_sent_success_total',
    'Total number of posts successfully sent',
    ['platform'],
    registry=registry
)

# Example: Counter for failed posts
# Usage: POSTS_SENT_FAILED.labels(platform='twitter', reason='api_error').inc()
POSTS_SENT_FAILED = Counter(
    'posts_sent_failed_total',
    'Total number of posts that failed to send',
    ['platform', 'reason'], # Labels for platform and failure reason
    registry=registry
)

# Example: Histogram for request latency on the /schedule endpoint
# Usage: SCHEDULE_REQUEST_LATENCY.labels(method='POST').observe(time_taken)
SCHEDULE_REQUEST_LATENCY = Histogram(
    'schedule_request_latency_seconds',
    'Latency of requests to the /schedule endpoint',
    ['method'], # Could add other labels like user_id if careful about cardinality
    registry=registry
)

# Example: Histogram for platform API call duration (measured in tasks.py)
# Usage: PLATFORM_API_DURATION.labels(platform='twitter').observe(api_time)
PLATFORM_API_DURATION = Histogram(
    'platform_api_duration_seconds',
    'Duration of API calls made to external platforms',
    ['platform'],
    registry=registry
)

# --- ASGI App for Metrics ---

# Create the ASGI app to expose the metrics for Prometheus scraping
# Use this app in main.py to mount at /metrics
metrics_app = make_asgi_app(registry=registry)

# --- TODO ---
# - Import these metrics into relevant modules (main.py, tasks.py)
# - Call .inc() or .observe() at appropriate points in the code.
# - Ensure Uvicorn is run with multiple workers if using multiprocess mode.
# - Verify the PROMETHEUS_MULTIPROC_DIR volume mount in docker-compose.yml.
