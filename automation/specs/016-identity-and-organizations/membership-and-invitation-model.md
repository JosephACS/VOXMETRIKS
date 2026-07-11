# Membership and Invitation Model — Spec 016

**Status**: DESIGN_APPROVED  
**Dominio propietario:** organizations

---

## organization_member

Estados: `active` · `suspended` · `left` · `removed` — ver `lifecycle-state-machines.md`.

Campos: id · organization_id · user_id · status · joined_at · suspended_at · left_at · removed_at · created_by · updated_at  

UNIQUE(organization_id, user_id). Multi-org desde v1 (decisión G). Historial conservado (no hard delete).

### Ownership acciones

| Acción | Actor típico |
|--------|----------------|
| create (via org/invite) | system tx |
| read | member.view |
| suspend/unsuspend | member.suspend |
| remove | member.remove |
| leave | self (si no last owner) |

---

## organization_invitation

Estados: `pending` · `accepted` · `expired` · `revoked`

Campos: id · organization_id · email_normalized · token_hash (**único**) · initial_role_codes · invited_by · expires_at · status · accepted_at · revoked_at · created_at · resend_count · last_sent_at

### Flujo completo

```text
autorizado (member.invite)
→ normalizar email
→ validar roles iniciales ⊆ catálogo fijo
→ generar token (mostrar/devolver UNA vez en modo académico)
→ almacenar solo hash
→ pending + expires_at
→ entrega: NotificationPort o modo académico (no afirmar email enviado)
→ accept: auth user email must match
→ membership + roles + audit + invalidate token (accepted)
```

### Casos obligatorios

| Caso | Resultado |
|------|-----------|
| válida | 200 + membership |
| vencida | 410 |
| revocada | 409/410 |
| ya utilizada (accepted) | 410 |
| ya miembro | 409 |
| email ≠ user autenticado | 403 |
| rol no permitido / custom | 422 |
| org suspended/closed | 403 |
| resend | rotate token; una pending por (org,email) |
| varias pending mismo correo | impedir; resend rota |
| aceptación concurrente | una gana; otra 409/410 |

### Modo académico (decisión D)

- Respuesta create puede incluir `invite_token` **una sola vez** en ENV development/academic flag.  
- MUST NOT loguear token.  
- MUST NOT afirmar “email enviado” si Port es stub.  
- Producción futura: NotificationPort sin devolver token en claro.

### Token

Tras create: cliente ve plaintext una vez. Persistencia: **solo hash**. Nunca en audit_log.
