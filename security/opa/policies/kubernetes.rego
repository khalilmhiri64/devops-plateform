# Conftest policies applied to rendered Kustomize output in CI (shift-left).
# The same rules are enforced at admission time by Gatekeeper (security/gatekeeper).
package main

import rego.v1

workload_kinds := {"Deployment", "StatefulSet", "DaemonSet", "Rollout", "Job"}

allowed_registries := ["localhost:5000/", "postgres:", "redis:", "curlimages/curl:"]

is_workload if input.kind in workload_kinds

containers contains c if {
	is_workload
	some c in input.spec.template.spec.containers
}

containers contains c if {
	is_workload
	some c in input.spec.template.spec.initContainers
}

pod_spec := input.spec.template.spec if is_workload

name := input.metadata.name

deny contains msg if {
	is_workload
	not input.metadata.labels["app.kubernetes.io/name"]
	msg := sprintf("%s/%s: missing label app.kubernetes.io/name", [input.kind, name])
}

deny contains msg if {
	some c in containers
	endswith(c.image, ":latest")
	msg := sprintf("%s/%s: container %s uses the ':latest' tag", [input.kind, name, c.name])
}

deny contains msg if {
	some c in containers
	not contains(c.image, ":")
	msg := sprintf("%s/%s: container %s image has no tag", [input.kind, name, c.name])
}

deny contains msg if {
	some c in containers
	not any_prefix(c.image, allowed_registries)
	msg := sprintf("%s/%s: image %s is not from an allowed registry", [input.kind, name, c.image])
}

deny contains msg if {
	some c in containers
	not c.resources.limits.memory
	msg := sprintf("%s/%s: container %s has no memory limit", [input.kind, name, c.name])
}

deny contains msg if {
	some c in containers
	not c.resources.limits.cpu
	msg := sprintf("%s/%s: container %s has no CPU limit", [input.kind, name, c.name])
}

deny contains msg if {
	some c in containers
	not c.resources.requests
	msg := sprintf("%s/%s: container %s has no resource requests", [input.kind, name, c.name])
}

deny contains msg if {
	is_workload
	not pod_spec.securityContext.runAsNonRoot
	msg := sprintf("%s/%s: pod must set securityContext.runAsNonRoot=true", [input.kind, name])
}

deny contains msg if {
	some c in containers
	c.securityContext.privileged
	msg := sprintf("%s/%s: container %s must not be privileged", [input.kind, name, c.name])
}

deny contains msg if {
	some c in containers
	not c.securityContext.allowPrivilegeEscalation == false
	msg := sprintf("%s/%s: container %s must set allowPrivilegeEscalation=false", [input.kind, name, c.name])
}

deny contains msg if {
	some c in containers
	not c.securityContext.readOnlyRootFilesystem
	msg := sprintf("%s/%s: container %s must use a read-only root filesystem", [input.kind, name, c.name])
}

deny contains msg if {
	some c in containers
	not "ALL" in object.get(c, ["securityContext", "capabilities", "drop"], [])
	msg := sprintf("%s/%s: container %s must drop ALL capabilities", [input.kind, name, c.name])
}

# Long-running workloads need probes; Jobs do not.
deny contains msg if {
	input.kind in {"Deployment", "StatefulSet", "Rollout"}
	some c in containers
	not c.readinessProbe
	msg := sprintf("%s/%s: container %s has no readinessProbe", [input.kind, name, c.name])
}

deny contains msg if {
	input.kind in {"Deployment", "StatefulSet", "Rollout"}
	some c in containers
	not c.livenessProbe
	msg := sprintf("%s/%s: container %s has no livenessProbe", [input.kind, name, c.name])
}

deny contains msg if {
	is_workload
	pod_spec.hostNetwork
	msg := sprintf("%s/%s: hostNetwork is not allowed", [input.kind, name])
}

deny contains msg if {
	input.kind == "Service"
	input.spec.type in {"NodePort", "LoadBalancer"}
	msg := sprintf("Service/%s: type %s is not allowed, use the Ingress", [name, input.spec.type])
}

# Secrets must come from Vault, never from Git.
deny contains msg if {
	input.kind == "Secret"
	msg := sprintf("Secret/%s: plain Secrets must not be committed; use a VaultStaticSecret", [name])
}

warn contains msg if {
	input.kind in {"Deployment", "Rollout"}
	input.spec.replicas < 2
	msg := sprintf("%s/%s: fewer than 2 replicas means no high availability", [input.kind, name])
}

any_prefix(s, prefixes) if {
	some p in prefixes
	startswith(s, p)
}
