<div align="center">

# 🔥 Flama Examples

**Production-ready examples for the Flama framework.**

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue?logo=python&logoColor=white)](https://python.org)
[![Flama](https://img.shields.io/badge/framework-flama-FF6F00)](https://flama.dev)
[![uv](https://img.shields.io/badge/pkg-uv-black?logo=astral&logoColor=white)](https://astral.sh/blog/uv)

A comprehensive collection of examples accompanying the [Flama documentation](https://flama.dev). From first steps to advanced patterns, each section is self-contained and ready to run.

---

</div>

## Why this repository?

Learning a framework is best done by example. This repository provides a structured, progressive set of examples that mirror the official documentation. Each section builds upon the previous one, taking you from a simple "hello world" to production-grade applications with Domain Driven Design, AI model serving, and more.

## Quick Start

```bash
# Clone
git clone https://github.com/vortico/flama-examples.git && cd flama-examples

# Install (using uv, recommended)
uv sync

# Run any example
cd <section> && python <script>.py
```

## Contents

| # | Section | Description |
|---|---------|-------------|
| [01](01-introduction/) | **Introduction** | First steps with Flama: minimal apps, routing basics, and project structure |
| [02](02-getting-started/) | **Getting Started** | Setting up your environment and building your first complete application |
| [03](03-fundamentals/) | **Fundamentals** | Applications, routes, components, modules, middleware, endpoints, resources, and responses |
| [04](04-cli-commands/) | **CLI Commands** | Flama CLI usage: run, serve, start, model, get, upgrade |
| [05](05-advanced-topics/) | **Advanced Topics** | Config, debug, client, pagination, background tasks, lifespan, authentication, and testing |
| [06](06-predictive-ai/) | **Predictive AI** | Model packaging, adding models, model resources, and model components |
| [07](07-generative-ai/) | **Generative AI** | Overview, serving LLMs, chatbot, and MCP |
| [08](08-domain-driven-design/) | **Domain Driven Design** | Data models, repositories, workers, resources, and full application |
| [09](09-contributing/) | **Contributing** | Contributing to Flama |

## What's Inside

```
flama-examples/
├── 01-introduction/            # Introduction to Flama
├── 02-getting-started/         # Getting started with Flama
├── 03-fundamentals/            # Applications, routes, components, modules, middleware, endpoints, resources, responses
├── 04-cli-commands/            # CLI usage: run, serve, start, model, get, upgrade
├── 05-advanced-topics/         # Config, debug, client, pagination, background tasks, lifespan, auth, testing
├── 06-predictive-ai/           # Model packaging, adding models, model resources, model components
├── 07-generative-ai/           # Overview, serving LLMs, chatbot, MCP
├── 08-domain-driven-design/    # Data models, repositories, workers, resources, full application
├── 09-contributing/            # Contributing to Flama
└── pyproject.toml              # Project config and dependencies
```

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| **Language** | Python 3.13+ | Core language |
| **Framework** | Flama | Async-first API framework with ML-native support |
| **ORM** | SQLAlchemy | Database access and modelling |
| **Migrations** | Alembic | Schema versioning |
| **Schemas** | Pydantic, Marshmallow, Typesystem | Data validation and serialisation |
| **Testing** | pytest, pytest-asyncio | Async test suite |
| **Package Manager** | uv | Fast, modern Python dependency management |

## Contributing

```bash
# 1. Clone and install
git clone https://github.com/vortico/flama-examples.git && cd flama-examples
uv sync

# 2. Make your changes

# 3. Submit a pull request
```

## License

This project is maintained by [Vortico](https://vortico.tech) as companion material for the [Flama documentation](https://flama.dev).

---

<div align="center">

**Built with 🔥 by [Vortico](https://vortico.tech)**

</div>
