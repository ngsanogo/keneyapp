# Community Health Files for KeneyApp

This directory contains GitHub's community health files that help manage and govern the repository.

## Files Overview

### Core Documentation

- **[CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)** - Community standards and behavior expectations
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Guidelines for contributors
- **[SECURITY.md](../SECURITY.md)** - Security policy and vulnerability reporting
- **[LICENSE](../LICENSE)** - Project license
- **[SUPPORT.md](../SUPPORT.md)** - How to get help and support

### GitHub-Specific Files

#### Issue Templates (`ISSUE_TEMPLATE/`)

- **bug_report.md** - Template for bug reports
- **feature_request.md** - Template for feature requests
- **documentation.md** - Template for documentation issues
- **performance.md** - Template for performance issues
- **config.yml** - Issue template configuration with helpful links

#### Pull Request Management

- **pull_request_template.md** - PR template with comprehensive checklist
- **CODEOWNERS** - Defines code ownership and automatic review requests

#### Repository Configuration

- **copilot-instructions.md** - Instructions for AI coding assistants
- **ai-commit-checklist.md** - Quality checklist for automated contributions
- **dependabot.yml** - Automated dependency updates configuration
- **labels.yml** - Standardized label definitions
- **FUNDING.yml** - Sponsorship and funding information
- **SECURITY_CONTACTS.md** - Security team contact information

#### Workflows (`workflows/`)

- **ci.yml** - Continuous Integration pipeline
- **security-scan.yml** - Security scanning workflow
- **release.yml** - Automated release process
- **stale.yml** - Stale issue and PR management
- **greetings.yml** - Welcome messages for first-time contributors
- **label-sync.yml** - Label synchronization automation

## Purpose of Each File

### Issue Templates

Help contributors provide consistent, high-quality issue reports with all necessary information.

### Pull Request Template

Ensures PRs include proper context, testing evidence, and follow quality standards.

### CODEOWNERS

Automatically requests reviews from relevant team members based on files changed.

### Dependabot

Keeps dependencies up-to-date automatically with weekly scans for Python, npm, Docker, and GitHub Actions.

### Workflows

Automate critical processes:

- Testing and quality checks (CI)
- Security scanning
- Release management
- Community engagement (greetings, stale issue management)

## Best Practices

### For Maintainers

1. **Review and update** templates regularly based on community feedback
2. **Keep labels synchronized** using the label-sync workflow
3. **Monitor security** through automated scans and Dependabot
4. **Respond promptly** to first-time contributors (greetings workflow helps)
5. **Manage stale issues** to keep the backlog clean

### For Contributors

1. **Use the appropriate template** when creating issues or PRs
2. **Fill out all sections** - they're there to ensure quality
3. **Reference related issues** using GitHub's linking syntax
4. **Follow the checklist** in the PR template before requesting review
5. **Be patient** - automated workflows and human reviewers both take time

## Updating Community Health Files

When making changes to these files:

1. **Test templates** by creating a draft issue/PR to see how they render
2. **Update documentation** if workflow behavior changes
3. **Communicate changes** in release notes or team channels
4. **Keep consistency** across all templates and documentation
5. **Follow GitHub best practices** - check the [GitHub Docs](https://docs.github.com/en/communities)

## Resources

- [GitHub Community Guidelines](https://docs.github.com/en/communities)
- [About Issue Templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)
- [About CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Questions or Suggestions?

If you have questions about any of these community health files or suggestions for improvement, please:

- Open an issue using the appropriate template
- Start a discussion in [GitHub Discussions](https://github.com/ISData-consulting/keneyapp/discussions)
- Contact the maintainers at <contact@isdataconsulting.com>
