# Checklist — Spec 017 CRM (borrador documental)

**Status**: DESIGN_APPROVED (borrador) · IMPLEMENTATION_PENDING

## Criterios de revisión del borrador

- [x] CHK001 CRM platform-scoped pre-conversión
- [x] CHK002 Procesos con estados (prospect…contract…conversion)
- [x] CHK003 Roles sales separados de roles org-cliente 016
- [x] CHK004 Cotizaciones versionadas e inmutables post-sent
- [x] CHK005 Aprobaciones con separación de funciones
- [x] CHK006 Contrato comercial ≠ subscription ≠ rights_contract
- [x] CHK007 Conversión diseñada vía Organizations 016
- [x] CHK008 Sin billing/pago/factura ocultos
- [x] CHK009 APIs futuras trazadas a casos/permisos
- [x] CHK010 Frontend futuro sin billing UI
- [x] CHK011 Pruebas futuras de aislamiento y doble conversión
- [x] CHK012 Nada marcado IMPLEMENTED sin serlo
- [x] CHK013 Contactos externos no se convierten en users automáticamente
- [x] CHK014 Probabilidad no presentada como IA
- [x] CHK015 feature.json / Constitución / 018 / Git intactos

## Decisiones humanas abiertas

- [ ] HUM001 Umbrales de descuento
- [ ] HUM002 Naming físico `app_*`
- [ ] HUM003 lead vs new
- [ ] HUM004 platform_finance en v1
- [ ] HUM005 Política owner/invite en conversión
- [ ] HUM006 Prefijo API unificado vs split
- [ ] HUM007 Package crm vs contracts
- [ ] HUM008 Whitelist monedas
- [ ] HUM009 Retención PII
- [ ] HUM010 Probabilidad: manual vs reglas por stage

## Gate formal

- [ ] REV001 Revisión humana aprueba DESIGN_APPROVED sin NEEDS_CORRECTIONS
- [ ] REV002 Autorización explícita para D0 (feature.json → 017)
