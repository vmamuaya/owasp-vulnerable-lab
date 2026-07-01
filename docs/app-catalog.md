# Deliberately Vulnerable Applications — Full Catalog

## 1. OWASP Mutillidae II

- **Repo:** https://github.com/webpwnized/mutillidae
- **OWASP:** https://owasp.org/www-project-mutillidae-ii/
- **Stack:** PHP + MySQL (LAMP/WAMP/XAMPP), Docker
- **Maturity:** One of the oldest deliberately vulnerable apps
- **Covers:** OWASP Top Ten 2007, 2010, 2013, 2017
- **Audience:** Labs, security enthusiasts, classrooms, CTF, scanner testing

### Vulnerabilities
- SQL Injection (error-based, blind, union-based)
- XSS (reflected, stored, DOM-based)
- CSRF
- Session Management flaws
- Authentication bypass
- LDAP Injection
- LFI/RFI
- Command Injection (OS)
- Path Traversal
- IDOR
- Information Exposure
- Broken Access Control
- HTML5 vulnerabilities
- Insecure deserialization

### Features
- 40+ vulnerabilities and challenges
- Actually vulnerable (real exploitable code, no "magic" statements)
- Built-in hints, tutorials, and video tutorials
- Security level system (0-5) toggles mitigations on/off per page
- Pre-installed on SamuraiWTF and OWASP BWA VM

### Docker
```bash
docker run -d -p 80:80 webpwnized/mutillidae
```

---

## 2. OWASP VulnerableApp

- **Repo:** https://github.com/SasanLabs/VulnerableApp
- **OWASP:** https://owasp.org/www-project-vulnerableapp/
- **Stack:** Java (Spring Boot), Docker
- **Purpose:** SAST/DAST scanner benchmarking

### Vulnerabilities
- XSS (reflected, stored)
- SQL Injection
- Path Traversal
- SSRF
- Insecure deserialization
- XXE
- Command Injection
- JWT issues

### Features
- Modular architecture — each vuln is an independent module
- Ships with `expected_issues.csv` manifest for scanner self-evaluation
- Extensible framework
- Docker Hub: sasanlabs/owasp-vulnerableapp

### Docker
```bash
docker run -d -p 8080:8080 sasanlabs/owasp-vulnerableapp
```

---

## 3. OWASP VulnerableApp Facade

- **Repo:** https://github.com/SasanLabs/VulnerableApp-facade
- **OWASP:** https://owasp.org/www-project-vulnerableapp-facade/
- **Stack:** Java (gateway) + Docker containers for registered apps

### Architecture
NOT a vulnerable app itself — it's a distributed farm orchestrator.
Acts as a web server and gateway that routes requests to multiple
registered vulnerable applications. Each app runs as its own Docker
container. Exposes a Vulnerability Definition contract.

### Features
- Tech-stack agnostic — aggregates apps in any language
- Unified API surface for scanner testing across multiple apps
- docker-compose.yml includes registered vulnerable applications

### Strengths
- Solves the "no single app covers all tech stacks" problem
- Best for large-scale scanner benchmarking

### Weaknesses
- Complex setup (Docker, multiple containers, contract understanding)
- Infrastructure tool, not a learning tool
- Niche use case

---

## 4. WackoPicko

- **Repo:** https://github.com/adamdoupe/WackoPicko
- **Origin:** "Why Johnny Can't Pentest: An Analysis of Black-box Web
  Vulnerability Scanners" (Adam Doupé et al.)
- **Stack:** PHP + MySQL
- **Purpose:** Benchmarking web vulnerability scanners

### Vulnerabilities
- Reflected XSS
- Stored XSS
- SQL Injection (login bypass, data extraction)
- Command Injection
- Session ID fixation
- Path Traversal / File Inclusion
- Parameter manipulation
- Authentication bypass
- Insecure file upload

### Features
- Realistic web application (photo gallery with accounts, uploads,
  purchases, comments)
- Used in academic research to evaluate 11 scanners
- Included in OWASP BWA VM project

### Notes
- No official Docker image — custom Dockerfile needed
- Not actively maintained (original project from 2011)
- Small vulnerability set (~14 known vulns)

---

## 5. OWASP Juice Shop

- **Repo:** https://github.com/juice-shop/juice-shop
- **OWASP:** https://owasp.org/www-project-juice-shop/
- **Stack:** Node.js, Express, Angular
- **Maturity:** Flagship OWASP vulnerable app, most modern

### Vulnerability Categories (mapped to standards)
- OWASP Top 10 (2021)
- OWASP ASVS
- OWASP API Security Top 10
- OWASP Automated Threat Handbook
- OWASP Top 10 Privacy Risks
- MITRE CWE

### Specific Vulnerabilities
- SQL/NoSQL Injection
- XSS (reflected, stored, DOM)
- Broken Authentication (JWT manipulation, brute force)
- Broken Access Control (IDOR, privilege escalation)
- Insecure Deserialization
- SSRF
- XXE
- Information Disclosure
- Vulnerable Components (known CVE dependencies)
- Business Logic flaws
- Race conditions
- Cryptographic flaws
- File upload vulnerabilities
- API security issues

### Features
- 113+ challenges across multiple vulnerability categories
- 13 tutorial challenges with enforced ordering (Tutorial Mode)
- 33 challenges include "Find It" phase (spot vulns in codebase) +
  coding challenge
- Gamification: scoreboard, difficulty stars, CTF flag system
- Companion guide: "Pwning OWASP Juice Shop" (free online book)
- CTF event hosting with scoreboard customization

### Docker
```bash
docker run -d -p 3000:3000 bkimminich/juice-shop
```

---

## 6. OWASP crAPI (Completely Ridiculous API)

- **Repo:** https://github.com/OWASP/crAPI
- **OWASP:** https://owasp.org/www-project-crapi/
- **Stack:** Microservices (Java Spring Boot backend, Vue.js frontend,
  Docker Compose)
- **Purpose:** API security training — OWASP API Security Top 10

### Vulnerability Categories (OWASP API Security Top 10)
1. Broken Object Level Authorization (BOLA/IDOR)
2. Broken Authentication (JWT flaws, weak tokens)
3. Broken Object Property Level Authorization (mass assignment, over-exposure)
4. Unrestricted Resource Consumption (no rate limiting, large payloads)
5. Broken Function Level Authorization (BFLA)
6. Server-Side Request Forgery (SSRF)
7. Security Misconfiguration
8. Improper Inventory Management (shadow/legacy APIs)
9. Unsafe Consumption of APIs (trusting third-party APIs)
10. Injection (SQLi, NoSQLi, command injection via API)

### Features
- Simulates a vehicle owner platform (API-driven, microservice-based)
- Docker Compose with multiple microservices
- Built-in CTF-style challenges

### Docker
```bash
git clone https://github.com/OWASP/crAPI
cd crAPI
docker compose -f deploy/docker-compose.yml up -d
```

---

## 7. OWASP WebGoat

- **Repo:** https://github.com/WebGoat/WebGoat
- **OWASP:** https://owasp.org/www-project-webgoat/
- **Stack:** Java (Spring Boot), Docker
- **Maturity:** One of the oldest OWASP training apps

### Vulnerability Categories
- SQL Injection (basic, advanced, blind)
- XSS (reflected, stored)
- Path Traversal
- Command Injection
- CSRF
- Broken Authentication
- Insecure Deserialization
- XXE
- JWT issues (alg=none, weak secret, token tampering)
- Access Control (IDOR, BFLA)
- SSRF
- Cryptography (weak hashing, encoding)
- Password flaws
- HTML5 web storage vulnerabilities
- Request forgery
- Bypassing CSRF protection
- Vulnerable Components
- Information leakage

### Features
- Lesson-based: each lesson has description, assignment, hints,
  solution, and mitigation
- Integrated with ZAP and Burp Suite
- WebWolf companion app for cross-site attack lessons
- Supports Docker and standalone JAR

### Docker
```bash
docker run -d -p 8080:8080 -p 9090:9090 webgoat/goatandwolf
```

---

## 8. DVGA (Damn Vulnerable GraphQL Application)

- **Repo:** https://github.com/dolevf/Damn-Vulnerable-GraphQL-Application
- **Stack:** Node.js, Express, GraphQL, Docker
- **Purpose:** GraphQL-specific security training

### Vulnerability Categories
- GraphQL Introspection exploitation
- GraphQL Field Suggestion (information leakage)
- GraphQL Batching attacks (query batching for brute force / DoS)
- GraphQL DoS (deeply nested queries, aliasing, circular queries)
- SQL Injection via GraphQL input
- NoSQL Injection via GraphQL
- SSRF via GraphQL
- Authorization bypass (IDOR through GraphQL queries)
- Code Execution through GraphQL resolvers
- Information Disclosure through error messages
- Mutation-based attacks (unauthorized data modification)
- Subscription-based attacks
- GraphQL Interface/Union type abuse

### Features
- Beginner and Expert modes (toggle difficulty)
- Supports queries, mutations, and subscriptions
- Docker deployment

### Docker
```bash
docker run -d -p 5042:5040 dolevf/dvga
```

---

## Comparison Matrix

| App              | Stack          | Focus            | Vulns | Gamified | Docker | Best For                    |
|------------------|----------------|------------------|-------|----------|--------|-----------------------------|
| Mutillidae II    | PHP/MySQL      | Web (legacy)     | 40+   | Hints    | Yes    | Beginners, classroom        |
| VulnerableApp    | Java/Spring    | Scanner benchmark| ~20   | No       | Yes    | SAST/DAST tool testing       |
| VulnApp Facade   | Java gateway   | Multi-app farm   | N/A   | No       | Yes    | Scanner testing at scale     |
| WackoPicko       | PHP/MySQL      | Scanner benchmark| ~14   | No       | Build  | Academic scanner eval        |
| Juice Shop       | Node/Angular   | Web (modern)     | 113+  | Yes      | Yes    | CTFs, training, awareness   |
| crAPI            | Java/Vue       | API security     | 10+   | Yes      | Yes    | API security training       |
| WebGoat          | Java/Spring    | Web (lessons)     | 30+   | Partial  | Yes    | Guided lesson learning      |
| DVGA             | Node/GraphQL   | GraphQL security | 12+   | No       | Yes    | GraphQL attack training     |

## Recommended Learning Path

### Beginner (never exploited a vuln)
1. WebGoat — structured lessons with solutions
2. Mutillidae II — practice with hints and security level slider

### Intermediate (understand OWASP Top 10)
3. Juice Shop — gamified challenges, increasing difficulty
4. DVGA — learn GraphQL-specific attacks

### Advanced (API and microservice security)
5. crAPI — master OWASP API Security Top 10
6. Juice Shop coding challenges — spot vulns in source code

### Tool Developer / Scanner Testing
7. VulnerableApp — benchmark SAST/DAST tools
8. VulnerableApp Facade — multi-app farm for comprehensive testing
9. WackoPicko — academic baseline for scanner comparison