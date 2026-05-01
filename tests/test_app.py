VALID_PAYLOAD = {
    "farm_name": "Acme Farms",
    "contact": "Jane Doe",
    "phone_email": "jane@acme.example",
    "location": "94110",
    "type": "Organic",
    "size": "Large",
    "grade": "AA",
    "pack": "12ct_carton",
    "quantity_value": 12,
    "quantity_unit": "dozen",
    "price_per_dozen": 4.50,
    "notes": "Test entry",
}


def test_healthz(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_submit_then_list_round_trip(client):
    # Submit two entries to also exercise the "more than one entry" rubric line.
    ids = []
    for i in range(2):
        payload = {**VALID_PAYLOAD, "farm_name": f"Acme {i}"}
        res = client.post("/submit", json=payload)
        assert res.status_code == 201, res.text
        body = res.json()
        assert "id" in body
        # uuid4 strings are 36 chars including hyphens.
        assert len(body["id"]) == 36
        ids.append(body["id"])

    listed = client.get("/entries")
    assert listed.status_code == 200
    rows = listed.json()
    assert isinstance(rows, list)
    listed_ids = {r["id"] for r in rows}
    assert set(ids).issubset(listed_ids)


def test_submit_missing_required_field_returns_friendly_422(client):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "farm_name"}
    res = client.post("/submit", json=payload)
    assert res.status_code == 422

    body = res.json()
    # The custom validation handler returns {"errors": [{"field", "message"}]},
    # never the default {"detail": [...]} shape.
    assert "errors" in body
    assert "detail" not in body

    fields = {err["field"] for err in body["errors"]}
    assert "farm_name" in fields

    # Every error has both "field" and "message" populated.
    for err in body["errors"]:
        assert err["field"]
        assert err["message"]
