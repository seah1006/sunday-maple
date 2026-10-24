import json

from src.site_data import main


def test_site_data_export(tmp_path):
    main(["--out", str(tmp_path), "--skip-prophet"])
    assert {p.name for p in tmp_path.iterdir()} == {"meta.json", "forecast.json", "backtest.json", "history.json", "rewards.json"}
    data = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in tmp_path.iterdir()}
    assert data["forecast"]["target_date"] == "2026-06-21"
    assert data["forecast"]["classifier"][0]["reward_norm"] == "몬스터컬렉션"
    assert data["forecast"]["prophet"] is None
    assert data["history"][0]["date"] == "2026-06-14"
    assert data["meta"]["backtest_data_through"] == "2026-06-07"
    assert {"generated_at", "sources", "split_cutoff", "random_seed", "data_through", "target_date"} <= data["meta"].keys()
    assert {"metrics", "per_date", "split_cutoff"} <= data["backtest"].keys()
    assert {"reward_norm", "appearances", "first_seen", "last_seen", "median_cycle_days", "is_discontinued"} <= data["rewards"][0].keys()
