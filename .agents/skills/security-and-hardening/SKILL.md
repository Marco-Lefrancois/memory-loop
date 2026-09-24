---
name: security-and-hardening
description: "Hardens code against vulnerabilities and enforces security boundaries. Use when auditing inputs, authentication, external integrations, OWASP compliance, or dependency supply-chain risks."
---

# Security and Hardening

## Overview

Security-first development practices for web applications and agentic workflows. Treat every external input as hostile, every secret as sacred, and every authorization check as mandatory. Security is a continuous constraint on every line of code touching user data, authentication, or external systems.

## When to Use

- Building anything that accepts user input or external webhooks
- Implementing authentication, session management, or authorization
- Storing or transmitting sensitive data (PII, credentials, tokens)
- Integrating with external APIs, file uploads, or third-party services
- Auditing dependencies for known CVEs or supply-chain risks

## 🧭 Threat Modeling First (STRIDE Protocol)

Before hardening, map trust boundaries and assets:

1. **Map Trust Boundaries** : HTTP requests, form fields, file uploads, webhooks, third-party APIs, message queues, and **LLM outputs**.
2. **Name the Assets** : Credentials, PII, payment data, administrative operations.
3. **Run STRIDE Analysis** :

| Threat | Key Question | Standard Mitigation |
| :--- | :--- | :--- |
| **S**poofing | Can an actor impersonate a user/service? | Authentication, signature verification |
| **T**ampering | Can data be altered in transit or at rest? | Integrity checks, parameterized queries, HTTPS |
| **R**epudiation | Can an action be denied later? | Audit logging of security events |
| **I**nformation disclosure | Can sensitive data leak? | Field allowlists, generic error messages |
| **D**enial of service | Can the service be overwhelmed? | Rate limiting, input caps, timeouts |
| **E**levation of privilege | Can a user gain unauthorized rights? | Authorization checks, principle of least privilege |

---

## 🛡️ The Three-Tier Boundary System

### 1. Always Do (Mandatory Standards)
- **Validate all external input** at system boundaries using schemas (Zod, Pydantic).
- **Parameterize all database queries** — never concatenate raw strings into SQL.
- **Encode output** to prevent XSS (use framework auto-escaping).
- **Use HTTPS** for all external communication.
- **Hash passwords** with bcrypt, scrypt, or argon2.
- **Set security headers** (CSP, HSTS, X-Frame-Options, X-Content-Type-Options).
- **Set httpOnly, secure, sameSite cookies** for sessions.
- **Audit dependencies** against committed lockfiles before release.

### 2. Ask First (Requires Explicit Approval)
- Modifying authentication or permission logic.
- Storing new categories of sensitive data or PII.
- Adding new external service integrations or changing CORS configuration.
- Adding file upload handlers or modifying rate limiting.

### 3. Never Do (Strict Guardrails)
- **Never commit secrets** to version control (API keys, passwords, tokens).
- **Never log sensitive data** (passwords, tokens, full credit card numbers).
- **Never trust client-side validation** as a security boundary.
- **Never disable security headers** for development convenience.

---

## 🛠️ Verification Checklist

Before delivering code touching security boundaries:

- [ ] All inputs validated with strict schemas at system boundaries
- [ ] Database queries parameterized with zero raw string concatenation
- [ ] Authentication checks enforced on every protected route
- [ ] Secrets stored in environment variables, never hardcoded
- [ ] Security headers active and verified
- [ ] Error messages return generic descriptions without leaking stack traces or internal paths
- [ ] Dependency vulnerabilities audited with zero high/critical CVEs

---

## 🏛️ References & Deep Guides
- **OWASP Top 10 & LLM Security Patterns** : `references/owasp_top_10_and_llm.md`
- **Privacy & Compliance (GDPR/CCPA)** : `references/privacy_and_compliance.md`
- **mLoop Security Protocols** : `standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md`

## 🛡️ Résilience & Dégradation Gracieuse
En cas d'anomalie de sécurité détectée lors d'un audit de dépendances ou d'une validation d'entrée, bloquer l'opération non autorisée, journaliser l'événement d'audit avec un identifiant de corrélation (`X-Correlation-ID`) et renvoyer une réponse d'erreur générique sans divulgation d'infrastructure.
