# Sequence — Login / OTP / Token / Refresh / Logout

```mermaid
sequenceDiagram
  autonumber
  participant App as Mobile App
  participant Auth as Auth API
  participant OTP as OTP Provider
  participant Keys as Key Service (JWKS)

  App->>Auth: POST /auth/start {identifier, channel}
  Auth->>OTP: Send OTP (SMS/email)
  OTP-->>Auth: Delivery accepted
  Auth-->>App: 200 {challenge_id, expires_in, resend_at}

  App->>Auth: POST /auth/otp/verify {challenge_id, otp}
  Auth-->>App: 200 {auth_code, expires_in}

  App->>Auth: POST /oauth/token (code+PKCE)
  Auth->>Keys: Sign JWT (kid=...)
  Auth-->>App: 200 {access_jwt, refresh_token}

  Note over App,Auth: Later...
  App->>Auth: POST /oauth/token (refresh_token)
  Auth-->>App: 200 {new access_jwt, new refresh_token}

  App->>Auth: POST /auth/logout or /auth/logout/all (Bearer/DPoP)
  Auth-->>App: 204


## `docs/flows/states.md`
```markdown
# States — Challenge & Refresh Family

```mermaid
stateDiagram-v2
  state "Challenge" as CH
  [*] --> New
  New --> Sent: OTP dispatched
  Sent --> Verified: correct OTP (within TTL)
  Sent --> Expired: TTL exceeded
  Verified --> Redeemed: auth_code exchanged
  Sent --> Blocked: attempts exceeded

  state "RefreshFamily" as RF
  RF: root_refresh
  [*] --> Active
  Active --> Rotated: refresh used, new issued
  Rotated --> Compromised: reuse old refresh detected
  Compromised --> Revoked: revoke family
  Active --> Revoked: logout all
