import importlib
import os

from fastapi.testclient import TestClient


def test_spa_fallback_and_api_not_shadowed(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<html>app</html>")
    (tmp_path / "secret.txt").write_text("x")
    monkeypatch.setenv("FRONTEND_DIST", str(tmp_path / "."))
    monkeypatch.setenv("HEALTHCAREONE_DB", ":memory:")
    import app.main as main

    main = importlib.reload(main)
    client = TestClient(main.app)
    assert "app" in client.get("/hospital/HCO-CENTRAL").text
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/nope").status_code == 404
    assert client.get("/secret.txt").text == "x"
    assert "app" in client.get("/..%2f..%2fetc/passwd").text
