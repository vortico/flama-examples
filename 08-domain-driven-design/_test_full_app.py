import asyncio
import importlib.util
import os
import sys

import httpx
from flama.client import Client


async def main():
    for db in (
        "ddd_full_app.db",
        "ddd_resources_demo.db",
        "ddd_worker_demo.db",
        "ddd_users.db",
        "ddd_repo_demo.db",
    ):
        if os.path.exists(db):
            os.unlink(db)

    spec = importlib.util.spec_from_file_location(
        "full_app", "domain-driven-design/6-full-app.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Wire the notification service transport for testing
    for component in mod.app.components:
        from flama.ddd import WorkerComponent
        from flama.ddd.workers.http import HTTPWorker

        if isinstance(component, WorkerComponent) and isinstance(
            component.worker, HTTPWorker
        ):
            component.worker._client_kwargs["transport"] = httpx.ASGITransport(
                app=mod.notification_service
            )

    from flama.client import LifespanContextManager

    async with LifespanContextManager(mod.notification_service):
        async with Client(app=mod.app) as client:
            r = await client.get("/")
            assert r.status_code == 200
            print("1. GET / => OK", r.json())

            r = await client.post(
                "/user/",
                json={
                    "name": "John",
                    "surname": "Doe",
                    "email": "john@doe.com",
                    "password": "123456",
                },
            )
            assert r.status_code == 200
            print("2. POST /user/ => OK (created)")

            r = await client.post(
                "/user/signin/", json={"email": "john@doe.com", "password": "123456"}
            )
            assert r.status_code == 400
            print("3. POST /user/signin/ (inactive) => OK (400)")

            r = await client.post(
                "/user/activate/", json={"email": "john@doe.com", "password": "123456"}
            )
            assert r.status_code == 200
            print("4. POST /user/activate/ => OK")

            r = await client.post(
                "/user/signin/", json={"email": "john@doe.com", "password": "123456"}
            )
            assert r.status_code == 200
            print("5. POST /user/signin/ (active) => OK", r.json())

            r = await client.post(
                "/user/deactivate/",
                json={"email": "john@doe.com", "password": "123456"},
            )
            assert r.status_code == 200
            print("6. POST /user/deactivate/ => OK")

            r = await client.post(
                "/user/signin/", json={"email": "john@doe.com", "password": "wrong"}
            )
            assert r.status_code == 401
            print("7. POST /user/signin/ (wrong pwd) => OK (401)")

            r = await client.post(
                "/user/signin/",
                json={"email": "nobody@nowhere.com", "password": "123456"},
            )
            assert r.status_code == 404
            print("8. POST /user/signin/ (not found) => OK (404)")

    print("\nAll tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
