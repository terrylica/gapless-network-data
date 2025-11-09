---
version: "1.0.0"
last_updated: "2025-11-08"
source: "MotherDuck Documentation"
---

# BigQuery Integration with MotherDuck

BigQuery is Google Cloud's fully-managed, serverless data warehouse that enables SQL queries using the processing power of Google's infrastructure.

To load data into MotherDuck, there are two options:

1. **[Using the `duckdb-bigquery` community extension](#1-using-the-duckdb-bigquery-community-extension)** (easiest to use) - Simple SQL-based approach for quick data transfers and exploration.
2. **[Using Google's BigQuery Python SDK](#2-using-googles-bigquery-python-sdk)** - For performance-optimized ETL pipelines with advanced control over data loading.

## Prerequisites

- DuckDB installed (via CLI or Python).
- Access to a GCP project with BigQuery enabled.
- Valid Google Cloud credentials via:
  - `GOOGLE_APPLICATION_CREDENTIALS` environment variable, or
  - `gcloud auth application-default login`.

Minimum required IAM roles:
- `BigQuery Data Editor`
- `BigQuery Job User`

## 1. Using the DuckDB BigQuery Community Extension

The following examples use the DuckDB CLI, but you can use any DuckDB/MotherDuck clients.

### Install and Load the Extension

```sql
INSTALL bigquery FROM community;
LOAD bigquery;
```

**Note**: A new experimental scan is now available and offers significantly improved performance. To enable it by default, run:

```sql
SET bq_experimental_use_incubating_scan=TRUE
```

### Attach BigQuery Project

To read data from your project, you attach it just like you would attach a DuckDB database with the following syntax:

```sql
ATTACH 'project=my-gcp-project' AS bq (TYPE bigquery, READ_ONLY);
```

To read from a public dataset, you can use the following syntax:

```sql
ATTACH 'project=bigquery-public-data dataset=pypi billing_project=my-gcp-project'
AS bq_public (TYPE bigquery, READ_ONLY);
```

### Query a Table

Once attached, you can query BigQuery tables directly using standard SQL syntax:

```sql
SELECT * FROM bq.dataset_name.table_name LIMIT 10;
```

#### Alternative Query Functions

Behind the scenes, the above query uses `bigquery_scan`. The extension provides two explicit functions for more control over data retrieval:

**`bigquery_scan`** - Efficient for reading entire tables or simple queries:

```sql
SELECT * FROM bigquery_scan('my_gcp_project.my_dataset.my_table');
```

**`bigquery_query`** - Execute custom GoogleSQL queries within your BigQuery project. Recommended for querying large tables with complex filters.

```sql
SELECT * FROM bigquery_query(
  'my_gcp_project',
  'SELECT * FROM `my_gcp_project.my_dataset.my_table` WHERE column = "value"'
);
```

### Loading Data to MotherDuck

Ensure the `motherduck_token` environment variable is set:

```sql
ATTACH 'md:';
```

You can use the `CREATE TABLE ... AS` syntax to create a new table, or `INSERT INTO ... SELECT` to append data to an existing table.

```sql
CREATE DATABASE IF NOT EXISTS pypi_playground;
USE pypi_playground;

CREATE TABLE IF NOT EXISTS duckdb_sample AS
SELECT *
FROM bq_public.pypi.file_downloads
WHERE project = 'duckdb'
AND timestamp = TIMESTAMP '2025-05-26 00:00:00'
LIMIT 100;
```

---

## 2. Using Google's BigQuery Python SDK

For optimized ETL pipeline performance—especially when working with large tables and filter pushdown—we recommend using the Google Cloud BigQuery Python SDK, which streams results efficiently directly to an Arrow table, enabling zero-copy loading to DuckDB.

### Install Required Libraries

```bash
pip install google-cloud-bigquery[bqstorage] duckdb
```

The "extras" option `[bqstorage]` installs `google-cloud-bigquery-storage`. By default, the `google-cloud-bigquery` client uses the **standard BigQuery API** to read query results. This is fine for small results, but **much slower and less efficient** for large datasets.

### Python End-to-End Pipeline Example

The above example has 3 functions:

- `get_bigquery_client()` - Authenticates and returns a BigQuery client using service account credentials or default authentication.
- `get_bigquery_result()` - Executes a BigQuery SQL query and returns the results as a PyArrow table.
- `create_duckdb_table_from_arrow()` - Creates a DuckDB table from PyArrow data in either local DuckDB or MotherDuck.

```python
import os
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth.exceptions import DefaultCredentialsError
import logging
import time
import pyarrow as pa
import duckdb

GCP_PROJECT = 'my-gcp-project'
DATASET_NAME = 'my_dataset'
TABLE_NAME = 'my_table'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_bigquery_client(project_name: str) -> bigquery.Client:
    """Get Big Query client"""
    try:
        service_account_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

        if service_account_path:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path
            )
            bigquery_client = bigquery.Client(
                project=project_name, credentials=credentials
            )
            return bigquery_client

        raise EnvironmentError(
            "No valid credentials found for BigQuery authentication."
        )

    except DefaultCredentialsError as creds_error:
        raise creds_error


def get_bigquery_result(
    query_str: str, bigquery_client: bigquery.Client
) -> pa.Table:
    """Get query result from BigQuery and yield rows as dictionaries."""
    try:
        # Start measuring time
        start_time = time.time()
        # Run the query and directly load into a DataFrame
        logging.info(f"Running query: {query_str}")
        pa_tbl = bigquery_client.query(query_str).to_arrow()
        # Log the time taken for query execution and data loading
        elapsed_time = time.time() - start_time
        logging.info(
            f"BigQuery query executed and data loaded in {elapsed_time:.2f} seconds")
        # Iterate over DataFrame rows and yield as dictionaries
        return pa_tbl

    except Exception as e:
        logging.error(f"Error running query: {e}")
        raise


def create_duckdb_table_from_arrow(
    pa_table: pa.Table,
    table_name: str,
    db_path: str,
    database_name: str = "bigquery",
) -> None:
    """
    Create a DuckDB table from PyArrow table data.

    Args:
        pa_table: PyArrow table containing the data
        table_name: Name of the table to create in DuckDB
        database_name: Name of the database to create/use (default: bigquery_playground)
        db_path: Database path - use 'md:' prefix for MotherDuck, file path for local or just :memory: for in-memory
    """
    try:
        # Connect to DuckDB
        if db_path.startswith("md:"):
            # check env var motherduck_token
            if not os.environ.get("motherduck_token"):
                raise EnvironmentError(
                    "motherduck_token environment variable is not set")
        conn = duckdb.connect(db_path)
        # Create database if not exists
        conn.sql(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        conn.sql(f"USE {database_name}")
        # Create table from PyArrow table
        conn.sql(
            f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM pa_table")
        logging.info(
            f"Successfully created table '{table_name}' in database '{database_name}' with {len(pa_table)} rows to {db_path}")

    except Exception as e:
        logging.error(f"Error creating DuckDB table: {e}")
        raise


if __name__ == "__main__":
    # Run the pipeline
    bigquery_client = get_bigquery_client(GCP_PROJECT)
    pa_table = get_bigquery_result(f"""SELECT * FROM `{GCP_PROJECT}.{DATASET_NAME}.{TABLE_NAME}}`""", bigquery_client)
    create_duckdb_table_from_arrow(
        pa_table=pa_table, table_name=TABLE_NAME, db_path="md:")
```

## Use Case: Ethereum Block Data Pipeline

For the gapless-network-data project, this integration enables:

1. **Query BigQuery**: Access 13M Ethereum blocks from `bigquery-public-data.crypto_ethereum.blocks`
2. **Stream to MotherDuck**: Load directly to cloud DuckDB without local storage
3. **Zero-Copy Transfer**: PyArrow → DuckDB with no intermediate serialization
4. **Cloud Analytics**: Query from anywhere without local database files

**Example workflow**:

```python
# 1. Query BigQuery for Ethereum blocks
query = """
SELECT timestamp, number, gas_limit, gas_used, base_fee_per_gas,
       transaction_count, difficulty, total_difficulty, size,
       blob_gas_used, excess_blob_gas
FROM `bigquery-public-data.crypto_ethereum.blocks`
WHERE number BETWEEN 11560000 AND 24000000
"""

# 2. Stream to MotherDuck
bigquery_client = get_bigquery_client('my-gcp-project')
pa_table = get_bigquery_result(query, bigquery_client)
create_duckdb_table_from_arrow(
    pa_table=pa_table,
    table_name='ethereum_blocks',
    db_path='md:',
    database_name='gapless_network_data'
)
```

**Benefits**:
- No local storage needed (760 MB → 0 MB local)
- Query from multiple machines
- Share data with team via MotherDuck access
- MotherDuck handles backup/availability
