from hivemind.data import FictionalDataProvider


def test_data_boundary_is_explicitly_fictional():
    result = FictionalDataProvider().fetch("FICT-001")
    assert result["source"] == "fictional"
    assert result["symbol"] == "FICT-001"