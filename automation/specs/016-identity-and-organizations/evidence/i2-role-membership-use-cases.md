# Spec 016 — I2 Role / membership use cases

**Fecha:** 2026-07-11  
**Estado:** PASS

## Membership

suspend · reactivate · leave · remove · list by org · list orgs for user  

## Roles

assign · revoke · list · `member_has_permission` deny-by-default  

## Last owner

`ensure_organization_has_active_owner_after_mutation` cuenta owners **en SQL** (`active` member + `active` owner role) antes de leave/suspend/remove/revoke owner.
