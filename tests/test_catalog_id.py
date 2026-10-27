from services.admin_data import _IMG_ID_RE, new_catalog_id, resolve_catalog_id


def test_new_catalog_id_skips_taken_and_matches_format():
    taken = [{"id": "ittest00000000"}]
    got = new_catalog_id(taken, "it")
    assert _IMG_ID_RE.match(got)
    assert got.startswith("it")
    assert got != "ittest00000000"
    second = new_catalog_id([*taken, {"id": got}], "it")
    assert second != got


def test_empty_id_from_panel_gets_generated():
    nid = resolve_catalog_id("", [{"id": "protection"}], "it")
    assert nid.startswith("it")
    assert nid != "protection"
    assert resolve_catalog_id("protection", [{"id": "protection"}], "it") == "protection"
