def test_login_page_ok(client):
    response = client.get("/contas/entrar/")
    assert response.status_code == 200
    assert b"RB Prospecta" in response.content


def test_dashboard_requer_login(client):
    response = client.get("/", follow=False)
    assert response.status_code == 302
    assert "/contas/entrar/" in response["Location"]


def test_health(client):
    response = client.get("/saude/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
