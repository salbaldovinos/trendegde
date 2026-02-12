# PRD-008: Authentication & User Management

**TrendEdge -- AI-Powered Futures Trading Platform**

Version 1.0 | February 2026 | CONFIDENTIAL

**Status:** Draft
**Owner:** TrendEdge Engineering
**Priority:** P0 (Critical Path -- Security Foundation)
**Dependencies:** PRD-001 (Infrastructure & DevOps)
**Depends On This:** PRD-002 (Trendline Engine), PRD-003 (Execution Pipeline), PRD-004 (Journaling), PRD-005 (Playbooks), PRD-006 (Analytics), PRD-007 (AI Features), PRD-009 (Notifications), PRD-010 (Integrations), PRD-011 (Billing & Subscriptions)

---

## Table of Contents

1. [Overview & Purpose](#1-overview--purpose)
2. [User Stories](#2-user-stories)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Dependencies](#5-dependencies)
6. [Testing Requirements](#6-testing-requirements)
7. [Security](#7-security)
8. [Phase Mapping](#8-phase-mapping)
9. [Acceptance Criteria](#9-acceptance-criteria)

---

## 1. Overview & Purpose

### 1.1 Summary

This PRD defines the authentication, authorization, user management, and data isolation layer for TrendEdge. As the most security-critical PRD in the system, it establishes how users register, authenticate, manage their profiles and broker connections, and how the platform enforces strict data isolation between users.

TrendEdge handles sensitive financial data -- broker API credentials, trading history, account balances, and proprietary strategies. A breach or data leak could result in direct financial loss to users. Every design decision in this document prioritizes security-by-default, defense-in-depth, and least-privilege access.

### 1.2 Auth Provider

**Supabase Auth** is the authentication provider. It provides:
- OAuth 2.0 and OpenID Connect flows out of the box
- Magic link (passwordless) authentication
- JWT-based session tokens with configurable expiry
- Row Level Security (RLS) integration with PostgreSQL
- Built-in email verification and password reset flows
- Team/organization support for prop firm accounts (Phase 3)

### 1.3 Build-Then-Productize Strategy

| Phase | Auth Scope | Users |
|-------|-----------|-------|
| Phase 1 | Single-user basic auth. Email/password login. Minimal profile. Direct database access with RLS policies in place from day one. | 1 (developer) |
| Phase 2 | Full auth flows. Magic links, OAuth (Google, GitHub), email verification, password reset, session management, broker credential encryption, API key management. | 1-100 (beta) |
| Phase 3 | Multi-tenant SaaS. Team/org support, member invitations, role-based access within teams, shared playbooks, onboarding wizard, GDPR-compliant account deletion. | 100-5,000+ |

### 1.4 User Model

```
User {
  id: UUID (PK, matches Supabase auth.users.id)
  email: string (unique, from Supabase auth)
  display_name: string (nullable)
  avatar_url: string (nullable)
  timezone: string (default: 'America/New_York')
  subscription_tier: enum ['free', 'trader', 'pro', 'team']
  settings: JSONB {
    trading_preferences: {
      default_instruments: string[]       // e.g., ['PL', 'CL', 'GC', 'YM']
      default_timeframe: string           // e.g., '4H'
      risk_per_trade_percent: decimal     // e.g., 1.0
      max_daily_loss: decimal             // e.g., 500.00
      max_concurrent_positions: integer   // e.g., 3
      paper_trading_mode: boolean         // default: true
    }
    notification_preferences: {
      telegram_enabled: boolean
      telegram_chat_id: string
      discord_webhook_url: string
      email_digest: enum ['none', 'daily', 'weekly']
      alert_on_fill: boolean
      alert_on_trendline: boolean
      alert_on_risk_breach: boolean
    }
    display_preferences: {
      theme: enum ['light', 'dark', 'system']
      currency_display: string            // e.g., 'USD'
      date_format: string                 // e.g., 'MM/DD/YYYY'
      compact_mode: boolean
    }
  }
  broker_connections: (separate table, see AU-FR-040)
  role: enum ['user', 'admin']
  team_id: UUID (nullable, FK -> teams.id, Phase 3)
  team_role: enum ['team_admin', 'team_member'] (nullable, Phase 3)
  onboarding_completed: boolean (default: false)
  onboarding_step: integer (default: 0)
  created_at: timestamptz
  updated_at: timestamptz
  last_login_at: timestamptz
  deleted_at: timestamptz (soft delete)
}
```

### 1.5 Subscription Tiers

| Tier | Price | Broker Connections | Accounts | Team Members |
|------|-------|-------------------|----------|--------------|
| Free | $0/mo | 0 (paper only) | 1 paper | -- |
| Trader | $49/mo | 1 broker | 1 account | -- |
| Pro | $99/mo | 3 brokers | 5 accounts | -- |
| Team | $199/mo | Unlimited | 20+ accounts | 5-20+ members |

---

## 2. User Stories

### 2.1 Registration & Authentication

| ID | As a... | I want to... | So that... | Phase |
|----|---------|-------------|-----------|-------|
| US-001 | New visitor | Register with my email and password | I can start using TrendEdge | 1 |
| US-002 | New visitor | Register using my Google account | I can sign up without creating another password | 2 |
| US-003 | New visitor | Register using my GitHub account | I can sign up quickly as a developer | 2 |
| US-004 | Registered user | Log in with a magic link sent to my email | I don't need to remember a password | 2 |
| US-005 | Registered user | Reset my password via email | I can regain access if I forget my password | 2 |
| US-006 | Registered user | Verify my email address | My account is secured and I can receive notifications | 2 |

### 2.2 Session & Profile Management

| ID | As a... | I want to... | So that... | Phase |
|----|---------|-------------|-----------|-------|
| US-007 | Logged-in user | Stay logged in across browser sessions | I don't have to re-authenticate every visit | 1 |
| US-008 | Logged-in user | See and revoke active sessions on other devices | I can secure my account if a device is lost | 2 |
| US-009 | Logged-in user | Update my display name, timezone, and avatar | My profile reflects my identity and correct time | 1 |
| US-010 | Logged-in user | Configure my default trading instruments and risk parameters | Trades use my preferred defaults automatically | 1 |
| US-011 | Logged-in user | Set my notification preferences | I only receive alerts I care about | 2 |

### 2.3 Broker Connections

| ID | As a... | I want to... | So that... | Phase |
|----|---------|-------------|-----------|-------|
| US-012 | Trader user | Connect my Interactive Brokers account securely | TrendEdge can execute trades on my behalf | 1 |
| US-013 | Trader user | Connect my Tradovate account securely | TrendEdge can route orders through Tradovate | 1 |
| US-014 | Pro user | Connect multiple broker accounts | I can trade across different brokers and accounts | 2 |
| US-015 | Trader user | See the connection status of my brokers at a glance | I know if execution is available right now | 1 |
| US-016 | Trader user | Re-authorize a broker whose credentials have expired | I can resume trading without re-entering everything | 2 |

### 2.4 Security & Data Isolation

| ID | As a... | I want to... | So that... | Phase |
|----|---------|-------------|-----------|-------|
| US-017 | Any user | Be certain no other user can see my trades or data | My trading strategy and performance are private | 1 |
| US-018 | Any user | Have my broker credentials encrypted at rest | My financial accounts are protected even in a breach | 1 |
| US-019 | Admin user | Access any user's data for support purposes | I can help users troubleshoot issues | 3 |
| US-020 | Any user | Generate API keys for TradingView webhooks | I can connect external signals securely | 2 |

### 2.5 Team / Organization (Phase 3)

| ID | As a... | I want to... | So that... | Phase |
|----|---------|-------------|-----------|-------|
| US-021 | Prop firm manager | Create a team and invite funded traders | I can manage all accounts from one dashboard | 3 |
| US-022 | Team admin | Assign roles (admin/member) to team members | I can control who manages vs. who trades | 3 |
| US-023 | Team admin | Share playbooks and analytics across my team | All funded traders follow the same strategy | 3 |
| US-024 | Team member | See only my own trades but shared team playbooks | I have the strategy context without seeing others' data | 3 |

### 2.6 Onboarding & Account Lifecycle

| ID | As a... | I want to... | So that... | Phase |
|----|---------|-------------|-----------|-------|
| US-025 | New user | Be guided through an onboarding wizard | I can set up my account correctly the first time | 3 |
| US-026 | Any user | Export all my data in a machine-readable format | I can take my data if I leave the platform | 3 |
| US-027 | Any user | Delete my account and all associated data | I can exercise my right to be forgotten | 3 |
| US-028 | Any user | Manage my API keys (create, revoke, view usage) | I can control external access to my account | 2 |

---

## 3. Functional Requirements

### 3.1 Supabase Auth Integration

#### AU-FR-001: Email/Password Registration

The system SHALL provide email/password registration using Supabase Auth.

**Flow:**
1. User navigates to `/register` and sees a registration form with fields: email, password, confirm password.
2. **Client-side validation (before submit):**
   - Email: RFC 5322 format validation. Error: "Please enter a valid email address."
   - Password: minimum 8 characters, at least 1 uppercase letter, at least 1 lowercase letter, at least 1 number, at least 1 special character (!@#$%^&*). Error: "Password must be at least 8 characters with 1 uppercase, 1 lowercase, 1 number, and 1 special character."
   - Confirm password: must match password. Error: "Passwords do not match."
3. **On submit:** Call `supabase.auth.signUp({ email, password })`.
4. **Success:** Display "Check your email to verify your account." Redirect to `/verify-email` page.
5. **Error states:**
   - Email already registered: "An account with this email already exists. Try logging in or resetting your password." (Do NOT reveal whether the email exists in production -- use generic message: "If this email is not already registered, you will receive a verification email.")
   - Rate limited: "Too many attempts. Please try again in 60 seconds."
   - Network error: "Unable to connect. Please check your connection and try again."
6. **Post-registration:** Create a corresponding row in `public.users` table via Supabase database trigger on `auth.users` insert, populated with default settings.

**Database trigger (on auth.users insert):**
```sql
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.users (id, email, subscription_tier, settings, role, created_at, updated_at)
  VALUES (
    NEW.id,
    NEW.email,
    'free',
    '{
      "trading_preferences": {
        "default_instruments": [],
        "default_timeframe": "4H",
        "risk_per_trade_percent": 1.0,
        "max_daily_loss": 500.00,
        "max_concurrent_positions": 3,
        "paper_trading_mode": true
      },
      "notification_preferences": {
        "telegram_enabled": false,
        "email_digest": "daily",
        "alert_on_fill": true,
        "alert_on_trendline": true,
        "alert_on_risk_breach": true
      },
      "display_preferences": {
        "theme": "system",
        "currency_display": "USD",
        "date_format": "MM/DD/YYYY",
        "compact_mode": false
      }
    }'::jsonb,
    'user',
    NOW(),
    NOW()
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

#### AU-FR-002: Magic Link (Passwordless) Authentication

The system SHALL support passwordless login via magic links.

**Flow:**
1. User navigates to `/login` and clicks "Sign in with magic link."
2. User enters their email address.
3. System calls `supabase.auth.signInWithOtp({ email })`.
4. **Success:** Display "Check your email for a login link. The link expires in 1 hour."
5. User clicks the link in their email, which redirects to `/auth/callback` with a token.
6. The callback page exchanges the token for a session via `supabase.auth.verifyOtp()`.
7. **Success:** Redirect to `/dashboard`.
8. **Error states:**
   - Expired link (>1 hour): "This link has expired. Request a new one." with a "Send new link" button.
   - Already-used link: "This link has already been used. Request a new one."
   - Invalid token: "Invalid login link. Please request a new one."

**Constraints:**
- Magic links are single-use.
- Rate limit: maximum 3 magic link requests per email per 15-minute window.
- Magic links expire after 1 hour (configurable via Supabase dashboard).

#### AU-FR-003: OAuth Provider Authentication (Google)

The system SHALL support Google OAuth login.

**Flow:**
1. User clicks "Continue with Google" on the login or registration page.
2. System calls `supabase.auth.signInWithOAuth({ provider: 'google' })`.
3. User is redirected to Google's consent screen.
4. On consent, Google redirects back to `/auth/callback`.
5. Supabase creates or links the user account automatically.
6. **New user:** Database trigger creates the `public.users` row with defaults.
7. **Existing user (same email):** Supabase links the OAuth identity to the existing account.
8. **Success:** Redirect to `/dashboard` (existing user) or `/onboarding` (new user, Phase 3).
9. **Error states:**
   - User denies consent: Redirect to `/login` with message "Google sign-in was cancelled."
   - OAuth state mismatch (CSRF): "Authentication failed. Please try again."

#### AU-FR-004: OAuth Provider Authentication (GitHub)

The system SHALL support GitHub OAuth login.

**Flow:** Identical to AU-FR-003 but using `provider: 'github'`. GitHub is relevant for the algo-curious developer persona who may prefer GitHub identity.

#### AU-FR-005: Email Verification Flow

The system SHALL require email verification before granting full account access.

**Flow:**
1. On registration (AU-FR-001), Supabase sends a verification email automatically.
2. **Unverified users CAN:** Access the dashboard in read-only mode, view the verification banner.
3. **Unverified users CANNOT:** Connect brokers, execute trades (including paper), create API keys.
4. The verification banner displays: "Please verify your email to unlock all features. Didn't receive the email? [Resend]"
5. Clicking "Resend" calls `supabase.auth.resend({ type: 'signup', email })`.
6. Rate limit: maximum 3 resend requests per hour.
7. Verification link expires after 24 hours.
8. On successful verification, the banner disappears and full features unlock immediately (no page reload required -- listen to `onAuthStateChange`).
9. **Error states:**
   - Expired verification link: "This verification link has expired." with "Send new verification email" button.
   - Already verified: Redirect to `/dashboard` with toast "Your email is already verified."

#### AU-FR-006: Password Reset Flow

The system SHALL provide a secure password reset mechanism.

**Flow:**
1. User clicks "Forgot password?" on the login page.
2. System displays an email input form.
3. On submit, system calls `supabase.auth.resetPasswordForEmail(email)`.
4. **Always display:** "If an account exists with that email, you will receive a password reset link." (Never reveal whether the email exists.)
5. Reset email contains a link to `/auth/reset-password` with a token.
6. Reset link expires after 1 hour.
7. Reset password form: new password + confirm password, with a real-time strength indicator (weak/fair/strong/very strong).
8. Password validation: same rules as AU-FR-001 (8+ chars, uppercase, lowercase, number, special).
9. System calls `supabase.auth.updateUser({ password: newPassword })`.
10. **Success:** "Password updated successfully." Redirect to `/login`.
11. All existing sessions for this user are invalidated on password reset.
12. **Error states:**
    - Expired token: "This reset link has expired. Request a new one." with button.
    - Already-used token: "This reset link has already been used."
    - New password matches old: "New password must be different from your current password."
    - Rate limit: maximum 3 reset requests per email per hour.

---

### 3.2 Session Management

#### AU-FR-010: JWT Token Handling

The system SHALL use Supabase-issued JWTs for all authenticated API requests.

**Implementation:**
1. On successful authentication, Supabase issues an access token (JWT, short-lived) and a refresh token (opaque, long-lived).
2. The access token is stored in memory (JavaScript variable) on the client. It is NEVER stored in `localStorage` or `sessionStorage`.
3. The refresh token is stored in an HTTP-only, Secure, SameSite=Lax cookie.
4. Every API request to the FastAPI backend includes the access token in the `Authorization: Bearer <token>` header.
5. The FastAPI backend validates the JWT by:
   - Verifying the signature against the Supabase JWT secret.
   - Checking the `exp` claim (reject if expired).
   - Checking the `aud` claim matches the expected audience.
   - Extracting `sub` (user ID) for RLS context.
6. The validated user ID is set as the PostgreSQL session variable for RLS: `SET request.jwt.claim.sub = '<user_id>'`.

#### AU-FR-011: Refresh Token Rotation

The system SHALL implement refresh token rotation to prevent token theft.

**Implementation:**
1. Access tokens expire after 15 minutes (900 seconds).
2. Refresh tokens expire after 7 days.
3. The Supabase client SDK automatically refreshes the access token when it is within 60 seconds of expiry.
4. On each refresh, the old refresh token is invalidated and a new one is issued (rotation).
5. If a previously-invalidated refresh token is used (indicating potential theft), ALL sessions for that user are revoked immediately, and the user receives an email: "We detected suspicious activity on your account. All sessions have been signed out for your protection."
6. **Offline/background tabs:** The client SDK handles token refresh across tabs using `BroadcastChannel`. Only one tab refreshes at a time.

#### AU-FR-012: Session Expiry Configuration

The system SHALL enforce configurable session expiry policies.

**Configuration (Supabase dashboard + environment variables):**
| Parameter | Value | Configurable |
|-----------|-------|-------------|
| Access token lifetime | 900 seconds (15 min) | Yes (env) |
| Refresh token lifetime | 604800 seconds (7 days) | Yes (env) |
| Inactivity timeout | 30 minutes (client-side) | Yes (user setting) |
| Maximum session age | 30 days | Yes (env) |

**Inactivity timeout behavior:**
1. Client tracks last user interaction (click, keypress, scroll).
2. After 25 minutes of inactivity, display a warning modal: "Your session will expire in 5 minutes due to inactivity. [Stay signed in]"
3. Clicking "Stay signed in" resets the timer and refreshes the token.
4. If no action after 30 minutes, the client calls `supabase.auth.signOut()` and redirects to `/login` with message "You were signed out due to inactivity."
5. Any unsaved form data is preserved in `sessionStorage` and restored on re-login.

#### AU-FR-013: Multi-Device Session Management

The system SHALL allow users to view and manage active sessions across devices.

**Flow:**
1. User navigates to `/settings/security/sessions`.
2. The page displays a list of active sessions with:
   - Device type (Desktop/Mobile/Tablet) derived from User-Agent.
   - Browser name and version.
   - IP address (last 2 octets masked for privacy: `192.168.xxx.xxx`).
   - Location (city, country) from IP geolocation.
   - Last active timestamp ("Active now", "2 hours ago", "3 days ago").
   - Current session is labeled "(this device)".
3. Each session (except current) has a "Revoke" button.
4. Clicking "Revoke" calls `supabase.auth.admin.deleteSession(sessionId)` (via backend proxy).
5. "Revoke all other sessions" button revokes everything except the current session.
6. **Confirmation modal:** "Are you sure you want to revoke this session? The device will need to log in again. [Cancel] [Revoke]"
7. Phase 2+ only. Phase 1 has single-user, single-session.

---

### 3.3 User Profile Management

#### AU-FR-020: Profile CRUD

The system SHALL provide profile viewing and editing capabilities.

**Profile fields:**
| Field | Type | Validation | Default | Editable |
|-------|------|-----------|---------|----------|
| Display name | string | 2-50 chars, letters/spaces/hyphens only | null | Yes |
| Email | string | RFC 5322 (managed by Supabase Auth) | from auth | Via email change flow |
| Avatar | URL/file | JPG/PNG, max 2MB, 200x200 min | null | Yes |
| Timezone | string | Valid IANA timezone identifier | America/New_York | Yes |

**Email change flow:**
1. User enters new email on profile page.
2. System sends verification link to the NEW email.
3. User clicks the link in the new email.
4. System sends a notification to the OLD email: "Your TrendEdge email was changed to [new-email]. If this wasn't you, contact support immediately."
5. Email is only updated after new email is verified.

**Avatar upload:**
1. User uploads image file or enters URL.
2. File is resized to 200x200 pixels server-side.
3. File is uploaded to Cloudflare R2 at `avatars/{user_id}.{ext}`.
4. URL is stored in `users.avatar_url`.

**Error states:**
- Display name too short: "Name must be at least 2 characters."
- Display name too long: "Name must not exceed 50 characters."
- Display name invalid chars: "Name can only contain letters, spaces, and hyphens."
- Avatar too large: "Image must be under 2MB."
- Avatar wrong format: "Please upload a JPG or PNG image."
- Timezone invalid: "Please select a valid timezone."

#### AU-FR-021: Trading Preferences

The system SHALL allow users to configure their default trading parameters.

**Fields and validation:**
| Preference | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| Default instruments | string[] | 0-20 items, valid CME symbols | [] | Instruments shown in dashboard |
| Default timeframe | enum | 1H, 4H, D, W | 4H | Primary analysis timeframe |
| Risk per trade (%) | decimal | 0.1 - 5.0 | 1.0 | % of account risked per trade |
| Max daily loss ($) | decimal | 50 - 50,000 | 500.00 | Circuit breaker threshold |
| Max concurrent positions | integer | 1 - 20 | 3 | Position limit |
| Paper trading mode | boolean | -- | true | Route to paper vs. live |

**Paper trading mode toggle:**
1. User toggles paper trading mode OFF.
2. System shows confirmation modal: "You are switching to LIVE trading. Real money will be at risk. Are you sure? [Stay in paper] [Switch to live]"
3. If the user has been in paper mode for fewer than 60 days, show additional warning: "We recommend at least 60 days of paper trading before going live. You have completed [X] days. [Continue anyway] [Stay in paper]"
4. Toggle state change is logged in the audit log.

#### AU-FR-022: Notification Preferences

The system SHALL allow users to configure notification channels and triggers.

**Configuration options:**
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| Telegram enabled | boolean | false | Enable Telegram notifications |
| Telegram chat ID | string | null | Chat ID for Telegram bot |
| Discord webhook URL | string | null | Discord channel webhook |
| Email digest frequency | enum [none, daily, weekly] | daily | Summary email cadence |
| Alert on fill | boolean | true | Notify when trade fills |
| Alert on trendline | boolean | true | Notify on A+ trendline detection |
| Alert on risk breach | boolean | true | Notify on risk limit hit |

**Telegram setup flow:**
1. User clicks "Connect Telegram."
2. System displays instructions: "1. Open Telegram. 2. Search for @TrendEdgeBot. 3. Send /start. 4. Copy the chat ID shown and paste it here."
3. User pastes chat ID. System sends a test message via the bot: "TrendEdge connected successfully!"
4. If test message fails: "Could not reach your Telegram. Please verify the chat ID and ensure you've started the bot."

---

### 3.4 Broker Connection Management

#### AU-FR-040: Broker Connection Data Model

The system SHALL store broker connections in a dedicated, encrypted table.

```
BrokerConnection {
  id: UUID (PK)
  user_id: UUID (FK -> users.id, NOT NULL)
  broker_type: enum ['ibkr', 'tradovate', 'webull', 'rithmic']
  display_name: string                  // e.g., "My IBKR Paper", "Tradovate Live"
  credentials_encrypted: bytea          // AES-256-GCM encrypted JSON blob
  credentials_iv: bytea                 // Initialization vector for AES
  credentials_key_id: string            // Reference to KMS key version
  status: enum ['active', 'expired', 'error', 'disconnected']
  last_connected_at: timestamptz
  last_error: text (nullable)
  account_id: string                    // Broker-specific account identifier
  is_paper: boolean                     // Paper vs. live account
  created_at: timestamptz
  updated_at: timestamptz
}
```

**Tier limits enforced at application layer:**
| Tier | Max Connections | Max Accounts |
|------|----------------|-------------|
| Free | 0 (paper only, no broker) | 1 (internal paper) |
| Trader | 1 | 1 |
| Pro | 3 | 5 |
| Team | Unlimited | 20+ |

Attempting to add a connection beyond the tier limit returns: "Your [tier] plan supports up to [N] broker connections. Upgrade to [next tier] for more. [Upgrade] [Cancel]"

#### AU-FR-041: Secure Credential Storage

The system SHALL encrypt all broker credentials at rest using AES-256-GCM.

**Encryption architecture:**
1. A master encryption key is stored in the environment (via Railway/Vercel encrypted environment variables) and NEVER in the database or source code.
2. Each broker connection generates a unique data encryption key (DEK) derived from the master key + connection ID using HKDF.
3. Credentials are serialized to JSON, then encrypted with AES-256-GCM using the DEK.
4. The encrypted blob, IV (initialization vector), and key version identifier are stored in the database.
5. On read, the DEK is re-derived and the credentials are decrypted in memory. Decrypted credentials are NEVER logged, NEVER returned in API responses, and NEVER cached.

**Credential format per broker:**
```json
// IBKR
{
  "host": "127.0.0.1",
  "port": 4002,
  "client_id": 1,
  "account": "DU1234567",
  "gateway_type": "paper|live"
}

// Tradovate
{
  "username": "...",
  "password": "...",  // encrypted within the encrypted blob
  "app_id": "...",
  "app_version": "...",
  "cid": "...",
  "sec": "...",
  "environment": "demo|live"
}

// Webull
{
  "app_key": "...",
  "app_secret": "...",
  "access_token": "...",
  "refresh_token": "...",
  "device_id": "...",
  "account_id": "..."
}
```

#### AU-FR-042: Connection Status Monitoring

The system SHALL monitor broker connection health continuously.

**Implementation:**
1. A background Celery task runs every 5 minutes for each active broker connection.
2. The health check attempts a lightweight API call to the broker (e.g., account info endpoint).
3. Status transitions:
   | From | Event | To | Action |
   |------|-------|-----|--------|
   | active | Health check succeeds | active | Update `last_connected_at` |
   | active | Health check fails (1st) | active | Log warning, retry in 1 min |
   | active | Health check fails (3 consecutive) | error | Set `last_error`, notify user |
   | active | Token expired (Tradovate/Webull) | expired | Attempt auto-refresh |
   | expired | Auto-refresh succeeds | active | Update credentials, clear error |
   | expired | Auto-refresh fails | expired | Notify user: "Re-authorize required" |
   | error | User re-authorizes | active | Clear error, reset status |
   | * | User disconnects | disconnected | Credentials retained but connection inactive |

4. Dashboard displays connection status with color indicators:
   - Green dot + "Connected" for active
   - Yellow dot + "Token expired -- re-authorize" for expired
   - Red dot + "Connection error: [last_error]" for error
   - Gray dot + "Disconnected" for disconnected

#### AU-FR-043: Multiple Broker Connections

The system SHALL support multiple broker connections per user, subject to tier limits.

**Flow (adding a new connection):**
1. User navigates to `/settings/brokers` and clicks "Add Broker Connection."
2. System checks tier limit (AU-FR-040). If at limit, show upgrade prompt.
3. User selects broker type from: Interactive Brokers, Tradovate, Webull.
4. System displays broker-specific connection form:
   - **IBKR:** IB Gateway host, port, client ID, account number. Instructions for IB Gateway setup.
   - **Tradovate:** Username, password, app credentials. OAuth flow for token generation.
   - **Webull:** App key, app secret. OAuth flow for token generation.
5. User enters credentials and clicks "Test Connection."
6. System attempts a test connection to the broker API.
7. **Success:** "Connection successful! Account: [account_id], Balance: $[balance]." User clicks "Save."
8. **Failure:** "Connection failed: [specific error]. Please verify your credentials." Common errors:
   - IBKR: "IB Gateway is not running or not reachable at [host]:[port]."
   - Tradovate: "Invalid username or password."
   - Webull: "App secret has expired. Generate a new one in the Webull developer portal."
9. On save, credentials are encrypted (AU-FR-041) and stored.
10. User can set a display name for the connection (e.g., "IBKR Paper", "Tradovate Live").

#### AU-FR-044: Broker Credential Refresh/Rotation

The system SHALL handle broker credential expiry and rotation automatically where possible.

**Tradovate token refresh:**
1. Tradovate access tokens expire every 60 minutes.
2. The system stores the refresh token and automatically requests a new access token 5 minutes before expiry.
3. If refresh fails 3 times, status transitions to `expired` and user is notified.

**Webull token refresh:**
1. Webull app secrets expire every 24 hours to 7 days (configurable in Webull portal).
2. The system cannot auto-refresh app secrets. When the secret expires, status transitions to `expired`.
3. User notification: "Your Webull connection has expired. Please generate a new app secret in the Webull developer portal and update your connection."

**IBKR:**
1. IBKR uses a persistent socket connection via IB Gateway. No token rotation required.
2. If IB Gateway restarts, the system automatically reconnects on the next health check cycle.

---

### 3.5 Row Level Security (RLS)

#### AU-FR-050: RLS Policy Architecture

The system SHALL enforce Row Level Security on ALL user-owned tables in PostgreSQL.

**Core principle:** Every table containing user data MUST have RLS enabled with policies that restrict access to rows where `user_id = auth.uid()`. No application-level filtering alone is sufficient -- RLS is the last line of defense.

**Tables requiring RLS policies:**

| Table | Policy | Phase |
|-------|--------|-------|
| users | SELECT/UPDATE own row only | 1 |
| broker_connections | All ops: `user_id = auth.uid()` | 1 |
| trades | All ops: `user_id = auth.uid()` | 1 |
| signals | All ops: `user_id = auth.uid()` | 1 |
| trendlines | All ops: `user_id = auth.uid()` | 1 |
| playbooks | All ops: `user_id = auth.uid()` | 1 |
| journal_entries | All ops: `user_id = auth.uid()` | 1 |
| api_keys | All ops: `user_id = auth.uid()` | 2 |
| teams | SELECT/UPDATE: `id = user.team_id` | 3 |
| team_members | SELECT: `team_id = user.team_id` | 3 |
| shared_playbooks | SELECT: `team_id = user.team_id` | 3 |

#### AU-FR-051: RLS Policy Implementation

The system SHALL implement the following RLS policy pattern for all user-owned tables.

**Standard user-owned table policy:**
```sql
-- Enable RLS
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;

-- Force RLS for table owner too (prevents bypassing)
ALTER TABLE trades FORCE ROW LEVEL SECURITY;

-- SELECT: users can only read their own rows
CREATE POLICY "Users can view own trades"
  ON trades FOR SELECT
  USING (user_id = auth.uid());

-- INSERT: users can only insert rows with their own user_id
CREATE POLICY "Users can insert own trades"
  ON trades FOR INSERT
  WITH CHECK (user_id = auth.uid());

-- UPDATE: users can only update their own rows
CREATE POLICY "Users can update own trades"
  ON trades FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

-- DELETE: users can only delete their own rows (soft delete preferred)
CREATE POLICY "Users can delete own trades"
  ON trades FOR DELETE
  USING (user_id = auth.uid());
```

**Apply this pattern to ALL tables listed in AU-FR-050.**

#### AU-FR-052: Admin Override Policy

The system SHALL provide admin users with controlled access to all data for support purposes.

```sql
-- Admin override for support (Phase 3)
CREATE POLICY "Admins can view all trades"
  ON trades FOR SELECT
  USING (
    user_id = auth.uid()
    OR
    EXISTS (
      SELECT 1 FROM users
      WHERE users.id = auth.uid()
      AND users.role = 'admin'
    )
  );
```

**Admin access constraints:**
1. Admin access is read-only for user data. Admins CANNOT modify user trades, journal entries, or playbooks.
2. Admin write access is limited to: user role assignment, subscription tier changes, account suspension.
3. All admin access to user data is logged in an audit table with: admin_user_id, target_user_id, action, timestamp, IP address.
4. Admin actions require re-authentication (password confirmation) if the admin session is older than 15 minutes.

#### AU-FR-053: Service Role Access

The system SHALL use a service role for backend operations that span users.

**Implementation:**
1. Background tasks (Celery workers) that need cross-user access (e.g., broker health checks across all connections) use the Supabase service role key.
2. The service role key bypasses RLS entirely.
3. The service role key is ONLY used in backend workers -- NEVER exposed to the frontend or API endpoints.
4. Service role operations are logged separately with the task name and context.

---

### 3.6 Role-Based Access Control

#### AU-FR-060: User Roles

The system SHALL enforce role-based access control with the following roles.

| Role | Scope | Description | Phase |
|------|-------|-------------|-------|
| user | Own data | Standard user. Can manage own profile, trades, playbooks, connections. | 1 |
| admin | All data | Platform administrator. Read-only access to all user data. Can manage roles, tiers, suspend accounts. | 2 |
| team_admin | Team data | Team/org administrator. Can manage team members, shared playbooks, view team analytics. | 3 |
| team_member | Own + shared | Team member. Own data + read access to shared team playbooks and aggregated team analytics. | 3 |

#### AU-FR-061: Permission Matrix

The system SHALL enforce the following permission matrix.

| Resource | user | admin | team_admin | team_member |
|----------|------|-------|-----------|-------------|
| Own profile (CRUD) | Yes | Yes | Yes | Yes |
| Own trades (CRUD) | Yes | Read | Yes | Yes |
| Own playbooks (CRUD) | Yes | Read | Yes | Yes |
| Own broker connections (CRUD) | Yes | Read | Yes | Yes |
| Own journal entries (CRUD) | Yes | Read | Yes | Yes |
| Own API keys (CRUD) | Yes | Read | Yes | Yes |
| Other users' data | No | Read | No | No |
| User role management | No | Yes | No | No |
| Subscription tier management | No | Yes | No | No |
| Account suspension | No | Yes | No | No |
| Team creation | No | Yes | Yes | No |
| Team member management | No | Yes | Yes (own team) | No |
| Shared playbooks (read) | No | Yes | Yes (own team) | Yes (own team) |
| Shared playbooks (write) | No | No | Yes (own team) | No |
| Team analytics (read) | No | Yes | Yes (own team) | Aggregated only |
| System configuration | No | Yes | No | No |

#### AU-FR-062: Role Assignment

The system SHALL provide mechanisms for role assignment.

**Rules:**
1. New users are assigned the `user` role by default.
2. The `admin` role can only be assigned by another admin or via direct database update (bootstrap).
3. The `team_admin` role is assigned when a user creates a team (Phase 3).
4. The `team_member` role is assigned when a user accepts a team invitation (Phase 3).
5. Role changes are logged in the audit table.
6. A user can have at most one role. `team_admin` and `team_member` are mutually exclusive within a team context.

---

### 3.7 Team / Organization Support (Phase 3)

#### AU-FR-070: Team Data Model

```
Team {
  id: UUID (PK)
  name: string (3-100 chars)
  slug: string (unique, URL-safe, auto-generated from name)
  owner_id: UUID (FK -> users.id)
  subscription_tier: enum ['team']
  max_members: integer (default: 5, max: 20 for Team tier)
  settings: JSONB {
    shared_instruments: string[]
    risk_parameters: {}
    require_paper_period: boolean
    paper_period_days: integer
  }
  created_at: timestamptz
  updated_at: timestamptz
}

TeamMember {
  id: UUID (PK)
  team_id: UUID (FK -> teams.id)
  user_id: UUID (FK -> users.id)
  role: enum ['team_admin', 'team_member']
  joined_at: timestamptz
  invited_by: UUID (FK -> users.id)
  invitation_status: enum ['pending', 'accepted', 'declined', 'revoked']
  invitation_email: string
  invitation_token: string (unique, for pending invitations)
  invitation_expires_at: timestamptz
}
```

#### AU-FR-071: Team Creation

The system SHALL allow users on the Team tier to create and manage teams.

**Flow:**
1. User with Team subscription navigates to `/settings/team` and clicks "Create Team."
2. User enters team name (3-100 characters, alphanumeric + spaces + hyphens).
3. System generates a URL-safe slug from the name.
4. System creates the team and assigns the creator as `team_admin`.
5. Creator's `team_id` is set on their user record.
6. **Validation:**
   - Team name already taken (by slug): "A team with a similar name already exists. Please choose a different name."
   - User already belongs to a team: "You are already a member of [team_name]. Leave that team before creating a new one."
   - User not on Team tier: "Team creation requires the Team plan ($199/mo). [Upgrade]"

#### AU-FR-072: Member Invitation Flow

The system SHALL provide a secure invitation flow for adding team members.

**Flow:**
1. Team admin navigates to `/settings/team/members` and clicks "Invite Member."
2. Admin enters the invitee's email address.
3. System checks:
   - Email is valid format.
   - Team has not reached `max_members` limit. Error: "Your team has reached its maximum of [N] members."
   - Email is not already a member or pending invitation. Error: "This email already has a pending invitation."
4. System creates a `TeamMember` record with `invitation_status: 'pending'` and generates a unique `invitation_token`.
5. System sends an invitation email: "You've been invited to join [team_name] on TrendEdge. [Accept Invitation]"
6. Invitation link: `/teams/join?token=[invitation_token]`
7. Invitation expires after 7 days.
8. **Invitee flow (existing user):**
   - Clicks link, logs in if not already.
   - Sees: "You've been invited to join [team_name] by [admin_name]. [Accept] [Decline]"
   - On accept: `invitation_status` -> `accepted`, user's `team_id` and `team_role` are set.
   - On decline: `invitation_status` -> `declined`.
9. **Invitee flow (new user):**
   - Clicks link, is directed to registration page with the invitation token preserved.
   - After registration and email verification, the invitation acceptance flow triggers automatically.
10. **Admin can revoke** pending invitations. Status -> `revoked`, link becomes invalid.

#### AU-FR-073: Role Assignment Within Teams

The system SHALL allow team admins to manage member roles.

**Capabilities:**
1. Team admin can promote a member to `team_admin` (co-admin).
2. Team admin can demote a `team_admin` to `team_member` (except the team owner).
3. Team admin can remove members from the team.
4. On removal: member's `team_id` and `team_role` are set to null. Member retains their own data.
5. Team owner cannot be removed or demoted. Team owner can transfer ownership to another admin.

#### AU-FR-074: Shared Playbooks and Analytics

The system SHALL support sharing playbooks and analytics within a team.

**Shared playbooks:**
1. Team admin can mark any of their playbooks as "shared with team."
2. Shared playbooks appear in all team members' playbook lists with a "Shared" badge.
3. Team members can use shared playbooks for trade classification but cannot edit them.
4. Team members can create their own private playbooks.

**Team analytics:**
1. Team admin can view aggregated analytics across all team members:
   - Total team P&L, win rate, average R-multiple.
   - Per-member performance summary (name, trade count, P&L, win rate).
   - Playbook performance across the team.
2. Team members can see their own analytics + aggregated team benchmarks (no individual member data).
3. All team analytics respect RLS -- aggregations are computed server-side.

---

### 3.8 User Onboarding Flow (Phase 3)

#### AU-FR-080: Welcome Wizard

The system SHALL guide new users through an onboarding wizard on first login.

**Wizard steps (4 steps):**

**Step 1: Welcome & Profile**
- Display: "Welcome to TrendEdge! Let's set up your trading system."
- Collect: display name, timezone (auto-detected from browser, editable).
- Skip: allowed (can complete later).

**Step 2: Trading Preferences**
- Display: "What do you trade?"
- Collect: default instruments (multi-select from common futures: ES, NQ, YM, CL, GC, PL, SI, HG, NG, ZB, ZN, 6E), default timeframe, risk per trade %.
- Show instrument cards with tick size, tick value, and margin requirements.
- Skip: allowed (defaults applied).

**Step 3: Broker Connection**
- Display: "Connect your broker to start trading."
- Options: "Connect Interactive Brokers", "Connect Tradovate", "Connect Webull", "Start with paper trading only."
- If user selects "Paper trading only," skip to Step 4.
- Otherwise: broker-specific connection flow (AU-FR-043).
- Skip: allowed (paper trading mode enabled by default).

**Step 4: First Playbook**
- Display: "Set up your first trading playbook."
- Options: "Use A+ Trendline Break (recommended)", "Use Standard Trendline Break", "Create custom playbook", "Skip for now."
- If selected, create the playbook with default criteria.
- Display: "You're all set! Your paper trading account is active. We recommend at least 60 days of paper trading before going live."

**Progress:**
- Progress bar at top: Step 1/4, Step 2/4, etc.
- "Skip setup" link available on every step. Clicking it marks `onboarding_completed = true` with `onboarding_step` at the current position.
- Users who skip see a persistent (dismissible) banner on the dashboard: "Complete your setup to get the most out of TrendEdge. [Continue setup]"

#### AU-FR-081: Paper Trading Mode Activation

The system SHALL default all new users to paper trading mode.

**Implementation:**
1. `paper_trading_mode` is `true` by default for all new users.
2. Paper trades are executed against simulated fills (signal price + configurable slippage).
3. Paper P&L is tracked in a separate column/flag (`trade.is_paper = true`).
4. Dashboard clearly distinguishes paper vs. live with a banner: "PAPER TRADING MODE" in orange.
5. Paper trade data is never mixed with live trade data in analytics unless the user explicitly enables a "Show paper trades" toggle.

---

### 3.9 Account Deletion & Data Export

#### AU-FR-090: Data Export

The system SHALL allow users to export all their data in machine-readable format.

**Flow:**
1. User navigates to `/settings/account` and clicks "Export my data."
2. System displays: "We'll prepare a download of all your TrendEdge data. This may take a few minutes for large accounts."
3. A background task collects all user data:
   - Profile information (JSON)
   - All trades with journal entries (CSV + JSON)
   - All playbooks with criteria (JSON)
   - All trendline detections (JSON)
   - All signals (JSON)
   - Settings and preferences (JSON)
   - API key metadata (no secrets) (JSON)
4. Data is packaged into a ZIP file and uploaded to temporary R2 storage.
5. User receives an email with a download link: "Your TrendEdge data export is ready. [Download] This link expires in 24 hours."
6. Download link expires after 24 hours and the file is deleted from R2.
7. Rate limit: 1 export request per 24 hours.

#### AU-FR-091: Account Deletion

The system SHALL allow users to permanently delete their account and all associated data.

**Flow:**
1. User navigates to `/settings/account` and clicks "Delete my account."
2. System displays a confirmation screen:
   - "This action is permanent and cannot be undone."
   - "All your data will be deleted, including: trades, journal entries, playbooks, trendlines, broker connections, API keys, and settings."
   - "Active broker connections will be disconnected."
   - "If you have an active subscription, it will be cancelled immediately with no refund for the current billing period."
3. User must type "DELETE" to confirm.
4. User must re-authenticate (enter password or confirm via OAuth).
5. **On confirmation:**
   a. Cancel any active subscription (via Stripe API).
   b. Disconnect all broker connections (revoke tokens where possible).
   c. Delete all API keys.
   d. Hard delete all user data from all tables (trades, journal_entries, playbooks, trendlines, signals, broker_connections, api_keys).
   e. Delete user avatar from R2 storage.
   f. Delete the `public.users` row.
   g. Delete the `auth.users` row via Supabase admin API (this invalidates all sessions).
6. Send confirmation email: "Your TrendEdge account has been deleted. If this was a mistake, contact support within 30 days."
7. **Grace period:** Data is soft-deleted (flagged) for 30 days before hard deletion. During this period, the user can contact support to restore their account.
8. After 30 days, a scheduled task hard-deletes all soft-deleted data.

---

### 3.10 API Key Management

#### AU-FR-100: API Key CRUD

The system SHALL allow users to create and manage API keys for webhook integrations.

**Data model:**
```
ApiKey {
  id: UUID (PK)
  user_id: UUID (FK -> users.id)
  name: string (3-50 chars)       // e.g., "TradingView Alerts"
  key_prefix: string (8 chars)     // Visible portion: "te_live_a1b2c3d4"
  key_hash: string                 // SHA-256 hash of full key
  permissions: string[]            // ['webhook:write', 'trades:read']
  last_used_at: timestamptz
  expires_at: timestamptz (nullable)
  is_active: boolean (default: true)
  created_at: timestamptz
  request_count: bigint (default: 0)
}
```

**Key generation:**
1. User navigates to `/settings/api-keys` and clicks "Create API Key."
2. User enters: name (required), expiration (optional: 30/60/90 days or never), permissions (multi-select).
3. System generates a cryptographically random 32-byte key, prefixed with `te_live_` (live) or `te_test_` (paper mode).
4. Full key format: `te_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6` (40 chars total).
5. System stores only the SHA-256 hash of the key. The plaintext key is shown ONCE.
6. Display: "Your API key has been created. Copy it now -- you won't be able to see it again."
7. Key is displayed in a copyable field with a "Copy" button.
8. After closing the dialog, only the key prefix and name are visible in the key list.

**Key validation (on webhook receipt):**
1. Incoming webhook includes the API key in the `X-API-Key` header or `api_key` query parameter.
2. System hashes the provided key with SHA-256.
3. System looks up the hash in the `api_keys` table.
4. Validation checks:
   - Key exists: if not, return HTTP 401 "Invalid API key."
   - Key is active: if not, return HTTP 401 "API key has been revoked."
   - Key is not expired: if expired, return HTTP 401 "API key has expired."
   - Key has required permission: if not, return HTTP 403 "Insufficient permissions."
5. On valid key: update `last_used_at` and increment `request_count`. Proceed with request processing.

**Key management actions:**
- **Revoke:** User clicks "Revoke" on a key. Confirmation: "Revoke API key '[name]'? Any integrations using this key will stop working. [Cancel] [Revoke]" Sets `is_active = false`.
- **Delete:** User clicks "Delete" on a revoked key. Removes the record entirely.
- **View usage:** Shows `request_count`, `last_used_at`, and a 30-day usage chart.

**Tier limits:**
| Tier | Max API Keys |
|------|-------------|
| Free | 1 |
| Trader | 5 |
| Pro | 20 |
| Team | 50 |

#### AU-FR-101: Webhook URL Generation

The system SHALL provide unique webhook URLs for TradingView integration.

**Implementation:**
1. Each API key generates a corresponding webhook URL: `https://api.trendedge.io/v1/webhooks/tradingview?api_key=te_live_...`
2. Alternatively, users can send the API key in the `X-API-Key` header (preferred for security).
3. The webhook endpoint accepts POST requests with JSON payload.
4. HMAC signature validation (optional but recommended): if the user configures a webhook secret, the system validates the `X-Signature` header using HMAC-SHA256.

---

## 4. Non-Functional Requirements

### 4.1 Performance

#### AU-NFR-001: Authentication Latency

All authentication operations (login, token validation, OAuth callback) SHALL complete within 200ms at the 95th percentile, excluding external provider latency (Google/GitHub OAuth redirect time is not counted).

| Operation | Target (p95) | Measurement |
|-----------|-------------|-------------|
| Email/password login | < 200ms | From request receipt to JWT issuance |
| Magic link generation | < 200ms | From request receipt to email queued |
| OAuth callback processing | < 200ms | From callback receipt to session created (excludes provider redirect) |
| Token refresh | < 100ms | From refresh request to new token issued |

#### AU-NFR-002: Session Validation Latency

Session validation (JWT verification on each API request) SHALL complete within 50ms at the 95th percentile. This is achieved via:
1. Local JWT signature verification (no database call for valid tokens).
2. Redis cache for user permissions and role lookups (TTL: 5 minutes).
3. Cached RLS context setting in the database connection pool.

#### AU-NFR-003: Concurrent Session Support

The system SHALL support at least 5,000 concurrent authenticated sessions without degradation.

| Metric | Target |
|--------|--------|
| Concurrent sessions | 5,000+ |
| Authentication requests/second | 100+ |
| Token refresh requests/second | 500+ |
| Session store memory (Redis) | < 500MB at 5,000 sessions |

### 4.2 Reliability

#### AU-NFR-004: Zero Unauthorized Data Access

The system SHALL ensure zero unauthorized cross-user data access.

1. RLS policies are the enforcement layer -- even if application code has a bug, RLS prevents cross-user data leakage.
2. Every database query passes through RLS.
3. No API endpoint returns data belonging to another user (except admin read-only, Phase 3).
4. Automated cross-user access tests run on every deployment (see Section 6.2).

#### AU-NFR-005: Authentication Availability

The authentication system SHALL maintain 99.9% availability (< 8.76 hours downtime per year).

1. Supabase Auth provides built-in redundancy.
2. JWT validation is stateless (works even if Supabase is temporarily unreachable, as long as tokens are not expired).
3. Refresh token rotation degrades gracefully: if Supabase is down, existing valid access tokens continue to work until expiry.

### 4.3 Scalability

#### AU-NFR-006: User Growth Support

The system SHALL scale to support the following growth targets without architectural changes.

| Phase | Users | Concurrent Sessions | Database Size |
|-------|-------|-------------------|---------------|
| Phase 1 | 1 | 1-3 | < 1GB |
| Phase 2 | 100 | 50-100 | < 10GB |
| Phase 3 | 5,000 | 2,000-5,000 | < 100GB |
| Phase 4 | 50,000 | 10,000-25,000 | < 1TB |

### 4.4 Compliance

#### AU-NFR-007: Data Privacy

The system SHALL comply with GDPR-like data privacy requirements.

1. Users can export all their data (AU-FR-090).
2. Users can delete their account and all data (AU-FR-091).
3. Broker credentials are encrypted at rest (AU-FR-041).
4. No user data is shared with third parties (except broker APIs for execution).
5. Privacy policy clearly states data collection, storage, and usage.

---

## 5. Dependencies

### 5.1 Infrastructure Dependencies (PRD-001)

| Dependency | Requirement | Impact if Missing |
|-----------|------------|------------------|
| Supabase Project | Auth, database, RLS | Cannot authenticate users or store data |
| PostgreSQL 16 | RLS policies, JSONB, triggers | No data isolation, no user storage |
| Redis (Upstash) | Session caching, rate limiting, token blacklist | Degraded performance, no rate limiting |
| Cloudflare R2 | Avatar storage, data export files | No avatars, no data export |
| Railway/Vercel | Environment variable management (encryption keys) | No secure credential storage |
| Domain + SSL | HTTPS for all auth endpoints | Insecure auth flows |
| SendGrid/Resend | Transactional email (verification, reset, invitations) | No email-based auth flows |

### 5.2 Downstream Dependencies

The following PRDs depend on this PRD being implemented first:

| PRD | Dependency | Required Features |
|-----|-----------|------------------|
| PRD-002 (Trendline Engine) | User context for per-user trendline storage | AU-FR-050 (RLS), AU-FR-010 (JWT) |
| PRD-003 (Execution Pipeline) | Broker credentials, user identity for orders | AU-FR-040-044, AU-FR-010 |
| PRD-004 (Journaling) | User identity for trade ownership | AU-FR-050, AU-FR-010 |
| PRD-005 (Playbooks) | User identity, team sharing | AU-FR-050, AU-FR-074 |
| PRD-006 (Analytics) | User identity for data scoping | AU-FR-050, AU-FR-010 |
| PRD-009 (Notifications) | Notification preferences, Telegram setup | AU-FR-022 |
| PRD-010 (Integrations) | API keys for webhooks | AU-FR-100, AU-FR-101 |
| PRD-011 (Billing) | User identity, subscription tier | AU-FR-060, User Model |

---

## 6. Testing Requirements

### 6.1 Auth Flow Testing

#### AU-TEST-001: Registration Testing

| Test Case | Input | Expected Outcome |
|-----------|-------|-----------------|
| Valid registration | valid email, strong password | Account created, verification email sent, user row in public.users |
| Duplicate email | existing email | Error message (generic in production), no duplicate account |
| Weak password | "password" | Validation error with specific requirements |
| Invalid email format | "not-an-email" | "Please enter a valid email address" |
| Empty fields | empty email or password | Field-level validation errors |
| SQL injection in email | `'; DROP TABLE users;--` | Input rejected, no SQL execution |
| XSS in display name | `<script>alert('xss')</script>` | Input sanitized, script not executed |

#### AU-TEST-002: Login Testing

| Test Case | Input | Expected Outcome |
|-----------|-------|-----------------|
| Valid email/password login | correct credentials | JWT issued, session created, redirect to dashboard |
| Invalid password | correct email, wrong password | "Invalid email or password" (generic) |
| Non-existent email | unregistered email | "Invalid email or password" (same message) |
| Unverified email login | correct credentials, unverified | Login succeeds, verification banner shown, features restricted |
| Magic link login | valid email | Magic link email sent, "Check your email" message |
| Expired magic link | link older than 1 hour | "This link has expired" with resend option |
| Google OAuth login | valid Google account | Session created, redirect to dashboard |
| GitHub OAuth login | valid GitHub account | Session created, redirect to dashboard |
| OAuth consent denied | user cancels on provider | Redirect to login with cancellation message |

#### AU-TEST-003: Password Reset Testing

| Test Case | Input | Expected Outcome |
|-----------|-------|-----------------|
| Valid reset request | registered email | Reset email sent, generic success message |
| Non-existent email reset | unregistered email | Same generic success message (no info leak) |
| Valid reset token | valid token, strong password | Password updated, all sessions invalidated |
| Expired reset token | expired token | "This link has expired" with request new link |
| Reused reset token | already-used token | "This link has already been used" |
| Same password reset | current password | "New password must be different from your current password" |

### 6.2 RLS Policy Testing

#### AU-TEST-010: Cross-User Access Testing

These tests MUST run on every deployment to verify data isolation.

| Test Case | Method | Expected Outcome |
|-----------|--------|-----------------|
| User A reads User B's trades | Authenticate as User A, query trades with User B's trade ID | Empty result set (0 rows) |
| User A updates User B's playbook | Authenticate as User A, UPDATE with User B's playbook ID | 0 rows affected |
| User A deletes User B's trendline | Authenticate as User A, DELETE with User B's trendline ID | 0 rows affected |
| User A inserts trade with User B's user_id | Authenticate as User A, INSERT with user_id = User B | RLS violation error |
| Direct SQL without auth context | Query without setting JWT claim | RLS blocks all rows |
| Service role access | Use service role key | Full access (intentional, for background tasks) |
| Admin reads User B's trades | Authenticate as admin, query User B's trades | Rows returned (Phase 3 only) |
| Admin updates User B's trades | Authenticate as admin, UPDATE User B's trades | 0 rows affected (admin is read-only on user data) |

**Automated test script (runs in CI/CD):**
```python
def test_rls_cross_user_isolation():
    """Verify User A cannot access User B's data across all tables."""
    tables = ['trades', 'signals', 'trendlines', 'playbooks',
              'journal_entries', 'broker_connections', 'api_keys']

    for table in tables:
        # Authenticate as User A
        client_a = create_authenticated_client(user_a_token)

        # Attempt to read User B's data
        result = client_a.from_(table).select('*').eq('user_id', user_b_id).execute()
        assert len(result.data) == 0, f"User A accessed User B's {table}"

        # Attempt to read by specific ID belonging to User B
        result = client_a.from_(table).select('*').eq('id', user_b_record_id).execute()
        assert len(result.data) == 0, f"User A accessed User B's {table} by ID"
```

### 6.3 Session Management Testing

#### AU-TEST-020: Session Lifecycle Testing

| Test Case | Setup | Expected Outcome |
|-----------|-------|-----------------|
| Token expiry | Wait 15+ minutes without refresh | API requests return 401, client auto-refreshes |
| Refresh token rotation | Refresh token used | Old refresh token invalidated, new one issued |
| Stolen refresh token detection | Use previously-invalidated refresh token | All sessions revoked, security email sent |
| Inactivity timeout | No interaction for 30 minutes | User signed out, redirect to login |
| Multi-device login | Login from two browsers | Both sessions active simultaneously |
| Session revocation | Revoke session from device A | Device A's next request returns 401 |
| Password change invalidation | Change password | All other sessions invalidated |

### 6.4 Credential Encryption Testing

#### AU-TEST-030: Encryption Verification

| Test Case | Method | Expected Outcome |
|-----------|--------|-----------------|
| Credentials encrypted at rest | Direct database query on broker_connections | `credentials_encrypted` column is binary, not readable JSON |
| Credentials decrypt correctly | Decrypt via application layer | Original credential JSON restored |
| Key rotation | Rotate master key | All credentials re-encrypted, old key invalid |
| Tampered ciphertext | Modify encrypted bytes | Decryption fails with authentication error (GCM tag mismatch) |
| Missing IV | Remove IV from record | Decryption fails gracefully |
| Direct API response check | GET /api/broker-connections | Response contains status, name, type -- NEVER credentials |

### 6.5 Penetration Testing Checklist

#### AU-TEST-040: Security Testing

| Category | Test | Pass Criteria |
|----------|------|--------------|
| Authentication Bypass | Attempt API access without token | HTTP 401 on all protected endpoints |
| Token Manipulation | Modify JWT payload (change user_id) | Signature verification fails, HTTP 401 |
| Privilege Escalation | Change role claim in JWT | Signature verification fails; role checked from DB, not JWT |
| SQL Injection | Inject SQL in all input fields | No SQL execution; parameterized queries only |
| XSS | Inject scripts in profile fields, notes | Input sanitized; Content-Security-Policy headers block execution |
| CSRF | Cross-origin POST to state-changing endpoints | CSRF token validation fails; SameSite cookies block |
| Session Fixation | Attempt to set session token before auth | Token regenerated on login; old token invalid |
| Brute Force | >10 login attempts in 1 minute | Account temporarily locked, rate limit response |
| Credential Exposure | Search logs, error messages, API responses | No credentials, tokens, or secrets in any output |
| RLS Bypass | Attempt direct database queries via exposed Supabase URL | RLS blocks all unauthorized access |
| IDOR | Access resources by guessing/iterating IDs | RLS + ownership check prevents access |

### 6.6 OWASP Authentication Testing

#### AU-TEST-050: OWASP Compliance

Based on OWASP Testing Guide v4.0, Authentication Testing section.

| OWASP Test ID | Test Name | Implementation |
|--------------|-----------|----------------|
| OTG-AUTHN-001 | Credentials transported over encrypted channel | All auth endpoints require HTTPS; HSTS header set |
| OTG-AUTHN-002 | Default credentials | No default accounts; admin bootstrap requires manual DB insert |
| OTG-AUTHN-003 | Account lockout mechanism | 10 failed attempts -> 15-minute lockout; 50 attempts -> 1-hour lockout |
| OTG-AUTHN-004 | Authentication bypass | Every API route has auth middleware; no unprotected state-changing endpoints |
| OTG-AUTHN-005 | Remember me / session timeout | Refresh tokens (7 days), inactivity timeout (30 min), max session age (30 days) |
| OTG-AUTHN-006 | Browser cache weaknesses | `Cache-Control: no-store` on all auth responses |
| OTG-AUTHN-007 | Password policy | 8+ chars, uppercase, lowercase, number, special char |
| OTG-AUTHN-008 | Security question/answer | Not used; magic link provides passwordless recovery |
| OTG-AUTHN-009 | Password change | Requires current password; all sessions invalidated |
| OTG-AUTHN-010 | HTTP Authentication | Not used; JWT Bearer tokens only |

---

## 7. Security

This is the most security-critical PRD in the TrendEdge platform. A compromise here can lead to direct financial loss for users.

### 7.1 Credential Encryption

#### AU-SEC-001: AES-256-GCM Encryption at Rest

All broker API credentials SHALL be encrypted using AES-256-GCM before storage.

**Implementation details:**
1. **Algorithm:** AES-256-GCM (Galois/Counter Mode) provides both confidentiality and authenticity.
2. **Master Key:** 256-bit key stored in Railway/Vercel encrypted environment variables. Key name: `BROKER_ENCRYPTION_MASTER_KEY`.
3. **Key Derivation:** Per-connection DEK derived using HKDF-SHA256 with the connection ID as context. This ensures each connection has a unique encryption key.
4. **IV Generation:** 96-bit (12-byte) cryptographically random IV generated per encryption operation using `os.urandom(12)`.
5. **Authentication Tag:** 128-bit GCM authentication tag stored with the ciphertext to detect tampering.
6. **Key Rotation:** When the master key is rotated, a background task re-encrypts all existing credentials with the new key. Both old and new keys are valid during the rotation window (max 24 hours).

**Python implementation reference:**
```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
import os, json

def encrypt_credentials(credentials: dict, master_key: bytes, connection_id: str) -> tuple[bytes, bytes]:
    """Encrypt broker credentials. Returns (ciphertext, iv)."""
    # Derive per-connection key
    dek = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=connection_id.encode(),
    ).derive(master_key)

    iv = os.urandom(12)
    plaintext = json.dumps(credentials).encode('utf-8')
    aesgcm = AESGCM(dek)
    ciphertext = aesgcm.encrypt(iv, plaintext, None)  # GCM tag appended automatically
    return ciphertext, iv

def decrypt_credentials(ciphertext: bytes, iv: bytes, master_key: bytes, connection_id: str) -> dict:
    """Decrypt broker credentials. Raises InvalidTag if tampered."""
    dek = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=connection_id.encode(),
    ).derive(master_key)

    aesgcm = AESGCM(dek)
    plaintext = aesgcm.decrypt(iv, ciphertext, None)
    return json.loads(plaintext.decode('utf-8'))
```

### 7.2 Broker API Key Storage Strategy

#### AU-SEC-002: Credential Lifecycle

| Stage | Security Measure |
|-------|-----------------|
| Input | Credentials entered over HTTPS. TLS 1.3 enforced. |
| Transit | Encrypted in transit via HTTPS. Never transmitted in query parameters. |
| Processing | Decrypted in memory only when needed for broker API calls. Memory is not swapped to disk (mlock where supported). |
| Storage | AES-256-GCM encrypted in PostgreSQL `bytea` column. |
| Display | NEVER displayed in API responses, UI, or logs. Masked format only: `****...a1b2`. |
| Deletion | Securely overwritten in memory after use. Database record hard-deleted on account deletion. |
| Logging | Credentials are NEVER logged at any log level. Log sanitization middleware strips any detected credential patterns. |

### 7.3 Rate Limiting

#### AU-SEC-003: Rate Limiting on Auth Endpoints

The system SHALL enforce rate limits on all authentication endpoints to prevent abuse.

| Endpoint | Rate Limit | Window | Lockout |
|----------|-----------|--------|---------|
| POST /auth/register | 5 requests | per IP per hour | 1 hour block |
| POST /auth/login | 10 requests | per IP per minute | 15 min block after 10 failures |
| POST /auth/login (per account) | 10 requests | per email per 15 min | 15 min block after 10 failures; 1 hour after 50 |
| POST /auth/magic-link | 3 requests | per email per 15 min | 15 min block |
| POST /auth/reset-password | 3 requests | per email per hour | 1 hour block |
| POST /auth/verify-email/resend | 3 requests | per email per hour | 1 hour block |
| POST /v1/webhooks/* | 60 requests | per API key per minute | 1 min block; key auto-disabled after 1000/hr |
| GET /api/* (authenticated) | 120 requests | per user per minute | 1 min block |

**Implementation:**
1. Rate limiting is implemented using Redis with sliding window counters.
2. Rate limit headers are returned on every response: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
3. Exceeded rate limit returns HTTP 429 with body: `{"error": "rate_limit_exceeded", "retry_after": <seconds>}`.

### 7.4 Brute Force Protection

#### AU-SEC-004: Account Lockout

The system SHALL protect against brute force login attempts.

**Lockout policy:**
1. After 5 consecutive failed login attempts for a given email: display CAPTCHA (hCaptcha).
2. After 10 consecutive failed attempts: lock account for 15 minutes. Display: "Account temporarily locked. Try again in 15 minutes or use a magic link."
3. After 50 consecutive failed attempts (across lockout periods): lock account for 1 hour and send email notification: "Multiple failed login attempts detected on your TrendEdge account. If this wasn't you, reset your password immediately."
4. Failed attempt counter resets on successful login.
5. Lockout is per-email, not per-IP (prevents attackers from using different IPs).

**IP-based protection:**
1. After 20 failed login attempts from a single IP (any email): temporary IP block for 15 minutes.
2. After 100 failed attempts from a single IP per hour: IP block for 1 hour.
3. IP blocks are logged and reviewed daily.

### 7.5 CSRF Protection

#### AU-SEC-005: CSRF Prevention

The system SHALL prevent Cross-Site Request Forgery attacks.

**Implementation:**
1. **SameSite cookies:** All auth cookies are set with `SameSite=Lax` (prevents CSRF on cross-origin POST requests).
2. **CSRF tokens:** For any state-changing requests from server-rendered forms (if any), include a CSRF token in a hidden field and validate it server-side.
3. **Origin/Referer validation:** The FastAPI backend validates the `Origin` header on all state-changing requests. Only requests from `https://app.trendedge.io` and `https://trendedge.io` are accepted.
4. **API requests:** JWT Bearer token in Authorization header provides implicit CSRF protection (tokens are not automatically sent by browsers in cross-origin requests).

### 7.6 XSS Prevention

#### AU-SEC-006: Cross-Site Scripting Prevention

The system SHALL prevent XSS attacks.

**Implementation:**
1. **Content Security Policy (CSP) headers:**
   ```
   Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-{random}'; style-src 'self' 'unsafe-inline'; img-src 'self' https://r2.trendedge.io; connect-src 'self' https://api.trendedge.io wss://api.trendedge.io; frame-ancestors 'none';
   ```
2. **Input sanitization:** All user-provided text is sanitized before storage using a server-side HTML sanitizer (e.g., `bleach` in Python). Only plain text is stored for profile fields. Journal entry notes allow limited Markdown (no raw HTML).
3. **Output encoding:** All user-provided content rendered in the frontend uses React's default JSX escaping. `dangerouslySetInnerHTML` is NEVER used with user content.
4. **HTTP headers:**
   ```
   X-Content-Type-Options: nosniff
   X-Frame-Options: DENY
   X-XSS-Protection: 0  (deprecated, CSP is preferred)
   Referrer-Policy: strict-origin-when-cross-origin
   ```

### 7.7 Session Fixation Prevention

#### AU-SEC-007: Session Fixation Prevention

The system SHALL prevent session fixation attacks.

**Implementation:**
1. On every successful authentication (login, OAuth callback, magic link), a new session token is generated. Any pre-existing session token is invalidated.
2. Session tokens are NEVER accepted from URL parameters or form fields -- only from HTTP-only cookies or Authorization headers.
3. Session tokens are bound to the user agent string. If the user agent changes, the session is invalidated.
4. Session tokens are regenerated after any privilege change (e.g., email verification, role change).

### 7.8 Additional Security Measures

#### AU-SEC-008: Security Headers

All responses from the application SHALL include the following security headers.

| Header | Value | Purpose |
|--------|-------|---------|
| Strict-Transport-Security | max-age=31536000; includeSubDomains; preload | Force HTTPS |
| Content-Security-Policy | (see AU-SEC-006) | Prevent XSS |
| X-Content-Type-Options | nosniff | Prevent MIME sniffing |
| X-Frame-Options | DENY | Prevent clickjacking |
| Referrer-Policy | strict-origin-when-cross-origin | Limit referrer leakage |
| Permissions-Policy | camera=(), microphone=(), geolocation=() | Disable unused APIs |

#### AU-SEC-009: Audit Logging

All security-relevant events SHALL be logged in an immutable audit log.

**Events logged:**
| Event | Data Captured |
|-------|-------------|
| User registration | user_id, email (hashed), IP, user_agent, timestamp |
| Login (success) | user_id, method (password/magic-link/oauth), IP, user_agent, timestamp |
| Login (failure) | email (hashed), method, IP, user_agent, failure_reason, timestamp |
| Password reset request | email (hashed), IP, timestamp |
| Password change | user_id, IP, timestamp |
| Email change | user_id, old_email (hashed), new_email (hashed), timestamp |
| Broker connection added | user_id, broker_type, is_paper, timestamp |
| Broker connection removed | user_id, broker_type, connection_id, timestamp |
| API key created | user_id, key_prefix, permissions, timestamp |
| API key revoked | user_id, key_prefix, timestamp |
| Role change | user_id, old_role, new_role, changed_by, timestamp |
| Account deletion | user_id, timestamp |
| Admin access to user data | admin_id, target_user_id, action, timestamp |
| Session revoked | user_id, session_id, revoked_by (self or admin), timestamp |
| Rate limit triggered | IP, endpoint, count, timestamp |

**Storage:** Audit logs are stored in a separate `audit_logs` table with no UPDATE or DELETE policies (append-only). RLS policy: users can read only their own audit entries. Admins can read all. Retention: 2 years.

---

## 8. Phase Mapping

### Phase 1: Single-User Basic Auth (Weeks 1-2)

**Goal:** Working authentication for a single developer user. Security foundations in place from day one.

| Requirement | ID | Priority | Notes |
|------------|-----|----------|-------|
| Email/password registration | AU-FR-001 | P0 | Single user; can be seeded via SQL |
| JWT token handling | AU-FR-010 | P0 | Supabase client SDK handles this |
| Refresh token rotation | AU-FR-011 | P0 | Built into Supabase |
| Session expiry (basic) | AU-FR-012 | P0 | Default Supabase settings |
| Profile CRUD (basic) | AU-FR-020 | P1 | Name, timezone, trading prefs |
| Trading preferences | AU-FR-021 | P0 | Required for execution pipeline |
| RLS policies (all tables) | AU-FR-050-051 | P0 | Critical: RLS from day one, even for single user |
| User role (user only) | AU-FR-060 | P0 | Single role, no admin UI |
| Broker connection model | AU-FR-040 | P0 | Required for execution pipeline |
| Credential encryption | AU-FR-041 | P0 | Security requirement |
| Connection status (basic) | AU-FR-042 | P1 | Manual check acceptable |
| Broker connection (IBKR) | AU-FR-043 | P0 | MVP broker |
| Broker connection (Tradovate) | AU-FR-043 | P0 | MVP broker |

**Definition of Done (Phase 1):**
- Can register and log in with email/password.
- JWT tokens are issued and validated on all API requests.
- User profile with trading preferences is stored and retrievable.
- At least one broker connection can be added with encrypted credentials.
- RLS policies are enabled on all tables and passing cross-user tests (even though there is only one user, the policies must be in place).
- All RLS tests pass in CI.

### Phase 2: Full Auth Flows (Weeks 9-14)

**Goal:** Production-ready authentication for beta users. All auth methods, session management, and security hardening.

| Requirement | ID | Priority | Notes |
|------------|-----|----------|-------|
| Magic link authentication | AU-FR-002 | P0 | Required for passwordless login |
| Google OAuth | AU-FR-003 | P0 | Primary OAuth provider |
| GitHub OAuth | AU-FR-004 | P1 | Developer persona |
| Email verification | AU-FR-005 | P0 | Required before broker connections |
| Password reset | AU-FR-006 | P0 | Required for production |
| Multi-device session management | AU-FR-013 | P1 | View and revoke sessions |
| Profile CRUD (full) | AU-FR-020 | P0 | Avatar, email change |
| Notification preferences | AU-FR-022 | P0 | Telegram, Discord, email |
| Multiple broker connections | AU-FR-043 | P0 | Pro tier feature |
| Broker credential refresh | AU-FR-044 | P0 | Tradovate/Webull auto-refresh |
| Admin role | AU-FR-060-062 | P1 | Support access |
| API key management | AU-FR-100 | P0 | Required for TradingView webhooks |
| Webhook URL generation | AU-FR-101 | P0 | Required for TradingView webhooks |
| Rate limiting | AU-SEC-003 | P0 | Security requirement |
| Brute force protection | AU-SEC-004 | P0 | Security requirement |
| CSRF protection | AU-SEC-005 | P0 | Security requirement |
| XSS prevention | AU-SEC-006 | P0 | Security requirement |
| Session fixation prevention | AU-SEC-007 | P0 | Security requirement |
| Security headers | AU-SEC-008 | P0 | Security requirement |
| Audit logging | AU-SEC-009 | P0 | Security requirement |
| All penetration tests pass | AU-TEST-040 | P0 | Security gate |
| OWASP compliance verified | AU-TEST-050 | P0 | Security gate |

**Definition of Done (Phase 2):**
- Users can register and log in via email/password, magic link, Google, and GitHub.
- Email verification is enforced.
- Password reset flow works end-to-end.
- Users can view and revoke sessions across devices.
- Multiple broker connections work with tier enforcement.
- API keys can be created, used for webhooks, and revoked.
- All rate limiting and brute force protection is active.
- All security headers are present on every response.
- Penetration test checklist is fully passing.
- Audit log captures all security events.

### Phase 3: Multi-Tenant + Teams + Onboarding (Weeks 15-22)

**Goal:** SaaS-ready multi-tenant platform with team support and user onboarding.

| Requirement | ID | Priority | Notes |
|------------|-----|----------|-------|
| Team creation | AU-FR-071 | P0 | Core Team tier feature |
| Member invitation flow | AU-FR-072 | P0 | Team growth |
| Team role assignment | AU-FR-073 | P0 | Admin vs. member |
| Shared playbooks | AU-FR-074 | P0 | Key team value prop |
| Team analytics | AU-FR-074 | P1 | Aggregated team view |
| Admin override policies | AU-FR-052 | P0 | Support access |
| Welcome wizard | AU-FR-080 | P0 | Reduce time-to-value |
| Paper trading activation | AU-FR-081 | P0 | Safe default |
| Data export | AU-FR-090 | P0 | GDPR compliance |
| Account deletion | AU-FR-091 | P0 | GDPR compliance |
| Team RLS policies | AU-FR-050 | P0 | Team data isolation |

**Definition of Done (Phase 3):**
- Teams can be created, members invited and managed.
- Team admins can share playbooks and view aggregated team analytics.
- Team members see only their own data plus shared resources.
- New users are guided through the onboarding wizard.
- Users can export all their data as a ZIP file.
- Users can delete their account with 30-day grace period.
- Team RLS policies prevent cross-team data access.
- All existing Phase 1 and Phase 2 tests continue to pass.

---

## 9. Acceptance Criteria

### 9.1 Phase 1 Acceptance Criteria

| ID | Criterion | Verification Method |
|----|----------|-------------------|
| AC-001 | A user can register with email/password and receive a JWT token | Automated test: POST /auth/register returns 201 with token |
| AC-002 | A registered user can log in and access the dashboard | Automated test: POST /auth/login returns 200 with token; GET /api/profile returns 200 |
| AC-003 | JWT tokens expire after 15 minutes and auto-refresh | Automated test: Wait 16 min, verify 401, verify client auto-refreshes |
| AC-004 | User profile with trading preferences can be read and updated | Automated test: GET/PATCH /api/profile |
| AC-005 | Broker credentials are encrypted at rest with AES-256-GCM | Automated test: Direct DB query shows binary data, not JSON |
| AC-006 | RLS prevents User A from reading User B's data on ALL tables | Automated test: AU-TEST-010 cross-user access test suite (all tables, all operations) |
| AC-007 | An IBKR broker connection can be added and tested | Manual test: Add IBKR paper connection, verify status = active |
| AC-008 | A Tradovate broker connection can be added and tested | Manual test: Add Tradovate demo connection, verify status = active |
| AC-009 | API responses never contain decrypted broker credentials | Automated test: GET /api/broker-connections response schema validation |
| AC-010 | User model matches specification with all default values | Automated test: New user has correct defaults for all settings fields |

### 9.2 Phase 2 Acceptance Criteria

| ID | Criterion | Verification Method |
|----|----------|-------------------|
| AC-020 | Magic link login works end-to-end | E2E test: Request magic link, extract from email, click, verify dashboard |
| AC-021 | Google OAuth login creates/links account correctly | E2E test: OAuth flow with test Google account |
| AC-022 | GitHub OAuth login creates/links account correctly | E2E test: OAuth flow with test GitHub account |
| AC-023 | Unverified users cannot connect brokers or execute trades | Automated test: POST /api/broker-connections returns 403 for unverified user |
| AC-024 | Password reset invalidates all existing sessions | Automated test: Reset password, verify old token returns 401 |
| AC-025 | Users can view active sessions with device/location info | Automated test: GET /api/sessions returns session list with metadata |
| AC-026 | Users can revoke sessions on other devices | Automated test: Revoke session, verify that device's token returns 401 |
| AC-027 | API keys can be created, used for webhooks, and revoked | Automated test: Create key, POST webhook with key succeeds, revoke, POST fails with 401 |
| AC-028 | Rate limiting blocks excessive login attempts | Automated test: 11th login attempt in 1 min returns 429 |
| AC-029 | Brute force protection locks account after 10 failures | Automated test: 10 failures, 11th attempt returns 423 (locked) |
| AC-030 | All security headers present on every response | Automated test: Check response headers on 10 random endpoints |
| AC-031 | Audit log captures all security events | Automated test: Perform login/logout/password-change/key-create, verify audit entries |
| AC-032 | Authentication latency < 200ms (p95) | Load test: 100 concurrent login requests, measure p95 latency |
| AC-033 | Session validation latency < 50ms (p95) | Load test: 1000 concurrent authenticated requests, measure p95 validation time |
| AC-034 | Tier limits enforced for broker connections and API keys | Automated test: Free user cannot add broker; Trader user cannot add 2nd broker |
| AC-035 | OWASP authentication test checklist fully passing | Manual + automated: AU-TEST-050 all rows verified |

### 9.3 Phase 3 Acceptance Criteria

| ID | Criterion | Verification Method |
|----|----------|-------------------|
| AC-040 | Team admin can create a team and invite members | E2E test: Create team, send invitation, accept invitation |
| AC-041 | Invited member receives email, accepts, and joins team | E2E test: Verify email delivery, link click, role assignment |
| AC-042 | Team member can see shared playbooks but not edit them | Automated test: GET shared playbook succeeds, PATCH returns 403 |
| AC-043 | Team member cannot see other members' individual trades | Automated test: Cross-member trade query returns 0 rows |
| AC-044 | Team admin can view aggregated team analytics | Automated test: GET /api/team/analytics returns aggregated data |
| AC-045 | New users see onboarding wizard on first login | E2E test: Register, login, verify wizard renders at step 1 |
| AC-046 | Onboarding wizard can be completed or skipped at any step | E2E test: Complete all 4 steps; separately, skip at step 2 |
| AC-047 | Data export produces a valid ZIP with all user data | Automated test: Request export, download ZIP, verify JSON/CSV contents match database |
| AC-048 | Account deletion removes all user data after grace period | Automated test: Delete account, verify soft delete, advance 30 days, verify hard delete |
| AC-049 | Account deletion cancels subscription and disconnects brokers | Automated test: Delete account, verify Stripe subscription cancelled, broker tokens revoked |
| AC-050 | System supports 5,000 concurrent sessions without degradation | Load test: Simulate 5,000 sessions, verify p95 response times within SLA |

---

## Appendix A: API Endpoint Summary

| Method | Endpoint | Auth | Description | Phase |
|--------|----------|------|-------------|-------|
| POST | /auth/register | Public | Email/password registration | 1 |
| POST | /auth/login | Public | Email/password login | 1 |
| POST | /auth/magic-link | Public | Request magic link | 2 |
| GET | /auth/callback | Public | OAuth/magic link callback | 2 |
| POST | /auth/reset-password | Public | Request password reset | 2 |
| POST | /auth/update-password | Authenticated | Set new password (reset flow) | 2 |
| POST | /auth/logout | Authenticated | Sign out current session | 1 |
| GET | /api/profile | Authenticated | Get user profile | 1 |
| PATCH | /api/profile | Authenticated | Update user profile | 1 |
| POST | /api/profile/avatar | Authenticated | Upload avatar | 2 |
| GET | /api/sessions | Authenticated | List active sessions | 2 |
| DELETE | /api/sessions/:id | Authenticated | Revoke a session | 2 |
| DELETE | /api/sessions | Authenticated | Revoke all other sessions | 2 |
| GET | /api/broker-connections | Authenticated | List broker connections | 1 |
| POST | /api/broker-connections | Authenticated | Add broker connection | 1 |
| POST | /api/broker-connections/:id/test | Authenticated | Test broker connection | 1 |
| PATCH | /api/broker-connections/:id | Authenticated | Update broker connection | 1 |
| DELETE | /api/broker-connections/:id | Authenticated | Remove broker connection | 1 |
| GET | /api/api-keys | Authenticated | List API keys | 2 |
| POST | /api/api-keys | Authenticated | Create API key | 2 |
| DELETE | /api/api-keys/:id | Authenticated | Revoke API key | 2 |
| POST | /v1/webhooks/tradingview | API Key | TradingView webhook receiver | 2 |
| POST | /api/teams | Authenticated | Create team | 3 |
| GET | /api/teams/:id | Authenticated | Get team details | 3 |
| PATCH | /api/teams/:id | Authenticated | Update team settings | 3 |
| POST | /api/teams/:id/invite | Authenticated | Invite team member | 3 |
| POST | /api/teams/join | Authenticated | Accept team invitation | 3 |
| DELETE | /api/teams/:id/members/:userId | Authenticated | Remove team member | 3 |
| GET | /api/teams/:id/analytics | Authenticated | Get team analytics | 3 |
| POST | /api/account/export | Authenticated | Request data export | 3 |
| DELETE | /api/account | Authenticated | Delete account | 3 |

## Appendix B: Environment Variables

| Variable | Description | Required | Phase |
|----------|------------|----------|-------|
| `SUPABASE_URL` | Supabase project URL | Yes | 1 |
| `SUPABASE_ANON_KEY` | Supabase anonymous (public) key | Yes | 1 |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (bypasses RLS) | Yes | 1 |
| `SUPABASE_JWT_SECRET` | JWT secret for signature verification | Yes | 1 |
| `BROKER_ENCRYPTION_MASTER_KEY` | AES-256 master key for broker credentials | Yes | 1 |
| `REDIS_URL` | Redis connection URL for caching and rate limiting | Yes | 1 |
| `R2_BUCKET_URL` | Cloudflare R2 bucket URL for file storage | Yes | 2 |
| `R2_ACCESS_KEY_ID` | R2 access key | Yes | 2 |
| `R2_SECRET_ACCESS_KEY` | R2 secret key | Yes | 2 |
| `SENDGRID_API_KEY` | SendGrid API key for transactional email | Yes | 2 |
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth client ID | Yes | 2 |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth client secret | Yes | 2 |
| `GITHUB_OAUTH_CLIENT_ID` | GitHub OAuth client ID | Yes | 2 |
| `GITHUB_OAUTH_CLIENT_SECRET` | GitHub OAuth client secret | Yes | 2 |
| `HCAPTCHA_SITE_KEY` | hCaptcha site key for brute force protection | Yes | 2 |
| `HCAPTCHA_SECRET_KEY` | hCaptcha secret key | Yes | 2 |
| `APP_DOMAIN` | Application domain for CORS/origin validation | Yes | 2 |

## Appendix C: Database Schema (SQL)

```sql
-- Users table (extends Supabase auth.users)
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    display_name TEXT,
    avatar_url TEXT,
    timezone TEXT NOT NULL DEFAULT 'America/New_York',
    subscription_tier TEXT NOT NULL DEFAULT 'free'
        CHECK (subscription_tier IN ('free', 'trader', 'pro', 'team')),
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    role TEXT NOT NULL DEFAULT 'user'
        CHECK (role IN ('user', 'admin')),
    team_id UUID REFERENCES public.teams(id) ON DELETE SET NULL,
    team_role TEXT CHECK (team_role IN ('team_admin', 'team_member')),
    onboarding_completed BOOLEAN NOT NULL DEFAULT false,
    onboarding_step INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

-- Broker connections table
CREATE TABLE public.broker_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    broker_type TEXT NOT NULL
        CHECK (broker_type IN ('ibkr', 'tradovate', 'webull', 'rithmic')),
    display_name TEXT NOT NULL,
    credentials_encrypted BYTEA NOT NULL,
    credentials_iv BYTEA NOT NULL,
    credentials_key_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'disconnected'
        CHECK (status IN ('active', 'expired', 'error', 'disconnected')),
    last_connected_at TIMESTAMPTZ,
    last_error TEXT,
    account_id TEXT,
    is_paper BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- API keys table
CREATE TABLE public.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key_prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    permissions TEXT[] NOT NULL DEFAULT '{}',
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_count BIGINT NOT NULL DEFAULT 0
);

-- Teams table (Phase 3)
CREATE TABLE public.teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    owner_id UUID NOT NULL REFERENCES public.users(id),
    max_members INTEGER NOT NULL DEFAULT 5,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Team members table (Phase 3)
CREATE TABLE public.team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES public.teams(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'team_member'
        CHECK (role IN ('team_admin', 'team_member')),
    joined_at TIMESTAMPTZ,
    invited_by UUID REFERENCES public.users(id),
    invitation_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (invitation_status IN ('pending', 'accepted', 'declined', 'revoked')),
    invitation_email TEXT NOT NULL,
    invitation_token TEXT UNIQUE,
    invitation_expires_at TIMESTAMPTZ
);

-- Audit logs table (append-only)
CREATE TABLE public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_broker_connections_user_id ON public.broker_connections(user_id);
CREATE INDEX idx_broker_connections_status ON public.broker_connections(status);
CREATE INDEX idx_api_keys_user_id ON public.api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON public.api_keys(key_hash);
CREATE INDEX idx_api_keys_is_active ON public.api_keys(is_active);
CREATE INDEX idx_team_members_team_id ON public.team_members(team_id);
CREATE INDEX idx_team_members_user_id ON public.team_members(user_id);
CREATE INDEX idx_team_members_invitation_token ON public.team_members(invitation_token);
CREATE INDEX idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON public.audit_logs(event_type);
CREATE INDEX idx_audit_logs_created_at ON public.audit_logs(created_at);
CREATE INDEX idx_users_team_id ON public.users(team_id);
CREATE INDEX idx_users_deleted_at ON public.users(deleted_at);

-- RLS Policies
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users FORCE ROW LEVEL SECURITY;
ALTER TABLE public.broker_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.broker_connections FORCE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys FORCE ROW LEVEL SECURITY;
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.teams FORCE ROW LEVEL SECURITY;
ALTER TABLE public.team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_members FORCE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs FORCE ROW LEVEL SECURITY;

-- Users: can only read/update own row
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (id = auth.uid());
CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (id = auth.uid()) WITH CHECK (id = auth.uid());

-- Broker connections: full CRUD on own rows
CREATE POLICY "Users can view own broker connections" ON public.broker_connections
    FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can insert own broker connections" ON public.broker_connections
    FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "Users can update own broker connections" ON public.broker_connections
    FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY "Users can delete own broker connections" ON public.broker_connections
    FOR DELETE USING (user_id = auth.uid());

-- API keys: full CRUD on own rows
CREATE POLICY "Users can view own API keys" ON public.api_keys
    FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can insert own API keys" ON public.api_keys
    FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "Users can update own API keys" ON public.api_keys
    FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY "Users can delete own API keys" ON public.api_keys
    FOR DELETE USING (user_id = auth.uid());

-- Audit logs: users can read own logs, insert only
CREATE POLICY "Users can view own audit logs" ON public.audit_logs
    FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "System can insert audit logs" ON public.audit_logs
    FOR INSERT WITH CHECK (true);  -- Inserts handled by service role

-- Teams: members can view their team (Phase 3)
CREATE POLICY "Team members can view their team" ON public.teams
    FOR SELECT USING (
        id IN (SELECT team_id FROM public.users WHERE id = auth.uid())
    );
CREATE POLICY "Team admins can update their team" ON public.teams
    FOR UPDATE USING (
        owner_id = auth.uid()
        OR EXISTS (
            SELECT 1 FROM public.team_members
            WHERE team_id = id AND user_id = auth.uid() AND role = 'team_admin'
        )
    );

-- Team members: can view members of their team (Phase 3)
CREATE POLICY "Users can view their team members" ON public.team_members
    FOR SELECT USING (
        team_id IN (SELECT team_id FROM public.users WHERE id = auth.uid())
    );
```

## Appendix D: State Diagrams

### User Account States

```
                    +--------------+
                    |  Registered  |
                    |  (Unverified)|
                    +------+-------+
                           |
                    Email verified
                           |
                    +------v-------+
              +---->|    Active     |<----+
              |     +------+-------+     |
              |            |             |
         Unlocked    Account locked   Restored
              |     (brute force)    (within 30d)
              |            |             |
              |     +------v-------+     |
              |     |    Locked     |     |
              |     +------+-------+     |
              |            |             |
              +--  Lockout expires       |
                                         |
                    +------+-------+     |
                    |   Deleted     +-----+
                    | (Soft, 30d)  |
                    +------+-------+
                           |
                    30 days elapsed
                           |
                    +------v-------+
                    | Hard Deleted  |
                    | (Irreversible)|
                    +--------------+
```

### Broker Connection States

```
    +---------------+
    | Disconnected  |<----- User disconnects
    +-------+-------+
            |
     User connects
            |
    +-------v-------+
    |    Active      |<----- Auto-refresh succeeds
    +-------+--------+      Health check OK
            |
    +-------+--------+--------+
    |                |        |
 3 failures    Token expires  User disconnects
    |                |        |
+---v---+     +------v---+   |
| Error |     | Expired  |   |
+---+---+     +------+---+   |
    |                |        |
 User re-auth   Auto-refresh  |
    |           fails 3x      |
    |                |         |
    +---> Active <---+    Disconnected
```

---

*This document is PRD-008 of 11 for the TrendEdge platform. It must be implemented before any other PRD that requires user identity, data isolation, or broker connectivity.*
