"""
Demo handoff data for pre-filling the builder form.
Each entry matches the form_data keys used by _fd() / _save_fd() in the builder.
"""

SALES_TO_CS_DEMOS = {
    "Meridian Analytics — Clean SaaS Deal": {
        "account_name": "Meridian Analytics",
        "product": "Professional · 50 seats",
        "arr": "$84,000",
        "close_date": "2026-04-01",
        "pain_points": (
            "Their data engineering team was spending 2–3 days per sprint manually reconciling pipeline "
            "failures across three environments. No single pane of glass — alerts were going to email, "
            "Slack, and PagerDuty depending on who set up the job. The tipping point was a silent failure "
            "in their billing pipeline that went undetected for 6 hours and caused a downstream SLA breach."
        ),
        "success_criteria": (
            "90-day goal: all pipelines monitored in one place, MTTR on failures reduced from ~4 hours to "
            "under 30 minutes. They'll measure this internally. Longer term: they want to use the alerting "
            "webhooks to auto-create Jira tickets — not in scope for onboarding but worth keeping in mind."
        ),
        "competitors": "Evaluated Monte Carlo and built an internal tool. Chose us on ease of setup and pricing.",
        "stakeholders": [
            {
                "name": "Priya Nair",
                "title": "Head of Data Engineering",
                "role": "Champion / Technical DRI",
                "savviness": "Strong — Python/Spark background, comfortable with APIs and YAML config",
                "sentiment": "Champion",
            },
            {
                "name": "Derek Olson",
                "title": "VP Engineering",
                "role": "Economic Buyer",
                "savviness": "Managerial — understands the problem space, won't be in the product day-to-day",
                "sentiment": "Positive",
            },
        ],
        "commitments_written": "Standard 30-day onboarding SLA per contract.",
        "commitments_verbal": (
            "Priya asked if we could prioritize their dbt integration during onboarding — I said we'd flag "
            "it for the CSM to address in week 2. Not a hard commitment but she's expecting it to come up."
        ),
        "commitments_functionality": "",
        "red_flags": [
            {
                "category": "Technical Risk",
                "description": (
                    "They're running a heavily customized Airflow setup (2.4, not latest). Our Airflow connector "
                    "works best on 2.6+. Priya knows this and is planning an upgrade but it's not scheduled yet. "
                    "Onboarding may need to start with manual webhook integration as a bridge."
                ),
            }
        ],
        "key_dates": (
            "Go-live target: May 1\n"
            "Derek's Q2 review with his CTO: mid-June — Priya wants a win to show by then\n"
            "Airflow upgrade: tentatively Q3, no firm date"
        ),
        "misc_notes": (
            "Priya is a great reference candidate if onboarding goes well — she mentioned they present at "
            "local data meetups. Worth flagging for the customer marketing team post-onboarding."
        ),
    },

    "Apex Financial — Enterprise, High Complexity": {
        "account_name": "Apex Financial Group",
        "product": "Enterprise · 200 seats",
        "arr": "$312,000",
        "close_date": "2026-03-28",
        "pain_points": (
            "Compliance-driven purchase. Their data governance team failed an internal audit because they "
            "couldn't demonstrate lineage on three regulatory reporting pipelines. The audit finding gave "
            "them a 90-day remediation window — that's why the deal closed fast. This was not a bottoms-up "
            "product evaluation; it was procurement-led under pressure."
        ),
        "success_criteria": (
            "Pass their next internal audit (scheduled for late June). Specifically: full lineage coverage "
            "on their SEC reporting pipelines and an exportable audit log. Everything else is secondary. "
            "If we hit this, renewal is automatic. If we don't, we're in trouble."
        ),
        "competitors": "No competitive evaluation — sole-sourced based on a recommendation from their auditor.",
        "stakeholders": [
            {
                "name": "Tom Fitzgerald",
                "title": "Chief Data Officer",
                "role": "Economic Buyer / Executive Sponsor",
                "savviness": "Low technical depth — strategy and compliance focus. Communicate in business/risk terms.",
                "sentiment": "Neutral",
            },
            {
                "name": "Sandra Chu",
                "title": "Head of Data Governance",
                "role": "Champion / Day-to-day owner",
                "savviness": "Moderate — understands data concepts, not an engineer. Will need hands-on support.",
                "sentiment": "Positive",
            },
            {
                "name": "Raj Patel",
                "title": "Senior Data Engineer",
                "role": "Technical DRI",
                "savviness": "Strong — he'll do the actual implementation. Was skeptical of the purchase, prefers open source.",
                "sentiment": "Skeptical",
            },
        ],
        "commitments_written": (
            "Dedicated onboarding engineer for the first 60 days (in the order form).\n"
            "Audit-ready lineage coverage for SQL-based pipelines in scope for their June audit."
        ),
        "commitments_verbal": (
            "Tom asked directly whether we could have them 'audit-ready' by June 15. I said yes assuming "
            "they complete the data source mapping by end of April. This is aggressive — flag for the CSM immediately."
        ),
        "commitments_functionality": (
            "Sandra asked about automated policy enforcement (blocking non-compliant pipelines from deploying). "
            "This is on the roadmap for H2. I told her it was 'coming this year' — she interpreted this as a "
            "commitment. Do not over-promise on timeline."
        ),
        "red_flags": [
            {
                "category": "Relationship Risk",
                "description": (
                    "Raj (the engineer who will do the work) didn't choose this product and is openly skeptical. "
                    "He asked pointed questions about our API rate limits and said he 'could build this in-house.' "
                    "If he has a bad technical experience early, he'll advocate internally to cancel."
                ),
            },
            {
                "category": "Commercial Risk",
                "description": (
                    "The June audit deadline is load-bearing for renewal. If we miss it for any reason — including "
                    "delays on their side — they may not renew regardless of whose fault it is."
                ),
            },
            {
                "category": "Technical Risk",
                "description": (
                    "They have 3 legacy COBOL-adjacent reporting pipelines that don't have standard metadata. "
                    "Lineage coverage for those will require custom parsers. Scope this carefully in kickoff."
                ),
            },
        ],
        "key_dates": (
            "Data source mapping deadline (their responsibility): April 30\n"
            "Audit-ready target: June 15\n"
            "Internal audit: late June (exact date TBD)\n"
            "Contract renewal: March 2027"
        ),
        "misc_notes": (
            "Tom is connected to three other CDOs in financial services who are evaluating similar tools. "
            "A successful audit outcome here has significant referral potential — coordinate with customer marketing.\n\n"
            "Do not schedule executive check-ins without Sandra — she manages Tom's relationship with vendors "
            "and will be offended if bypassed."
        ),
    },
}

TAM_TO_TAM_DEMOS = {
    "Cascade Systems — Healthy Account, Active Expansion": {
        "account_name": "Cascade Systems",
        "arr": "$156,000",
        "region": "West / Pacific Northwest",
        "renewal_date": "2027-02-01",
        "contract_tier": "Enterprise",
        "health_score": "🟢 Green",
        "products": "Core Platform, Observability Add-on",
        "csm_counterpart": "Jamie Park",
        "tech_stack": (
            "AWS-native (us-west-2), Terraform for infra, dbt + Snowflake data warehouse, "
            "GitHub Actions CI/CD, Datadog for infra monitoring. Engineering team is ~40 people, "
            "Python-heavy, strong DevOps culture."
        ),
        "deployment": "Cloud (AWS us-west-2) — fully managed, no on-prem components",
        "scale": "~180 seats active, 2.1M events/day ingested, 4 environments (dev/staging/prod/dr)",
        "tech_debt": (
            "Their DR environment is 2 versions behind prod — they've deprioritized keeping it current. "
            "Not a blocker but worth flagging if they ever need to failover."
        ),
        "stakeholders": [
            {
                "name": "Alex Tran",
                "title": "VP of Engineering",
                "role": "Economic Buyer / Executive Sponsor",
                "savviness": "Strong technical background, now mostly strategic. Appreciates concise data-led updates.",
                "sentiment": "Champion",
            },
            {
                "name": "Maya Singh",
                "title": "Staff Engineer, Platform",
                "role": "Technical DRI / Day-to-day",
                "savviness": "Deep — she built their Terraform modules integrating with our platform. Primary technical contact.",
                "sentiment": "Champion",
            },
            {
                "name": "Chris Booker",
                "title": "Director of Engineering",
                "role": "Day-to-day stakeholder",
                "savviness": "Moderate — understands the stack, delegates technical decisions to Maya",
                "sentiment": "Positive",
            },
        ],
        "active_projects": (
            "POC for Governance Module (started 3 weeks ago) — Maya is leading, targeting a decision by end of Q2. "
            "They have budget approved for expansion if the POC goes well (~$40K uplift). "
            "No blockers currently; they're in the data mapping phase."
        ),
        "escalations": "No open escalations. Last P2 was resolved in January (false-positive alert rule, fixed in 3.4.1).",
        "feature_requests": (
            "FR-4821: Custom retention policies per data source (filed Feb). Medium priority internally.\n"
            "FR-4903: Slack digest for weekly pipeline summary (filed March). Low priority, workaround in place via webhook."
        ),
        "product_gaps": (
            "Multi-region support — they've asked about active-active across us-west-2 and eu-west-1 for a future "
            "EU expansion. This is 12+ months out on our roadmap. Manage expectations proactively."
        ),
        "promises": (
            "I committed to a roadmap preview call with Maya and our PM when the Governance Module GA date is confirmed. "
            "Coordinate with PM team before that comes up."
        ),
        "red_flags": [
            {
                "category": "Other",
                "description": (
                    "Maya mentioned she's been approached by a competitor (didn't name them) at a conference. "
                    "She seemed unimpressed but worth noting — keep the relationship warm and POC on track."
                ),
            }
        ],
        "key_dates": (
            "Governance Module POC decision: end of Q2 (June)\n"
            "Renewal: February 2027 — plenty of runway but expansion decision in Q2 sets the tone\n"
            "Alex's annual strategy review: September — he'll want a TAM briefing before that"
        ),
        "misc_notes": (
            "Maya responds best to async Slack updates with specific detail — don't schedule a call when a "
            "well-written message will do. Alex prefers quarterly in-person or video QBRs, minimal email.\n\n"
            "The team celebrates wins visibly — when the POC goes well, a congratulatory note to Alex with "
            "specifics goes a long way."
        ),
    },

    "Vertex Corp — At-Risk, Renewal in 8 Months": {
        "account_name": "Vertex Corporation",
        "arr": "$228,000",
        "region": "Central / Midwest",
        "renewal_date": "2026-12-01",
        "contract_tier": "Enterprise Plus",
        "health_score": "🔴 Red",
        "products": "Core Platform, Security Add-on, Premium Support",
        "csm_counterpart": "Rachel Kim",
        "tech_stack": (
            "Hybrid — on-prem Kubernetes cluster (aging, on k8s 1.24) plus AWS for new workloads. "
            "Mixed Python/Java codebase. Data team uses Databricks. Significant platform fragmentation; "
            "they're mid-migration and it's messy."
        ),
        "deployment": "Hybrid (on-prem Kubernetes + AWS us-east-1) — migration to full cloud is in progress, ETA unknown",
        "scale": "~320 seats licensed, ~190 actively using (59% utilization — this is a red flag for renewal)",
        "tech_debt": (
            "On-prem cluster is running k8s 1.24 which is EOL. Our agent has known instability on anything "
            "below 1.26. This has caused 3 of the last 4 escalations. They know they need to upgrade but "
            "it keeps getting deprioritized. This is the root cause of most of their support pain."
        ),
        "stakeholders": [
            {
                "name": "Brian Kowalski",
                "title": "CTO",
                "role": "Economic Buyer",
                "savviness": "Low — delegated all technical decisions. Relationship is cold; hasn't attended last 2 QBRs.",
                "sentiment": "Skeptical",
            },
            {
                "name": "Dana Reyes",
                "title": "Director of Infrastructure",
                "role": "Technical DRI / Day-to-day",
                "savviness": "Strong — she understands the k8s issue and agrees it needs fixing, but doesn't control the roadmap.",
                "sentiment": "Neutral",
            },
            {
                "name": "Marcus Webb",
                "title": "IT Procurement Manager",
                "role": "Renewal decision influencer",
                "savviness": "Non-technical — focuses on cost per seat and utilization. Low utilization is on his radar.",
                "sentiment": "Skeptical",
            },
        ],
        "active_projects": (
            "Cloud migration project — no firm timeline, been 'in progress' for 14 months. "
            "Dana is pushing for completion but resourcing keeps getting pulled. "
            "Until the migration completes, the k8s stability issues will persist."
        ),
        "escalations": (
            "ESC-2891 (open, P2): Agent crashes on their on-prem cluster during peak load. "
            "Root cause is k8s 1.24 incompatibility. Workaround in place (reduced polling frequency) "
            "but it degrades monitoring fidelity. Waiting on them to upgrade.\n\n"
            "ESC-2744 (closed, resolved Feb): Data source connector timeout — fixed in our 3.5.2 patch. "
            "They took 6 weeks to apply the patch, which extended the incident unnecessarily."
        ),
        "feature_requests": (
            "FR-3901: On-prem HA mode without requiring cloud connectivity (filed a year ago). "
            "Not on our roadmap — I've been non-committal. Do not make any promises here.\n\n"
            "FR-4102: Reduced agent footprint for resource-constrained nodes. In backlog, no ETA."
        ),
        "product_gaps": (
            "On-prem HA without cloud dependency — this is a legitimate gap for their architecture. "
            "We can't serve this use case well until their migration completes or we ship FR-3901 (not planned). "
            "Be honest with Dana about this; she already knows."
        ),
        "promises": (
            "I committed to a joint technical review with our support team and Dana's team to document "
            "a clear k8s upgrade path. This was scheduled for March and didn't happen — reschedule immediately, "
            "this is a trust issue.\n\n"
            "No roadmap commitments have been made, but Brian's team has implied they expect FR-3901 to be addressed "
            "before renewal. Do not confirm this."
        ),
        "red_flags": [
            {
                "category": "Commercial Risk",
                "description": (
                    "59% seat utilization with renewal in 8 months. Marcus is tracking this. "
                    "If utilization doesn't improve significantly by Q3, expect a downsell conversation at renewal."
                ),
            },
            {
                "category": "Relationship Risk",
                "description": (
                    "Brian (CTO, economic buyer) has gone cold — missed last 2 QBRs with no reschedule. "
                    "Rachel (CSM) has tried to re-engage through Dana with limited success. "
                    "We may not have executive sponsorship at renewal time."
                ),
            },
            {
                "category": "Technical Risk",
                "description": (
                    "EOL Kubernetes (1.24) is causing recurring agent instability. The workaround degrades "
                    "their monitoring. Until they upgrade, we cannot reliably resolve ESC-2891, and "
                    "support will continue to be painful for both sides."
                ),
            },
        ],
        "key_dates": (
            "Joint k8s upgrade review (overdue, reschedule ASAP)\n"
            "Q2 TAM check-in with Dana: target end of April\n"
            "Renewal: December 1, 2026 — procurement conversations typically start 90 days out (September)\n"
            "Cloud migration (unofficial target): Q4 2026 — if this slips, renewal risk increases"
        ),
        "misc_notes": (
            "The relationship is salvageable but requires immediate action on two things: "
            "(1) reschedule the k8s review that was missed in March, and "
            "(2) get executive re-engagement with Brian before Q3.\n\n"
            "Dana is your ally — she wants the platform to succeed and will help you navigate internally if "
            "she trusts you. Don't let her down again on the k8s review.\n\n"
            "Do not bring up expansion or upsell until the health issues are resolved. Marcus will use it against you."
        ),
    },
}
