# Loop Assignment

Given solution is related to the problem statement given for ake-home interview

## Problem Statement

Loop monitors several restaurants in the US and needs to track whether each store is online during its business hours. All restaurants are expected to be online during those hours, but due to unknown issues, a store may go inactive for certain periods. Restaurant owners want a report showing how often this happened in the past (uptime and downtime) for the last hour, last day, and last week.

## Proposed Solution

A lightweight report generation service built with FastAPI. The service:

- Uses pre-processed data from a database (Postgres).

- Calculates uptime and downtime based on store status logs and business hours.

- Exposes APIs for report generation and retrieval.

- Offloads heavy report generation tasks to a BullMQ worker with Redis as a task queue.

This ensures the web server stays responsive while reports are generated asynchronously and stored for later download.

## Intuition

#### Timezone Handling

- Store status timestamps are saved as UTC.

- Business hours, originally in local time, are also converted to UTC for consistent comparisons.

- Python’s timezone libraries handle daylight savings automatically.

#### Report Generation

- A BullMQ worker fetches store status data, computes uptime/downtime for the past hour/day/week, and writes results into a CSV report.

- Reports are persisted on disk with metadata stored in Postgres.

#### Why FastAPI?

- Excellent async support, which aligns well with Prisma and BullMQ.

- Since the workload is I/O heavy, async provides concurrency benefits.
- Also has inbuilt testing and documentation feature, saving time writing API documentation.

## System Requirements

- Postgres: persistent store for pre-processed status and business hour data.

- Redis: background job queue for asynchronous report generation.

- FastAPI: lightweight API layer to request and retrieve reports.

- Prisma (Python client): ORM to interact with Postgres.

- Python (3.10+): runtime environment.

## Local Development Setup

### Prerequisites

- [Python](https://www.python.org/)
- [Docker](https://www.docker.com/products/docker-desktop)
- [Git](https://git-scm.com/)

### Clone the repository

```bash
git clone https://github.com/DSB2004/loop_assignment.git
cd loop_assignment
```

### Start Postgres with Docker

```bash
docker run --name postgres-db \
-e POSTGRES_PASSWORD=12345678 \
-p 5432:5432 \
-d postgres

```

### Setting Up Env

- Create a .env file in the root of the project.

- Use the .env.example file provided in the repository as a reference.

```bash
# .env
DATABASE_URL="postgres://postgres:12345678@localhost:5432/store_report"
REDIS_URL="redis://localhost:6379/0"

```

### Running Server Locally

#### Create a python development env

```bash
# create
python -m ./env venv
# run it
./env/Scripts/activate

```

#### Install dependencies

```bash
pip install -r requirements.txt

```

#### Settings up Prisma Client

```bash
# create a prisma instance
prisma generate

# if running first time, or reseting the database
prisma migrate reset

# to push new schema changes to db
prisma migrate dev --name <migration-name>

```

#### Start the development server

```bash
# start worker server
fastapi dev src/main.py

# start worker server
python src/worker.py
```


## Improvements

- Large CSVs are not scalable; Postgres is better for indexing, querying, and maintaining data consistency.
- Frequently requested reports can be cached to avoid recomputation.

## References and Documentation

- [FastAPI](https://fastapi.tiangolo.com/)
- [BullMQ](https://bullmq.io/)
- [Prisma Python Client](https://prisma-client-py.readthedocs.io/en/stable/)
