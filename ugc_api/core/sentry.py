import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

def setup_sentry(dsn: str, environment: str, release: str | None = None):
    if not dsn:
        logging.info("sentry_disabled")
        return
    sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
    sentry_sdk.init(dsn=dsn, environment=environment, release=release, integrations=[sentry_logging])
