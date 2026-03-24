import json

import flama
from flama import Flama
from flama.mcp.data_structures import Elicit, Elicitation

app = Flama(
    openapi={
        "info": {
            "title": "Generative AI API",
            "version": "1.0.0",
            "description": "Model Context Protocol servers with Flama 🔥",
        },
    },
)

app.mcp.add_server("/mcp/tools/", "tools", version="2.0.0", instructions="Flama demo MCP tools server")
app.mcp.add_server("/mcp/math/", "math", version="2.0.0")


@app.mcp.tool("add", description="Add two integers", mcp="tools")
def add(a: int, b: int) -> int:
    return a + b


@app.mcp.tool("square", task=True, description="Square a number as a background task", mcp="tools")
async def square(x: int) -> int:
    return x * x


@app.mcp.tool("confirm", description="Confirm an action through an elicitation round-trip", mcp="tools")
def confirm(elicitation: Elicitation) -> str:
    if "confirm" not in elicitation:
        return Elicit.require("Are you sure?", {"type": "boolean"}, name="confirm")
    return f"confirmed={elicitation['confirm']}"


@app.mcp.resource("config://app", name="config", description="Application configuration",
                  mime_type="application/json", mcp="tools")
def config():
    return json.dumps({"debug": True, "name": "flama-mcp"})


@app.mcp.prompt("summarise", description="Summarise the given text", mcp="tools")
def summarise(text: str):
    return f"Summarise the following:\n\n{text}"


@app.mcp.app_template("ui://widget", name="widget", description="A small UI widget", mcp="tools")
def widget():
    return "<html><body><h1>Flama widget</h1></body></html>"


@app.mcp.tool("with_ui", description="A tool that declares a prefetchable UI template",
              ui_template="ui://widget", mcp="tools")
def with_ui() -> str:
    return "rendered"


@app.mcp.tool("multiply", description="Multiply two integers", mcp="math")
def multiply(a: int, b: int) -> int:
    return a * b


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
