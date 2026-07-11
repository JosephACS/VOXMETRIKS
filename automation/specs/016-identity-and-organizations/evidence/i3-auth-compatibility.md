# Spec 016 — I3 Auth compatibility

**Fecha:** 2026-07-11  
**Estado:** PASS

Bearer session opaca reutilizada (`require_user_id`).  
login → /me → logout → 401 OK.  
Rutas personales sin org OK.  
`app_user` = 5.  

**Nota:** un smoke temprano de I3 escribió orgs en warehouse; se limpiaron (`_i3_warehouse_cleanup.txt`). Tests API usan DuckDB de pytest. Orgs warehouse = **0**.
