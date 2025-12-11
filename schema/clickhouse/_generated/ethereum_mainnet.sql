-- AUTO-GENERATED from schema/clickhouse/ethereum_mainnet.yaml
-- DO NOT EDIT - regenerate with: uv run gapless-network-data schema generate-ddl
-- Generated at: 2025-12-10T15:08:12.499959

CREATE TABLE IF NOT EXISTS ethereum_mainnet.blocks (
    timestamp DateTime64(3) NOT NULL CODEC(DoubleDelta, ZSTD) COMMENT 'Block timestamp with millisecond precision',
    number Int64 NOT NULL CODEC(DoubleDelta, ZSTD) COMMENT 'Block number - used as deduplication key',
    gas_limit Int64 NOT NULL CODEC(Delta, ZSTD) COMMENT 'Maximum gas allowed in block',
    gas_used Int64 NOT NULL CODEC(T64, ZSTD) COMMENT 'Total gas consumed by transactions',
    base_fee_per_gas Int64 NOT NULL CODEC(T64, ZSTD) COMMENT 'EIP-1559 base fee per gas unit (wei)',
    transaction_count Int64 NOT NULL CODEC(T64, ZSTD) COMMENT 'Number of transactions in block',
    difficulty UInt256 NOT NULL CODEC(ZSTD(3)) COMMENT 'Mining difficulty (0 post-Merge, Sep 2022)',
    total_difficulty UInt256 NOT NULL CODEC(ZSTD(3)) COMMENT 'Cumulative difficulty (frozen post-Merge)',
    size Int64 NOT NULL CODEC(T64, ZSTD) COMMENT 'Block size in bytes',
    blob_gas_used Nullable(Int64) CODEC(T64, ZSTD) COMMENT 'EIP-4844 blob gas used (null pre-Dencun, Mar 2024)',
    excess_blob_gas Nullable(Int64) CODEC(T64, ZSTD) COMMENT 'EIP-4844 excess blob gas (null pre-Dencun)'
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (number)
SETTINGS index_granularity = 8192;

-- Projection: blocks_by_timestamp
ALTER TABLE ethereum_mainnet.blocks ADD PROJECTION blocks_by_timestamp (
    SELECT * ORDER BY (timestamp, number)
);
ALTER TABLE ethereum_mainnet.blocks MATERIALIZE PROJECTION blocks_by_timestamp;
