---
name: subscriptions
description: Maintain and grow BetBudAI's subscriber base and subscription funnel — sign-up, 3-day trial, free conversion, retention, and the Site Analytics admin tab. Use whenever touching registration, trial/subscription status, the Subscribe-for-Free gate, subscriber emails, or the admin analytics dashboard. The site's stated goal (set 2026-07-22) is finding winners AND growing subscribers to 100,000 - use this skill whenever a task touches growth, retention, or conversion, not just when something is visibly broken.
metadata:
  type: skill
---

# Subscriptions Skill

## The goal

Two things matter above everything else on this site: **find winners, and grow subscribers — target 100,000.** These aren't competing priorities. Winners are the product; subscriber count is the scoreboard that says the product is working. Every change to the sign-up/trial/retention funnel should be evaluated against "does this help get to 100,000," not just "does this look nice."

As of 2026-07-22, the real subscriber count is in the low-to-mid dozens (61 at the last admin panel check, 79 real subscriber rows found scanning the table the same day) — there is a very long way to go, and the funnel has real, fixable leaks (see below) before spend-heavy growth tactics are worth it.

## The funnel, as it actually works (not as the marketing copy implies)

1. **Registration** (`POST /api/register`) — user signs up, immediately gets `subscription_status = 'trialing'` and a `trial_end_timestamp` 3 days out, **regardless of which CTA button they clicked** (the "Free" card on the homepage sets `selectedTrialTier: 'premium'` internally — everyone starts on a full-featured trial, not a bare free tier).
2. **3-day trial** — full access, framed as free ("no card required, ever"), but internally a temporary status.
3. **Trial lapses** — `_normalize_local_trial_status()` (in `backend/api/lambda_function.py`) lazily checks `trial_end_timestamp` on next login/fetch. If expired: users who joined **before 2026-07-01** are grandfathered straight to `free_subscriber` (no gate, they already have full access forever). Users who joined **on or after 2026-07-01** flip to `trial_expired` and are shown the `SubscribeFreeGate` component — **blocked until they click "Subscribe for Free"** (`POST /api/subscribe-free`), which is a genuine one-click, no-card action that converts them to permanent `free_subscriber`.
4. **Or**: user upgrades to paid via Stripe checkout at any point → `active`/`canceling` states.

## Known leaks in this funnel (found 2026-07-22, still mostly unaddressed)

- **No warning before the day-3 cliff.** A user who signs up, likes the product, and doesn't happen to log back in right at the 3-day mark gets silently blocked with zero notice. This is very plausibly a major contributor to the retention numbers: only ~7 of 61 subscribers were active in the last 30 days at last check (~11%).
  - **Partial fix shipped 2026-07-22**: `trial-reminder-emailer` Lambda (daily EventBridge cron `BetBudAI-TrialReminder-Daily`, `cron(0 9 * * ? *)`) emails anyone whose trial ends within 24 hours and hasn't already been reminded (`trial_reminder_sent` flag). Source: `trial_reminder_emailer.py` at repo root, deployed as its own Lambda (reuses `BettingPicksAPIRole` for DynamoDB + SES permissions).
  - **This does not yet actually reach most subscribers** — see the SES sandbox blocker below. The code is correct and tested (ran cleanly against live data, `checked: 79, eligible: 0` at test time since no one happened to be in the 24h window that day); it just can't deliver broadly yet.
  - **Next step if this matters**: re-apply for SES production access (see below), then re-verify the reminder is actually landing in inboxes, not just being "accepted" by SES.
- **SES is in sandbox mode, production access DENIED** (case 177585279500302, confirmed 2026-07-22). Only 4 verified recipient identities exist (`betbudai.com`, `barbara.anders@gmail.com`, `dryanfitness@gmail.com`, `charles.mccarthy@gmail.com`). This means **every transactional email to a real subscriber who isn't one of those 4 addresses currently fails to deliver** — welcome emails, verification emails, the new trial reminder, everything. This is arguably the single highest-leverage fix available: re-apply for SES production access. The last approved use-case description said "transactional only, no marketing or bulk email" — if adding more lifecycle/retention emails (which you should, to hit 100k), update the use-case description honestly when re-applying so it doesn't get denied again for scope-creep vs. what was approved.
- **Mismatched marketing vs. mechanics**: the homepage's "Free" card explicitly promises "No card required, ever" and "Create Free Account," but the actual state under the hood is a temporary trial requiring a second action. This isn't necessarily wrong (sampling premium features before locking in free is a reasonable growth tactic) but the *lack of any disclosure or reminder* turns it into silent churn instead of a deliberate upsell-then-downgrade funnel.
- **Site Analytics admin tab: fixed 2026-07-22.** `GET /api/admin/analytics` was a 404 (never implemented) until built against the GA4 Data API on 2026-07-22. The first credential used (an OAuth `authorized_user` refresh token) turned out to be dead (`invalid_grant`) — replaced same day with the existing GCP service account (`analytics-data-sa@betbudai-ga4-sa.iam.gserviceaccount.com`) using proper JWT signing, plus granting it Viewer access in GA4's own Property Access Management (a separate permission system from GCP IAM - both are required). Confirmed working end-to-end with a live test (18 active users / 60 sessions / 191 pageviews, last 7 days). Full setup/rotation/troubleshooting reference: **`.claude/skills/ga4-analytics-setup.md`** — use that skill whenever this credential needs touching again.

## Where to look for each piece

| Concern | File / resource |
|---|---|
| Registration, trial status, subscribe-free, admin analytics | `backend/api/lambda_function.py` (`register_subscriber`, `_normalize_local_trial_status`, `subscribe_free`, `get_admin_analytics`) |
| Day-2 trial reminder | `trial_reminder_emailer.py` (Lambda: `trial-reminder-emailer`; schedule: EventBridge rule `BetBudAI-TrialReminder-Daily`) |
| Homepage sign-up CTA / SubscribeFreeGate UI | `frontend/src/App.js` (search `SubscribeFreeGate`, `CLEAN 2-OPTION CTA`) |
| Frontend GA4 tracking | `frontend/src/analytics.js`, `frontend/.env.production` (measurement ID + `GA4_PROPERTY_ID`) |
| Admin Site Analytics tab | `frontend/src/App.js` (search `activeSection === 'analytics'`) |
| SES identities / sandbox status | `aws sesv2 get-account --region eu-west-1` (check `ProductionAccessEnabled`), `aws ses list-identities --region eu-west-1` |
| GA4 credential | `aws secretsmanager get-secret-value --secret-id ga4-service-account --region eu-west-1` |

## Growth levers worth considering next (ordered by likely leverage)

1. **Re-apply for SES production access** — until this happens, no retention/lifecycle email strategy can actually work at scale, regardless of how good the copy or timing is. This blocks almost everything else on this list, including the day-2 reminder actually reaching anyone. **Still open as of 2026-07-22.**
2. ~~Fix the GA4 credential~~ — **done 2026-07-22**, see above. Real traffic/conversion numbers are now visible in-app; use them to track whether the other levers on this list are actually moving the needle toward 100,000.
3. **Disclose the trial mechanic honestly** on the homepage CTA, or make the reminder email robust enough that the two-step nature never surprises anyone — silent churn at day 3 is pure waste at this subscriber count.
4. **Referral or social-proof mechanics** — nothing currently incentivises existing subscribers to bring others; at low-hundreds of subscribers, word-of-mouth/referral is proportionally powerful.
5. **Re-engagement email for `trial_expired`/lapsed users** who never came back — a second, later nudge beyond the day-2 reminder, once SES access allows it.
