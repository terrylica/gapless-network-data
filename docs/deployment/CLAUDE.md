# Deployment Documentation

Local navigation hub for infrastructure deployment guides, configuration, and operational procedures.

## Files

- [Real-Time Collector](./realtime-collector.md) - VM deployment guide, systemd service configuration, Alchemy WebSocket setup
- [Secret Manager Migration](./secret-manager-migration.md) - Migration from Doppler to GCP Secret Manager, IAM permissions, best practices
- [Backfill Options](./backfill-options.md) - Historical backfill deployment options, trade-offs, recommendations

## Deployment Directories

Infrastructure deployment code is organized under `deployment/`:

- `deployment/cloud-run/` - BigQuery → MotherDuck hourly sync (Cloud Run Job)
- `deployment/vm/` - Real-time collector (e2-micro VM with systemd)
- `deployment/backfill/` - Historical backfill script (2015-2025, 23.8M blocks)
- `deployment/oracle/` - Oracle Cloud monitoring (gap detection, Healthchecks.io)

Each directory contains:

- Production Python scripts
- Infrastructure files (Dockerfile, systemd service)
- README.md with deployment instructions

## Related Documentation

- [Root CLAUDE.md](../../CLAUDE.md) - Project overview and operational status
- [Architecture Documentation](../architecture/) - System architecture and design
- [VM Infrastructure Ops Skill](../../.claude/skills/vm-infrastructure-ops/SKILL.md) - VM troubleshooting workflows
- [Historical Backfill Execution Skill](../../.claude/skills/historical-backfill-execution/SKILL.md) - Backfill operational workflows
