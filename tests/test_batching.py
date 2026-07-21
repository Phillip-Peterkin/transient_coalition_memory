import numpy as np

from tcm import BatchedReserveCellular


def test_closed_form_matches_repeated_recurrence():
    old = 0.37
    decay = 0.91
    deltas = [0.1, -0.03, 0.07, 0.02]
    repeated = old
    for delta in deltas:
        repeated = decay * repeated + delta
    batched = BatchedReserveCellular._closed_form(old, decay, deltas)
    assert np.isclose(repeated, batched)
