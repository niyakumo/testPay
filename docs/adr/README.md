# ADR — Decision Log (short)

- ADR-001: JWT algorithm = ES256 (alt: EdDSA). Reason: compact, widely supported.
- ADR-002: OAuth flow = Authorization Code + PKCE. Reason: native apps, security.
- ADR-003: Refresh = rotating with reuse detection. Reason: session security.
- ADR-004: Optional DPoP. Reason: sender-constrained tokens for higher assurance.
- ADR-005: Error format = RFC7807. Reason: consistency & observability (traceId).
