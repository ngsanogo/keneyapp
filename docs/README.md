# KeneyApp Documentation

Welcome to the KeneyApp documentation! This directory contains comprehensive guides and references for developers, operators, and users.

## 📚 Documentation Index

### Getting Started

| Document | Description |
|----------|-------------|
| [Quick Start Guide](QUICK_START.md) | Fast-track guide to get KeneyApp running locally |
| [Development Guide](DEVELOPMENT.md) | Complete development environment setup and workflow |
| [API Reference](API_REFERENCE.md) | Full REST API documentation with examples |

### Deployment & Operations

| Document | Description |
|----------|-------------|
| [Deployment Guide](DEPLOYMENT.md) | General deployment instructions |
| [Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md) | Step-by-step production deployment with Docker/K8s |
| [Operations Runbook](OPERATIONS_RUNBOOK.md) | Day-to-day operations, troubleshooting, and maintenance |
| [Monitoring & Alerting](MONITORING_ALERTING.md) | Setting up Prometheus, Grafana, and alert rules |
| [Disaster Recovery](DISASTER_RECOVERY.md) | Backup, restore, and disaster recovery procedures |
| [Incident Response](INCIDENT_RESPONSE.md) | Step-by-step incident handling playbook |

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

### Testing & Quality

| Document | Description |
|----------|-------------|
| [E2E Testing Guide](E2E_TESTING.md) | ⭐ Comprehensive end-to-end integration testing in Docker |
| [E2E Test Scenarios](E2E_TEST_SCENARIOS.md) | ⭐ **Detailed test scenarios with complete user journeys** |
| [E2E Test Methodology](E2E_TEST_METHODOLOGY.md) | ⭐ **Complete testing methodology (11 phases)** |
| [E2E Testing Quick Reference](E2E_TESTING_QUICK_REF.md) | Quick commands and troubleshooting for E2E tests |
| [E2E Testing Architecture](E2E_TESTING_ARCHITECTURE.md) | Architecture diagrams and data flow |
| [E2E Testing Checklist](E2E_TESTING_CHECKLIST.md) | Execution and interpretation checklist |
| [Testing Guide](TESTING_GUIDE.md) | Comprehensive testing strategies and best practices |
| [Performance Testing](PERFORMANCE_TESTING.md) | Load testing, benchmarking, and optimization |
| [Code Quality](CODE_QUALITY.md) | Code quality standards and tooling |

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
├── QUICK_START.md                      # Get started quickly
├── DEVELOPMENT.md                      # Development setup
├── API_REFERENCE.md                    # API documentation
│
├── Deployment & Operations
│   ├── DEPLOYMENT.md
│   ├── PRODUCTION_DEPLOYMENT_GUIDE.md
│   ├── OPERATIONS_RUNBOOK.md
│   ├── MONITORING_ALERTING.md
│   ├── DISASTER_RECOVERY.md
│   └── INCIDENT_RESPONSE.md
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
│   └── CODE_QUALITY.md
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

1. Start with [Quick Start](QUICK_START.md)
2. Read [Development Guide](DEVELOPMENT.md)
3. Review [API Reference](API_REFERENCE.md)
4. Follow [Code Quality](CODE_QUALITY.md) standards
5. Learn about [Testing Guide](TESTING_GUIDE.md)

### For DevOps Engineers

1. Review [Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md)
2. Set up [Monitoring & Alerting](MONITORING_ALERTING.md)
3. Implement [Security Best Practices](SECURITY_BEST_PRACTICES.md)
4. Understand [Operations Runbook](OPERATIONS_RUNBOOK.md)
5. Prepare [Disaster Recovery](DISASTER_RECOVERY.md) plan

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
