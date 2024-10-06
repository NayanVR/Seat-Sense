# Seat Sense

Seat sense is a auditorium seat occupancy detection and attendance management system.

## Setup

### Pre-requisites

- Python 3.11+
- [TimescaleDB](https://docs.timescale.com/self-hosted/latest/install/)
- [uv package manager](https://docs.astral.sh/uv/)

### Installation

Install all the dependencies with the following command:
```
cd seat-sense
```
```bash
uv sync
```

Set environment variables in `.env` file from the `.env.example` file.
```bash
cp .env.example .env
```

ℹ️ To add any specific dependencies:
```bash
uv add <package-name>
```

### Working with Alembic

```bash
cd seat-sense/app
```

> To use Alembic, you need to set the `sqlalchemy.url` in `alembic.ini` file. eg.
```sqlalchemy.url = postgresql+psycopg2://<username>:<password>@localhost/<database>```

Update database with latest migrations
```bash
alembic upgrade head
```

ℹ️ To create new migrations (use carefully):
```bash
alembic revision --autogenerate -m "<message>"
```

### Run the application
Run the application with the following command at root level:
```bash
uv run -- uvicorn app.main:app --reload
```