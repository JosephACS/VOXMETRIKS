# Data model — Spec 029

## Tables (additive)

| Table | Owner |
|-------|-------|
| personal_plan | catalog |
| personal_plan_price | catalog |
| personal_plan_feature | catalog |
| personal_subscription | user_id, owner_type='user' |
| household | owner_user_id |
| household_member | user_id |
| household_invitation | token_hash |
| personal_invoice | user_id |
| personal_invoice_item | invoice_id |
| personal_payment_attempt | user_id, idempotency_key |
| personal_entitlement | user_id |
| personal_subscription_event | audit |

B2B tables (`app_plan`, `app_subscription`, `app_invoice`) unchanged.
