# Integration Checklist

Before submitting a pull request for review, ensure all items are completed. This checklist prevents integration issues and ensures consistency across modules.

## Pre-PR Validation

### Code Quality

- [ ] All code follows project style guidelines (PEP 8 for Python, ESLint rules for TypeScript)
- [ ] No console.log/print statements remain (except structured logging)
- [ ] Comments added for complex logic
- [ ] Unused imports/variables removed
- [ ] No commented-out code blocks

### Testing

- [ ] All new tests pass locally
- [ ] Existing tests still pass
- [ ] Test coverage for new features
- [ ] Edge cases and error scenarios tested

**Backend:**
```bash
pytest
pytest --cov=app
```

**Frontend:**
```bash
npm run test -- --run
npm run build
```

### Linting & Formatting

- [ ] No linting errors
- [ ] Code formatted correctly

**Backend:**
```bash
flake8 app/
black app/
```

**Frontend:**
```bash
npm run lint
npm run format
```

### Security

- [ ] No secrets in code (.env files, API keys, passwords)
- [ ] .gitignore covers all sensitive files
- [ ] Password hashing applied (backend)
- [ ] No sensitive data logged
- [ ] CORS properly configured
- [ ] Input validation present
- [ ] Authorization checks enforced (not just frontend)

## Schema & Data Model Checks

### Database Models

For any changes to models in `app/models/`:

- [ ] Changes documented in `docs/database-schema.md`
- [ ] No conflicts with other modules' models
- [ ] Foreign keys properly defined
- [ ] Constraints appropriate
- [ ] UUIDs used for primary keys
- [ ] Timestamps in UTC
- [ ] Monetary fields use NUMERIC(15,2)
- [ ] Status values are documented enums

### Migrations

For any schema changes:

- [ ] Migration file created via `flask db migrate`
- [ ] Migration tested on fresh database
- [ ] Rollback tested (migration down then up)
- [ ] Migration file named descriptively
- [ ] No direct SQL in migrations (use SQLAlchemy)

### Shared Models

If using shared models (User, Customer, etc.):

- [ ] No changes to structure without team discussion
- [ ] Relationships preserved
- [ ] Backward compatible
- [ ] Documented in PR description

## API Contract Checks

### Response Format

All API responses follow the standard format:

- [ ] Success responses have `success: true` and `data` field
- [ ] Error responses have `success: false` and `error` object
- [ ] Error includes `code`, `message`, and optionally `details`
- [ ] HTTP status codes match response content
- [ ] Timestamps in ISO 8601 format
- [ ] Monetary values are numbers with 2 decimals

**Example Success:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message"
}
```

**Example Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is required",
    "details": { "fields": ["email"] }
  }
}
```

### Endpoint Documentation

For new endpoints:

- [ ] Endpoint path follows `/api/v1/{resource}` pattern
- [ ] HTTP method appropriate (GET/POST/PUT/DELETE/PATCH)
- [ ] Authentication requirement documented
- [ ] Permissions required documented
- [ ] Request body schema documented
- [ ] Response schema documented
- [ ] Error cases documented
- [ ] Status codes documented

Add to `docs/api-contracts.md`:

```markdown
### Endpoint Name

**METHOD** `/api/v1/path`

Requires: Authentication, Permission

Request:
```json
{ ... }
```

Response:
```json
{ ... }
```

Error codes: CODE1, CODE2
```

### Status Values

Any new status fields must use documented values:

- [ ] Status values are predefined strings (not integers)
- [ ] Documented in `docs/database-schema.md`
- [ ] All possible transitions documented
- [ ] Status change logic validated

## Frontend Checks

### Component & UI

- [ ] Components follow React best practices
- [ ] Proper use of hooks
- [ ] Props properly typed (TypeScript)
- [ ] Responsive design (mobile/tablet/desktop)
- [ ] Loading states implemented
- [ ] Error states implemented
- [ ] Empty states implemented

### Authentication

- [ ] Protected routes properly guarded
- [ ] ProtectedRoute component used
- [ ] useAuth hook used correctly
- [ ] Token refresh handled
- [ ] Logout clears all state

### Forms

- [ ] React Hook Form used
- [ ] Zod validation applied
- [ ] Error messages displayed
- [ ] Required fields marked
- [ ] Submit button disabled during submission
- [ ] Success/error feedback shown

### API Integration

- [ ] TanStack Query used for data fetching
- [ ] API service (apiClient) used
- [ ] Error handling proper
- [ ] Loading states shown
- [ ] No hardcoded URLs

## Backend Checks

### Route Handlers

- [ ] @jwt_required() decorator on protected routes
- [ ] Request validation present
- [ ] Try/except blocks for database errors
- [ ] Appropriate HTTP status codes
- [ ] Response format consistent
- [ ] Empty/null responses handled

### Database Operations

- [ ] Database transactions used for multi-step operations
- [ ] db.session.rollback() on errors
- [ ] Foreign keys verified before operations
- [ ] Soft deletes implemented where appropriate
- [ ] Indexes used for frequently queried columns
- [ ] N+1 queries avoided

### Error Handling

- [ ] Invalid input returns 400 Bad Request
- [ ] Missing auth returns 401 Unauthorized
- [ ] Insufficient permissions returns 403 Forbidden
- [ ] Not found returns 404 Not Found
- [ ] Conflicts return 409 Conflict
- [ ] Server errors return 500 Internal Server Error

### Authentication & Authorization

- [ ] Routes verify user authentication
- [ ] Routes check user permissions
- [ ] Customer records verify customer ownership
- [ ] Admin-only operations protected
- [ ] No bypassing of authorization via ID manipulation

## Module Coordination Checks

### New Module Dependencies

If your module needs data from another module:

- [ ] Discussed with other module owner
- [ ] Data contract agreed upon
- [ ] Documented in PR description
- [ ] API endpoint exists (or planned)
- [ ] Fallback behavior defined if dependency unavailable

### Shared Resource Changes

If modifying shared models (User, Customer, Audit):

- [ ] Created GitHub issue for discussion
- [ ] Team consensus obtained
- [ ] All affected parties notified
- [ ] Changes backward compatible where possible
- [ ] All modules updated simultaneously

### Database Integrity

- [ ] Foreign keys don't create circular dependencies
- [ ] Shared models remain consistent
- [ ] Cascading deletes appropriate
- [ ] No orphaned records possible

## Documentation

### Code Documentation

- [ ] Functions have docstrings/comments
- [ ] Complex logic explained
- [ ] Type hints present (TypeScript, Python)
- [ ] Edge cases documented

### API Documentation

- [ ] Endpoint documented in `docs/api-contracts.md`
- [ ] Request/response schema clear
- [ ] Error cases documented
- [ ] Authentication requirements stated

### Database Documentation

- [ ] Model changes reflected in `docs/database-schema.md`
- [ ] Relationships documented
- [ ] Status values documented
- [ ] Indexes documented

### README Updates

- [ ] If setup instructions changed, README updated
- [ ] If new environment variables, .env.example updated
- [ ] If new commands, documented in README

## Git & PR Quality

### Commit History

- [ ] Commits have clear, descriptive messages
- [ ] Follows Conventional Commits format
- [ ] Commits are logical/atomic (not one giant commit)
- [ ] No merge commits in feature branch (rebased)

### PR Description

- [ ] Clear summary of changes
- [ ] Related issue linked (if applicable)
- [ ] Type of change marked
- [ ] Related models/APIs listed
- [ ] Testing approach described
- [ ] Breaking changes noted (if any)

### File Changes

- [ ] No unrelated changes in this PR
- [ ] .env files not committed
- [ ] Only necessary files modified
- [ ] Large refactors separated from feature additions

## Testing Commands

Before submitting PR, run these locally:

### Backend

```bash
cd backend

# Tests
pytest

# Linting
flake8 app/
black --check app/

# Type checking (optional)
mypy app/ --ignore-missing-imports
```

### Frontend

```bash
cd frontend

# Tests
npm run test -- --run

# Linting
npm run lint

# Build
npm run build

# Type checking (TypeScript)
tsc -b
```

## Integration Testing

Before marking as ready for review:

- [ ] Backend starts without errors: `flask run`
- [ ] Frontend starts without errors: `npm run dev`
- [ ] Database migrations applied: `flask db upgrade`
- [ ] Can log in with test credentials
- [ ] Protected routes require authentication
- [ ] User role/permissions enforced
- [ ] No console errors or warnings

## Final Checklist

- [ ] All above items completed
- [ ] No secrets committed
- [ ] Tests pass
- [ ] Code reviewed locally
- [ ] Ready for peer review

## Review Completeness

Reviewer verifies:

- [ ] All changes present and complete
- [ ] No partial implementations
- [ ] Database state consistent
- [ ] API contracts honored
- [ ] Security measures in place
- [ ] Documentation accurate
- [ ] No conflicts with other modules
- [ ] Deployable to production

## Merge Approval

Merge only when:

- [ ] All checks pass
- [ ] Minimum 1 code review approval
- [ ] No requested changes outstanding
- [ ] No conflicts with develop branch
- [ ] All integration tests pass

---

**Having issues with the checklist?** Create a GitHub discussion or ask the team lead for clarification.
