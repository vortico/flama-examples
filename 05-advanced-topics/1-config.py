import dataclasses
import os

from flama.config import Config, Secret

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------

os.environ["API_KEY"] = "sk_prod_987654321"
os.environ["DEBUG"] = "false"
os.environ["FEATURE_FLAGS"] = '{"enable_new_ui": true, "max_daily_limit": 500}'


# ---------------------------------------------------------------------------
# Config file
# ---------------------------------------------------------------------------

CONFIG_CONTENT = """
DEBUG: true

HOST: "127.0.0.1"
PORT: 8000

DATABASE:
  host: "db.internal"
  port: 5432
  name: "flama_production"
  user: "admin"
"""

CONFIG_FILE_PATH = "config.yaml"
with open(CONFIG_FILE_PATH, "w") as f:
    f.write(CONFIG_CONTENT)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str

    def __post_init__(self):
        self.port = int(self.port)

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}@{self.host}:{self.port}/{self.name}"


@dataclasses.dataclass
class FeatureFlags:
    enable_new_ui: bool
    max_daily_limit: int


config = Config(CONFIG_FILE_PATH, format="yaml")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

DEBUG = config("DEBUG", cast=bool)
print(f"DEBUG:        {DEBUG}")

API_KEY = config("API_KEY", cast=Secret)
print(f"API_KEY:      {API_KEY!r}")

HOST = config("HOST")
print(f"HOST:         {HOST}")

DB = config("DATABASE", cast=DatabaseConfig)
print(f"DB Conn:      {DB.connection_string}")

FEATURES = config("FEATURE_FLAGS", cast=FeatureFlags)
print(f"Features:     {FEATURES}")
print(f"  - New UI:   {FEATURES.enable_new_ui}")
print(f"  - Limit:    {FEATURES.max_daily_limit}")

os.remove(CONFIG_FILE_PATH)
