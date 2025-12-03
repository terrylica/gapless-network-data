-- AUTO-GENERATED from schema/clickhouse/ethereum_mainnet.yaml
-- DO NOT EDIT - regenerate with: uv run gapless-network-data schema generate-ddl
-- Generated at: 2025-12-02T20:01:56.726941

CREATE TABLE IF NOT EXISTS ethereum_mainnet.blocks (
    timestamp DateTime64(3) NOT NULL COMMENT 'Block timestamp with millisecond precision',
    number Int64 NOT NULL COMMENT 'Block number - used as deduplication key',
    gas_limit Int64 NOT NULL COMMENT 'Maximum gas allowed in block',
    gas_used Int64 NOT NULL COMMENT 'Total gas consumed by transactions',
    base_fee_per_gas Int64 NOT NULL COMMENT 'EIP-1559 base fee per gas unit (wei)',
    transaction_count Int64 NOT NULL COMMENT 'Number of transactions in block',
    difficulty UInt256 NOT NULL COMMENT 'Mining difficulty (0 post-Merge, Sep 2022)',
    total_difficulty UInt256 NOT NULL COMMENT 'Cumulative difficulty (frozen post-Merge)',
    size Int64 NOT NULL COMMENT 'Block size in bytes',
    blob_gas_used Nullable(Int64) COMMENT 'EIP-4844 blob gas used (null pre-Dencun, Mar 2024)',
    excess_blob_gas Nullable(Int64) COMMENT 'EIP-4844 excess blob gas (null pre-Dencun)'
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (number)
SETTINGS index_granularity = 8192;
