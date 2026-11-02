// CI/CD pipeline for the Jobs Platform.
//
//  feature/*  : lint -> unit -> build -> scan -> integration/E2E/perf (ephemeral compose stack)
//  main       : ... + push -> GitOps bump staging -> smoke tests on staging
//  tag v*     : ... + manual approval -> GitOps bump production (Argo Rollouts canary / blue-green)
pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
    timeout(time: 60, unit: 'MINUTES')
    buildDiscarder(logRotator(numToKeepStr: '20'))
    disableConcurrentBuilds(abortPrevious: true)
  }

  parameters {
    booleanParam(name: 'RUN_LOAD_TEST', defaultValue: false, description: 'Run the 5-minute k6 load test')
    choice(name: 'E2E_BROWSERS', choices: ['chrome', 'chrome,firefox'], description: 'Selenium Grid browsers')
  }

  environment {
    REGISTRY      = 'localhost:5000'                         // local registry started by scripts/bootstrap.sh
    VERSION       = "${env.TAG_NAME ?: "0.1.${env.BUILD_NUMBER}-${env.GIT_COMMIT?.take(7) ?: 'local'}"}"
    COMPOSE       = "docker compose -p ci-${env.BUILD_NUMBER} -f docker-compose.yml -f docker-compose.test.yml"
    TRIVY_CONFIG  = 'tests/security/trivy.yaml'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'mkdir -p reports && git log -1 --oneline'
      }
    }

    stage('Static analysis') {
      parallel {
        stage('Lint Python') {
          steps { sh 'docker run --rm -v "$PWD/services:/src" -w /src ghcr.io/astral-sh/ruff:0.8.4 check .' }
        }
        stage('Lint Dockerfiles') {
          steps { sh 'for f in services/*/Dockerfile; do docker run --rm -i hadolint/hadolint:v2.12.0 < "$f"; done' }
        }
        stage('Policy check (OPA)') {
          steps {
            sh '''
              for env in staging production; do
                kustomize build k8s/overlays/$env > reports/$env.yaml
                conftest test reports/$env.yaml -p security/opa/policies --all-namespaces
              done
              conftest verify -p security/opa/policies
            '''
          }
        }
        stage('Terraform validate') {
          steps {
            sh 'docker run --rm -v "$PWD/terraform:/tf" -w /tf hashicorp/terraform:1.10 fmt -check -recursive'
            sh 'docker run --rm -v "$PWD/terraform:/tf" -w /tf hashicorp/terraform:1.10 init -backend=false -input=false'
            sh 'docker run --rm -v "$PWD/terraform:/tf" -w /tf hashicorp/terraform:1.10 validate'
          }
        }
        stage('Secret scan') {
          steps { sh 'trivy fs --config $TRIVY_CONFIG --scanners secret --exit-code 1 .' }
        }
      }
    }

    stage('Unit tests') {
      parallel {
        stage('API') {
          steps {
            sh '''
              docker build -q --target test -t jobs/api-test:$VERSION services/api
              docker run --rm -v "$PWD/reports/api:/reports" jobs/api-test:$VERSION
            '''
          }
        }
        stage('Worker') {
          steps {
            sh '''
              docker build -q --target test -t jobs/worker-test:$VERSION services/worker
              docker run --rm -v "$PWD/reports/worker:/reports" jobs/worker-test:$VERSION
            '''
          }
        }
      }
      post {
        always {
          junit 'reports/*/junit.xml'
          recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/*/coverage.xml']],
                         qualityGates: [[threshold: 80.0, metric: 'LINE', baseline: 'PROJECT', criticality: 'FAILURE']])
        }
      }
    }

    stage('Build images') {
      steps {
        script {
          ['api', 'worker', 'frontend'].each { svc ->
            def target = svc == 'frontend' ? '' : '--target runtime'
            sh "docker build ${target} --build-arg VERSION=\$VERSION -t \$REGISTRY/jobs-${svc}:\$VERSION -t jobs/${svc}:\$VERSION services/${svc}"
          }
        }
      }
    }

    stage('Image scan (Trivy)') {
      steps {
        script {
          ['api', 'worker', 'frontend'].each { svc ->
            sh "trivy image --config $TRIVY_CONFIG --ignorefile tests/security/.trivyignore --format template --template '@/usr/local/share/trivy/templates/junit.tpl' -o reports/trivy-${svc}.xml $REGISTRY/jobs-${svc}:$VERSION || true"
            // second run is the actual gate (table output in the log)
            sh "trivy image --config $TRIVY_CONFIG --ignorefile tests/security/.trivyignore $REGISTRY/jobs-${svc}:$VERSION"
          }
        }
      }
      post { always { junit allowEmptyResults: true, testResults: 'reports/trivy-*.xml' } }
    }

    stage('Ephemeral environment tests') {
      stages {
        stage('Start stack') {
          steps { sh '$COMPOSE --profile test up -d --wait postgres redis api worker frontend selenium-hub chrome firefox' }
        }
        stage('Test') {
          parallel {
            stage('Integration') {
              steps { sh '$COMPOSE --profile test run --rm integration' }
            }
            stage('E2E (Selenium Grid)') {
              steps { sh 'BROWSER=$E2E_BROWSERS $COMPOSE --profile test run --rm e2e' }
            }
            stage('Performance smoke (k6)') {
              steps { sh '$COMPOSE --profile test run --rm k6' }
            }
            stage('DAST (OWASP ZAP)') {
              steps {
                sh '''
                  docker run --rm --network ci-${BUILD_NUMBER}_app -v "$PWD/tests/security:/zap/wrk:rw" \
                    ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t http://frontend:8080 \
                    -c zap-rules.tsv -r zap-report.html -I
                  mv tests/security/zap-report.html reports/ || true
                '''
              }
            }
          }
        }
        stage('Load test') {
          when { expression { params.RUN_LOAD_TEST } }
          steps { sh '$COMPOSE --profile test run --rm k6 run --summary-export=/reports/load.json /scripts/load.js' }
        }
      }
      post {
        always {
          sh '$COMPOSE logs --no-color > reports/compose.log 2>&1 || true'
          sh '$COMPOSE --profile test down -v --remove-orphans || true'
          junit allowEmptyResults: true, testResults: 'reports/integration/junit.xml, reports/e2e/junit.xml'
          publishHTML(target: [reportName: 'E2E report', reportDir: 'reports/e2e', reportFiles: 'report.html', allowMissing: true, keepAll: true])
          publishHTML(target: [reportName: 'ZAP report', reportDir: 'reports', reportFiles: 'zap-report.html', allowMissing: true, keepAll: true])
        }
      }
    }

    stage('Push images') {
      when { anyOf { branch 'main'; buildingTag() } }
      steps {
        script {
          ['api', 'worker', 'frontend'].each { svc -> sh "docker push $REGISTRY/jobs-${svc}:$VERSION" }
        }
      }
    }

    stage('Deploy to staging (GitOps)') {
      when { branch 'main' }
      steps {
        sh 'scripts/gitops-bump.sh staging $VERSION'
        // ArgoCD auto-syncs staging; wait for it to converge before testing.
        sh 'kubectl -n jobs-staging rollout status deploy/api --timeout=300s'
        sh 'kubectl -n jobs-staging rollout status deploy/frontend --timeout=300s'
      }
    }

    stage('Staging smoke tests') {
      when { branch 'main' }
      steps {
        sh 'scripts/smoke-test.sh http://staging.jobs.localtest.me'
        sh 'docker run --rm --network host -e BASE_URL=http://staging.jobs.localtest.me -v "$PWD/tests/performance:/scripts:ro" grafana/k6:0.55.0 run /scripts/smoke.js'
      }
    }

    stage('Approve production') {
      when { buildingTag() }
      steps {
        timeout(time: 1, unit: 'HOURS') {
          input message: "Promote ${VERSION} to production?", ok: 'Deploy', submitter: 'admin,release-managers'
        }
      }
    }

    stage('Deploy to production (GitOps)') {
      when { buildingTag() }
      steps {
        sh 'scripts/gitops-bump.sh production $VERSION'
        // API: canary with automated Prometheus analysis. Frontend: blue-green, promoted after preview smoke test.
        sh 'kubectl argo rollouts status api -n jobs-production --timeout 900s'
        sh 'scripts/smoke-test.sh http://preview.jobs.localtest.me'
        sh 'kubectl argo rollouts promote frontend -n jobs-production'
        sh 'kubectl argo rollouts status frontend -n jobs-production --timeout 300s'
      }
      post {
        failure {
          sh 'kubectl argo rollouts abort api -n jobs-production || true'
          sh 'kubectl argo rollouts abort frontend -n jobs-production || true'
        }
      }
    }
  }

  post {
    always { archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true }
    cleanup { cleanWs() }
  }
}
