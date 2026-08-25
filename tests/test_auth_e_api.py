"""Testes de autenticação e autorização da API."""

import pytest

from rosita.app_factory import create_app
from rosita.settings import load_settings
from werkzeug.security import generate_password_hash


@pytest.fixture()
def contexto(tmp_path, monkeypatch):
    """App isolado com credenciais conhecidas para testes de API."""
    monkeypatch.setenv("ROSITA_SECRET_KEY", "chave-de-teste")
    monkeypatch.setenv("ROSITA_AI_PROVIDER", "gateway")
    monkeypatch.setenv("ROSITA_GATEWAY_URL", "http://teste-local:8000")
    # Set password hashes instead of plaintext passwords for tests
    monkeypatch.setenv("ROSITA_ADMIN_PASSWORD_HASH", generate_password_hash("admin123"))
    monkeypatch.setenv("ROSITA_USER_PASSWORD_HASH", generate_password_hash("usuario123"))
    app = create_app()
    app.config.update(TESTING=True)
    return app, db_path


def _login(client, username, password):
    return client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )


def test_login_sucesso(contexto):
    app, _ = contexto
    client = app.test_client()
    resp = _login(client, "admin", "admin123")
    assert resp.status_code == 200
    dados = resp.get_json()
    assert dados["authenticated"] is True
    assert dados["role"] == "admin"


def test_load_settings_preserva_hash_entre_aspas_e_dolares(monkeypatch):
    hash_com_dolares = "scrypt:32768:8:1$abc$def"
    monkeypatch.setenv("ROSITA_ADMIN_PASSWORD_HASH", f'"{hash_com_dolares}"')
    monkeypatch.delenv("ROSITA_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("ROSITA_USER_PASSWORD_HASH", raising=False)
    monkeypatch.delenv("ROSITA_USER_PASSWORD", raising=False)

    settings = load_settings()

    assert settings.admin_password_hash == hash_com_dolares


def test_login_senha_errada(contexto):
    app, _ = contexto
    resp = _login(app.test_client(), "admin", "senha-errada")
    assert resp.status_code == 401
    assert resp.get_json()["authenticated"] is False


def test_login_campos_faltando(contexto):
    app, _ = contexto
    resp = app.test_client().post("/api/auth/login", json={"username": "admin"})
    assert resp.status_code == 400


def test_chat_liberado_sem_login(contexto):
    app, _ = contexto
    resp = app.test_client().post("/api/chat", json={"mensagem": "oi"})
    assert resp.status_code == 200
    assert b"[ERRO]" in resp.data or b"[FIM]" in resp.data


def test_health_e_publico_e_tem_estrutura(contexto):
    app, _ = contexto
    resp = app.test_client().get("/api/health")
    # Público (sem login). 200 se o provedor responde; 503 se indisponível.
    assert resp.status_code in (200, 503)
    dados = resp.get_json()
    assert dados["status"] in ("ok", "degraded")
    assert "ia" in dados and "ok" in dados["ia"]
    assert (resp.status_code == 200) == dados["ia"]["ok"]


def test_rate_limit_no_login(contexto):
    pytest.importorskip("flask_limiter")
    app, _ = contexto
    client = app.test_client()
    codigos = [
        _login(client, "x", "y").status_code for _ in range(11)
    ]
    assert 429 in codigos
