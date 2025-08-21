
# Acceptance & Negative Scenarios

## Positive

- P01: Start → Verify → Token (PKCE) → OK
- P02: Refresh rotation → old refresh invalid

## Negative

- N01: Wrong OTP → 400 code=otp_invalid
- N02: Expired OTP → 400 code=otp_expired
- N03: Resend limit exceeded → 429 + Retry-After
- N04: Verify attempts exceeded → 429 / 400 rate_limited
- N05: Reuse auth_code → 400 code=code_redeemed
- N06: Reuse old refresh → 400 code=token_reused + revoke family
