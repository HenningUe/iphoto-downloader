# GitHub Configuration

This directory contains GitHub-specific configuration files for the Foto Pool project.

## 📁 Directory Structure

```
.github/
├── workflows/           # GitHub Actions workflows
│   ├── ci.yml          # Continuous Integration
│   ├── release.yml     # Release and Publishing
│   ├── dependencies.yml # Dependency Management
│   ├── nightly.yml     # Nightly Builds and Extended Tests
│   └── quality.yml     # Code Quality and Documentation
├── ISSUE_TEMPLATE/     # Issue templates
│   ├── bug_report.md   # Bug report template
│   ├── feature_request.md # Feature request template
│   └── 2fa_issue.md    # 2FA-specific issue template
├── pull_request_template.md # Pull request template
└── README.md           # This file
```

## 🔄 Workflow Overview

### CI Workflow (`ci.yml`)
- **Triggers**: Push to main/develop, Pull requests
- **Purpose**: Run tests, linting, type checking, and validation
- **Features**:
  - Multi-Python version testing
  - Code coverage reporting
  - Dependency validation
  - Build script verification

### Release Workflow (`release.yml`)
- **Triggers**: GitHub releases, Manual dispatch
- **Purpose**: Build and publish executables
- **Features**:
  - Cross-platform executable building
  - APT package creation
  - WinGet manifest generation
  - Automatic GitHub release asset upload

### Dependencies Workflow (`dependencies.yml`)
- **Triggers**: Weekly schedule, Manual dispatch
- **Purpose**: Keep dependencies up to date
- **Features**:
  - Automated dependency updates
  - Security auditing
  - Automated PR creation

### Nightly Builds (`nightly.yml`)
- **Triggers**: Daily schedule, Manual dispatch
- **Purpose**: Extended testing and validation
- **Features**:
  - Cross-platform compatibility testing
  - Performance benchmarks
  - Memory usage analysis
  - Automated issue creation on failure

### Code Quality (`quality.yml`)
- **Triggers**: Push to main/develop, Pull requests
- **Purpose**: Code quality analysis and documentation validation
- **Features**:
  - Security scanning
  - Documentation coverage
  - Dependency analysis
  - License compliance

## 🚀 Release Process

1. **Create Release**: Use GitHub's release interface or workflow dispatch
2. **Automated Building**: Workflows build Windows and Linux executables
3. **Package Creation**: APT and WinGet packages are prepared
4. **Asset Upload**: All artifacts are attached to the GitHub release
5. **Publication**: Packages are submitted to respective repositories

## 🔧 Configuration

### Secrets Required
- `GITHUB_TOKEN` (automatically provided)
- Additional secrets may be needed for package repository publishing

### Environment Variables
- Workflows use standard GitHub Actions environment variables
- Platform-specific variables are set within each job

## 📋 Issue Templates

- **Bug Report**: Structured template for reporting bugs
- **Feature Request**: Template for suggesting new features
- **2FA Issue**: Specialized template for authentication problems

## 🤝 Contributing

When contributing to this project:
1. Use the appropriate issue template when reporting problems
2. Follow the pull request template when submitting changes
3. Ensure all CI checks pass before requesting review
4. Update documentation as needed

## 📚 Workflow Status

Check the [Actions tab](../../actions) to see the current status of all workflows.
