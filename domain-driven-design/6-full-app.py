import hashlib
import http
import typing as t
import uuid

import flama
import pydantic
import sqlalchemy
from flama import Flama, types
from flama.ddd import WorkerComponent
from flama.ddd.exceptions import NotFoundError
from flama.ddd.repositories.http import HTTPRepository
from flama.ddd.repositories.sqlalchemy import SQLAlchemyTableRepository
from flama.ddd.workers.http import HTTPWorker
from flama.ddd.workers.sqlalchemy import SQLAlchemyWorker
from flama.exceptions import HTTPException
from flama.http import APIResponse
from flama.resources import Resource
from flama.resources.routing import ResourceRoute
from flama.sqlalchemy import SQLAlchemyModule, metadata

# ===========================================================================
# Notification service (simulated backend)
# ===========================================================================

notification_service = Flama()
_sent_notifications: list[dict] = []


class WelcomePayload(pydantic.BaseModel):
    email: str
    name: str


@notification_service.post("/notifications/welcome/send/")
async def send_welcome(
    data: t.Annotated[types.Schema, types.SchemaMetadata(WelcomePayload)],
):
    _sent_notifications.append({"type": "welcome", **dict(data)})
    return {"status": "sent"}


# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------

user_table = sqlalchemy.Table(
    "user",
    metadata,
    sqlalchemy.Column(
        "id",
        sqlalchemy.String,
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    ),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("surname", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("email", sqlalchemy.String, nullable=False, unique=True),
    sqlalchemy.Column("password", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("active", sqlalchemy.Boolean, nullable=False),
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class UserCredentials(pydantic.BaseModel):
    email: str
    password: str


class UserDetails(UserCredentials):
    name: str
    surname: str


class User(UserDetails):
    id: t.Optional[str] = None
    active: t.Optional[bool] = False


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class UserRepository(SQLAlchemyTableRepository):
    _table = user_table


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------


class RegisterWorker(SQLAlchemyWorker):
    user: UserRepository


# ---------------------------------------------------------------------------
# Notification repository and worker (HTTP-based)
# ---------------------------------------------------------------------------


class WelcomeNotificationRepository(HTTPRepository):
    _resource = "notifications/welcome"

    async def send(self, email: str, name: str) -> None:
        response = await self._client.post(
            f"{self._resource}/send/",
            json={"email": email, "name": name},
        )
        response.raise_for_status()


class NotificationWorker(HTTPWorker):
    welcome: WelcomeNotificationRepository


# ---------------------------------------------------------------------------
# Password helper
# ---------------------------------------------------------------------------

ENCRYPTION_SALT = uuid.uuid4().hex
ENCRYPTION_PEPPER = uuid.uuid4().hex


class Password:
    def __init__(self, password: str):
        self._password = password

    def encrypt(self) -> str:
        return hashlib.sha512(
            (
                hashlib.sha512((self._password + ENCRYPTION_SALT).encode()).hexdigest()
                + ENCRYPTION_PEPPER
            ).encode()
        ).hexdigest()


# ---------------------------------------------------------------------------
# Resource
# ---------------------------------------------------------------------------


class UserResource(Resource):
    name = "user"
    verbose_name = "User"

    @ResourceRoute.method("/", methods=["POST"], name="create")
    async def create(
        self,
        worker: RegisterWorker,
        notification_worker: NotificationWorker,
        data: t.Annotated[types.Schema, types.SchemaMetadata(UserDetails)],
    ):
        """
        tags:
            - User
        summary:
            User create
        description:
            Create a new user with the provided details.
        responses:
            200:
                description:
                    User created successfully.
        """
        async with worker:
            try:
                await worker.user.retrieve(email=data["email"])
            except NotFoundError:
                await worker.user.create(
                    {
                        **data,
                        "password": Password(data["password"]).encrypt(),
                        "active": False,
                    }
                )

        async with notification_worker:
            await notification_worker.welcome.send(
                email=data["email"], name=data["name"]
            )

        return APIResponse(status_code=http.HTTPStatus.OK)

    @ResourceRoute.method("/signin/", methods=["POST"], name="signin")
    async def signin(
        self,
        worker: RegisterWorker,
        data: t.Annotated[types.Schema, types.SchemaMetadata(UserCredentials)],
    ):
        """
        tags:
            - User
        summary:
            User sign in
        description:
            Authenticate a user with email and password.
        responses:
            200:
                description:
                    User signed in successfully.
            400:
                description:
                    User not active.
            401:
                description:
                    Invalid credentials.
            404:
                description:
                    User not found.
        """
        async with worker:
            password = Password(data["password"])
            try:
                user = await worker.user.retrieve(email=data["email"])
            except NotFoundError:
                raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND)

            if user["password"] != password.encrypt():
                raise HTTPException(status_code=http.HTTPStatus.UNAUTHORIZED)

            if not user["active"]:
                raise HTTPException(
                    status_code=http.HTTPStatus.BAD_REQUEST,
                    detail="User must be activated via /user/activate/",
                )

        return APIResponse(
            status_code=http.HTTPStatus.OK,
            schema=t.Annotated[types.Schema, types.SchemaMetadata(User)],
            content=user,
        )

    @ResourceRoute.method("/activate/", methods=["POST"], name="activate")
    async def activate(
        self,
        worker: RegisterWorker,
        data: t.Annotated[types.Schema, types.SchemaMetadata(UserCredentials)],
    ):
        """
        tags:
            - User
        summary:
            User activate
        description:
            Activate an existing user account.
        responses:
            200:
                description:
                    User activated successfully.
            401:
                description:
                    Invalid credentials.
            404:
                description:
                    User not found.
        """
        async with worker:
            try:
                user = await worker.user.retrieve(email=data["email"])
            except NotFoundError:
                raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND)

            if user["password"] != Password(data["password"]).encrypt():
                raise HTTPException(status_code=http.HTTPStatus.UNAUTHORIZED)

            if not user["active"]:
                await worker.user.update({"active": True}, id=user["id"])

        return APIResponse(status_code=http.HTTPStatus.OK)

    @ResourceRoute.method("/deactivate/", methods=["POST"], name="deactivate")
    async def deactivate(
        self,
        worker: RegisterWorker,
        data: t.Annotated[types.Schema, types.SchemaMetadata(UserCredentials)],
    ):
        """
        tags:
            - User
        summary:
            User deactivate
        description:
            Deactivate an existing user account.
        responses:
            200:
                description:
                    User deactivated successfully.
            401:
                description:
                    Invalid credentials.
            404:
                description:
                    User not found.
        """
        async with worker:
            try:
                user = await worker.user.retrieve(email=data["email"])
            except NotFoundError:
                raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND)

            if user["password"] != Password(data["password"]).encrypt():
                raise HTTPException(status_code=http.HTTPStatus.UNAUTHORIZED)

            if user["active"]:
                await worker.user.update({"active": False}, id=user["id"])

        return APIResponse(status_code=http.HTTPStatus.OK)


# ---------------------------------------------------------------------------
# Application assembly
# ---------------------------------------------------------------------------

DATABASE_URL = "sqlite+aiosqlite:///ddd_full_app.db"
NOTIFICATION_SERVICE_URL = "http://notifications:8001"

app = Flama(
    openapi={
        "info": {
            "title": "Domain-driven API",
            "version": "1.0.0",
            "description": "Domain-driven design with Flama 🔥",
        },
    },
    docs="/docs/",
    modules=[SQLAlchemyModule(DATABASE_URL)],
    components=[
        WorkerComponent(worker=RegisterWorker()),
        WorkerComponent(worker=NotificationWorker(url=NOTIFICATION_SERVICE_URL)),
    ],
)

app.resources.add_resource("/user/", UserResource)


@app.get("/", name="info")
def info():
    """
    tags:
        - Info
    summary:
        Ping
    description:
        Returns a brief description of the API.
    responses:
        200:
            description:
                Successful response with API info.
    """
    return {
        "title": app.schema.openapi["info"]["title"],
        "description": app.schema.openapi["info"]["description"],
        "public": True,
    }


@app.on_event("startup")
async def on_startup():
    async with app.sqlalchemy.engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
