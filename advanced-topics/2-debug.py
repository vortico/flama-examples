import flama
from flama import Flama

app = Flama(debug=True)


@app.route("/")
def home():
    """
    tags:
        - Home
    summary:
        Home Page
    description:
        A simple endpoint to verify the server is running.
    """
    return {
        "message": "Hello! The API is running in DEBUG mode.",
        "instructions": [
            "1. Visit http://localhost:8000/divide/10/0/ to trigger a 500 Internal Server Error.",
            "2. Visit http://localhost:8000/non-existent-page/ to trigger a 404 Not Found error.",
        ],
    }


@app.route("/divide/{a:int}/{b:int}/")
def divide(a: int, b: int):
    """
    tags:
        - Debugging Demo
    summary:
        Division Endpoint
    description:
        A simple division endpoint. Try passing b=0 to trigger a ZeroDivisionError
        and see the interactive traceback page!
    """
    result = a / b
    return {"result": result}


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
