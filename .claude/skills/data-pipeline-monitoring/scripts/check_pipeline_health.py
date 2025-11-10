#!/usr/bin/env python3
"""
Universal health check for dual-pipeline data collection systems.

Supports:
- GCP Cloud Run Jobs (batch pipelines)
- GCP Compute Engine VMs with systemd services (real-time pipelines)
- Generic process-based checks

Usage:
    python3 check_pipeline_health.py --config health_check_config.yaml
    python3 check_pipeline_health.py --gcp-project PROJECT --vm-name VM --vm-zone ZONE --systemd-service SERVICE --cloud-run-job JOB --region REGION
"""

import argparse
import subprocess
import sys
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional


class HealthCheckResult:
    """Health check result with status and details."""

    def __init__(self, component: str, status: str, message: str, details: Optional[Dict] = None):
        self.component = component
        self.status = status  # OK, WARNING, CRITICAL, UNKNOWN
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return {
            "component": self.component,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }


def run_command(cmd: List[str], check=True) -> subprocess.CompletedProcess:
    """Run shell command and return result."""
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def check_vm_systemd_service(project: str, vm_name: str, zone: str, service_name: str) -> HealthCheckResult:
    """Check systemd service status on GCP VM."""
    try:
        # Check service status
        cmd = [
            "gcloud", "compute", "ssh", vm_name,
            "--zone", zone,
            "--project", project,
            "--command", f"sudo systemctl is-active {service_name}"
        ]

        result = run_command(cmd, check=False)

        if result.returncode == 0 and result.stdout.strip() == "active":
            return HealthCheckResult(
                component=f"VM Service ({vm_name}/{service_name})",
                status="OK",
                message=f"Service {service_name} is active on VM {vm_name}",
                details={"vm": vm_name, "zone": zone, "service": service_name}
            )
        else:
            return HealthCheckResult(
                component=f"VM Service ({vm_name}/{service_name})",
                status="CRITICAL",
                message=f"Service {service_name} is not active: {result.stdout.strip()}",
                details={"vm": vm_name, "zone": zone, "service": service_name, "output": result.stdout}
            )

    except Exception as e:
        return HealthCheckResult(
            component=f"VM Service ({vm_name}/{service_name})",
            status="UNKNOWN",
            message=f"Failed to check service: {str(e)}",
            details={"error": str(e)}
        )


def check_cloud_run_job(project: str, job_name: str, region: str) -> HealthCheckResult:
    """Check Cloud Run Job last execution status."""
    try:
        # Get latest execution
        cmd = [
            "gcloud", "run", "jobs", "executions", "list",
            "--job", job_name,
            "--region", region,
            "--project", project,
            "--limit", "1",
            "--format", "json"
        ]

        result = run_command(cmd)
        executions = json.loads(result.stdout)

        if not executions:
            return HealthCheckResult(
                component=f"Cloud Run Job ({job_name})",
                status="WARNING",
                message=f"No executions found for job {job_name}",
                details={"job": job_name, "region": region}
            )

        latest = executions[0]
        status = latest.get("status", {}).get("conditions", [{}])[0].get("type", "UNKNOWN")

        if status == "Completed":
            return HealthCheckResult(
                component=f"Cloud Run Job ({job_name})",
                status="OK",
                message=f"Latest execution of {job_name} completed successfully",
                details={
                    "job": job_name,
                    "region": region,
                    "execution": latest.get("metadata", {}).get("name", "unknown"),
                    "completion_time": latest.get("status", {}).get("completionTime", "unknown")
                }
            )
        else:
            return HealthCheckResult(
                component=f"Cloud Run Job ({job_name})",
                status="CRITICAL",
                message=f"Latest execution of {job_name} failed: {status}",
                details={
                    "job": job_name,
                    "region": region,
                    "status": status,
                    "execution": latest.get("metadata", {}).get("name", "unknown")
                }
            )

    except Exception as e:
        return HealthCheckResult(
            component=f"Cloud Run Job ({job_name})",
            status="UNKNOWN",
            message=f"Failed to check job: {str(e)}",
            details={"error": str(e)}
        )


def main():
    parser = argparse.ArgumentParser(description="Universal health check for dual-pipeline data collection")
    parser.add_argument("--gcp-project", help="GCP project ID")
    parser.add_argument("--vm-name", help="VM instance name")
    parser.add_argument("--vm-zone", help="VM zone")
    parser.add_argument("--systemd-service", help="systemd service name")
    parser.add_argument("--cloud-run-job", help="Cloud Run Job name")
    parser.add_argument("--region", help="Cloud Run region")
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    results = []

    # Check VM service if configured
    if args.vm_name and args.systemd_service:
        if not args.gcp_project or not args.vm_zone:
            print("Error: --gcp-project and --vm-zone required for VM checks", file=sys.stderr)
            sys.exit(1)

        result = check_vm_systemd_service(
            args.gcp_project,
            args.vm_name,
            args.vm_zone,
            args.systemd_service
        )
        results.append(result)

    # Check Cloud Run Job if configured
    if args.cloud_run_job:
        if not args.gcp_project or not args.region:
            print("Error: --gcp-project and --region required for Cloud Run checks", file=sys.stderr)
            sys.exit(1)

        result = check_cloud_run_job(
            args.gcp_project,
            args.cloud_run_job,
            args.region
        )
        results.append(result)

    # Output results
    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        print("=" * 80)
        print("Data Pipeline Health Check")
        print("=" * 80)
        print()

        for result in results:
            status_symbol = {
                "OK": "✅",
                "WARNING": "⚠️ ",
                "CRITICAL": "❌",
                "UNKNOWN": "❓"
            }.get(result.status, "?")

            print(f"{status_symbol} {result.component}: {result.status}")
            print(f"   {result.message}")
            if result.details:
                for key, value in result.details.items():
                    print(f"   {key}: {value}")
            print()

    # Exit with error code if any critical failures
    if any(r.status == "CRITICAL" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
