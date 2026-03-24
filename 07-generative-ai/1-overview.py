import flama
from flama import Flama

app = Flama(
    openapi={
        "info": {
            "title": "Generative AI API",
            "version": "1.0.0",
            "description": "Serving large language models with Flama 🔥",
        },
    },
    docs="/docs/",
)

app.models.add_model(
    path="/llm/",
    model="google_gemma-4-E2B-it.flm",
    name="assistant",
    serving=("native", "openai"),
)


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
