import flama
from flama import Flama
from flama import types as t

openapi: t.OpenAPISpec = {
    "info": {
        "title": "Hello-🔥",
        "version": "1.0",
        "description": "My first API using Flama, demonstrating basic app setup and OpenAPI integration.",
    },
    "tags": [
        {"name": "Salute", "description": "Endpoints that offer simple greetings."},
    ],
}

app = Flama(
    openapi=openapi,
    schema="/custom-schema/",
    docs="/custom-api-docs/",
)


@app.route("/")
def home():
    """
    tags:
        - Salute
    summary:
        Home
    description: |
        This endpoint provides a simple greeting from the <FlamaName /> application.
        It serves as a basic example to:
        1. Verify that the application is running correctly.
        2. Illustrate how OpenAPI documentation is automatically generated from
           correctly formatted docstrings in route handler functions.
    responses:
        "200":
            description: Warming hello message returned successfully!
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            message:
                                type: string
                                example: "Hello 🔥"
    """
    return {"message": "Hello 🔥"}


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
