from pathlib import Path

root = Path(__file__).resolve().parents[1] / "frontend" / "src" / "app"
wrong = "from '../../core/services/i18n.service'"
for p in root.rglob("*.ts"):
    text = p.read_text(encoding="utf-8")
    if wrong not in text:
        continue
    depth = len(p.relative_to(root).parts) - 1
    correct = f"from '{'../' * depth}core/services/i18n.service'"
    p.write_text(text.replace(wrong, correct), encoding="utf-8")
    print(p.relative_to(root), "->", correct)
