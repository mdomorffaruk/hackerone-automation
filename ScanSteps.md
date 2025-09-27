# Bug Bounty Checklist & Recon Template

This document provides a comprehensive checklist and template for bug bounty hunting.

## Pre-Hunt Preparation Checklist

### Program Research

- [ ] Read program rules completely (twice!).
- [ ] Identify in-scope assets and domains.
- [ ] Note out-of-scope restrictions.
- [ ] Check forbidden endpoints/actions.
- [ ] Understand acceptable testing methods.
- [ ] Review past disclosed reports for patterns.
- [ ] Join program's communication channels.
- [ ] Set up proper testing environment.

### Tool Preparation

- [ ] Burp Suite configured and ready.
- [ ] Custom wordlists prepared.
- [ ] VPN/proxy setup verified.
- [ ] Screenshot tools ready.
- [ ] Note-taking system established.
- [ ] Backup documentation method ready.

## Systematic Recon Template

### Phase 1: Information Gathering

#### Subdomain Discovery

- [ ] Certificate transparency logs (crt.sh).
- [ ] DNS brute forcing with quality wordlists.
- [ ] Search engine dorking (`site:target.com`).
- [ ] GitHub/GitLab repository searches.
- [ ] Social media and public documents.
- [ ] Third-party service integrations.
- [ ] Historical DNS data (SecurityTrails, etc.).

#### Port & Service Enumeration

- [ ] Nmap comprehensive scan.
- [ ] Service version identification.
- [ ] Banner grabbing.
- [ ] SSL/TLS configuration review.
- [ ] Uncommon port discovery.
- [ ] Service-specific vulnerability checks.

### Phase 2: Web Application Analysis

#### Technology Stack Identification

- [ ] HTTP response headers analysis.
- [ ] JavaScript framework detection.
- [ ] CMS/platform identification (Wappalyzer).
- [ ] Third-party service integration mapping.
- [ ] CDN and hosting provider identification.
- [ ] Database technology indicators.

#### Content Discovery

- [ ] Directory brute forcing (common paths).
- [ ] File extension discovery.
- [ ] Backup file hunting (.bak, .old, .tmp).
- [ ] Configuration file searches.
- [ ] API endpoint discovery.
- [ ] Admin panel location.
- [ ] Development/staging environment detection.

### Phase 3: Parameter Discovery

- [ ] URL parameter discovery.
- [ ] POST parameter identification.
- [ ] Hidden form field analysis.
- [ ] Cookie parameter review.
- [ ] Header parameter testing.
- [ ] JSON/API parameter mapping.

### Phase 4: Vulnerability Assessment

#### Input Validation Testing

- [ ] Cross-Site Scripting (XSS).
- [ ] SQL Injection.
- [ ] Command Injection.
- [ ] Path Traversal.
- [ ] File Upload vulnerabilities.
- [ ] XXE (XML External Entity).

#### Authentication & Session Management

- [ ] Weak password policies.
- [ ] Session fixation.
- [ ] Session hijacking possibilities.
- [ ] Brute force protection.
- [ ] Password reset vulnerabilities.
- [ ] Multi-factor authentication bypass.

#### Business Logic Testing

- [ ] Race conditions.
- [ ] Price manipulation.
- [ ] Privilege escalation.
- [ ] Workflow bypass.
- [ ] Rate limiting bypass.
- [ ] Payment processing flaws.

## Manual Mode Workflow

This is "manual mode" - it works, but requires discipline and organization.

### 1. Setup Your Workspace

Create this folder structure:

```
BugBounty_Workspace/
├── Active_Targets/
├── Completed_Targets/
├── Templates/
├── Tools_and_Scripts/
├── Learning_Notes/
└── Reports_Ready/
```

### 2. Use Physical/Digital Notebooks

- [ ] Keep a master target list.
- [ ] Maintain daily hunting logs.
- [ ] Track methodology improvements.
- [ ] Record interesting techniques found.

### 3. Follow the Checklists

- [ ] Print out recon checklist.
- [ ] Use finding templates consistently.
- [ ] Follow systematic workflow.
- [ ] Don't skip documentation steps.

### 4. Time Management

- [ ] Set specific time blocks for each phase.
- [ ] Use pomodoro technique for focus.
- [ ] Don't get lost in rabbit holes.
- [ ] Regular progress reviews.