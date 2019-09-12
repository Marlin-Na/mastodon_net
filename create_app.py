
from mastodon import Mastodon

APP_NAME = "test_crawler"

Mastodon.create_app(
    APP_NAME,
    scopes=["read"],
    api_base_url="https://mastodon.social",
    to_file="crawler_secret"
)
