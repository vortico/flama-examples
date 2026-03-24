import http
import pytest
import sqlalchemy

from src import models

pytestmark = pytest.mark.asyncio


class TestCaseIntegration:
    @pytest.fixture(scope="function", autouse=True)
    async def animals(self, connection):
        data = [
            {"name": "test.animal.first"},
            {"name": "test.animal.second"},
        ]
        await connection.execute(sqlalchemy.insert(models.table).values(data))
        return data

    @pytest.mark.parametrize(
        ["expected_status", "expected_names"],
        [
            pytest.param(
                http.HTTPStatus.OK,
                ["test.animal.first", "test.animal.second"],
                id="ok_list_animals",
            ),
        ],
    )
    async def test_list(self, client, expected_status, expected_names):
        r = await client.get(
            str(client.app.resolve_url("animal:list").path), params={"page_size": 100}
        )

        assert r.status_code == expected_status, r.json()

        if r.status_code == http.HTTPStatus.OK:
            assert set([x["name"] for x in r.json()["data"]]) == set(expected_names)

    @pytest.mark.parametrize(
        ["data", "expected_status"],
        [
            pytest.param(
                {"name": "new.animal.third"},
                http.HTTPStatus.CREATED,
                id="ok_create",
            ),
            pytest.param(
                {},
                http.HTTPStatus.BAD_REQUEST,
                id="fails_missing_name",
            ),
        ],
    )
    async def test_create(self, connection, client, data, expected_status):
        r = await client.post(
            str(client.app.resolve_url("animal:create").path), json=data
        )

        assert r.status_code == expected_status, r.json()

        if r.status_code == http.HTTPStatus.CREATED:
            response = r.json()

            db_animal = (
                (
                    await connection.execute(
                        sqlalchemy.select(models.table).where(
                            models.table.c["id"] == response["id"]
                        )
                    )
                )
                .fetchone()
                ._asdict()
            )
            assert db_animal["name"] == data["name"]

