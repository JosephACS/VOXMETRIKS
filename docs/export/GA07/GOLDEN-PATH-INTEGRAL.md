# Golden Path integral (Specs 001–031)

**Ubicación de prueba:** `apps/backend/tests/test_final_integral_golden_path.py`
**Anclaje documental:** Spec 028 integración global + evidencia final (no Spec 032).
**Resultado 2026-07-15:** **4 passed**

## Cadena cubierta (laboratorio)

```
Publicar (031) → B2C Individual 4.99 mock (029) → Fondo/regalías/payout simulado (030)
+ negativos: CRM 403 oyente · contrato 90% · self-approve bloqueado
```

Complementos (suites existentes):

| Suite | Rol |
|-------|-----|
| S028 | Enterprise org/CRM/billing/CS/reporting smoke |
| S029 | Personal subscriptions full |
| S030 | Royalties dedicadas |
| S031 | Catalog publishing dedicadas |

## Cómo ejecutar

```bash
cd apps/backend
set EMAIL_PROVIDER=console
python -m pytest tests/test_final_integral_golden_path.py tests/test_catalog_publishing_golden_path_s031.py tests/test_royalties_golden_path_s030.py tests/test_personal_subscriptions_s029.py tests/test_enterprise_golden_path_s028.py -q
```

## Demostración manual (orden)

Ver `docs/DEMO-FINAL-PASO-A-PASO.md`.
