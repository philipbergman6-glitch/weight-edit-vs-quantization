from wevq.controls import paired


def test_paired_counts_each_direction_separately():
    ids = ["a", "b", "c", "d"]
    ref = {u: {"correct": v} for u, v in zip(ids, [True, True, False, False])}
    row = {u: {"correct": v} for u, v in zip(ids, [True, False, True, False])}
    lost, gained, p = paired(ref, row, ids, "correct")
    assert (lost, gained) == (1, 1)
    assert p == 1.0
