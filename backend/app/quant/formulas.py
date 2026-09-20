"""Single source of truth for quantitative math. Owned by Satish.

All formulas per docs/math_eq.md. Samarth/Somesh must import from here.
Uses NumPy + Pandas (+ SciPy where needed). No quantum, no LLM here.

Extended with Somesh-compatible signatures (backward compatible).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

# ---------- Returns ----------

def simple_return(prices: pd.Series) -> pd.Series:
    return prices.pct_change()


def log_return(prices: pd.Series) -> pd.Series:
    return np.log(prices / prices.shift(1))


def cumulative_return(returns: pd.Series) -> float:
    r = returns.dropna()
    if len(r) == 0:
        return 0.0
    return float((1 + r).prod() - 1)


def total_return(prices: pd.Series) -> float:
    """Total return over entire period (Somesh API)."""
    if len(prices) < 2:
        return 0.0
    return float(prices.iloc[-1] / prices.iloc[0] - 1)


def cagr(start_or_prices, end_value=None, years=None, trading_days=252):
    """CAGR - supports both signatures: (start, end, years) or (prices, trading_days)."""
    if isinstance(start_or_prices, pd.Series):
        prices = start_or_prices.dropna()
        n_days = len(prices)
        if n_days < 2 or prices.iloc[0] <= 0:
            return 0.0
        total = prices.iloc[-1] / prices.iloc[0]
        yrs = n_days / trading_days
        return float(total ** (1.0 / yrs) - 1.0)
    else:
        start_val = float(start_or_prices)
        if start_val <= 0 or end_value is None or years is None or years <= 0:
            return 0.0
        return float((end_value / start_val) ** (1.0 / years) - 1.0)


def annualized_return(returns: pd.Series, periods_per_year: int = 252, trading_days: int | None = None) -> float:
    r = returns.dropna()
    if len(r) == 0:
        return 0.0
    total = (1 + r).prod()
    return float(total ** (periods_per_year / len(r)) - 1)

# Somesh API aliases
def cagr_from_prices(prices: pd.Series, trading_days: int = 252) -> float:
    """Somesh API: CAGR from price series."""
    return cagr(prices, trading_days=trading_days)


# ---------- Indicators ----------

def sma(prices: pd.Series, period: int) -> pd.Series:
    return prices.rolling(period).mean()


def ema(prices: pd.Series, period: int) -> pd.Series:
    alpha = 2 / (period + 1)
    return prices.ewm(alpha=alpha, adjust=False).mean()


def momentum(prices: pd.Series, period: int = 20) -> pd.Series:
    return prices / prices.shift(period) - 1


def z_score(series: pd.Series, window: int = 20) -> pd.Series:
    mu = series.rolling(window).mean()
    sigma = series.rolling(window).std(ddof=1)
    return (series - mu) / sigma.replace(0, np.nan)


def percentile_rank(series: pd.Series, window: int = 252) -> pd.Series:
    return series.rolling(window).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]) / 100, raw=False)


# ---------- Risk ----------

def volatility(
    returns: pd.Series,
    window: int | None = None,
    annualization: int = 252,
    trading_days: int | None = None,
) -> float | pd.Series:
    """
    Volatility of returns.
    If window is provided, returns rolling pd.Series.
    If trading_days is provided, returns annualised scalar float.
    """
    if window is not None and window > 0:
        ann = trading_days or annualization
        return returns.rolling(window=window).std(ddof=1) * np.sqrt(ann)

    if trading_days is not None:
        r = returns.dropna()
        return float(r.std(ddof=1) * np.sqrt(trading_days)) if len(r) > 1 else 0.0

    return returns.rolling(window=20).std(ddof=1) * np.sqrt(annualization)


def downside_deviation(
    returns: pd.Series,
    target_or_rf: float = 0.0,
    trading_days: int | None = None,
    target: float | None = None,
) -> float:
    """Downside deviation below target threshold."""
    t = target if target is not None else target_or_rf
    r = returns.dropna()
    downside = np.minimum(r - t, 0.0)
    ann = np.sqrt(trading_days) if trading_days else 1.0
    return float(np.sqrt((downside ** 2).mean()) * ann)


def sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.05,
    annualization: int = 252,
    trading_days: int | None = None,
) -> float:
    """Annualised Sharpe ratio."""
    ann = trading_days or annualization
    r = returns.dropna()
    if len(r) < 2:
        return 0.0
    sd = float(r.std(ddof=1))
    if sd < 1e-12:
        return 0.0
    excess = float(r.mean() * ann - risk_free_rate)
    vol = sd * np.sqrt(ann)
    return float(excess / vol) if vol != 0 else 0.0


def sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.05,
    annualization: int = 252,
    trading_days: int | None = None,
) -> float:
    """Annualised Sortino ratio."""
    ann = trading_days or annualization
    r = returns.dropna()
    dd = downside_deviation(r) * np.sqrt(ann)
    if dd == 0:
        return 0.0
    excess = float(r.mean() * ann - risk_free_rate)
    return float(excess / dd)


def max_drawdown(equity: pd.Series) -> dict:
    if len(equity) == 0:
        return {"max_drawdown": 0.0, "peak_date": None, "trough_date": None, "recovery_date": None, "series": []}
    peak = equity.cummax()
    dd = (equity - peak) / peak.replace(0, np.nan)
    dd = dd.fillna(0.0)
    trough_idx = dd.idxmin()
    mdd = float(dd.min())
    peak_before = equity.loc[:trough_idx].idxmax()
    after = equity.loc[trough_idx:]
    peak_val = float(equity.loc[peak_before])
    rec_idx = after[after >= peak_val].index
    rec = rec_idx[0] if len(rec_idx) else None
    return {
        "max_drawdown": mdd,
        "peak_date": str(peak_before),
        "trough_date": str(trough_idx),
        "recovery_date": str(rec) if rec is not None else None,
        "series": [{"date": str(i), "value": float(v)} for i, v in zip(dd.index.astype(str), dd.values)][:: max(1, len(dd) // 200)],
    }


def drawdown_duration(equity: pd.Series) -> int:
    return 0  # duration derivable from peak/recovery dates; kept simple


def drawdown_series(equity: pd.Series) -> pd.Series:
    """Drawdown series for each period."""
    peak = equity.cummax()
    dd = (equity - peak) / peak.replace(0, np.nan)
    return dd.fillna(0.0)


def calmar_ratio(
    cagr_or_returns,
    mdd_or_prices=None,
    trading_days: int = 252,
) -> float:
    """Calmar ratio = CAGR / |Max Drawdown|."""
    if isinstance(cagr_or_returns, pd.Series):
        prices = mdd_or_prices if isinstance(mdd_or_prices, pd.Series) else (1.0 + cagr_or_returns).cumprod()
        c = cagr(prices, trading_days=trading_days)
        m = float(max_drawdown(prices)["max_drawdown"])
        return float(c / abs(m)) if m != 0 else 0.0
    else:
        cagr_val = float(cagr_or_returns)
        mdd = float(mdd_or_prices or 0.0)
        if mdd == 0:
            return 0.0
        return float(cagr_val / abs(mdd))


def omega_ratio(returns: pd.Series, threshold: float = 0.0) -> float:
    r = returns.dropna()
    gains = np.maximum(r - threshold, 0).sum()
    losses = np.maximum(threshold - r, 0).sum()
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return float(gains / losses)


def value_at_risk(
    returns: pd.Series,
    confidence: float = 0.95,
    method: str = "historical",
) -> float:
    """Value at Risk (positive magnitude of loss)."""
    r = returns.dropna()
    if len(r) == 0:
        return 0.0
    if method == "parametric":
        mu, sigma = r.mean(), r.std(ddof=1)
        return float(-(mu + sigma * stats.norm.ppf(1 - confidence)))
    return float(-r.quantile(1 - confidence))


def conditional_var(
    returns: pd.Series,
    confidence: float = 0.95,
    method: str = "historical",
) -> float:
    """Conditional Value at Risk / Expected Shortfall (positive magnitude of loss)."""
    r = returns.dropna()
    if len(r) == 0:
        return 0.0
    var = value_at_risk(r, confidence, method=method)
    tail = r[r <= -var]
    if len(tail) == 0:
        return var
    return float(-tail.mean())


# ---------- Benchmark ----------

def beta(strategy_returns: pd.Series, market_returns: pd.Series) -> float:
    """Beta against benchmark."""
    s, m = strategy_returns.align(market_returns, join="inner")
    s, m = s.dropna(), m.dropna()
    s, m = s.align(m, join="inner")
    if len(s) < 2:
        return 0.0
    mv = float(m.var(ddof=1))
    if mv < 1e-12 or pd.isna(mv):
        return 0.0
    cov = float(s.cov(m))
    if pd.isna(cov):
        return 0.0
    return float(cov / mv)


def alpha(
    strategy_or_return,
    beta_or_benchmark,
    market_or_rf: float = 0.05,
    risk_free: float = 0.05,
    trading_days: int = 252,
) -> float:
    """Jensen's Alpha."""
    if isinstance(strategy_or_return, pd.Series):
        r_strat = strategy_or_return
        r_bench = beta_or_benchmark
        rf = float(market_or_rf)
        b = beta(r_strat, r_bench)
        r_s = annualized_return(r_strat, trading_days=trading_days)
        r_m = annualized_return(r_bench, trading_days=trading_days)
        return float(r_s - (rf + b * (r_m - rf)))
    else:
        strat_ret = float(strategy_or_return)
        b_val = float(beta_or_benchmark)
        m_ret = float(market_or_rf)
        return float(strat_ret - (risk_free + b_val * (m_ret - risk_free)))


def treynor_ratio(
    strategy_or_return,
    beta_or_benchmark,
    risk_free: float = 0.05,
    trading_days: int = 252,
) -> float:
    """Treynor ratio."""
    if isinstance(strategy_or_return, pd.Series):
        r_strat = strategy_or_return
        r_bench = beta_or_benchmark
        b = beta(r_strat, r_bench)
        if b == 0:
            return 0.0
        r_s = annualized_return(r_strat, trading_days=trading_days)
        return float((r_s - risk_free) / b)
    else:
        strat_ret = float(strategy_or_return)
        b_val = float(beta_or_benchmark)
        if b_val == 0:
            return 0.0
        return float((strat_ret - risk_free) / b_val)


def tracking_error(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    annualization: int = 252,
) -> float:
    """Annualised tracking error."""
    s, m = strategy_returns.align(benchmark_returns, join="inner")
    diff = (s - m).dropna()
    if len(diff) < 2:
        return 0.0
    return float(diff.std(ddof=1) * np.sqrt(annualization))


def information_ratio(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    annualization: int = 252,
) -> float:
    """Information ratio."""
    s, m = strategy_returns.align(benchmark_returns, join="inner")
    diff = (s - m).dropna()
    te = tracking_error(s, m, annualization)
    if te == 0:
        return 0.0
    return float(diff.mean() * annualization / te)


def _capture(strategy: pd.Series, benchmark: pd.Series, up: bool) -> float:
    s, m = strategy.align(benchmark, join="inner")
    mask = m > 0 if up else m < 0
    if mask.sum() == 0:
        return 0.0
    strat = (1 + s[mask]).prod() - 1
    bench = (1 + m[mask]).prod() - 1
    if bench == 0:
        return 0.0
    return float(strat / bench * 100)


def upside_capture(strategy: pd.Series, benchmark: pd.Series) -> float:
    return _capture(strategy, benchmark, True)


def downside_capture(strategy: pd.Series, benchmark: pd.Series) -> float:
    return _capture(strategy, benchmark, False)


def covariance_matrix(
    returns_df: pd.DataFrame,
    trading_days: int = 252,
) -> np.ndarray:
    """Annualised covariance matrix."""
    return (returns_df.cov() * trading_days).values


def correlation_matrix(returns_df: pd.DataFrame) -> np.ndarray:
    """Correlation matrix."""
    return returns_df.corr().values


# ---------- Trading analytics ----------

def turnover(
    trade_values_or_old,
    avg_portfolio_value_or_new=None,
) -> float:
    """Portfolio turnover."""
    if isinstance(trade_values_or_old, np.ndarray) and isinstance(avg_portfolio_value_or_new, np.ndarray):
        return float(np.abs(avg_portfolio_value_or_new - trade_values_or_old).sum() / 2.0)
    elif isinstance(trade_values_or_old, pd.Series):
        if avg_portfolio_value_or_new is None or avg_portfolio_value_or_new == 0:
            return 0.0
        avg_val = float(avg_portfolio_value_or_new)
        return float(trade_values_or_old.abs().sum() / avg_val)
    return 0.0


def expectancy(
    win_prob_or_wins,
    avg_win_or_losses=None,
    loss_prob=None,
    avg_loss=None,
) -> float:
    """Trading expectancy."""
    if isinstance(win_prob_or_wins, pd.Series) and isinstance(avg_win_or_losses, pd.Series):
        wins, losses = win_prob_or_wins, avg_win_or_losses
        total = len(wins) + len(losses)
        if total == 0:
            return 0.0
        p_win = len(wins) / total
        p_loss = len(losses) / total
        a_win = wins.mean() if len(wins) > 0 else 0.0
        a_loss = abs(losses.mean()) if len(losses) > 0 else 0.0
        return float(p_win * a_win - p_loss * a_loss)
    else:
        wp = float(win_prob_or_wins)
        aw = float(avg_win_or_losses or 0.0)
        lp = float(loss_prob or (1.0 - wp))
        al = float(avg_loss or 0.0)
        return float(wp * aw - lp * al)


def profit_factor(
    gross_profit_or_wins,
    gross_loss_or_losses,
) -> float:
    """Profit factor."""
    if isinstance(gross_profit_or_wins, pd.Series) and isinstance(gross_loss_or_losses, pd.Series):
        gp = gross_profit_or_wins.sum() if len(gross_profit_or_wins) > 0 else 0.0
        gl = abs(gross_loss_or_losses.sum()) if len(gross_loss_or_losses) > 0 else 0.0
    else:
        gp = float(gross_profit_or_wins)
        gl = abs(float(gross_loss_or_losses))
    if gl == 0:
        return float("inf") if gp > 0 else 0.0
    return float(gp / gl)


def win_rate(wins: int, total: int) -> float:
    return float(wins / total) if total else 0.0


def risk_reward(avg_win: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 0.0
    return float(avg_win / abs(avg_loss))


def max_consecutive_losses(trade_pnl_or_results) -> int:
    """Longest streak of consecutive losing trades."""
    if isinstance(trade_pnl_or_results, list):
        best = cur = 0
        for w in trade_pnl_or_results:
            cur = 0 if w else cur + 1
            best = max(best, cur)
        return best
    elif isinstance(trade_pnl_or_results, pd.Series):
        losing = trade_pnl_or_results < 0
        if not losing.any():
            return 0
        groups = (~losing).cumsum()
        return int(losing.groupby(groups).sum().max())
    return 0


def position_size(
    capital: float,
    risk_per_trade_or_fraction: float,
    entry_price_or_stop_distance: float,
    stop_loss: float | None = None,
) -> float:
    """Position size based on risk."""
    if stop_loss is not None:
        risk_amount = capital * risk_per_trade_or_fraction
        per_share_risk = abs(entry_price_or_stop_distance - stop_loss)
        if per_share_risk == 0:
            return 0.0
        return float(risk_amount / per_share_risk)
    else:
        stop_dist = entry_price_or_stop_distance
        if stop_dist <= 0:
            return 0.0
        return float(capital * risk_per_trade_or_fraction / stop_dist)


def mae_mfe(entry: float, path: pd.Series) -> tuple[float, float]:
    rel = (path - entry) / entry
    return float(rel.min()), float(rel.max())


def drawdown_series(equity: pd.Series) -> pd.Series:
    """Drawdown series for each period."""
    peak = equity.cummax()
    dd = (equity - peak) / peak.replace(0, np.nan)
    return dd.fillna(0.0)


# ---------- Relationship / regime ----------

def regime_score(
    returns_or_ret,
    vol,
    momentum_series_or_mom,
    vol_val=None,
    w=(0.35, 0.30, 0.20, 0.15),
) -> float | pd.DataFrame:
    """Composite regime score / feature matrix."""
    if isinstance(returns_or_ret, pd.Series) and isinstance(vol, pd.Series) and isinstance(momentum_series_or_mom, pd.Series):
        return pd.DataFrame({
            "returns": returns_or_ret,
            "volatility": vol,
            "momentum": momentum_series_or_mom,
        }).dropna()
    else:
        ret = float(returns_or_ret)
        trend = float(vol)
        mom = float(momentum_series_or_mom)
        v = float(vol_val or 0.0)
        wr, wt, wm, wv = w
        return float(wr * ret + wt * trend + wm * mom - wv * v)


def rolling_statistics(
    prices_or_series: pd.Series,
    window: int = 20,
) -> pd.DataFrame:
    """Rolling summary statistics."""
    rets = simple_return(prices_or_series)
    return pd.DataFrame({
        "sma": sma(prices_or_series, window),
        "vol": volatility(rets, window=window),
        "momentum": momentum(prices_or_series, window),
    }).dropna()


# ---------- Portfolio ----------

def portfolio_return(weights: np.ndarray, expected_returns: np.ndarray) -> float:
    return float(np.dot(weights, expected_returns))


def portfolio_variance(weights: np.ndarray, cov: np.ndarray) -> float:
    return float(weights.T @ cov @ weights)


def portfolio_volatility(weights: np.ndarray, cov: np.ndarray) -> float:
    return float(np.sqrt(max(portfolio_variance(weights, cov), 0)))


def portfolio_sharpe(weights: np.ndarray, expected_returns: np.ndarray, cov: np.ndarray, risk_free: float = 0.05) -> float:
    vol = portfolio_volatility(weights, cov)
    if vol == 0:
        return 0.0
    return float((portfolio_return(weights, expected_returns) - risk_free) / vol)


def equal_weight(n: int) -> np.ndarray:
    return np.full(n, 1 / n)


def inverse_volatility_weight(vols: np.ndarray) -> np.ndarray:
    inv = 1 / np.maximum(vols, 1e-12)
    return inv / inv.sum()


# ---------- Trading analytics ----------

def rolling_correlation(a: pd.Series, b: pd.Series, window: int = 30) -> pd.Series:
    return a.rolling(window).corr(b)


def regime_score(ret: float, trend: float, mom: float, vol: float, w=(0.35, 0.30, 0.20, 0.15)) -> float:
    wr, wt, wm, wv = w
    return float(wr * ret + wt * trend + wm * mom - wv * vol)


def rolling_statistics(prices: pd.Series, window: int = 20) -> pd.DataFrame:
    rets = simple_return(prices)
    return pd.DataFrame({
        "sma": sma(prices, window),
        "vol": volatility(rets, window),
        "momentum": momentum(prices, window),
    })
