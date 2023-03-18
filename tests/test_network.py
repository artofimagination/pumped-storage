import pytest
from src.network import Message, Network


dataColumns = ("data", "expected")
createTestData = [
    (
        # Input data
        {
            "data:": [
                Message("$ADTA", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]),
                Message("$ADTA", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
            ],
            "filter": []
        },
        # Expected
        {
            False,
            True
        }),

    (
        # Input data
        {
            "data": [
                Message("$ADTA", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]),
                Message("$ACTL", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]),
                Message("$ADTA", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]),
            ],
            "filter": []
        },
        # Expected
        {
            False,
            False,
            True
        })
]

ids = ['Case 1', 'Case 2']


@pytest.mark.parametrize(dataColumns, createTestData, ids=ids)
def test_filter_send_duplicates(data, expected):
    network = Network()
    for data in data["data"]:
        network._filter_send_duplicates(data, data["filter"])
