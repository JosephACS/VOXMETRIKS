# Presentation day checklist

Day-of checks. **No secrets.**

## Night before

- [ ] `VOXMETRIKS-DEMO-RUNTIME` exported and copied to USB + laptop sibling folder
- [ ] `.\scripts\restore_demo_runtime.ps1` worked once on the presentation laptop
- [ ] `.\scripts\setup_demo.ps1` completed (venv + npm)
- [ ] Video backup exported / on USB (`docs/VIDEO-BACKUP-SCRIPT.md`)
- [ ] Browser bookmarks: `http://127.0.0.1:4200`, `http://127.0.0.1:8000/health`, `http://127.0.0.1:8000/docs`
- [ ] Wi‑Fi optional; demo does not need internet if packages already installed

## Morning of

- [ ] Power + sleep settings: never sleep while on AC
- [ ] Close Teams/Slack screen-share noise; hide desktop clutter
- [ ] `.\scripts\start_demo.ps1`
- [ ] `.\scripts\verify_demo.ps1` green
- [ ] Login smoke: `demo.artist`, `listener.free`, `demo.business` (password from env only)
- [ ] Zoom browser to 110–125% if projector is soft

## 60 seconds before talk

- [ ] Backend `/health` OK
- [ ] Frontend root loads
- [ ] Org selector ready on **VOXMETRIKS Demo** for B2B accounts
- [ ] Emergency video cued on second monitor/USB

## After talk

- [ ] `.\scripts\stop_demo.ps1`
- [ ] Do not leave `.env` on a shared machine without encrypting/removing
