# VM Real-Time Ethereum Collector Deployment

Deployment scripts for the real-time Ethereum block collector running on GCP e2-micro VM.

## Files

- `realtime_collector.py` - Python script that subscribes to Alchemy WebSocket for real-time blocks
- `eth-collector.service` - Systemd service file (no hardcoded secrets)
- `deploy.sh` - Deployment script with Secret Manager integration

## Prerequisites

1. GCP project configured: `eonlabs-ethereum-bq`
2. VM instance created: `eth-realtime-collector` (e2-micro, us-east1-b)
3. Secrets stored in Secret Manager:
   - `alchemy-api-key`
   - `motherduck-token`
4. VM service account has `roles/secretmanager.secretAccessor`:
   - `893624294905-compute@developer.gserviceaccount.com`

## Deployment

```bash
cd deployment/vm
./deploy.sh
```

The script performs:

1. Verify Secret Manager permissions for VM service account
2. Copy `realtime_collector.py` to VM
3. Install Python dependencies (websockets, duckdb, pyarrow, google-cloud-secret-manager)
4. Move script to `~/eth-collector/`
5. Install systemd service
6. Verify service status and Secret Manager access

## Service Management

View logs:

```bash
gcloud compute ssh eth-realtime-collector --zone=us-east1-b --project=eonlabs-ethereum-bq --command='sudo journalctl -u eth-collector -f'
```

Check status:

```bash
gcloud compute ssh eth-realtime-collector --zone=us-east1-b --project=eonlabs-ethereum-bq --command='sudo systemctl status eth-collector'
```

Restart service:

```bash
gcloud compute ssh eth-realtime-collector --zone=us-east1-b --project=eonlabs-ethereum-bq --command='sudo systemctl restart eth-collector'
```

Stop service:

```bash
gcloud compute ssh eth-realtime-collector --zone=us-east1-b --project=eonlabs-ethereum-bq --command='sudo systemctl stop eth-collector'
```

## Data Flow

```
Alchemy WebSocket (newHeads) → realtime_collector.py → MotherDuck (ethereum_mainnet.blocks)
```

**Collection rate**: ~12 seconds per block (matches Ethereum block time)
**Write mode**: Batch (default) or Real-time

### Batch vs Real-Time Modes

**Batch Mode (Default, Recommended)**:

- Buffers blocks in memory for 5 minutes (~25 blocks)
- Writes all buffered blocks in a single batch INSERT
- **Reduces MotherDuck compute units by 25x** (216K → 8.6K writes/month)
- **Stays within free tier** (8.6K × 2 CU = 17,280 CU/month < 36,000 limit)
- Data lag: Max 5 minutes
- Set via: `Environment="BATCH_INTERVAL_SECONDS=300"` (default in service file)

**Real-Time Mode (Optional)**:

- Writes each block immediately upon receipt (~12 second lag)
- **Exceeds free tier** (216K × 2 CU = 432,000 CU/month >> 36,000 limit)
- Requires MotherDuck paid plan ($25/month minimum)
- Set via: `Environment="BATCH_INTERVAL_SECONDS=0"`

**Switching Modes**:

```bash
# Edit service file to change BATCH_INTERVAL_SECONDS
gcloud compute ssh eth-realtime-collector --zone=us-east1-b --command='sudo nano /etc/systemd/system/eth-collector.service'

# Reload systemd and restart service
gcloud compute ssh eth-realtime-collector --zone=us-east1-b --command='sudo systemctl daemon-reload && sudo systemctl restart eth-collector'
```

## Security

- No secrets in environment variables or systemd service files
- All credentials fetched from Secret Manager at runtime
- Service runs as non-root user
- `.strip()` applied to secrets to prevent gRPC metadata validation errors
