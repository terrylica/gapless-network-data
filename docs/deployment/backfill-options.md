# Historical Backfill Deployment Options

## Problem

Running backfill locally means:

- ❌ Requires MacBook to stay on for ~10-15 minutes
- ❌ Depends on local network stability
- ❌ Cannot close laptop during process

## Solution: Run on Google Cloud

---

### Option 1: Run on Existing e2-micro VM ⭐ RECOMMENDED

**Why**: VM is already running, minimal setup, $0 cost

**Steps**:

1. Copy backfill script to VM
2. Run in background (tmux or nohup)
3. Check logs when complete

**Pros**:

- ✅ $0 cost (VM already running for real-time collector)
- ✅ Fast setup (~2 minutes)
- ✅ Can monitor progress via SSH
- ✅ Runs independently of MacBook

**Cons**:

- ⚠️ Shares 1 GB RAM with real-time collector (but 800 MB free)
- ⚠️ Manual start (not automated like Cloud Run)

**Estimated Usage**:

- Memory spike during backfill: ~300-500 MB
- Duration: 10-15 minutes
- Total RAM: Real-time (95 MB) + Backfill (500 MB) = 595 MB < 1 GB ✅

---

### Option 2: Create Separate Cloud Run Job

**Why**: Automated, isolated, but requires setup

**Steps**:

1. Deploy backfill as Cloud Run Job
2. Trigger once
3. Job runs and exits

**Pros**:

- ✅ Isolated from real-time collector
- ✅ Automatic resource scaling
- ✅ Built-in logging

**Cons**:

- ❌ ~$0.10 cost for single run (negligible)
- ⚠️ More setup time (~10 minutes)

---

## Recommendation: Option 1 (e2-micro VM)

**Rationale**:

- VM already running ($0 marginal cost)
- 800 MB RAM free (plenty for backfill)
- Quick to deploy (2 minutes vs 10 minutes)
- Minimalistic (user's preference)

**Command**:

```bash
# Copy script to VM
gcloud compute scp /tmp/probe/motherduck/historical_backfill.py \
  eth-realtime-collector:~/eth-collector/ \
  --zone=us-east1-b \
  --project=eonlabs-ethereum-bq

# SSH and run in background
gcloud compute ssh eth-realtime-collector \
  --zone=us-east1-b \
  --project=eonlabs-ethereum-bq \
  --command="
    cd ~/eth-collector
    nohup python3 historical_backfill.py > backfill.log 2>&1 &
    echo 'Backfill started in background. Check progress with: tail -f ~/eth-collector/backfill.log'
  "

# Monitor progress (from local Mac)
gcloud compute ssh eth-realtime-collector \
  --zone=us-east1-b \
  --project=eonlabs-ethereum-bq \
  --command="tail -f ~/eth-collector/backfill.log"
```

**After completion**: Close MacBook! ✅ Process continues on VM.
