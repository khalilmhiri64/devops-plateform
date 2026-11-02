FROM jenkins/jenkins:2.479.2-lts-jdk17
USER root
# Tooling the pipeline shells out to: docker CLI, kubectl, kustomize, trivy, conftest.
ARG KUBECTL_VERSION=v1.31.4 KUSTOMIZE_VERSION=5.5.0 TRIVY_VERSION=0.58.1 CONFTEST_VERSION=0.56.0
RUN apt-get update && apt-get install -y --no-install-recommends docker.io curl jq python3 python3-venv make \
 && rm -rf /var/lib/apt/lists/* \
 && curl -fsSLo /usr/local/bin/kubectl https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl \
 && chmod +x /usr/local/bin/kubectl \
 && curl -fsSL https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv${KUSTOMIZE_VERSION}/kustomize_v${KUSTOMIZE_VERSION}_linux_amd64.tar.gz | tar xz -C /usr/local/bin \
 && curl -fsSL https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz | tar xz -C /usr/local/bin trivy \
 && curl -fsSL https://github.com/open-policy-agent/conftest/releases/download/v${CONFTEST_VERSION}/conftest_${CONFTEST_VERSION}_Linux_x86_64.tar.gz | tar xz -C /usr/local/bin conftest \
 && curl -fsSL https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64 -o /usr/local/bin/kubectl-argo-rollouts \
 && chmod +x /usr/local/bin/kubectl-argo-rollouts
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY casc.yaml /var/jenkins_home/casc.yaml
