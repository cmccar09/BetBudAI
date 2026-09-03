"""
Feature-level Plackett-Luce (win-only conditional logit) rebuild — 2026-09-03 session.

Same methodology as vegas.md's 2026-09-01 "Model fit at both aggregate and
feature level" section, rerun on the larger 2026-06-01 -> 2026-09-02 dataset
(3,367 races / 33,552 observations after the exactly-one-winner filter),
using the empirically dead-factor list found by factor_stats.py on THIS
dataset (not blindly copied from the older, narrower-window analysis).

Model: race-conditional softmax (P(winner) = softmax(X @ w) over the race's
valid runners), L2-regularized on standardized features, no intercept
(a race-level constant cancels under softmax). Fit by full-batch gradient
descent (Adam) — scipy is unavailable in this environment (blocked by a
local Application Control policy), so this is hand-rolled in numpy.

CV: leave-one-day-out across every date present in the (sub)population.
lambda chosen by the CV curve itself (no nested loop) — same as vegas.md's
stated method ("L2-regularized ... lambda chosen via the same leave-one-
day-out CV").

Usage: python fit_feature_model.py [--segment aw|full] [--lambdas 1,3,10,30]
"""
import argparse
import json
import numpy as np
from pathlib import Path

DATASET = Path(__file__).parent / 'dataset.json'
TEMP = 20.0  # matches live get_vegas_picks() score->prob softmax temperature

# ── Feature set (from factor_stats.py on this dataset) ─────────────────────
# 67 keys observed total. Removed:
#   21 truly dead (0/33552 nonzero): DISTANCE_HINT, aw_evening_penalty,
#     aw_low_class_penalty, bounce_back, cheltenham_festival, claiming_jockey,
#     course_performance, heavy_going_penalty, irish_handicap_penalty,
#     jockey_course_bonus, jockey_hot_form, losing_streak_penalty,
#     meeting_focus, novice_penalty, pace_profile, race_type_adj,
#     sire_going_signal, track_handedness, track_pattern_bonus,
#     trainer_hot_form, watchlist_improver
#   4 meta/post-hoc corrections (not independent factors): signals_fired,
#     score_cap, final_score_cap, no_form_cap
#   4 effectively-dead / too-thin-to-fit (<30 nonzero obs out of 33,552):
#     cd_bonus (11), database_history (6), db_history (2), PRICE_DROP_FLAG (1)
CANDIDATE_FEATURES = [
    'DEBUTANT_MARKET_CONFIDENCE', 'DEBUTANT_STEAM', 'PEDIGREE_CLASS',
    'PURCHASE_PRICE', 'SIRE_TIER', 'age_bonus', 'beaten_fav_penalty',
    'consistency', 'deep_form', 'distance_suitability', 'draw_bias',
    'favorite_correction', 'form_trend', 'going_suitability', 'jockey_quality',
    'large_field_penalty', 'learning_odds', 'maiden_fav_penalty',
    'market_leader', 'market_leader_no_form', 'official_rating_bonus',
    'optimal_odds', 'price_steam', 'recent_win', 'rpr_class',
    'same_trainer_rival', 'short_form_improvement', 'small_field_bonus',
    'sweet_spot', 'timeform_stars', 'total_wins', 'trainer_live_form',
    'trainer_reputation', 'unexposed_bonus', 'unknown_trainer_penalty',
    'weight_penalty', 'winless_penalty', 'won_last_2_runs',
]

AW_TRACKS = {'lingfield', 'kempton', 'southwell', 'wolverhampton', 'newcastle', 'dundalk'}


def load_races(segment='full'):
    data = json.loads(DATASET.read_text())
    races = data['races']
    out = []
    for race in races:
        date_str, course, race_time = race['race_key']
        if segment == 'aw' and course.strip().lower() not in AW_TRACKS:
            continue
        runners = []
        for r in race['runners']:
            try:
                odds = float(r.get('odds') or 0)
            except (TypeError, ValueError):
                odds = 0.0
            if odds <= 1.01:
                continue
            bd = r.get('score_breakdown') or {}
            feat = np.array([float(bd.get(k, 0) or 0) for k in CANDIDATE_FEATURES], dtype=np.float64)
            try:
                score = float(r.get('comprehensive_score') or 0)
            except (TypeError, ValueError):
                score = 0.0
            runners.append({
                'horse': r.get('horse'),
                'odds': odds,
                'outcome': r.get('outcome'),
                'feat': feat,
                'score': score,
            })
        wins = [r for r in runners if r['outcome'] == 'win']
        if len(runners) < 2 or len(wins) != 1:
            continue
        winner_idx = next(i for i, r in enumerate(runners) if r['outcome'] == 'win')
        out.append({'date': date_str, 'course': course, 'race_time': race_time,
                     'runners': runners, 'winner_idx': winner_idx})
    return out


def build_tensor(races):
    n = len(races)
    d = len(CANDIDATE_FEATURES)
    max_field = max(len(r['runners']) for r in races)
    X = np.zeros((n, max_field, d), dtype=np.float64)
    mask = np.zeros((n, max_field), dtype=bool)
    winner_idx = np.zeros(n, dtype=np.int64)
    odds = np.zeros((n, max_field), dtype=np.float64)
    old_score = np.zeros((n, max_field), dtype=np.float64)
    dates = np.array([r['date'] for r in races])
    n_runners = np.zeros(n, dtype=np.int64)
    for i, race in enumerate(races):
        m = len(race['runners'])
        n_runners[i] = m
        for j, runner in enumerate(race['runners']):
            X[i, j, :] = runner['feat']
            mask[i, j] = True
            odds[i, j] = runner['odds']
            old_score[i, j] = runner['score']
        winner_idx[i] = race['winner_idx']
    return dict(X=X, mask=mask, winner_idx=winner_idx, odds=odds,
                old_score=old_score, dates=dates, n_runners=n_runners)


def softmax_masked(logits, mask):
    """logits, mask: (n, max_field). Returns probs summing to 1 over valid slots."""
    masked_logits = np.where(mask, logits, -1e18)
    m = masked_logits.max(axis=1, keepdims=True)
    ex = np.where(mask, np.exp(masked_logits - m), 0.0)
    s = ex.sum(axis=1, keepdims=True)
    s = np.where(s <= 0, 1.0, s)
    return ex / s


def nll_and_grad(w, X, mask, winner_idx, lam):
    n = X.shape[0]
    logits = np.einsum('nmd,d->nm', X, w)
    probs = softmax_masked(logits, mask)
    p_winner = probs[np.arange(n), winner_idx]
    p_winner = np.clip(p_winner, 1e-12, 1.0)
    nll = -np.sum(np.log(p_winner)) + 0.5 * lam * np.sum(w ** 2)
    onehot = np.zeros_like(probs)
    onehot[np.arange(n), winner_idx] = 1.0
    diff = probs - onehot  # (n, max_field)
    grad = np.einsum('nmd,nm->d', X, diff) + lam * w
    return nll, grad


def fit_weights(X, mask, winner_idx, lam, epochs=400, lr=0.05):
    d = X.shape[2]
    w = np.zeros(d)
    m_t = np.zeros(d)
    v_t = np.zeros(d)
    beta1, beta2, eps = 0.9, 0.999, 1e-8
    n = max(X.shape[0], 1)
    for t in range(1, epochs + 1):
        _, grad = nll_and_grad(w, X, mask, winner_idx, lam)
        grad = grad / n
        m_t = beta1 * m_t + (1 - beta1) * grad
        v_t = beta2 * v_t + (1 - beta2) * (grad ** 2)
        m_hat = m_t / (1 - beta1 ** t)
        v_hat = v_t / (1 - beta2 ** t)
        w -= lr * m_hat / (np.sqrt(v_hat) + eps)
    return w


def standardize(X, mask, train_mask_rows):
    """Compute mean/std from train rows' valid slots, apply to all of X."""
    Xtr = X[train_mask_rows]
    Mtr = mask[train_mask_rows]
    flat = Xtr[Mtr]  # (n_valid_obs, d)
    mean = flat.mean(axis=0)
    std = flat.std(axis=0)
    std = np.where(std < 1e-8, 1.0, std)
    Xs = (X - mean) / std
    Xs = Xs * mask[:, :, None]  # zero out padded slots again after shift
    return Xs, mean, std


def market_probs(odds, mask):
    inv = np.where(mask, 1.0 / np.where(odds > 0, odds, 1e18), 0.0)
    s = inv.sum(axis=1, keepdims=True)
    s = np.where(s <= 0, 1.0, s)
    return inv / s


def old_score_probs(old_score, mask, temp=TEMP):
    masked = np.where(mask, old_score, -1e18)
    m = masked.max(axis=1, keepdims=True)
    ex = np.where(mask, np.exp((masked - m) / temp), 0.0)
    s = ex.sum(axis=1, keepdims=True)
    s = np.where(s <= 0, 1.0, s)
    return ex / s


def nll_from_probs(probs, winner_idx):
    n = probs.shape[0]
    p = probs[np.arange(n), winner_idx]
    p = np.clip(p, 1e-12, 1.0)
    return -np.log(p)  # per-race NLL array


def run(segment, lambdas):
    races = load_races(segment)
    n_dates = len({r['date'] for r in races})
    print(f'[{segment}] {len(races)} races across {n_dates} dates (after >=2 '
          f'valid-odds runners + exactly-one-winner filter)')
    if len(races) < 20:
        print('Too few races to fit — skipping.')
        return

    t = build_tensor(races)
    X, mask, winner_idx = t['X'], t['mask'], t['winner_idx']
    odds, old_score, dates = t['odds'], t['old_score'], t['dates']
    unique_dates = sorted(set(dates.tolist()))

    mkt_p = market_probs(odds, mask)
    old_p = old_score_probs(old_score, mask)
    mkt_nll_per_race = nll_from_probs(mkt_p, winner_idx)
    old_nll_per_race = nll_from_probs(old_p, winner_idx)
    print(f'Market NLL/race:            {mkt_nll_per_race.mean():.3f}')
    print(f'Old hand-tuned score NLL/race: {old_nll_per_race.mean():.3f}  '
          f'(TEMP={TEMP} softmax of comprehensive_score, no market blend)')
    uniform_nll = np.log(t['n_runners'].astype(float)).mean()
    print(f'Uniform (no-info) NLL/race: {uniform_nll:.3f}  (mean log field size)')

    results = {}
    for lam in lambdas:
        fold_nlls = []
        fold_weighted_n = []
        coef_signs = {k: [] for k in CANDIDATE_FEATURES}  # per-fold sign, when |coef|>1e-6
        blended_nlls = []
        for held_out in unique_dates:
            train_rows = dates != held_out
            test_rows = dates == held_out
            n_test = int(test_rows.sum())
            if n_test == 0:
                continue
            Xs, mean, std = standardize(X, mask, train_rows)
            w = fit_weights(Xs[train_rows], mask[train_rows], winner_idx[train_rows], lam)
            for k, coef in zip(CANDIDATE_FEATURES, w):
                if abs(coef) > 1e-6:
                    coef_signs[k].append(1 if coef > 0 else -1)

            logits_test = np.einsum('nmd,d->nm', Xs[test_rows], w)
            probs_test = softmax_masked(logits_test, mask[test_rows])
            nll_test = nll_from_probs(probs_test, winner_idx[test_rows])
            fold_nlls.append(nll_test.sum())
            fold_weighted_n.append(n_test)

            # Blend: fit alpha/beta on TRAIN only (log-lik of blended softmax over
            # training races, using this fold's already-fit w for p_model), then
            # apply to the held-out day. No peeking at held-out day for alpha/beta.
            logits_train = np.einsum('nmd,d->nm', Xs[train_rows], w)
            p_model_train = softmax_masked(logits_train, mask[train_rows])
            p_mkt_train = mkt_p[train_rows]
            m_train = mask[train_rows]
            wi_train = winner_idx[train_rows]

            best_ab = (1.0, 1.0)
            best_train_nll = np.inf
            grid = np.arange(0.0, 1.76, 0.25)
            log_pm_train = np.where(m_train, np.log(np.clip(p_model_train, 1e-12, 1)), 0.0)
            log_mk_train = np.where(m_train, np.log(np.clip(p_mkt_train, 1e-12, 1)), 0.0)
            for a in grid:
                for b in grid:
                    if a == 0 and b == 0:
                        continue
                    comb_logit = a * log_pm_train + b * log_mk_train
                    comb_p = softmax_masked(comb_logit, m_train)
                    nll_tr = nll_from_probs(comb_p, wi_train).sum()
                    if nll_tr < best_train_nll:
                        best_train_nll = nll_tr
                        best_ab = (a, b)

            a, b = best_ab
            p_model_test = probs_test
            p_mkt_test = mkt_p[test_rows]
            m_test = mask[test_rows]
            log_pm_test = np.where(m_test, np.log(np.clip(p_model_test, 1e-12, 1)), 0.0)
            log_mk_test = np.where(m_test, np.log(np.clip(p_mkt_test, 1e-12, 1)), 0.0)
            comb_logit_test = a * log_pm_test + b * log_mk_test
            comb_p_test = softmax_masked(comb_logit_test, m_test)
            blend_nll_test = nll_from_probs(comb_p_test, winner_idx[test_rows])
            blended_nlls.append((blend_nll_test.sum(), n_test, a, b))

        total_n = sum(fold_weighted_n)
        mean_cv_nll = sum(fold_nlls) / total_n if total_n else float('nan')
        blend_total_nll = sum(b[0] for b in blended_nlls)
        blend_mean_nll = blend_total_nll / total_n if total_n else float('nan')
        mean_alpha = np.mean([b[2] for b in blended_nlls]) if blended_nlls else float('nan')
        mean_beta = np.mean([b[3] for b in blended_nlls]) if blended_nlls else float('nan')

        signal, noise, unfired = [], [], []
        for k in CANDIDATE_FEATURES:
            signs = coef_signs[k]
            if len(signs) == 0:
                unfired.append(k)
            elif all(s == signs[0] for s in signs):
                signal.append((k, len(signs)))
            else:
                noise.append((k, len(signs), signs.count(1), signs.count(-1)))

        results[lam] = dict(mean_cv_nll=mean_cv_nll, blend_mean_nll=blend_mean_nll,
                             mean_alpha=mean_alpha, mean_beta=mean_beta,
                             signal=signal, noise=noise, unfired=unfired,
                             n_folds=len(fold_nlls))
        print(f'\nlambda={lam:>5}: feature-model CV NLL/race={mean_cv_nll:.3f}  '
              f'blended CV NLL/race={blend_mean_nll:.3f}  '
              f'(mean alpha={mean_alpha:.2f}, beta={mean_beta:.2f}, folds={len(fold_nlls)})')

    best_lam = min(results, key=lambda l: results[l]['mean_cv_nll'])
    print(f'\n=== Best lambda by feature-model CV NLL: {best_lam} ===')
    r = results[best_lam]
    print(f'Feature model CV NLL/race: {r["mean_cv_nll"]:.3f}')
    print(f'Blended CV NLL/race:       {r["blend_mean_nll"]:.3f}  '
          f'(mean alpha={r["mean_alpha"]:.2f}, beta={r["mean_beta"]:.2f})')
    print(f'Market NLL/race:           {mkt_nll_per_race.mean():.3f}')
    print(f'\nSIGNAL (sign-stable across all folds where nonzero), n_folds_fired:')
    for k, n in sorted(r['signal'], key=lambda x: -x[1]):
        print(f'  {k:30s} fired in {n}/{r["n_folds"]} folds')
    print(f'\nNOISE (sign flips across folds):')
    for k, n, pos, neg in r['noise']:
        print(f'  {k:30s} fired in {n}/{r["n_folds"]} folds ({pos} positive / {neg} negative)')
    if r['unfired']:
        print(f'\nNEVER FIRED in any fold (coef stayed ~0 everywhere): {r["unfired"]}')

    out = {
        'segment': segment,
        'n_races': len(races),
        'n_dates': n_dates,
        'market_nll': float(mkt_nll_per_race.mean()),
        'old_score_nll': float(old_nll_per_race.mean()),
        'uniform_nll': float(uniform_nll),
        'best_lambda': best_lam,
        'feature_model_cv_nll': r['mean_cv_nll'],
        'blended_cv_nll': r['blend_mean_nll'],
        'mean_alpha': r['mean_alpha'],
        'mean_beta': r['mean_beta'],
        'signal_features': [k for k, n in r['signal']],
        'noise_features': [k for k, n, p, ng in r['noise']],
        'never_fired_in_cv': r['unfired'],
        'all_lambda_results': {str(l): {kk: vv for kk, vv in v.items() if kk not in ('signal', 'noise', 'unfired')}
                                for l, v in results.items()},
    }
    out_path = Path(__file__).parent / f'fit_results_{segment}.json'
    out_path.write_text(json.dumps(out, indent=2))
    print(f'\nWrote {out_path}')

    # Fit final weights on ALL data at best lambda for downstream use (paper trading)
    Xs_full, mean_full, std_full = standardize(X, mask, np.ones(len(races), dtype=bool))
    w_full = fit_weights(Xs_full, mask, winner_idx, best_lam)
    model_out = {
        'segment': segment,
        'features': CANDIDATE_FEATURES,
        'weights': w_full.tolist(),
        'feature_mean': mean_full.tolist(),
        'feature_std': std_full.tolist(),
        'lambda': best_lam,
        'temp_for_reference': TEMP,
        'trained_on_races': len(races),
        'trained_on_dates': [str(d) for d in unique_dates],
    }
    model_path = Path(__file__).parent / f'model_{segment}.json'
    model_path.write_text(json.dumps(model_out, indent=2))
    print(f'Wrote {model_path}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', default='full', choices=['full', 'aw'])
    ap.add_argument('--lambdas', default='1,3,10,30,100')
    args = ap.parse_args()
    lambdas = [float(x) for x in args.lambdas.split(',')]
    run(args.segment, lambdas)
