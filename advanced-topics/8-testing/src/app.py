from flama import Flama
from flama.sqlalchemy import SQLAlchemyModule

from src.config import APP, DATABASE
from src.schemas import AnimalResource

app = Flama(
    modules=[
        SQLAlchemyModule(
            DATABASE.url(APP.database, APP.database_user, APP.database_password),
        )
    ]
)
app.resources.add_resource("/animal/", AnimalResource)
