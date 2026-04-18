# Security

## Threat Model

- Assets: user data, payments, secrets.
- Adversaries: external attacker, malicious tenant, insider.
- Trust boundaries: browser <-> API <-> DB / 3rd party.

## STRIDE

| Threat | Where | Mitigation |
|--------|-------|-----------|
| Spoofing | login | MFA, rate limit |
| Tampering | API | HTTPS, signed tokens |
| Repudiation | actions | audit log |
| Info disclosure | DB | encryption at rest, RBAC |
| DoS | API | rate limit, WAF |
| Elevation | endpoints | authZ checks per route |

## Controls

- AuthN: OAuth2 + bcrypt/argon2
- AuthZ: RBAC, deny-by-default
- Secrets: env + secret manager, never in repo
- Transport: TLS 1.2+
- Storage: AES-256 at rest
- Headers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- Input: pydantic validation at boundary
- Output: escape on render
- Dependencies: Dependabot + `pip-audit` / `bun audit`

## Compliance

- [ ] GDPR
- [ ] SOC 2
- [ ] HIPAA (if PHI)
- [ ] PCI (if card data; prefer Stripe-hosted)

## Incident Response

1. Detect (alert)
2. Contain
3. Eradicate
4. Recover
5. Postmortem in [20-decision-log.md](20-decision-log.md)

## Secret Rotation

- Cadence: 90 days.
- On-exposure: immediate.
