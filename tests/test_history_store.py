"""Testes do HistoryStore: isolamento por usuário, limite, persistência e limpeza."""

from rosita.utils.history_store import HistoryStore


def test_append_and_get_em_ordem(tmp_path):
    store = HistoryStore(tmp_path / "h.sqlite3")
    store.append("ana", "user", "oi")
    store.append("ana", "assistant", "olá")

    msgs = store.get("ana")
    assert msgs == [
        {"role": "user", "content": "oi"},
        {"role": "assistant", "content": "olá"},
    ]


def test_isolamento_entre_usuarios(tmp_path):
    store = HistoryStore(tmp_path / "h.sqlite3")
    store.append("ana", "user", "pergunta da ana")
    store.append("bob", "user", "pergunta do bob")

    assert len(store.get("ana")) == 1
    assert len(store.get("bob")) == 1
    assert store.get("ana")[0]["content"] == "pergunta da ana"


def test_limite_retorna_mais_recentes_em_ordem(tmp_path):
    store = HistoryStore(tmp_path / "h.sqlite3")
    for i in range(5):
        store.append("ana", "user", f"msg{i}")

    recentes = store.get("ana", limit=2)
    assert [m["content"] for m in recentes] == ["msg3", "msg4"]


def test_clear_isolado(tmp_path):
    store = HistoryStore(tmp_path / "h.sqlite3")
    store.append("ana", "user", "a")
    store.append("bob", "user", "b")

    store.clear("ana")
    assert store.get("ana") == []
    assert len(store.get("bob")) == 1


def test_persistencia_apos_reabrir(tmp_path):
    caminho = tmp_path / "h.sqlite3"
    store = HistoryStore(caminho)
    store.append("ana", "user", "persistente")

    # Nova instância lendo o mesmo arquivo simula reinício do servidor.
    store2 = HistoryStore(caminho)
    assert store2.get("ana") == [{"role": "user", "content": "persistente"}]


def test_username_vazio_e_ignorado(tmp_path):
    store = HistoryStore(tmp_path / "h.sqlite3")
    store.append("", "user", "sem dono")
    assert store.get("") == []


def test_consentimento_e_exportacao_do_usuario(tmp_path):
    store = HistoryStore(tmp_path / "h.sqlite3")
    store.append("ana", "user", "mensagem privada")
    store.save_consent("ana", "2026-11-14", True)

    dados = store.export_user_data("ana")

    assert dados["consentimento"]["notice_version"] == "2026-11-14"
    assert dados["mensagens"][0]["content"] == "mensagem privada"


def test_excluir_dados_remove_historico_e_consentimento(tmp_path):
    store = HistoryStore(tmp_path / "h.sqlite3")
    store.append("ana", "user", "mensagem privada")
    store.save_consent("ana", "2026-11-14", True)

    store.delete_user_data("ana")

    assert store.export_user_data("ana") == {"consentimento": None, "mensagens": []}


def test_retentao_zero_preserva_e_dias_remove_mensagens_antigas(tmp_path):
    store = HistoryStore(tmp_path / "h.sqlite3")
    store.append("ana", "user", "mensagem recente")

    assert store.purge_older_than(0) == 0
    assert store.get("ana")[0]["content"] == "mensagem recente"

    with store._lock, store._connect() as con:
        con.execute(
            "UPDATE messages SET created_at = datetime('now', '-10 days') "
            "WHERE username = ?",
            ("ana",),
        )

    assert store.purge_older_than(7) == 1
    assert store.get("ana") == []
