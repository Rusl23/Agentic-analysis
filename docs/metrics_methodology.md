# Metrics Methodology

This document explains the simplified data model and metric definitions used in this project.

The project is intentionally small and deterministic. It is designed to demonstrate a reproducible churn and revenue reporting workflow, not to model every detail of a real subscription billing system.

## Current Dataset Assumptions

The input dataset is generated as a user-month table: one row per user per month.

Current assumptions:

- all users belong to a single cohort acquired in month 1;
- no new users are acquired after month 1;
- each user has exactly one subscription plan;
- a user's plan does not change over time;
- each user can have at most one payment attempt per month;
- there are no upgrades, downgrades, add-ons, refunds, discounts, taxes or multiple invoices;
- once a user churns, the user stays inactive in all following months;
- failed payments produce zero revenue;
- an active user can still have a failed payment in a given month.

These assumptions make the dataset easy to inspect and the metrics easy to reproduce.

## Why An Active User Can Be Non-Paying

In this project, product activity and successful payment are modeled as separate concepts.

An active user can have:

```text
is_active = True
payment_status = failed
amount_paid = 0
```

This can represent a simplified version of real-world situations such as:

- a failed card charge during a grace period;
- a user who still has temporary access while payment retry logic is running;
- a billing failure that has not yet resulted in subscription cancellation;
- a product activity signal that is tracked separately from billing status.

Because of this, `active_users` can be greater than `paid_users`.

If a business defines activity strictly as successful payment, then this assumption should be changed and failed payments should likely make the user inactive for that month.

## Metric Definitions

The metrics are calculated in `src/pipeline/metrics.py` and saved to `data/monthly_metrics.csv`.

### active_users

Number of unique users with `is_active = True` in the month.

```text
active_users = count_distinct(user_id where is_active = True)
```

### paid_users

Number of unique active users with a successful payment in the month.

```text
paid_users = count_distinct(user_id where is_active = True and payment_status = "paid")
```

This metric excludes active users whose payment failed.

### monthly_revenue

Sum of `amount_paid` across all rows in the month.

```text
monthly_revenue = sum(amount_paid)
```

In the current dataset, one user has only one subscription and one payment attempt per month. Therefore this is equivalent to summing successful monthly subscription charges.

In a real billing model, revenue would usually be calculated from invoice or payment tables rather than from a user-month table.

### churned_users

Number of users who were active in the previous month but are not active in the current month.

```text
churned_users = previous_month_active_users - current_month_active_users
```

Example:

```text
Month 1 active users: {1, 2, 3, 4, 5}
Month 2 active users: {1, 2, 4}

Month 2 churned users: {3, 5}
churned_users = 2
```

This is month-over-month churn, not a full cohort retention model.

### churn_rate

Share of previously active users who churned in the current month.

```text
churn_rate = churned_users / active_users_previous_month
```

Example:

```text
Month 1 active_users = 1000
Month 2 churned_users = 43

Month 2 churn_rate = 43 / 1000 = 0.043
```

This metric answers: "What percentage of users active last month became inactive this month?"

### arpu

Average revenue per active user.

```text
arpu = monthly_revenue / active_users
```

Because the denominator is active users, not paid users, failed payments reduce ARPU.

A related metric that could be added later is ARPPU:

```text
arppu = monthly_revenue / paid_users
```

ARPPU answers: "How much revenue did we generate per paying user?"

## Month-Over-Month Churn vs Cohort Churn

The current project uses month-over-month churn because the dataset contains a single cohort and no new users.

This works for a simple demonstration, but it is not the same as a full cohort-based approach.

In a cohort model, users are grouped by their acquisition or subscription start month. Metrics are then calculated separately for each cohort over its lifetime.

Example:

```text
January cohort:
month 0: 1000 users
month 1: 920 retained
month 2: 850 retained

February cohort:
month 0: 700 users
month 1: 650 retained
month 2: 610 retained
```

A cohort approach can answer questions such as:

- how retention differs between users acquired in different months;
- whether newer cohorts are better or worse than older cohorts;
- what percentage of the original cohort remains after 1, 3, 6 or 12 months;
- how revenue develops over a customer lifetime;
- how acquisition channel, plan, geography or product segment affects retention.

For a production subscription analytics system, a cohort model is usually more useful than only month-over-month churn.

## What A More Realistic Model Would Add

A more complete version of this project would likely include separate tables for:

- users;
- subscriptions;
- subscription events;
- invoices;
- payments;
- refunds;
- plans and pricing;
- product activity.

It could then calculate additional metrics:

- new users;
- reactivated users;
- expansion revenue;
- contraction revenue;
- gross revenue churn;
- net revenue retention;
- cohort retention;
- cumulative churn from original cohort size;
- ARPPU;
- MRR and ARR.

The current implementation should be read as a simplified reporting workflow that is easy to validate, not as a complete billing analytics model.
