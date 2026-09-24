# OWASP Top 10 & LLM Security Implementation Patterns

This reference provides implementation patterns for mitigating top security vulnerabilities.

## 1. SSRF Mitigation
- Validate URLs at the boundary using an allowlist of trusted domains.
- Block loopback (`127.0.0.1`), link-local (`169.254.169.254`), and private RFC 1918 IP addresses.
- Enforce `https:` protocol and disable automatic HTTP redirects.

## 2. SQL & Command Injection
- Parameterize all queries using ORMs or prepared statements.
- Never concatenate user input into shell commands or SQL strings.

## 3. Cross-Site Scripting (XSS) & Content Security Policy (CSP)
- Use framework auto-escaping in templates.
- Enforce strict CSP headers (`default-src 'self'`).
- Use `httpOnly`, `secure`, and `sameSite=strict` cookies for session tokens.

## 4. LLM-Specific Vulnerabilities (OWASP Top 10 for LLM)
- **Prompt Injection** : Treat model output as untrusted data before passing it to downstream interpreters.
- **Excessive Agency** : Grant agents only minimal necessary tools and read-only sandboxes by default.
- **Insecure Output Handling** : Sanitize and validate LLM outputs before storing in database or rendering in UI.
