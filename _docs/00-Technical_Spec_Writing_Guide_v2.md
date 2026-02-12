# Technical Spec Writing Guide

**The root cause of "empty shell" MVPs is documentation that describes what features exist rather than how they work.** When developers (or AI agents) receive a PRD saying "users can reset their password," they build a password reset page—but not the validation logic, error states, email timing, token expiration, or edge cases that make it actually function. The fix requires documenting *behavior*, not just *structure*.

This guide synthesizes best practices from Joel Spolsky's functional specifications, modern AI coding assistant workflows, BDD methodology, and technology-specific patterns for WordPress and Laravel development. The goal: lean documentation that ensures complete implementations for small teams and AI-assisted development.

**Who this guide is for:** Solo developers, small teams, and anyone using AI coding assistants (Cursor, Claude Code, Copilot) who want to stop getting scaffolding and start getting working software. The templates and patterns scale down to a one-person shop and up to a small agency.

---

## The critical layer between PRD and code

The documentation hierarchy has four levels, but most teams skip the one that matters most:

**PRD → Functional Specification → Technical Design → Code**

The **functional specification** is the missing bridge. PRDs describe *what* from the business perspective ("users can register"). Technical docs describe *how* internally (database schemas, APIs). Functional specs describe *how it works from the user's perspective*—every screen, every button, every error message, every state transition. Joel Spolsky's formulation: "A functional specification describes how a product will work entirely from the user's perspective. It doesn't care how the thing is implemented. It talks about features, screens, menus, dialogs."

The problem is that functional specs take time, so teams skip them. They write a PRD, then hand it to developers expecting working software. Instead, they get file structures and stub functions.

**What makes the difference:**

| Documentation that produces shells | Documentation that produces working software |
|-----------------------------------|---------------------------------------------|
| "User can log in with email and password" | Login with invalid email → "Please enter a valid email address" |
| "System sends reset link" | Reset link valid for 24 hours; expired link shows "This link has expired. Request a new one." with button |
| "Form validates input" | Name: 2-50 chars, no numbers. Email: RFC 5322 format. Password: 8+ chars, 1 uppercase, 1 number |

The functional spec should be detailed enough that you could write test cases from it without asking any questions. Every decision a developer would otherwise have to make should already be made.

---

## Seven documentation gaps that create empty shells

Research across multiple sources identifies these recurring failures. Each gap maps to a specific fix covered later in this guide.

| # | Gap | What goes wrong | Where to find the fix |
|---|-----|-----------------|----------------------|
| 1 | **Happy path only** | Developers implement success scenarios; errors crash or show placeholder text | Acceptance criteria (negative scenarios), Functional flow documentation |
| 2 | **Vague requirements** | "Fast" and "intuitive" get interpreted arbitrarily or ignored | Acceptance criteria (specific testable values), Non-functional requirements in templates |
| 3 | **Missing state transitions** | Disconnected pages with no logical flow between them | State transition documentation pattern |
| 4 | **Assumed knowledge** | New developers or AI agents skip steps "everyone knows" | Functional flow documentation (document every decision) |
| 5 | **Undocumented defaults** | Empty states, first-load behavior, and pre-selected values get decided randomly in code | Functional flow documentation (initial states), Data flow documentation |
| 6 | **No negative scenarios** | Security holes and data corruption live in undocumented "what NOT to do" cases | Acceptance criteria (negative scenarios), Edge case documentation |
| 7 | **Structure without behavior** | Perfectly organized codebase that doesn't actually work | The entire approach in this guide—every template prioritizes behavior over structure |

---

## Documentation that AI coding assistants can actually use

AI agents like Cursor, Copilot, and Claude Code have specific needs that differ from human developers. Understanding these prevents the common failure mode where AI generates scaffolding but not functionality.

**Why AI creates placeholder code:**

The "70% problem" (per Google's Addy Osmani) describes AI's ability to rapidly reach ~70% completion while the remaining 30%—edge cases, error handling, integration—requires human oversight. AI creates scaffolding when it lacks the context to complete the remaining 30%.

**What AI agents need:**

| Requirement | Why it matters | Example |
|-------------|----------------|---------|
| Explicit project structure | AI can't infer architecture | `server/routes/` for API endpoints, `client/src/components/` for React |
| Tech stack with versions | Dependencies affect implementation | Python 3.11, Flask 2.3, SQLAlchemy 2.0 |
| Build/test commands | Verification that code works | `pytest tests/unit/`, `npm run typecheck` |
| Existing patterns with file references | AI mimics what it sees | "Follow the pattern in `routes/users.py` for new endpoints" |
| Specific code style rules | Vague guidelines get ignored | "Use early returns for error conditions" not "write clean code" |
| Business domain knowledge | AI has no implicit understanding | Document domain terms, validation rules, business logic explicitly |

**Documentation formats that work for AI:**

Modern AI coding tools use configuration files that provide persistent context:
- `.github/copilot-instructions.md` for GitHub Copilot
- `.cursor/rules/*.mdc` for Cursor (path-specific rules)
- `CLAUDE.md` for Claude Code
- `requirements.md` → `plan.md` → `tasks.md` for spec-driven development

**The spec-driven development pattern:**

```markdown
# requirements.md
## Goal
Build user registration with email verification

## Functional Requirements
1. Users register with email/password
2. System sends verification email within 30 seconds
3. Users cannot login until verified
4. Password: 8+ chars, 1 number, 1 symbol
```

```markdown
# tasks.md  
- [ ] Create User model with email, password_hash, verified columns
- [ ] Add POST /api/register endpoint with Pydantic validation
- [ ] Implement password hashing with bcrypt
- [ ] Create SendGrid email service wrapper
- [ ] Write pytest tests for each endpoint
```

Breaking work into explicit task lists with specific implementation details gives AI agents targets to hit rather than vague goals to interpret.

**Anti-patterns that cause AI scaffolding:**

- "Write a function to fetch user data" → Too vague; AI will stub it
- "Make it work like the other endpoints" → AI needs explicit file references
- Assuming AI remembers previous sessions → Provide fresh context each time
- Asking for complete applications in one prompt → Break into phases: scaffold → implement core → add features → write tests

---

## Acceptance criteria that catch incomplete implementations

The difference between acceptance criteria that verify functionality and criteria that just verify existence comes down to specificity and testability.

**Anatomy of testable acceptance criteria:**

❌ **Bad:** "Export works"  
✅ **Good:** "Exported file contains all user records in CSV format (UTF-8 encoded), downloadable within 10 seconds for up to 10,000 users"

❌ **Bad:** "The system should be user-friendly"  
✅ **Good:** "All form fields have placeholder text and error messages appear within 1 second of invalid input"

**Four formats that work:**

**Given-When-Then (Gherkin)** works best for complex user interactions:
```gherkin
Given I'm on the login page
When I click "Forgot password" and enter a registered email
Then I receive a reset link within 5 minutes
```

**Checklist style** works for validation rules:
- Password must be minimum 8 characters
- Must contain at least one uppercase letter
- Must not match last 3 passwords

**Rules-based** works for business logic:
```
If payment fails → send alert to billing team
If three consecutive failures → lock account AND notify user
```

**Scenario-based** works for end-to-end workflows with multiple paths:
```markdown
## Scenario: Returning customer checkout

### Path A: Saved payment method
1. Customer clicks "Buy Now" → System pre-fills saved card ending in 4242
2. Customer confirms → System charges card → Order confirmation shown
3. Card declined → "Payment failed. Try another card or contact your bank."

### Path B: New payment method
1. Customer clicks "Buy Now" → System shows empty payment form
2. Customer enters card → System validates via Stripe → saves if "Remember" checked
3. Invalid card number → "Please check your card number" (inline, no page reload)

### Path C: Guest checkout
1. Customer clicks "Buy Now" → System prompts login/guest choice
2. Guest selected → email required for receipt, no card saved
3. Email already has account → "An account exists with this email. Log in or continue as guest."
```

**Critical: include negative scenarios.**

Every acceptance criteria set should include what happens when things go wrong:

```gherkin
Given I'm on the checkout page
When payment gateway times out
Then I see "Payment processing delayed" message
And I can retry without losing my cart
And no duplicate charge is created
```

**Definition of Done checklist:**

Work is "Done" only when it meets both quality standards AND functionality requirements. This checklist is intentionally weighted toward *behavior* over *structure*—a feature that builds and deploys but doesn't handle errors is not done.

1. ✓ All acceptance criteria verified (happy path AND error paths)
2. ✓ Every user-facing state documented in spec is implemented (empty, loading, success, error, edge case)
3. ✓ Error handling implemented and tested with specific messages from spec
4. ✓ Edge cases from spec are covered
5. ✓ Code complete (no TODOs, no placeholder functions, no hardcoded test data)
6. ✓ Unit tests written and passing (≥80% coverage)
7. ✓ Integration tests passing
8. ✓ Builds without errors
9. ✓ Deployed to test environment and manually verified
10. ✓ Documentation updated (API docs, README, inline comments for non-obvious logic)

---

## Documenting functional flows and state transitions

Features fail when documentation describes *what exists* but not *how it works*. Three documentation patterns ensure the logic gets built:

**Functional flow documentation:**

```markdown
## Feature: Password Reset

### Initial State
- Login page shows "Forgot Password?" link below the password field
- Link is always visible (not conditional on failed login)

### Main Flow
1. User clicks "Forgot Password" on login screen
2. System shows email input form
3. On submit:
   - Empty email → "Please enter your email address"
   - Invalid format → "Please enter a valid email address"  
   - Email not found → Show same success message (security: do not reveal which emails exist)
   - Email found → Send email, show confirmation
4. Reset email contains link valid for 24 hours
5. Expired link → "This link has expired" + "Request new link" button
6. Reset form: new password + confirm, strength indicator
7. Success → "Password updated" → redirect to login

### Edge Cases
- User requests multiple resets → only latest link works, previous links invalidated
- User tries used link → "This link has already been used"
- User already logged in → redirect to account settings
- User's account is locked/suspended → "Contact support to reset your password"
```

**Data flow documentation:**

| Data Element | Source | Processing | Destination |
|--------------|--------|------------|-------------|
| User email | Form input | Validate format, check DB | Reset token generator |
| Reset token | UUID generator | Hash, store with expiry | Email template, tokens table |
| New password | Form input | Validate rules, bcrypt hash | Users table |

**State transition documentation:**

For features where entities move through states (orders, subscriptions, user accounts), document the state machine:

| From State | Event | Guard | To State | Action |
|------------|-------|-------|----------|--------|
| Draft | submit | [items valid] | Submitted | Send to payment |
| Submitted | payment_received | — | Processing | Charge card |
| Submitted | timeout | [>24 hours] | Cancelled | Release items |
| Processing | ship | — | Shipped | Generate tracking |
| * | cancel | [not shipped] | Cancelled | Process refund |

**User story mapping prevents half-built features:**

Jeff Patton's story mapping technique creates a two-dimensional view:
- **Horizontal axis (backbone):** High-level user activities in narrative order
- **Vertical axis (body):** Detailed tasks beneath each activity
- **Release slices (horizontal lines):** Minimum viable groupings

This prevents the common failure of building complete depth in one area while leaving others empty. Each release slice spans the full user journey at increasing depth.

---

## Documenting dependencies and integrations

Third-party services, APIs, and external systems are where implementations most often stall—the spec says "send email" but doesn't document the provider, credentials, error handling, or fallback behavior.

**Integration documentation template:**

```markdown
## Integration: [Service Name]

**Provider:** [e.g., SendGrid, Stripe, Twilio]
**Purpose:** [What this integration does in your system]
**Environment:** 
- API Key location: [e.g., .env → SENDGRID_API_KEY]
- Sandbox/test mode: [How to test without hitting production]

### Endpoints Used
| Action | Method | Endpoint | Rate Limit |
|--------|--------|----------|------------|
| Send transactional email | POST | /v3/mail/send | 100/sec |
| Check bounce status | GET | /v3/suppression/bounces | 500/min |

### Error Handling
| Error | Cause | Our Response |
|-------|-------|-------------|
| 401 Unauthorized | Bad API key | Log critical error, alert ops, queue for retry |
| 429 Rate Limited | Too many requests | Exponential backoff: 1s, 2s, 4s, max 3 retries |
| 500 Server Error | Provider outage | Queue message, retry in 5 min, alert after 3 failures |
| Timeout (>10s) | Network issue | Retry once, then queue for background processing |

### Fallback Behavior
If [service] is unavailable for >15 minutes: [what happens — e.g., "queue emails locally, process when service recovers, show user 'Email will arrive shortly' instead of immediate confirmation"]

### Webhook Handling (if applicable)
- **Endpoint:** POST /webhooks/sendgrid
- **Authentication:** Signature verification using SENDGRID_WEBHOOK_KEY
- **Events handled:** delivered, bounced, spam_report
- **Retry policy:** SendGrid retries for 72 hours; our endpoint must be idempotent
```

---

## WordPress plugin documentation essentials

WordPress plugins fail when lifecycle hooks, data structures, and integrations aren't documented for implementation.

**Plugin lifecycle hooks:**

| Hook | Purpose | Must Document |
|------|---------|---------------|
| `register_activation_hook()` | Setup on install | Database tables created, default options, capabilities added, permalinks flushed |
| `register_deactivation_hook()` | Cleanup on disable | Scheduled events removed, caches cleared, temporary data deleted |
| `register_uninstall_hook()` | Complete removal | All tables dropped, options deleted, user meta removed, files deleted |

**Hook and filter documentation template:**

```php
/**
 * Filter: myplugin_process_data
 * @param array $data The data being processed
 * @param int $user_id Current user ID
 * @return array Modified data array
 * @since 1.0.0
 */
```

**Database schema documentation:**

```markdown
## Table: {$wpdb->prefix}plugin_orders

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint(20) | PK, AUTO_INCREMENT | Order ID |
| user_id | bigint(20) | FK→users, INDEX | Customer |
| status | varchar(20) | DEFAULT 'pending' | Order state |
| created_at | datetime | NOT NULL | Creation timestamp |

Version: 1.0 | Created: activation | Removed: uninstall
```

**REST API endpoint documentation:**

```markdown
## Endpoint: GET /wp-json/myplugin/v1/items

**Authentication:** Requires `read` capability
**Parameters:**
- page (int): Page number, default 1
- per_page (int): Results per page, default 10, max 100

**Response 200:**
{ "items": [...], "total": 150, "pages": 15 }

**Error 401:** { "code": "unauthorized", "message": "Authentication required" }
**Error 403:** { "code": "forbidden", "message": "Insufficient permissions" }
```

---

## Laravel SaaS documentation essentials

Laravel applications need explicit documentation of routes, services, multi-tenancy boundaries, and background job behavior.

**Route documentation standard:**

```php
/**
 * @route POST /api/v1/subscriptions
 * @middleware api, auth:sanctum, verified
 * @body { plan_id: int, payment_method_id: string }
 * @response 201 { subscription: {...}, invoice: {...} }
 * @throws 402 Payment failed
 * @throws 422 Invalid plan or payment method
 */
```

**Service layer documentation:**

```markdown
## Service: SubscriptionService

**Dependencies:** PaymentGateway, UserRepository, EventDispatcher

### create(User $user, Plan $plan, string $paymentMethodId): Subscription
Creates new subscription, charges payment method, dispatches SubscriptionCreated event.

**Throws:**
- PaymentFailedException: Card declined or insufficient funds
- InvalidPlanException: Plan not found or inactive

**Events:** SubscriptionCreated, PaymentProcessed
```

**Multi-tenancy documentation:**

| Aspect | Our Implementation |
|--------|-------------------|
| Identification | Subdomain-based (tenant.app.com) |
| Data isolation | Separate database per tenant |
| Central routes | routes/web.php (marketing, auth) |
| Tenant routes | routes/tenant.php (app features) |
| Tenant migrations | database/migrations/tenant/ |
| Shared data | Central DB: plans, features, global settings |

**Queue and job documentation:**

```markdown
## Job: ProcessSubscriptionRenewal

**Queue:** subscriptions  
**Connection:** redis  
**Timeout:** 120 seconds  
**Retries:** 3 with backoff [60, 300, 600]

**On success:** Dispatches SubscriptionRenewed event  
**On failure:** Dispatches SubscriptionFailed, notifies billing team  
**On max retries:** Moves to failed_jobs, alerts operations
```

---

## Practical templates

### One-page feature specification

```markdown
# Feature: [Name]
**Owner:** [Name] | **Status:** Draft/Review/Approved/Done | **Last Updated:** [Date]

## Problem
[1-2 sentences on what this solves and why it matters now]

## User Story  
As a [user type], I want [action] so that [benefit]

## Acceptance Criteria
- [ ] Given [context], when [action], then [result]
- [ ] Given [error condition], when [action], then [error handling with specific message]
- [ ] Edge case: [scenario] → [behavior]
- [ ] Negative: System must NOT [unsafe/unintended behavior]

## Functional Flow
### Initial State
[What the user sees before any interaction]

### Main Flow
1. User does X → System shows Y
2. User submits → System validates [specific rules]
3. Success → System does Z, shows "[exact confirmation message]"
4. Failure → System shows "[exact error message]"

### Edge Cases
- [Scenario] → [Behavior]

## Data
- **Input:** [fields with validation rules, types, and constraints]
- **Output:** [response structure with example]  
- **Stored:** [what persists, where, for how long]

## Non-Functional Requirements
- **Performance:** [e.g., "Page loads in <2s on 3G," "API responds in <300ms for up to 1000 records"]
- **Security:** [e.g., "Input sanitized against XSS," "Rate limited to 10 requests/minute per IP"]
- **Accessibility:** [e.g., "All form fields have labels," "Error messages announced to screen readers"]

## Dependencies
- **External services:** [APIs, payment processors, email providers — link to integration doc if exists]
- **Internal dependencies:** [Other features/modules this relies on]

## Open Questions
- [ ] [Unresolved item — spec is not "Approved" until this section is empty]
```

### AI-friendly specification template

```markdown
# Feature: [Name]

## Context
[Brief description of feature purpose and where it fits in the system]

## Tech Stack
- [Framework and version]
- [Database]
- [Relevant libraries with versions]

## Implementation Tasks
- [ ] Create [model/table] with [specific columns and types]
- [ ] Add [endpoint] with [request/response format including error responses]
- [ ] Implement [business logic] following pattern in [existing file path]
- [ ] Handle errors: [list specific error cases and exact messages]
- [ ] Write tests for [specific scenarios including edge cases]

## Reference Files
- Follow patterns in: [path/to/similar/feature]
- Use existing utilities from: [path/to/utils]
- Do NOT modify: [files that should remain untouched]

## Validation Rules
- [Field]: [specific rule with values, e.g., "email: required, RFC 5322, max 254 chars"]
- [Field]: [specific rule with values]

## Error Messages
- [Condition]: "[Exact message to display]"
- [Condition]: "[Exact message to display]"

## States the UI Must Handle
- **Empty/first load:** [What to show when there's no data yet]
- **Loading:** [What to show during async operations]
- **Success:** [What to show on completion]
- **Error:** [What to show when something fails]
- **Partial:** [What to show for edge cases like partial data]

## Verification
- Run: [specific test command]
- Manually verify: [specific thing to check in browser/API]
- Expected result: [what correct behavior looks like]
```

---

## Spec completeness checklist

Run through this before handing any spec to a developer or AI agent. If you can't answer every question, your spec has gaps that will become placeholder code.

**Behavior:**
- [ ] Can I write a test for every acceptance criterion without asking any questions?
- [ ] Have I documented what happens for every error the user could encounter?
- [ ] Have I specified exact error messages, not just "show an error"?
- [ ] Have I documented empty states, loading states, and first-time-use states?

**Scope:**
- [ ] Have I documented what this feature should NOT do? (Prevents scope creep during implementation)
- [ ] Are all external dependencies identified with their error/fallback behavior?
- [ ] Are there open questions? (If yes, the spec isn't ready)

**Specificity:**
- [ ] Are all validation rules listed with specific values (min/max lengths, formats, ranges)?
- [ ] Are performance requirements stated with measurable numbers?
- [ ] Could two different developers read this spec and build the same thing?

**For AI-assisted development, also verify:**
- [ ] Are file paths to reference patterns included?
- [ ] Are tech stack versions specified?
- [ ] Is there a verification command the AI can run to check its own work?
- [ ] Have I broken the work into tasks small enough for a single prompt?

---

## Keeping specs alive

Specs that aren't maintained become lies. But over-documenting changes creates overhead that kills the practice entirely. For small teams, keep it simple:

**When to update a spec:** When the implemented behavior intentionally diverges from what's documented. Bug fixes that match the spec don't need updates. New features or changed requirements do.

**How to track changes:** Add a changelog section at the bottom of the spec. One line per change is enough:

```markdown
## Changelog
- 2025-03-15: Added rate limiting to login (5 attempts/15 min) — [your name]
- 2025-02-01: Initial spec — [your name]
```

**When to archive vs. update:** If more than 50% of the spec no longer reflects reality, start a new version rather than trying to patch the old one.

---

## Conclusion: the minimum viable spec

Empty shell MVPs result from documentation that describes structure without behavior. The fix is straightforward but requires discipline: document every user-facing decision before writing code.

**Three non-negotiable practices:**

1. **Document error states as thoroughly as success states.** If your spec only covers the happy path, developers will only build the happy path.

2. **Make acceptance criteria testable with specific values.** "Fast" cannot be tested. "Response under 300ms for queries up to 1000 records" can be tested.

3. **For AI-assisted development, provide explicit context and verification methods.** AI agents need file references, existing patterns to follow, specific implementation details, and test cases to validate against.

**Quick reference — the four questions every feature spec must answer:**

| Question | If missing, you get... |
|----------|----------------------|
| What does the user see in each state? (empty, loading, success, error) | Blank screens, missing loading indicators, generic error pages |
| What happens on each user action? (click, submit, navigate) | Buttons that do nothing, forms that submit but don't respond |
| What errors are possible and how are they handled? | Crashes, console errors, silent failures |
| How do I verify it works? (test commands, manual checks) | "It builds" mistaken for "it works" |

Skip any of these, and you'll get scaffolding instead of software.
