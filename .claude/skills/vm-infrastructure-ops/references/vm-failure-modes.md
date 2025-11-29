# VM Failure Modes and Troubleshooting

**Version**: 1.0.0
**Last Updated**: 2025-11-13
**VM Instance**: eth-realtime-collector (e2-micro, us-east1-b)

## Common Failure Scenarios

### 1. gRPC Metadata Validation Error

**Symptom**:
```
ERROR: grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:
    status = StatusCode.INVALID_ARGUMENT
    details = "Metadata value contains invalid characters"
>
```

**Root Cause**: Secret values from GCP Secret Manager contain trailing newlines when not stripped.

**Solution**:
1. Verify Secret Manager credentials are stripped:
   ```python
   # In deployment/vm/eth_realtime_collector.py
   def get_secret(secret_id: str) -> str:
       response = client.access_secret_version(request={"name": name})
       return response.payload.data.decode('UTF-8').strip()  # .strip() is critical
   ```

2. Restart service:
   ```bash
   gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
     --command='sudo systemctl restart eth-collector'
   ```

**Historical Occurrence**: 2025-11-10 (resolved with `.strip()` fix)

### 2. VM Network Connectivity Failure

**Symptom**:
```
ERROR: DNS resolution failed
ERROR: Could not reach metadata server
ERROR: Connection refused
```

**Root Cause**: VM network interface lost connectivity, metadata server unreachable.

**Solution**:
1. Check VM status:
   ```bash
   gcloud compute instances describe eth-realtime-collector --zone=us-east1-b
   ```

2. Hard reset VM (restores network):
   ```bash
   gcloud compute instances reset eth-realtime-collector --zone=us-east1-b
   ```

3. Verify service restarted after reset:
   ```bash
   gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
     --command='sudo systemctl status eth-collector'
   ```

4. Check logs for block ingestion:
   ```bash
   gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
     --command='sudo journalctl -u eth-collector -f'
   ```

**Historical Occurrence**: 2025-11-10 07:00 UTC (resolved in <15 minutes with VM reset)

### 3. Service Failed to Start

**Symptom**:
```
● eth-collector.service - Ethereum Real-Time Collector
   Loaded: loaded (/etc/systemd/system/eth-collector.service; enabled)
   Active: failed (Result: exit-code)
```

**Root Cause**: Python script crashed on startup (missing dependencies, invalid config, etc.)

**Solution**:
1. Check detailed service status:
   ```bash
   gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
     --command='sudo systemctl status eth-collector'
   ```

2. View recent logs for error messages:
   ```bash
   gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
     --command='sudo journalctl -u eth-collector -n 100'
   ```

3. Common fixes:
   - **Missing dependencies**: SSH to VM, install with `pip install <package>`
   - **Invalid Secret Manager permissions**: Verify service account has `roles/secretmanager.secretAccessor`
   - **Code errors**: Deploy updated code, restart service

### 4. No Blocks for >5 Minutes

**Symptom**: MotherDuck shows no new blocks for >5 minutes (expected: ~12 second intervals).

**Root Cause**: Real-time stream disconnected or service stopped.

**Solution**:
1. Check service status:
   ```bash
   .claude/skills/vm-infrastructure-ops/scripts/check_vm_status.sh
   ```

2. If service active, check logs for errors:
   ```bash
   gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
     --command='sudo journalctl -u eth-collector -f'
   ```

3. If no errors visible, restart service:
   ```bash
   .claude/skills/vm-infrastructure-ops/scripts/restart_collector.sh
   ```

4. Verify data flow:
   ```bash
   uv run scripts/clickhouse/verify_blocks.py
   ```

### 5. WebSocket Disconnection

**Symptom**:
```
WARNING: WebSocket connection lost, reconnecting...
ERROR: Max reconnection attempts reached
```

**Root Cause**: Alchemy WebSocket stream disconnected (network issues, Alchemy API downtime).

**Solution**:
1. Service should auto-reconnect (built-in retry logic)

2. If reconnection fails, check Alchemy API status:
   ```bash
   curl -X POST https://eth-mainnet.g.alchemy.com/v2/<API_KEY> \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
   ```

3. Restart service to force new connection:
   ```bash
   gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
     --command='sudo systemctl restart eth-collector'
   ```

### 6. Insufficient VM Resources

**Symptom**:
```
ERROR: Out of memory
WARNING: High CPU usage (>90%)
```

**Root Cause**: e2-micro VM resources exhausted (0.5 vCPU, 1 GB RAM).

**Solution**:
1. Check VM metrics in GCP Console:
   - Navigate to Compute Engine > VM Instances
   - Click eth-realtime-collector
   - View CPU and memory graphs

2. Restart service to clear memory:
   ```bash
   gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
     --command='sudo systemctl restart eth-collector'
   ```

3. If persistent, consider upgrading VM type:
   ```bash
   # Stop VM first
   gcloud compute instances stop eth-realtime-collector --zone=us-east1-b

   # Change machine type
   gcloud compute instances set-machine-type eth-realtime-collector \
     --zone=us-east1-b \
     --machine-type=e2-small

   # Start VM
   gcloud compute instances start eth-realtime-collector --zone=us-east1-b
   ```

## Diagnostic Workflow

```
1. Check service status
   ↓
   └─ Active? ──No──> Check logs for startup errors ──> Fix and restart
         │
        Yes
         ↓
2. Check logs for errors
   ↓
   └─ Errors? ──Yes──> Identify error type ──> Apply specific solution
         │
         No
         ↓
3. Check data flow to MotherDuck
   ↓
   └─ Recent blocks? ──No──> Restart service ──> Verify data flow
         │
        Yes
         ↓
4. System healthy ✅
```

## Related Documentation

- [SKILL.md](/.claude/skills/vm-infrastructure-ops/SKILL.md) - VM operations workflows
- [Systemd Commands Reference](/.claude/skills/vm-infrastructure-ops/references/systemd-commands.md) - Complete systemd operations
- [MotherDuck Dual Pipeline Architecture](/docs/architecture/_archive/motherduck-dual-pipeline.md) - Architecture overview (DEPRECATED - see MADR-0013)

## Operational History

### 2025-11-10 Network Failure Recovery

**Timeline**:
- 07:00 UTC: VM network failure detected (DNS resolution failed)
- 07:05 UTC: VM hard reset executed
- 07:10 UTC: Network connectivity restored
- 07:12 UTC: eth-collector service restarted with `.strip()` fix
- 07:15 UTC: Data flow verified (blocks streaming every ~12 seconds)

**Root Causes**:
1. VM network interface lost connectivity (metadata server unreachable)
2. gRPC metadata validation error (trailing newline in Secret Manager credentials)

**Fixes Applied**:
1. VM hard reset restored network connectivity
2. Added `.strip()` to Secret Manager credential retrieval
3. Service restarted successfully

**SLO Achievement**: Critical infrastructure failure resolved in <30 minutes (Maintainability SLO met).
