# Privacy & Compliance Reference (GDPR & CCPA)

Implementation checklist for handling sensitive user data and regulatory compliance:

## 1. Data Minimization
- Collect only the minimum necessary personal data required for the specific business function.
- Do not log sensitive data (PII, credentials, payment tokens) in application logs or traces.

## 2. Right to Erasure & Access (GDPR Art. 17 & CCPA)
- Provide endpoints or procedures to delete all user-related records upon request.
- Ensure cascaded deletion across secondary caches, backups, and analytical stores.

## 3. Encryption at Rest & in Transit
- Encrypt database columns containing PII using industry-standard algorithms (AES-GCM-256).
- Enforce TLS 1.3 for all inter-service and client-server network communications.
