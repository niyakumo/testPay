# States — Challenge & Refresh Family

```mermaid
stateDiagram-v2
  [*] --> New
  New --> Sent: OTP dispatched
  Sent --> Verified: correct OTP
  Sent --> Expired: TTL exceeded
  Verified --> Redeemed: auth_code exchanged
  Sent --> Blocked: attempts exceeded

  state "RefreshFamily" as RF
  [*] --> Active
  Active --> Rotated: refresh used, new issued
  Rotated --> Compromised: old refresh reused
  Compromised --> Revoked
  Active --> Revoked: logout all
