import pytest

from src.build_tidy import build_tidy, load_raw_views
from src.observations import append_observations, load_manual_observations
from src.forecast import train_classifier, backtest, predict_next, next_sunday_after


@pytest.fixture(scope="module")
def trained():
    tidy, _ = build_tidy(*load_raw_views(), as_of="2026-06-10")
    return tidy, train_classifier(tidy)


def test_next_sunday_after():
    assert str(next_sunday_after("2026-06-14").date()) == "2026-06-21"
    assert str(next_sunday_after("2026-06-17").date()) == "2026-06-21"


def test_predict_next_matches_phase20_forecast(trained):
    tidy, bundle = trained
    combined = append_observations(tidy, load_manual_observations())
    result = predict_next(combined, bundle, "2026-06-21")
    assert result.iloc[0].reward_norm == "몬스터컬렉션"
    assert result.iloc[0].score_pct == 66.7
    assert {"현상금_경험치", "불꽃늑대_경험치", "스타포스_1+1강화", "스타포스_성공확률"}.isdisjoint(result.reward_norm)


def test_backtest_rf_date_hit_rate(trained):
    tidy, bundle = trained
    metrics, per_date = backtest(tidy, bundle, include_prophet=False)
    rates = metrics.set_index("method").date_hit_rate.round(4).to_dict()
    assert {k: v for k, v in rates.items() if k != "random_forest_gated"} == {"gap_rule": 0.3478, "prior_rate": 0.3623, "logistic": 0.3913, "random_forest": 0.4493}
    assert per_date.rf_hit.mean() == metrics.loc[metrics.method == "random_forest", "date_hit_rate"].iloc[0]

    from src.predict_dataset import _eligible_rows, _candidate_rewards, gate_candidates
    eligible = _eligible_rows(tidy)
    candidates = _candidate_rewards(eligible.loc[eligible.date < "2025-01-01"], 20)
    for row in per_date.itertuples():
        assert set(row.gated_predicted) <= set(gate_candidates(eligible, candidates, row.date))
        assert "스타포스_1+1강화" not in row.gated_predicted
        assert set(row.actual_all) == set(row.actual) | set(row.outside_candidates)

        for reward in row.gated_predicted:
            last = eligible.loc[(eligible.reward_norm == reward) & (eligible.date < row.date), "date"].max()
            assert (row.date - last).days <= 180


def test_operational_training_uses_full_history_and_no_domain_ban(trained):
    from src.forecast import train_operational_classifier, operational_inference_frame
    tidy, _ = trained
    combined = append_observations(tidy, load_manual_observations())
    bundle = train_operational_classifier(combined)
    assert bundle.prediction_frame.date.max().strftime('%Y-%m-%d') == '2026-06-14'
    unfiltered = operational_inference_frame(combined, '2026-06-21', gate=False)
    assert '스타포스_1+1강화' in set(unfiltered.reward_norm)
