from app.packages.streaming.services.display_text import sanitize_display_text, clean_catalog_row


def test_sanitize_display_text_strips_noise():
    assert sanitize_display_text("La Bachata — #1185289") == "La Bachata"
    assert sanitize_display_text("Track [syn-42]") == "Track"
    assert sanitize_display_text("Broken\uFFFDName") == "BrokenName"
    assert sanitize_display_text("") == "—"


def test_clean_catalog_row_sanitizes_names():
    row = clean_catalog_row({"nombre_track": "Song [syn-1]", "nombre_artista": "Artist — #99"})
    assert row["nombre_track"] == "Song"
    assert row["nombre_artista"] == "Artist"
