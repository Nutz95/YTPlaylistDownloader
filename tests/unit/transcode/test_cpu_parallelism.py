from ytpd.transcode.cpu_parallelism import CpuParallelism


def test_cpu_parallelism_at_least_one() -> None:
    assert CpuParallelism().worker_count() >= 1
