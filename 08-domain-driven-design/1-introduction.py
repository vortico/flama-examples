import flama
from flama import Flama

app = Flama(
    openapi={
        "info": {
            "title": "Domain-driven API",
            "version": "1.0.0",
            "description": "Domain-driven design with Flama 🔥",
        },
    },
    docs="/docs/",
)


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


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
