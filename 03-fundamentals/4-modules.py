import typing as t

import flama
from flama import Flama
from flama.modules import Module
from flama.http import PlainTextResponse


# ---------------------------------------------------------------------------
# Internationalisation Service
# ---------------------------------------------------------------------------


class I18nService:
    def __init__(self, translations: t.Dict[str, t.Dict[str, str]], default_lang: str):
        self._translations = translations
        self._default_lang = default_lang

    def translate(
        self, key: str, lang: str, default_message: t.Optional[str] = None
    ) -> str:
        if default_message is None:
            default_message = key

        return self._translations.get(lang, {}).get(key, default_message)


# ---------------------------------------------------------------------------
# Internationalisation Module
# ---------------------------------------------------------------------------


class I18nModule(Module):
    name = "i18n"

    def __init__(
        self, translations_data: t.Dict[str, t.Dict[str, str]], default_lang: str = "en"
    ):
        super().__init__()
        self._translations_data = translations_data
        self._default_lang = default_lang
        self.service: t.Optional[I18nService] = None

    async def on_startup(self):
        self.service = I18nService(
            translations=self._translations_data, default_lang=self._default_lang
        )

    async def on_shutdown(self):
        self.service = None

    def translate(
        self,
        key: str,
        lang: t.Optional[str] = None,
        default_message: t.Optional[str] = None,
    ) -> str:
        if not self.service:
            raise RuntimeError(
                "I18nService is not initialised. Ensure the application has started."
            )

        target_lang = lang if lang else self._default_lang
        return self.service.translate(key, target_lang, default_message=default_message)


# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------

sample_translations = {
    "en": {
        "welcome": "Welcome to our amazing application!",
        "farewell": "Goodbye and thank you for visiting!",
        "item_info": "This item is named '{item_name}'.",
    },
    "es": {
        "welcome": "¡Bienvenido/a a nuestra increíble aplicación!",
        "farewell": "¡Adiós y gracias por su visita!",
        "item_info": "Este artículo se llama '{item_name}'.",
    },
    "fr": {
        "welcome": "Bienvenue sur notre application incroyable !",
    },
}

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = Flama(
    modules=[I18nModule(translations_data=sample_translations, default_lang="en")]
)


@app.route("/home")
async def home_page():
    i18n_module = t.cast(I18nModule, app.i18n)
    welcome_message = i18n_module.translate("welcome")
    return PlainTextResponse(welcome_message)


@app.route("/home/{lang_code}")
async def home_page_localised(lang_code: str):
    i18n_module = t.cast(I18nModule, app.i18n)
    welcome_message = i18n_module.translate("welcome", lang=lang_code)
    return PlainTextResponse(welcome_message)


@app.route("/item/{item_id}")
async def item_details(item_id: str, lang: t.Optional[str] = None):
    i18n_module = t.cast(I18nModule, app.i18n)
    item_name_for_translation = f"Item {item_id}"
    item_message = i18n_module.translate("item_info", lang=lang).format(
        item_name=item_name_for_translation
    )
    farewell_message = i18n_module.translate(
        "farewell", lang=lang, default_message="Come back soon!"
    )
    return PlainTextResponse(f"{item_message}\n{farewell_message}")


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
