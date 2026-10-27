from ytpd.runtime.pool_worker_limits import PoolWorkerLimits


def test_download_workers_capped_at_two() -> None:
    assert PoolWorkerLimits().download_workers() == 2


def test_match_workers_at_most_eight() -> None:
    assert PoolWorkerLimits().match_workers() <= 8
    assert PoolWorkerLimits().match_workers() >= 1
