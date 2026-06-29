# Principles

## 1. Live Reality Wins

Documentation describes the server. It does not replace live checks. After every repair or migration, update the docs from actual process state, logs, and health checks.

## 2. Preserve Memory Before Cleanup

Do not delete agent memory, Telegram sessions, project workspaces, or archives until you have a verified backup and a classification decision.

## 3. No Silent Fallbacks

Each profile should have one primary provider/model route. Keep fallback providers empty unless an owner explicitly approves the cost, privacy, and behavior tradeoff.

## 4. Passive Work Is Opt-In

Recurring tasks, indexing, monitoring, and background analysis can burn tokens or expose data. They must have an owner, schedule, budget expectation, log path, and stop condition.

## 5. Secrets Stay Out Of Git

Never commit tokens, session files, private keys, OAuth JSON, API hashes, phone numbers, TOTP seeds, or raw logs with private conversations.

## 6. One Role Per Profile

A profile should have a job. If a profile becomes responsible for infra, analytics, communications, and content at the same time, split it.
