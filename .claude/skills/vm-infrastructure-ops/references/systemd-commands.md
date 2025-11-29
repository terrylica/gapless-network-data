# Systemd Commands Reference

**Version**: 1.0.0
**Last Updated**: 2025-11-13
**Service**: eth-collector.service

## Quick Reference

### Service Control

```bash
# Check service status
sudo systemctl status eth-collector

# Start service
sudo systemctl start eth-collector

# Stop service
sudo systemctl stop eth-collector

# Restart service
sudo systemctl restart eth-collector

# Reload configuration (without stopping service)
sudo systemctl reload eth-collector
```

### Service State Management

```bash
# Enable service (start on boot)
sudo systemctl enable eth-collector

# Disable service (don't start on boot)
sudo systemctl disable eth-collector

# Check if service is enabled
sudo systemctl is-enabled eth-collector

# Check if service is active
sudo systemctl is-active eth-collector

# Check if service failed
sudo systemctl is-failed eth-collector
```

### Log Viewing

```bash
# View all logs for service
sudo journalctl -u eth-collector

# View last 100 lines
sudo journalctl -u eth-collector -n 100

# Follow logs (live tail)
sudo journalctl -u eth-collector -f

# View logs since last boot
sudo journalctl -u eth-collector -b

# View logs for specific time range
sudo journalctl -u eth-collector --since "2025-11-13 10:00:00" --until "2025-11-13 11:00:00"

# View logs from last hour
sudo journalctl -u eth-collector --since "1 hour ago"

# View logs with priority level (0=emerg, 3=err, 6=info, 7=debug)
sudo journalctl -u eth-collector -p err  # Only errors

# Export logs to file
sudo journalctl -u eth-collector > eth-collector.log
```

### Service File Management

```bash
# View service file
sudo systemctl cat eth-collector

# Edit service file
sudo systemctl edit eth-collector  # Creates override file
sudo systemctl edit --full eth-collector  # Edits main file

# Reload systemd configuration (after editing service files)
sudo systemctl daemon-reload

# Show service dependencies
sudo systemctl list-dependencies eth-collector
```

### Troubleshooting

```bash
# Show failed services
sudo systemctl --failed

# Reset failed status
sudo systemctl reset-failed eth-collector

# Kill all processes for service
sudo systemctl kill eth-collector

# Show resource usage
sudo systemctl status eth-collector  # Shows memory/CPU in status output
```

## Service File Location

```bash
# Main service file
/etc/systemd/system/eth-collector.service

# Override files (if using systemctl edit)
/etc/systemd/system/eth-collector.service.d/override.conf
```

## Service File Structure

```ini
[Unit]
Description=Ethereum Real-Time Collector
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=opc
WorkingDirectory=/home/opc/eth-realtime-collector
ExecStart=/usr/bin/python3 /home/opc/eth-realtime-collector/eth_realtime_collector.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment variables (if needed)
# Environment="MOTHERDUCK_TOKEN=<token>"
# Environment="ALCHEMY_API_KEY=<key>"

[Install]
WantedBy=multi-user.target
```

## Common Systemd Patterns

### Restart Service After Crash

```bash
# Automatically restart on failure (already configured)
[Service]
Restart=always
RestartSec=10
```

### Start Service After Network Available

```bash
# Wait for network before starting (already configured)
[Unit]
After=network-online.target
Wants=network-online.target
```

### Limit Restart Attempts

```bash
# Add to service file to prevent restart loops
[Service]
StartLimitIntervalSec=300  # 5 minutes
StartLimitBurst=5          # Max 5 restarts in interval
```

### Graceful Shutdown

```bash
# Send SIGTERM, wait 30s, then SIGKILL
[Service]
TimeoutStopSec=30
KillMode=mixed  # Send signal to main process and all children
```

## Exit Status Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Generic error |
| 2 | Invalid arguments |
| 3 | Unimplemented feature |
| 4 | Insufficient permissions |
| 5 | Not installed |
| 6 | Not configured |
| 7 | Not running |

## Remote Execution via gcloud

All systemd commands can be executed remotely via gcloud SSH:

```bash
# Pattern
gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
  --command='sudo systemctl <command> eth-collector'

# Examples
gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
  --command='sudo systemctl status eth-collector'

gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
  --command='sudo systemctl restart eth-collector'

gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
  --command='sudo journalctl -u eth-collector -f'
```

## Best Practices

1. **Always use `sudo`** - systemctl requires root permissions for service management
2. **Use `daemon-reload` after editing** - Reload systemd configuration after any service file changes
3. **Check status before restart** - Verify current state to understand what's happening
4. **Monitor logs after restart** - Always check logs to confirm successful restart
5. **Use `journalctl -f` for debugging** - Live tail helps identify issues in real-time
6. **Avoid `kill -9`** - Use `systemctl stop` for graceful shutdown; `systemctl kill` as last resort

## Useful Aliases

Add to `~/.bashrc` for convenience:

```bash
# Service management
alias ethstatus='sudo systemctl status eth-collector'
alias ethstart='sudo systemctl start eth-collector'
alias ethstop='sudo systemctl stop eth-collector'
alias ethrestart='sudo systemctl restart eth-collector'

# Log viewing
alias ethlogs='sudo journalctl -u eth-collector'
alias ethfollow='sudo journalctl -u eth-collector -f'
alias ethtail='sudo journalctl -u eth-collector -n 100'
```

## Related Documentation

- [SKILL.md](/.claude/skills/vm-infrastructure-ops/SKILL.md) - VM operations workflows
- [VM Failure Modes](/.claude/skills/vm-infrastructure-ops/references/vm-failure-modes.md) - Troubleshooting guide
- [systemd documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html) - Official systemd reference
