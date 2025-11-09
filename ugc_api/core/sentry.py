import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


def init_sentry(dsn: str, environment: str = "dev") -> None:
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        integrations=[
            LoggingIntegration(level=None, event_level=None),
            FastApiIntegration(),
        ],
        traces_sample_rate=1.0,
        send_default_pii=True,
    )
