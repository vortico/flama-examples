import typing as t

import pydantic

import flama
from flama import Flama, http, schemas
from flama.http import (
    APIErrorResponse,
    APIResponse,
    HTMLResponse,
    JSONResponse,
    NDJSONResponse,
    PlainTextResponse,
    RedirectResponse,
    ServerSentEvent,
    ServerSentEventResponse,
)

app = Flama(
    openapi={
        "info": {
            "title": "Responses",
            "version": "1.0.0",
            "description": "Buffered and streaming responses with Flama 🔥",
        },
    },
    docs="/docs/",
)


# ---------------------------------------------------------------------------
# Buffered responses
# ---------------------------------------------------------------------------


@app.route("/json/", name="json")
def json():
    return JSONResponse({"message": "hello"})


@app.route("/text/", name="text")
def text():
    return PlainTextResponse("hello")


@app.route("/html/", name="html")
def html():
    return HTMLResponse("<h1>hello</h1>")


@app.route("/old/", name="old")
def old():
    return RedirectResponse("/new/")


# ---------------------------------------------------------------------------
# Schema-validated responses
# ---------------------------------------------------------------------------


class Puppy(pydantic.BaseModel):
    id: int
    name: str


@app.route("/puppy/", name="puppy")
def puppy():
    return APIResponse(
        {"id": 1, "name": "Canna"},
        schema=t.Annotated[schemas.Schema, schemas.SchemaMetadata(Puppy)],
    )


@app.route("/fail/", name="fail")
def fail():
    return APIErrorResponse(detail="Puppy not found", status_code=404)


# ---------------------------------------------------------------------------
# Streaming responses
# ---------------------------------------------------------------------------


@app.route("/ndjson/", name="ndjson")
def ndjson():
    async def numbers() -> t.AsyncIterator[dict]:
        for i in range(50):
            yield {"i": i, "square": i * i}

    return NDJSONResponse(numbers())


@app.route("/sse/", name="sse")
def sse():
    async def ticks() -> t.AsyncIterator[ServerSentEvent]:
        for i in range(50):
            if i % 10 == 0:
                yield ServerSentEvent(comment="heartbeat")
            yield ServerSentEvent(data=str(i), event="tick", id=str(i))

    return ServerSentEventResponse(ticks())


@app.route("/sse/resume/", name="sse_resume")
def sse_resume(request: http.Request):
    start = int(request.headers.get("last-event-id", "-1")) + 1

    async def ticks() -> t.AsyncIterator[ServerSentEvent]:
        for i in range(start, start + 5):
            yield ServerSentEvent(data=str(i), event="tick", id=str(i))

    return ServerSentEventResponse(ticks())


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
