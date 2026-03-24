import asyncio
import time
import typing as t

import flama
from flama import Flama, http, types
from flama.middleware import Middleware


# ---------------------------------------------------------------------------
# Custom middleware
# ---------------------------------------------------------------------------


class TimingMiddleware:
    def __init__(self, app: types.App):
        self.app: Flama = t.cast("Flama", app)

    async def __call__(
        self, scope: types.Scope, receive: types.Receive, send: types.Send
    ):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()

        async def send_with_timing_header(message: types.Message):
            if message["type"] == "http.response.start":
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                headers = list(message.get("headers", []))
                headers.append(
                    (b"x-process-time-ms", f"{duration_ms:.2f}".encode("latin-1"))
                )
                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_with_timing_header)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = Flama(middleware=[Middleware(TimingMiddleware)])


@app.route("/fast")
async def fast_endpoint():
    return http.PlainTextResponse("This was fast! Check X-Process-Time-MS header.")


@app.route("/slow")
async def slow_endpoint():
    await asyncio.sleep(0.5)
    time.sleep(0.5)
    return http.PlainTextResponse(
        "This was a bit slower. Check X-Process-Time-MS header."
    )


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8080)
