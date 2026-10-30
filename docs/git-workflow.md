# Git Workflow & Collaboration Guidelines

This document establishes the git workflow for SubscriptIQ development to prevent conflicts and ensure smooth integration.

## Branch Strategy

We use a modified Git Flow with clear separation of concerns.

### Branch Naming

```
main              - Production-ready code (protected)
develop           - Integration branch (protected)
feature/*         - Feature or bugfix branches
module/*          - Module-specific branches
```

### Branch Protection Rules

**main branch:**
- Require pull request review (minimum 1 approval)
- Require status checks to pass (tests, build, lint)
- Require branches to be up to date before merge
- Restrict force pushes
- Require commit signatures

**develop branch:**
- Require pull request review (minimum 1 approval)
- Require status checks to pass
- Dismiss stale pull request approvals

## Development Workflow

### Starting a New Feature

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/description-of-feature

# Make commits with clear messages
git commit -m "type(scope): description"
```

### Module-Specific Work

Each developer should work on their module's dedicated feature branch:

```bash
# Member 2 (Sales & Subscriptions)
git checkout -b module/2-customer-management

# Member 3 (Billing & Payments)
git checkout -b module/3-invoice-generation

# Member 4 (Analytics & Notifications)
git checkout -b module/4-dashboard-analytics
```

### Commit Messages

Follow Conventional Commits format:

```
<type>(<scope>): <description>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Formatting changes (no code logic)
- `refactor` - Code refactoring without feature change
- `perf` - Performance improvement
- `test` - Adding or updating tests
- `chore` - Dependency updates, config changes

**Examples:**
```
feat(auth): implement JWT token refresh endpoint
fix(models): correct subscription status validation
docs(api): update authentication section in contracts
test(auth): add login flow integration tests
chore(deps): upgrade flask-sqlalchemy to 3.1.1
```

### Before Pushing

1. Sync with develop to catch conflicts early:
```bash
git fetch origin
git rebase origin/develop
```

2. Run local validation:
```bash
# Backend
cd backend
pytest
flake8 app/
black --check app/

# Frontend
cd frontend
npm run lint
npm run test -- --run
npm run build
```

3. Verify no untracked secrets:
```bash
git status
# Check .env is NOT listed (should be ignored)
```

### Creating a Pull Request

1. Push to remote:
```bash
git push -u origin feature/your-feature
```

2. Create PR on GitHub:
   - Base: `develop`
   - Compare: `feature/your-feature`
   - Title: 70 characters or less
   - Description: Follow PR template

3. PR Title Format:
```
[Module X] Brief description of changes
```

**Example:**
```
[Module 1] Implement JWT token refresh and CORS
[Module 2] Add customer and subscription models
```

### PR Description Template

```markdown
## Description
Brief explanation of changes.

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation
- [ ] Breaking change

## Related Models/APIs
- Customer (read: yes, write: no, delete: no)
- Invoice (read: no, write: yes, delete: no)

## Testing
Describe testing performed:
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No breaking changes OR breaking changes documented
- [ ] Tests pass locally
- [ ] No new warnings (linting)
- [ ] No secrets committed (.env, keys, etc.)

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Migration Required?
- [ ] Database migration needed (describe)
- [ ] Configuration changes needed
- [ ] Deployment steps required
```

### Code Review Checklist

Reviewers should verify:

- **Functionality:**
  - Does it work as described?
  - Are edge cases handled?
  - Error handling appropriate?

- **Data Models:**
  - Matches database schema in docs/
  - Foreign keys correct
  - No duplicate fields with other modules

- **API Contracts:**
  - Response format matches api-contracts.md
  - Error codes documented
  - Status values are documented enums

- **Security:**
  - No secrets in code or .env files
  - Authentication/authorization enforced
  - Input validation present
  - No SQL injection risks
  - Sensitive data not logged

- **Performance:**
  - No N+1 query problems
  - Pagination used for lists
  - Reasonable database indexes

- **Testing:**
  - New code has test coverage
  - Tests pass
  - Edge cases tested

- **Documentation:**
  - Code commented where complex
  - API docs updated
  - Database schema documented

- **Integration:**
  - No conflicts with other modules
  - Shared models not modified by this PR
  - Integration points documented

## Handling Conflicts

If develop has changes and your branch diverges:

```bash
# Fetch latest
git fetch origin

# Rebase onto develop
git rebase origin/develop

# If conflicts occur:
git status  # See conflicting files

# Edit conflicting files (look for <<<, ===, >>>)
# Keep the version that makes sense (ask for help!)

# After resolving:
git add .
git rebase --continue
git push -f origin feature/your-feature  # Force after rebase
```

## Merging Strategy

### Squash vs Merge

- **Squash**: Single commit with all feature changes
- **Rebase**: Preserves individual commits
- **Merge Commit**: Creates explicit merge commit

**Policy:**
- Squash small, single-topic PRs (1-3 commits)
- Rebase medium PRs (multiple related commits)
- Use merge commit only for major release branches

### Merge to develop

Only when:
- ✅ All checks passed
- ✅ Code reviewed and approved
- ✅ Tests pass locally and in CI
- ✅ No conflicts with develop
- ✅ No secrets committed

```bash
# On your feature branch
git rebase origin/develop
git push

# GitHub: Squash and merge
# (or use CLI)
git checkout develop
git pull origin develop
git merge --squash feature/your-feature
git commit -m "..."
git push origin develop
```

## Release Process

### Version Numbers

Use Semantic Versioning: `MAJOR.MINOR.PATCH`

- `1.0.0` - Initial release
- `1.1.0` - New features (minor bump)
- `1.0.1` - Bug fixes (patch bump)
- `2.0.0` - Breaking changes (major bump)

### Release Branch

```bash
git checkout -b release/1.1.0

# Update version numbers
# Update CHANGELOG
# Final testing

git push origin release/1.1.0
```

### Merge to main

After approval:

```bash
# Tag the release
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0

# Merge to main
git checkout main
git pull origin main
git merge --no-ff release/1.1.0
git push origin main
```

### Back-merge to develop

```bash
git checkout develop
git pull origin develop
git merge main
git push origin develop
```

## Common Scenarios

### "I committed to the wrong branch"

```bash
# If not pushed yet:
git reset --soft HEAD~1  # Undo commit, keep changes
git checkout -b correct-branch
git commit -m "..."

# If already pushed:
# Ask team before force pushing
```

### "I need to sync my branch with develop changes"

```bash
git fetch origin
git rebase origin/develop
git push -f origin feature/your-feature
```

### "I want to discard all changes and start fresh"

```bash
git reset --hard origin/develop
```

### "I accidentally pushed a secret"

1. **Immediately notify the team**
2. **Rotate the secret** (API key, password, token)
3. Remove from history:
```bash
git filter-branch --tree-filter 'rm -f .env' HEAD
git push -f origin feature/your-feature
```
4. If merged to main/develop, consider rotation urgent

## Collaboration Rules

### Module Boundaries

- **Do NOT** modify another module's models/tables without agreement
- **Do NOT** force push to develop/main
- **Do NOT** commit secrets (use .env.example instead)

### Shared Resources

For shared database models (user, audit_log, etc.):

1. **Discussion Phase**: Propose changes in a GitHub issue
2. **Review Phase**: All affected parties review
3. **Implementation Phase**: Single developer makes changes
4. **Coordination Phase**: All modules sync before merge

### Communication

If your changes affect other modules:

1. Create a GitHub discussion issue
2. Tag affected team members
3. Link PR to discussion
4. Wait for feedback before merging

## Tools & Configuration

### Git Config

```bash
# Set your identity
git config user.name "Your Name"
git config user.email "your@email.com"

# Optional: set up GPG signing
git config user.signingkey YOUR_KEY_ID
```

### Pre-commit Hooks

Optional: Set up pre-commit checks:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
# Runs linters before commit
```

### Git Aliases (Optional)

```bash
# Add to ~/.gitconfig
[alias]
  co = checkout
  br = branch
  ci = commit
  st = status
  unstage = reset HEAD --
  last = log -1 HEAD
  visual = log --graph --oneline --all
```

## Emergency Procedures

### Hotfix for Production Issue

```bash
git checkout main
git checkout -b hotfix/critical-issue
# Make minimal fix
# Test thoroughly
# Create PR to main and develop
# Deploy immediately
git tag v1.0.1
```

### Reverting a Bad Merge

```bash
git revert -m 1 <merge-commit-hash>
git push origin develop

# Creates a revert commit (doesn't rewrite history)
```

## Enforcement

- **Automated:** CI/CD checks enforce rules
- **Manual:** Code reviews enforce data model contracts
- **Technical:** Branch protection prevents force pushes

## Questions?

If unsure about git workflow:
1. Ask the team lead
2. Check GitHub discussions
3. Create an issue for documentation gaps
