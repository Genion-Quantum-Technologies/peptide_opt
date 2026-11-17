#!/bin/bash
set -euo pipefail
printf "%s\n" "Polling service deployment is retired. Deploy the Argo WorkflowTemplate through infra/k3s-manifests; see docs/argo-runtime.md." >&2
exit 2
