import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.build_tidy import build_tidy, load_raw_views
from src.observations import append_observations, load_manual_observations
from src.forecast import SPLIT_CUTOFF, RANDOM_SEED, train_classifier, backtest, predict_next, prophet_next, next_sunday_after
from src.parse import parse_by_date
from src.predict_dataset import build_inference_frame, DOMAIN_DISCONTINUED


def _clean(value):
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.strftime("%Y-%m-%d")
    if pd.isna(value):
        return None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return round(float(value), 3)
    return value


def export_site_data(out="data/site", target_date=None, skip_prophet=False):
    by_type, by_date = load_raw_views()
    parsed = pd.DataFrame(parse_by_date(by_date))
    as_of = pd.to_datetime(parsed.loc[parsed.reward_raw.notna(), "date"]).max()
    tidy, _ = build_tidy(by_type, by_date, as_of=as_of)
    combined = append_observations(tidy, load_manual_observations())
    analysis = combined.loc[combined.reward_norm.notna() & ~combined.is_future.astype(bool)].copy()
    data_through = analysis.date.max()
    target = pd.Timestamp(target_date) if target_date else next_sunday_after(data_through)
    bundle = train_classifier(tidy)
    metrics, per_date = backtest(tidy, bundle, include_prophet=not skip_prophet)
    rf = predict_next(combined, bundle, target)
    inference = build_inference_frame(combined, target, candidate_cutoff=SPLIT_CUTOFF)
    classifier = rf.merge(inference[["reward_norm", "category", "days_since_last"]], on="reward_norm")
    prior = analysis.loc[analysis.date < target]
    last_seen = prior.groupby("reward_norm").date.max()
    classifier["last_seen"] = classifier.reward_norm.map(last_seen)
    classifier = classifier[["rank", "reward_norm", "category", "score", "days_since_last", "last_seen"]]
    ungated = predict_next(combined, bundle, target, gate=False)
    excluded = [{"reward_norm": reward, "reason": "domain_discontinued" if reward in DOMAIN_DISCONTINUED else "recency_gate"} for reward in ungated.reward_norm if reward not in set(rf.reward_norm)]
    prophet = None if skip_prophet else prophet_next(combined, target).to_dict("records")
    raw_meta = json.loads(Path("data/raw/inven_20563_meta.json").read_text(encoding="utf-8"))
    meta = {"generated_at": datetime.now(timezone.utc).isoformat(), "data_through": data_through, "backtest_data_through": as_of, "target_date": target, "sources": [{"name": "인벤 역대 썬데이메이플 정리", "url": "https://www.inven.co.kr/board/maple/2304/20563", "fetched_at": raw_meta["fetched_at"]}, {"name": "수동 관측(공식 공지 확인)", "path": "data/interim/manual_obs_20260614.csv"}], "split_cutoff": SPLIT_CUTOFF, "random_seed": RANDOM_SEED}
    history = []
    for date, group in analysis.groupby("date", sort=True):
        contexts = group.event_context.dropna()
        history.append({"date": date, "event_context": contexts.iloc[0] if len(contexts) else None, "is_special": bool(group.is_special.fillna(False).any()), "rewards": group[["reward_raw", "reward_norm", "category"]].to_dict("records")})
    rewards = []
    for reward, group in analysis.groupby("reward_norm", sort=True):
        categories = group.category.dropna().mode()
        rewards.append({"reward_norm": reward, "category": categories.iloc[0] if len(categories) else None, "appearances": len(group), "first_seen": group.date.min(), "last_seen": group.date.max(), "median_cycle_days": group.cycle_days.median(), "is_discontinued": bool(group.is_discontinued.fillna(False).any())})
    payloads = {"meta": meta, "forecast": {"target_date": target, "classifier": classifier.to_dict("records"), "prophet": prophet, "excluded": excluded}, "backtest": {"split_cutoff": SPLIT_CUTOFF, "metrics": metrics.to_dict("records"), "per_date": per_date.rename(columns={"rf_top": "predicted", "rf_hit": "hit"}).to_dict("records")}, "history": history[::-1], "rewards": rewards}
    output = Path(out)
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (output / f"{name}.json").write_text(json.dumps(_clean(payload), ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return payloads


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/site")
    parser.add_argument("--target-date")
    parser.add_argument("--skip-prophet", action="store_true")
    args = parser.parse_args(argv)
    export_site_data(args.out, args.target_date, args.skip_prophet)


if __name__ == "__main__":
    main()
