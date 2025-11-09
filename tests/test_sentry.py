from ugc_api.core import sentry as sentry_mod


async def test_init_sentry_noop_with_empty_dsn():
    sentry_mod.init_sentry("")
    assert True
