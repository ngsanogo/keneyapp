# KeneyApp Documentation

Welcome to the KeneyApp documentation! This directory contains comprehensive guides and references for developers, operators, and users.

## 📚 Documentation Index

### Getting Started & Product Guides

| Document | Description |
|----------|-------------|
| [Quick Start Guide](QUICK_START.md) | Fast-track guide to get KeneyApp running locally |
| [User Guide](USER_GUIDE.md) | End-user walkthrough for roles, navigation, and core workflows |
| [Development Guide](DEVELOPMENT.md) | Complete development environment setup and workflow |
| [API Reference](API_REFERENCE.md) | Full REST API documentation with examples |

### Codebase & Architecture

| Document | Description |
|----------|-------------|
| [Codebase Overview](CODEBASE_OVERVIEW.md) | How the backend, frontend, tests, and infrastructure are organized |
| [Architecture Overview](ARCHITECTURE.md) | System design and deployment topology |
| [Technology Choices](TECHNOLOGY_CHOICES.md) | Rationale behind major platform decisions |
| [DMI Architecture Alignment](DMI_ARCHITECTURE_ALIGNMENT.md) | Alignment of target DMI architecture with current system and migration plan |

### Deployment & Operations

| Document | Description |
|----------|-------------|
| [Deployment Guide](DEPLOYMENT.md) | General deployment instructions |
| [Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md) | Step-by-step production deployment with Docker/K8s |
| [Operations Runbook](OPERATIONS_RUNBOOK.md) | Day-to-day operations, troubleshooting, and maintenance |
| [Monitoring & Alerting](MONITORING_ALERTING.md) | Setting up Prometheus, Grafana, and alert rules |
| [Disaster Recovery](DISASTER_RECOVERY.md) | Backup, restore, and disaster recovery procedures |
| [Incident Response](INCIDENT_RESPONSE.md) | Step-by-step incident handling playbook |
| [Automation Guide](guides/AUTOMATION_GUIDE.md) | CI/CD, pre-commit, and quality automation overview |
| [Local CI Testing](guides/LOCAL_CI_TESTING.md) | How to mirror CI pipelines locally before pushing |

### Security & Compliance

| Document | Description |
|----------|-------------|
| [Security Best Practices](SECURITY_BEST_PRACTICES.md) | Security guidelines and hardening procedures |
| [Security Compliance](SECURITY_COMPLIANCE.md) | GDPR, HIPAA, and HDS compliance documentation |
| [Encryption Guide](ENCRYPTION_GUIDE.md) | Data encryption at rest implementation |
| [OAuth Guide](OAUTH_GUIDE.md) | OAuth2/OIDC authentication setup |

### Healthcare Standards

| Document | Description |
|----------|-------------|
| [FHIR Guide](FHIR_GUIDE.md) | HL7 FHIR R4 interoperability implementation |
| [Medical Terminologies](MEDICAL_TERMINOLOGIES.md) | ICD-11, SNOMED CT, LOINC, ATC, CPT/CCAM coding standards |
| [DMI Architecture Alignment](DMI_ARCHITECTURE_ALIGNMENT.md) | Alignment of target DMI architecture with current system and migration plan |

### Engineering Guides

| Document | Description |
|----------|-------------|
| [Build Guide](guides/BUILD.md) | How to build backend, frontend, and container images |
| [Dependency Updates](guides/DEPENDENCY_UPDATES.md) | Workflow for updating dependencies safely |
| [Git & GitHub Best Practices](guides/GIT_GITHUB_BEST_PRACTICES.md) | Branching, commit messages, and PR workflow |
| [Local CI Testing](guides/LOCAL_CI_TESTING.md) | How to mirror CI pipelines locally before pushing |

### Reports & Audits

| Document | Description |
|----------|-------------|
| [Repository Analysis Report](reports/REPOSITORY_ANALYSIS_REPORT.md) | Assessment of repository hygiene and structure |
| [Code Quality Audit](reports/CODE_QUALITY_AUDIT.md) | Findings from static analysis and code review |
| [Security Audit](reports/SECURITY_AUDIT.md) | Security review outcomes and remediation actions |
| [Docker Optimization Summary](reports/DOCKER_OPTIMIZATION_SUMMARY.md) | Image size reduction highlights |
| [Docker Optimization Results](reports/DOCKER_OPTIMIZATION_RESULTS.md) | Detailed before/after metrics for each service |
| [Comprehensive Audit (Nov 2025)](reports/AUDIT_COMPLET_NOVEMBRE_2025.md) | Full audit deliverable for November 2025 |
| [Corrective Action Plan](reports/PLAN_ACTIONS_CORRECTIVES.md) | Follow-up actions from audits |
| [Synthesis Audit](reports/SYNTHESE_AUDIT.md) | Consolidated audit summary |
| [Test Run Results](reports/TEST_RUN_RESULTS.md) | Recorded outcomes from structured test runs |

### Testing & Quality

| Document | Description |
|----------|-------------|
| [Testing Strategy](TESTING_STRATEGY.md) | Unified plan for unit, integration, and E2E coverage with CI gates |
| [Testing Guide](TESTING_GUIDE.md) | Comprehensive testing strategies and best practices |
| [Performance Testing](PERFORMANCE_TESTING.md) | Load testing, benchmarking, and optimization |
| [Coding Standards & Style Guides](CODING_STANDARDS.md) | Enforced conventions for backend, frontend, and infrastructure code |
| [Code Quality](CODE_QUALITY.md) | Code quality standards and tooling |

### Community & Support

| Document | Description |
|----------|-------------|
| [Community Playbook](COMMUNITY.md) | Collaboration norms, issue triage cadence, and engagement channels |
| [Support](../SUPPORT.md) | Support expectations, response times, and escalation paths |

### Development Resources

| Document | Description |
|----------|-------------|
| [API Best Practices](API_BEST_PRACTICES.md) | REST API design patterns and conventions |
| [Performance Guide](PERFORMANCE_GUIDE.md) | Performance optimization techniques |
| [Integration Plan](INTEGRATION_PLAN.md) | Third-party integration guidelines |
| [Continuous Improvement](CONTINUOUS_IMPROVEMENT.md) | Continuous improvement process and methodology |
| [New Features](NEW_FEATURES.md) | Documentation of v2.0 enterprise features |
| [Patterns: New Resource Scaffold](patterns/new_resource_scaffold.md) | Step-by-step template to add a REST resource (RBAC, tenancy, PHI, caching, audit) |
| [Patterns: GraphQL Extension](patterns/graphql_extension.md) | How to extend schema/resolvers with tenancy and RBAC |
| [Checklist: PHI Logging](patterns/phi_logging_checklist.md) | Do/Don'ts for logging without PHI leaks |
| [Guide: Cache Keys](patterns/cache_keys.md) | Key families, TTLs, and invalidation triggers |

## 🗂️ Documentation Structure

```
docs/
├── README.md                           # This file - documentation index
├── index.md                            # Documentation portal landing page
├── QUICK_START.md                      # Get started quickly
├── USER_GUIDE.md                       # End-user workflows and navigation
├── DEVELOPMENT.md                      # Development setup
├── API_REFERENCE.md                    # API documentation
├── ARCHITECTURE.md                     # System architecture overview
├── TECHNOLOGY_CHOICES.md               # Technology rationale
├── DMI_ARCHITECTURE_ALIGNMENT.md       # DMI architecture alignment
├── CODEBASE_OVERVIEW.md                # Repository layout and development workflow
│
├── Deployment & Operations
│   ├── DEPLOYMENT.md
│   ├── PRODUCTION_DEPLOYMENT_GUIDE.md
│   ├── OPERATIONS_RUNBOOK.md
│   ├── MONITORING_ALERTING.md
│   ├── DISASTER_RECOVERY.md
│   └── INCIDENT_RESPONSE.md
│
├── Engineering Guides
│   ├── guides/README.md
│   ├── guides/AUTOMATION_GUIDE.md
│   ├── guides/BUILD.md
│   ├── guides/GIT_GITHUB_BEST_PRACTICES.md
│   ├── guides/DEPENDENCY_UPDATES.md
│   ├── guides/E2E_SETUP_GUIDE.md
│   └── guides/LOCAL_CI_TESTING.md
│
├── Security & Compliance
│   ├── SECURITY_BEST_PRACTICES.md
│   ├── SECURITY_COMPLIANCE.md
│   ├── ENCRYPTION_GUIDE.md
│   └── OAUTH_GUIDE.md
│
├── Healthcare Standards
│   ├── FHIR_GUIDE.md
│   └── MEDICAL_TERMINOLOGIES.md
│
├── Testing & Quality
│   ├── TESTING_GUIDE.md
│   ├── PERFORMANCE_TESTING.md
│   ├── CODING_STANDARDS.md
│   └── CODE_QUALITY.md
│
├── Community
│   └── COMMUNITY.md
│
├── Reports & Audits
│   ├── reports/README.md
│   ├── reports/AUDIT_COMPLET_NOVEMBRE_2025.md
│   ├── reports/CODE_QUALITY_AUDIT.md
│   ├── reports/DOCKER_OPTIMIZATION_RESULTS.md
│   ├── reports/DOCKER_OPTIMIZATION_SUMMARY.md
│   ├── reports/PLAN_ACTIONS_CORRECTIVES.md
│   ├── reports/REPOSITORY_ANALYSIS_REPORT.md
│   ├── reports/SECURITY_AUDIT.md
│   ├── reports/SYNTHESE_AUDIT.md
│   └── reports/TEST_RUN_RESULTS.md
│
└── Development Resources
    ├── API_BEST_PRACTICES.md
    ├── PERFORMANCE_GUIDE.md
    ├── INTEGRATION_PLAN.md
    ├── CONTINUOUS_IMPROVEMENT.md
    └── NEW_FEATURES.md
```

## 🎯 Quick Links by Role

### For Developers

1. Start with [Quick Start](QUICK_START.md) and the [Codebase Overview](CODEBASE_OVERVIEW.md)
2. Read [Development Guide](DEVELOPMENT.md)
3. Review [API Reference](API_REFERENCE.md)
4. Follow [Coding Standards & Style Guides](CODING_STANDARDS.md)
5. Enforce [Code Quality](CODE_QUALITY.md) standards
6. Align with the [Testing Strategy](TESTING_STRATEGY.md) and dig into the [Testing Guide](TESTING_GUIDE.md)

### For DevOps Engineers

1. Review [Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md)
2. Set up [Monitoring & Alerting](MONITORING_ALERTING.md)
3. Implement [Security Best Practices](SECURITY_BEST_PRACTICES.md)
4. Understand [Operations Runbook](OPERATIONS_RUNBOOK.md)
5. Prepare [Disaster Recovery](DISASTER_RECOVERY.md) plan

### For Clinicians & Admin Users

1. Review the [User Guide](USER_GUIDE.md)
2. Learn feature set in [New Features v3.0](NEW_FEATURES_V3.md)
3. Manage documents and sharing with [FHIR Guide](FHIR_GUIDE.md) and [Medical Terminologies](MEDICAL_TERMINOLOGIES.md)
4. Reference [Security Compliance](SECURITY_COMPLIANCE.md) for patient data handling

### For Healthcare Compliance Officers

1. Review [Security Compliance](SECURITY_COMPLIANCE.md)
2. Understand [Medical Terminologies](MEDICAL_TERMINOLOGIES.md)
3. Check [FHIR Guide](FHIR_GUIDE.md) for interoperability
4. Review [Encryption Guide](ENCRYPTION_GUIDE.md)
5. Audit [Security Best Practices](SECURITY_BEST_PRACTICES.md)

### For QA Engineers

1. Read [Testing Guide](TESTING_GUIDE.md)
2. Perform [Performance Testing](PERFORMANCE_TESTING.md)
3. Follow [Code Quality](CODE_QUALITY.md) checks
4. Use [API Reference](API_REFERENCE.md) for test cases

## 📖 Additional Resources

- **Main Repository**: [README.md](../README.md)
- **Contributing**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Code of Conduct**: [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)
- **Security Policy**: [SECURITY.md](../SECURITY.md)
- **Changelog**: [CHANGELOG.md](../CHANGELOG.md)
- **Architecture**: [ARCHITECTURE.md](../ARCHITECTURE.md)
- **Governance**: [GOVERNANCE.md](../GOVERNANCE.md)
- **Support**: [SUPPORT.md](../SUPPORT.md)
- **AI Commit Checklist**: [.github/ai-commit-checklist.md](../.github/ai-commit-checklist.md)

## 🆕 Recently Updated

Check the git history for recently updated documentation:

```bash
git log --oneline --all -- docs/
```

## 🤝 Contributing to Documentation

Found an issue or want to improve documentation?

1. Check if an issue already exists
2. Follow the [Contributing Guide](../CONTRIBUTING.md)
3. Submit a pull request with clear descriptions
4. Keep documentation up-to-date with code changes

## 📝 Documentation Standards

When contributing to documentation:

- ✅ Use clear, concise language
- ✅ Include code examples where appropriate
- ✅ Add diagrams for complex concepts (Mermaid preferred)
- ✅ Keep table of contents updated
- ✅ Cross-reference related documents
- ✅ Test all commands and code snippets
- ✅ Update this index when adding new documents

---

**Last Updated**: November 2025
Made with ❤️ by ISDATA Consulting
