import flama
from flama import Component, Flama


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class Address:
    def __init__(self, street: str, city: str, zip_code: str):
        self.street = street
        self.city = city
        self.zip_code = zip_code

    def to_dict(self):
        return {"street": self.street, "city": self.city, "zip_code": self.zip_code}


class Person:
    def __init__(self, name: str, age: int, address: Address):
        self.name = name
        self.age = age
        self.address = address

    def to_dict(self):
        return {"name": self.name, "age": self.age, "address": self.address.to_dict()}


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


class AddressComponent(Component):
    def resolve(self, street: str, city: str, zip_code: str) -> Address:
        return Address(street=street, city=city, zip_code=zip_code)


class PersonComponent(Component):
    def resolve(self, name: str, age: int, address: Address) -> Person:
        return Person(name=name, age=age, address=address)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = Flama(
    openapi={
        "info": {
            "title": "Hello-🔥",
            "version": "1.0",
            "description": "My first API",
        },
    },
    components=[PersonComponent(), AddressComponent()],
)


@app.get("/person-info/")
def get_person_details(person_instance: Person):
    return {"data": person_instance.to_dict()}


@app.get("/address-info/")
def get_address_details(address_instance: Address):
    return {"data": address_instance.to_dict()}


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
