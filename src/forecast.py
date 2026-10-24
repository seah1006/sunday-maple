from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

from src.predict_dataset import FEATURE_COLUMNS, DEFAULT_RECENCY_GATE_DAYS, DOMAIN_DISCONTINUED, _eligible_rows, _candidate_rewards, build_prediction_frame, build_inference_frame, gate_candidates
from src.prophet_cycle import build_weekly_series, fit_predict_reward, rank_candidates

SPLIT_CUTOFF = pd.Timestamp("2025-01-01")
RANDOM_SEED = 42


@dataclass
class ClassifierBundle:
    model: RandomForestClassifier
    feature_columns: list[str]
    prediction_frame: pd.DataFrame


def train_classifier(tidy, split_cutoff=SPLIT_CUTOFF, seed=RANDOM_SEED):
    frame = build_prediction_frame(tidy, candidate_cutoff=split_cutoff)
    features = pd.get_dummies(frame[FEATURE_COLUMNS], columns=["category"], dummy_na=True).fillna(-1)
    train = frame["date"] < pd.Timestamp(split_cutoff)
    model = RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=seed)
    model.fit(features.loc[train], frame.loc[train, "y"].astype(int))
    return ClassifierBundle(model, features.columns.tolist(), frame)


def _evaluate(y_true, y_score, dates):
    y_true = pd.Series(y_true).astype(int).reset_index(drop=True)
    y_score = pd.Series(y_score).astype(float).reset_index(drop=True)
    dates = pd.Series(dates).reset_index(drop=True)
    y_pred = (y_score >= 0.5).astype(int)
    work = pd.DataFrame({"date": dates, "y": y_true, "score": y_score})
    def date_hit(group):
        k = int(group["y"].sum())
        if k < 1:
            return np.nan
        return float(group.nlargest(k, "score")["y"].max())
    auc = roc_auc_score(y_true, y_score) if y_true.nunique() > 1 else np.nan
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": auc,
        "date_hit_rate": work.groupby("date", sort=True).apply(date_hit).mean(),
    }


def backtest(tidy, bundle, split_cutoff=SPLIT_CUTOFF, seed=RANDOM_SEED, include_prophet=True):
    frame = bundle.prediction_frame
    train = frame.loc[frame.date < pd.Timestamp(split_cutoff)]
    test = frame.loc[frame.date >= pd.Timestamp(split_cutoff)]
    features = pd.get_dummies(frame[FEATURE_COLUMNS], columns=["category"], dummy_na=True).reindex(columns=bundle.feature_columns, fill_value=0).fillna(-1)
    logistic = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed)
    logistic.fit(features.loc[train.index], train.y.astype(int))
    rf_scores = bundle.model.predict_proba(features.loc[test.index])[:, 1]
    scores = [
        ("gap_rule", "간격규칙", (test.roll_gap_median.notna() & (test.days_since_last >= test.roll_gap_median)).astype(float)),
        ("prior_rate", "사전확률", test.past_rate.clip(0, 1)),
        ("logistic", "로지스틱", logistic.predict_proba(features.loc[test.index])[:, 1]),
        ("random_forest", "랜덤포레스트", rf_scores),
    ]
    metrics = [{"method": method, "label": label, **_evaluate(test.y, score, test.date)} for method, label, score in scores]
    scored = test.assign(score=rf_scores)
    per_date = []
    for date, group in scored.groupby("date", sort=True):
        actual = group.loc[group.y == 1, "reward_norm"].tolist()
        top = group.nlargest(len(actual), "score")["reward_norm"].tolist()
        per_date.append({"date": date, "actual": actual, "rf_top": top, "rf_hit": float(bool(set(actual) & set(top))) if actual else np.nan})
    if include_prophet:
        eligible = _eligible_rows(tidy)
        candidates = _candidate_rewards(eligible.loc[eligible.date < pd.Timestamp(split_cutoff)], 20)
        dates = pd.DatetimeIndex(sorted(eligible.loc[eligible.date >= pd.Timestamp(split_cutoff), "date"].unique()))
        actual_by_date = {date: set(group.reward_norm) for date, group in eligible.groupby("date", sort=False)}
        forecasts = {}
        for reward in candidates:
            series = build_weekly_series(tidy, reward, split_cutoff)
            forecasts[reward] = fit_predict_reward(series, dates).set_index("ds")["yhat"]
        hits = []
        for date in dates:
            gated = gate_candidates(eligible, candidates, date)
            actual = actual_by_date.get(date, set())
            k = len(actual & set(candidates))
            ranked = sorted(gated, key=lambda reward: (-float(forecasts[reward].loc[date]), reward))
            hits.append(float(bool(set(ranked[:k]) & actual)) if k and gated else np.nan)
        metrics.append({"method": "prophet", "label": "Prophet", "date_hit_rate": pd.Series(hits).mean()})
    return pd.DataFrame(metrics), pd.DataFrame(per_date)


def predict_next(tidy, bundle, target_date, gate=True):
    frame = build_inference_frame(tidy, target_date, candidate_cutoff=SPLIT_CUTOFF, recency_gate_days=DEFAULT_RECENCY_GATE_DAYS if gate else None, domain_discontinued=DOMAIN_DISCONTINUED if gate else frozenset())
    features = pd.get_dummies(frame[FEATURE_COLUMNS], columns=["category"], dummy_na=True).reindex(columns=bundle.feature_columns, fill_value=0).fillna(-1)
    table = frame[["date", "reward_norm"]].copy()
    table["score"] = bundle.model.predict_proba(features)[:, 1]
    table = table.sort_values(["score", "reward_norm"], ascending=[False, True]).reset_index(drop=True)
    table["rank"] = np.arange(1, len(table) + 1)
    table["score_pct"] = (table["score"] * 100).round(1)
    return table


def prophet_next(tidy, target_date, split_cutoff=SPLIT_CUTOFF):
    eligible = _eligible_rows(tidy)
    candidates = _candidate_rewards(eligible.loc[eligible.date < pd.Timestamp(split_cutoff)], 20)
    return rank_candidates(tidy, candidates, as_of=target_date, target_date=target_date)


def next_sunday_after(date):
    date = pd.Timestamp(date).normalize()
    return date + pd.Timedelta(days=(6 - date.dayofweek) % 7 or 7)
