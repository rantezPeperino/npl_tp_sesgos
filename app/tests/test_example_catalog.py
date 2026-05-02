from app.agents import example_catalog


def test_pick_random_respects_dimension():
    ex = example_catalog.pick_random("genero")
    assert ex["dimension"] == "genero"
    assert ex["pedido"]
    assert ex["id"]
