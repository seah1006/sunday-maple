import json

import pytest

from src.site_data import main


@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("site")
    from src.observations import load_manual_observations
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr('src.site_data.load_reviewed_observations', load_manual_observations)
        main(["--out", str(tmp_path), "--skip-prophet"])
    return tmp_path


def test_site_data_export(exported):
    tmp_path = exported
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



def test_appearances_count_unique_dates(exported):
    data = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in exported.iterdir()}
    for reward in data["rewards"]:
        dates = {row["date"] for row in data["history"] if any(item["reward_norm"] == reward["reward_norm"] for item in row["rewards"])}
        assert reward["appearances"] == len(dates)


def test_backtest_hit_is_integer_or_null(exported):
    data = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in exported.iterdir()}
    assert all(row["hit"] is None or type(row["hit"]) is int and row["hit"] in {0, 1} for row in data["backtest"]["per_date"])


def test_reviewed_backfill_reaches_latest_date(tmp_path):
    main(["--out", str(tmp_path), "--skip-prophet"])
    meta = json.loads((tmp_path / 'meta.json').read_text(encoding='utf-8'))
    assert meta['data_through'] == '2026-10-25'
    assert meta['target_date'] == '2026-11-01'
    assert meta['backtest_data_through'] == '2026-06-07'
    history = json.loads((tmp_path / 'history.json').read_text(encoding='utf-8'))
    latest = history[0]
    assert latest['date'] == '2026-10-25'
    rune = next(row for row in latest['rewards'] if row['reward_norm'] == '룬_지속시간증가')
    assert rune['category'] == '성장'
    assert rune['scope'] == 'all'
