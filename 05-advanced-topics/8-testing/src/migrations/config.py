import dataclasses
import logging
import uuid

from flama.config import Config

import src.config

__all__ = ["APP", "DATABASE"]

config = Config()
logger = logging.getLogger(__name__)


@dataclasses.dataclass
class User:
    id: uuid.UUID
    name: str
    email: str
    password: str
    organisation: uuid.UUID

    def __post_init__(self):
        self.id = uuid.UUID(str(self.id))
        self.organisation = uuid.UUID(str(self.organisation))


# App config:
APP = src.config.APP

# Database config:
DATABASE = src.config.DATABASE
