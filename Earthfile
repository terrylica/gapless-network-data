VERSION 0.8

FROM python:3.11-slim
WORKDIR /app

# Cached dependency layer
deps:
    RUN pip install uv
    COPY pyproject.toml uv.lock README.md ./
    RUN uv sync --frozen
    SAVE IMAGE --cache-hint

# Build - copy source files
build:
    FROM +deps
    COPY --dir src schema tests ./
    COPY docs/schema docs/schema
    SAVE ARTIFACT src /src
    SAVE ARTIFACT schema /schema

# Unit tests (no secrets)
test-unit:
    FROM +build
    RUN uv run pytest tests/ -v

# Schema generation (no secrets)
test-schema-generate:
    FROM +build
    RUN uv run gapless-network-data schema generate-types
    RUN uv run gapless-network-data schema generate-ddl
    RUN uv run gapless-network-data schema doc
    RUN test -f src/gapless_network_data/schema/_generated/blocks.py
    RUN test -f schema/clickhouse/_generated/ethereum_mainnet.sql
    RUN test -f docs/schema/ethereum_mainnet.md
    SAVE ARTIFACT src/gapless_network_data/schema/_generated AS LOCAL ./earthly-artifacts/types
    SAVE ARTIFACT schema/clickhouse/_generated AS LOCAL ./earthly-artifacts/ddl
    SAVE ARTIFACT docs/schema AS LOCAL ./earthly-artifacts/docs

# Schema validation (requires secrets)
test-schema-validate:
    FROM +build
    RUN --secret CLICKHOUSE_HOST_READONLY \
        --secret CLICKHOUSE_USER_READONLY \
        --secret CLICKHOUSE_PASSWORD_READONLY \
        uv run gapless-network-data schema validate

# Full E2E workflow (requires secrets)
test-schema-e2e:
    FROM +build
    RUN uv run gapless-network-data schema generate-types
    RUN uv run gapless-network-data schema generate-ddl
    RUN uv run gapless-network-data schema doc
    RUN --secret CLICKHOUSE_HOST_READONLY \
        --secret CLICKHOUSE_USER_READONLY \
        --secret CLICKHOUSE_PASSWORD_READONLY \
        uv run gapless-network-data schema validate
    SAVE ARTIFACT src/gapless_network_data/schema/_generated AS LOCAL ./earthly-artifacts/e2e/types
    SAVE ARTIFACT schema/clickhouse/_generated AS LOCAL ./earthly-artifacts/e2e/ddl
    SAVE ARTIFACT docs/schema AS LOCAL ./earthly-artifacts/e2e/docs

# All non-secret targets
all:
    BUILD +test-unit
    BUILD +test-schema-generate
