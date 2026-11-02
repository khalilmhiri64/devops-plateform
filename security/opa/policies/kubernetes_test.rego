package main

import rego.v1

good_deployment := {
	"kind": "Deployment",
	"metadata": {"name": "api", "labels": {"app.kubernetes.io/name": "api"}},
	"spec": {
		"replicas": 2,
		"template": {"spec": {
			"securityContext": {"runAsNonRoot": true},
			"containers": [{
				"name": "api",
				"image": "localhost:5000/jobs-api:1.0.0",
				"resources": {"requests": {"cpu": "100m"}, "limits": {"cpu": "500m", "memory": "256Mi"}},
				"securityContext": {
					"allowPrivilegeEscalation": false,
					"readOnlyRootFilesystem": true,
					"capabilities": {"drop": ["ALL"]},
				},
				"readinessProbe": {"httpGet": {"path": "/health/ready"}},
				"livenessProbe": {"httpGet": {"path": "/health/live"}},
			}],
		}},
	},
}

test_good_deployment_passes if {
	count(deny) == 0 with input as good_deployment
	count(warn) == 0 with input as good_deployment
}

test_latest_tag_denied if {
	bad := json.patch(good_deployment, [{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value": "localhost:5000/jobs-api:latest"}])
	some msg in deny with input as bad
	contains(msg, "latest")
}

test_untrusted_registry_denied if {
	bad := json.patch(good_deployment, [{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value": "evil.io/miner:1.0"}])
	some msg in deny with input as bad
	contains(msg, "allowed registry")
}

test_missing_limits_denied if {
	bad := json.patch(good_deployment, [{"op": "remove", "path": "/spec/template/spec/containers/0/resources/limits"}])
	count(deny) == 2 with input as bad
}

test_root_denied if {
	bad := json.patch(good_deployment, [{"op": "remove", "path": "/spec/template/spec/securityContext"}])
	some msg in deny with input as bad
	contains(msg, "runAsNonRoot")
}

test_missing_probe_denied if {
	bad := json.patch(good_deployment, [{"op": "remove", "path": "/spec/template/spec/containers/0/readinessProbe"}])
	some msg in deny with input as bad
	contains(msg, "readinessProbe")
}

test_single_replica_warns if {
	bad := json.patch(good_deployment, [{"op": "replace", "path": "/spec/replicas", "value": 1}])
	count(warn) == 1 with input as bad
}

test_nodeport_denied if {
	some msg in deny with input as {"kind": "Service", "metadata": {"name": "x"}, "spec": {"type": "NodePort"}}
	contains(msg, "NodePort")
}

test_plain_secret_denied if {
	some msg in deny with input as {"kind": "Secret", "metadata": {"name": "db"}}
	contains(msg, "Vault")
}
