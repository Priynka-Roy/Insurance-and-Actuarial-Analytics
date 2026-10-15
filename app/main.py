"""Aggregate-only insurance analytics interface; no data download or fitting."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.styles import apply_styles

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "dashboard.json"
SECTIONS = (
    "Insurance Overview", "Portfolio Explorer", "Claim Frequency", "Claim Severity",
    "Pure Premium & Pricing", "Model Validation", "Portfolio Risk Simulator",
    "Actuarial Governance & About",
)
COLORS = ["#147b7d", "#193c58", "#8ca7bb", "#d99b44", "#706a9c"]


@st.cache_data(show_spinner=False)
def load_dashboard(path: str, modified: int) -> dict:
    """Read only the repository's JSON artifact, with cache invalidation on edit."""
    del modified
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def humanize(key):
    return str(key).replace("_", " ").replace("tweedie", "Tweedie").capitalize()


def number(value, decimals=2):
    if value is None:
        return "Unavailable"
    if isinstance(value, (int, float)):
        return f"{value:,.{decimals}f}"
    return str(value)


def table(rows, caption=None):
    if isinstance(rows, dict):
        rows = [{"measure": humanize(k), "value": v} for k, v in rows.items()]
    if not rows:
        st.info("This diagnostic is unavailable in the saved analysis.")
        return
    frame = pd.DataFrame(rows)
    for column in frame.columns:
        if frame[column].map(lambda x: isinstance(x, (dict, list))).any():
            frame[column] = frame[column].map(
                lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x)
    st.dataframe(frame, hide_index=True, width="stretch")
    if caption:
        st.caption(caption)


def chart(fig, title=None, ytitle=None):
    fig.update_layout(
        template="plotly_white", font={"family": "Arial", "color": "#203d51"},
        colorway=COLORS, margin={"l": 30, "r": 25, "t": 55 if title else 25, "b": 40},
        title=title, height=380, legend={"orientation": "h", "y": -0.22},
        paper_bgcolor="white", plot_bgcolor="white", yaxis_title=ytitle,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})


def hero(section, description):
    st.markdown('<p class="eyebrow">ACTUARYLAB AI · INSURANCE ANALYTICS</p>', unsafe_allow_html=True)
    st.title(section)
    st.markdown(f'<p class="lead">{description}</p>', unsafe_allow_html=True)


def case_study(data, letter):
    cases = data.get("case_studies", [])
    case = next((c for c in cases if str(c.get("id", c.get("case", ""))).upper().replace("CASE ", "") == letter), None)
    if case is None:
        return
    with st.expander(f"Guided case {letter} · {case.get('title', case.get('question', 'Explore the evidence'))}"):
        for key in ("question", "method", "results", "result", "interpretation", "limitations", "limitation"):
            value = case.get(key)
            if value is None:
                continue
            st.markdown(f"**{humanize(key)}**")
            if isinstance(value, list) and value and isinstance(value[0], dict):
                table(value)
            elif isinstance(value, dict):
                table(value)
            elif isinstance(value, list):
                for item in value:
                    st.write(f"• {item}")
            else:
                st.write(value)


def model_comparison(data, family):
    rows = data.get("models", {}).get(family, [])
    partition = st.radio("Evaluation partition", ["test", "validation"],
                         format_func=lambda x: "Final holdout" if x == "test" else "Development validation",
                         horizontal=True, key=f"partition_{family}")
    flat = []
    for row in rows:
        metrics = row.get(partition, {})
        flat.append({"Model": row.get("model", row.get("name", "Unnamed")),
                     "Selected on validation": row.get("selected", False), **metrics})
    primary_metric = {"frequency": "poisson_deviance_per_exposure", "severity": "gamma_deviance", "pure_premium": "tweedie_deviance_p1_5"}[family]
    metric_rows = [{"Model": r["Model"], "Score": r.get(primary_metric),
                    "Choice": "Selected on validation" if r["Selected on validation"] else "Comparator"} for r in flat]
    if metric_rows:
        fig = px.bar(pd.DataFrame(metric_rows), x="Score", y="Model", color="Choice", orientation="h",
                     color_discrete_map={"Selected on validation": COLORS[0], "Comparator": COLORS[2]})
        chart(fig, f"{humanize(primary_metric)} · {'holdout' if partition == 'test' else 'validation'}", None)
        st.caption("The highlighted model was selected using validation data. The holdout chart does not change that choice.")
    frame = pd.DataFrame(flat)
    if not frame.empty:
        frame.columns = [humanize(c) for c in frame.columns]
    table(frame.to_dict("records"), "Lower actuarial deviance is better. Each target is evaluated on its own compatible scoring rule; selection used development validation only.")
    return frame


def metric_grid(items):
    for start in range(0, len(items), 4):
        columns = st.columns(4)
        for col, (label, value, help_text) in zip(columns, items[start:start + 4], strict=False):
            col.metric(label, value, help=help_text)


def overview(data):
    hero("Insurance Overview", "From historical motor policies to exposure-aware claim models, transparent pricing assumptions and simulated portfolio risk.")
    s = data["summary"]
    specs = [
        ("Reconciled modeling policies", "policies", 0, "Primary reconciled modeling cohort only; source row counts are reported separately in the audit."),
        ("Exposure years", "exposure_years", 1, "Sum of valid primary-cohort policy exposures, measured in years."),
        ("Positive-payment claims", "claims", 0, "Positive-payment claims in the primary reconciled cohort, compatible with the severity model."),
        ("Claims / exposure-year", "frequency", 4, "Primary-cohort positive-payment claim count divided by primary-cohort exposure."),
        ("Aggregate paid claims", "claim_amount", 0, "Primary-cohort paid amounts in source monetary units (SMU)."),
        ("Mean positive payment", "severity", 0, "Positive payments divided by positive-payment claim records."),
        ("Pure premium / year", "pure_premium", 2, "Paid claim amount divided by valid policy exposure years."),
        ("Zero-claim share", "zero_claim_policy_proportion", 1, "Primary-cohort proportion with no positive-payment claim, distinct from annual frequency."),
    ]
    items = []
    for label, key, decimals, help_text in specs:
        value = s.get(key)
        if key == "zero_claim_policy_proportion" and value is not None:
            value = f"{100 * value:.1f}%"
        else:
            value = number(value, decimals)
        items.append((label, value, help_text))
    metric_grid(items)
    st.caption("All eight KPIs describe the primary reconciled modeling cohort. Monetary values retain historical source monetary units (SMU); the source does not establish a current EUR valuation. No currency conversion is performed.")
    if s.get("denominators"):
        with st.expander("Metric definitions and denominators"):
            table(s["denominators"])
    st.markdown("### Follow the actuarial chain")
    st.markdown("**Policy exposure → annual claim frequency × mean payment → pure premium → illustrative charged premium → portfolio loss distribution**")
    st.info("Educational research on historical French motor third-party liability data. This is not a commercial insurance quote, a current Nordic tariff or a regulatory capital model.")
    st.markdown("### Reconciliation before modeling")
    st.write("Policy and claim tables are audited before aggregation. Reported event counts and positive paid-claim counts remain separate; the two-part loss model uses compatible paid-claim definitions.")
    table(data.get("audit", {}))
    case_study(data, "A")


def segment_frame(data, feature):
    return pd.DataFrame(data.get("segments", {}).get(feature, []))


def explorer(data):
    hero("Portfolio Explorer", "Inspect exposure and claims across historical policy groups. These are descriptive associations, with visible denominators and sparse-group warnings.")
    segments = data.get("segments", {})
    if not segments:
        st.info("No saved segment summaries available.")
        return
    feature = st.selectbox("Policy characteristic", list(segments), format_func=humanize)
    frame = segment_frame(data, feature)
    if frame.empty:
        return
    group_col = next((c for c in ("group", "segment", "category", feature) if c in frame), frame.columns[0])
    values = frame[group_col].astype(str).tolist()
    chosen = st.multiselect("Visible groups", values, default=values, help="Filters saved aggregate groups; no individual policy records are loaded.")
    filtered = frame[frame[group_col].astype(str).isin(chosen)]
    if filtered.empty:
        st.info("Select at least one group to explore its exposure and claims.")
        return
    numeric = [c for c in ("frequency", "positive_frequency", "severity", "pure_premium", "exposure", "policies") if c in filtered]
    if numeric:
        measure = st.selectbox("Measure", numeric, format_func=humanize)
        chart(px.bar(filtered, x=group_col, y=measure, color_discrete_sequence=COLORS),
              f"{humanize(measure)} by {humanize(feature)}", humanize(measure))
    if "sparse" in filtered and filtered["sparse"].any():
        st.warning("At least one visible group has sparse exposure or claims. Treat its averages and calibration as unstable.")
    table(filtered.to_dict("records"), "Holdout groups only. Frequency denominators are exposure years; severity denominators are positive payments. Sparse groups cannot support stable pricing conclusions.")
    with st.expander("Primary-cohort exposure and claim-count distributions"):
        for name, axis, label in (("exposure_histogram", "policies", "Policy exposure (years)"),
                                  ("claim_amount_histogram", "claims", "Individual payment (SMU)")):
            bins = data.get("diagnostics", {}).get("charts", {}).get(name, [])
            if bins:
                distribution = pd.DataFrame(bins)
                distribution["interval"] = distribution.apply(lambda r: f"{r['lower']:,.2f}–{r['upper']:,.2f}", axis=1)
                chart(px.bar(distribution, x="interval", y=axis, color_discrete_sequence=COLORS), label, humanize(axis))
        counts = data.get("summary", {}).get("count_distribution", [])
        if counts:
            chart(px.bar(pd.DataFrame(counts), x="claims", y="policies", color_discrete_sequence=COLORS), "Positive-payment claims per policy", "Policies")
    case_study(data, "F")


def diagnostics(data, key):
    value = data.get("diagnostics", {}).get(key)
    if isinstance(value, list):
        table(value)
    elif isinstance(value, dict):
        table(value)


def frequency(data):
    hero("Claim Frequency", "Estimate annual positive-payment claim rates while keeping policy duration explicit. Expected paid-claim counts equal exposure × annual frequency.")
    st.latex(r"\mathbb{E}[N_i\mid X_i,e_i]=e_i\lambda(X_i)")
    st.caption("The modeled count is the reconciled positive-payment process, not the original reported-event count. Exposure-weighted annual-rate Poisson fitting is equivalent to a log-exposure offset for count means. Exposure is not an unconstrained rating predictor.")
    st.markdown("### Frequency model comparison")
    model_comparison(data, "frequency")
    st.markdown("### Dispersion and zero counts")
    diagnostics(data, "frequency_residuals")
    validation_chart(data, "frequency")
    st.markdown("### GLM rate relativities")
    explain = data.get("explainability", {})
    table(explain.get("frequency_glm_relativities", []), "Multiplicative fitted associations, not causal effects or approved rating factors.")
    case_study(data, "B")


def severity(data):
    hero("Claim Severity", "Model strictly positive individual claim payments, preserving the parent policy split and the observed large-loss tail.")
    st.latex(r"\mu(X_i)=\mathbb{E}[Y_{ij}\mid Y_{ij}>0,X_i]")
    st.markdown("### Severity model comparison")
    model_comparison(data, "severity")
    st.markdown("### Large claims and distributional fit")
    diagnostics(data, "severity_distribution")
    diagnostics(data, "tail_fit_diagnostic")
    st.markdown("### Development-only large-claim sensitivity")
    diagnostics(data, "large_claim_sensitivity")
    validation_chart(data, "severity")
    st.warning("A Gamma mean model does not establish that extreme losses follow a Gamma tail. Tail simulation assumptions and observed large-claim sensitivity are reported separately.")
    case_study(data, "C")


def premium_curve(data):
    rows = data.get("validation", {}).get("premium_deciles", [])
    if not rows:
        return
    frame = pd.DataFrame(rows).sort_values("decile")
    if not {"exposure", "observed_loss"}.issubset(frame):
        return
    x = np.r_[0, frame.exposure.cumsum() / frame.exposure.sum()]
    y = np.r_[0, frame.observed_loss.cumsum() / frame.observed_loss.sum()]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name="Observed paid loss", line={"color": COLORS[0]}))
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], name="Equal loss per exposure", line={"dash": "dash", "color": COLORS[2]}))
    fig.update_xaxes(title="Cumulative share of exposure (increasing fitted risk)", tickformat=".0%")
    fig.update_yaxes(tickformat=".0%")
    chart(fig, "Grouped holdout loss concentration", "Cumulative observed loss share")
    st.caption("Approximate curve through ten saved risk groups; numerical concentration scores use the full policy ordering. This is an exposure-axis concentration index, not a normalized Gini or a causal fairness measure.")


def quote_calculator(data):
    from actuarylab.pricing import quote

    profiles = data.get("profiles", [])
    if not profiles:
        st.info("Synthetic profile predictions are unavailable.")
        return
    names = [p.get("name", f"Profile {i + 1}") for i, p in enumerate(profiles)]
    selected = st.selectbox("Synthetic policy example", range(len(profiles)), format_func=lambda i: names[i])
    profile = profiles[selected]
    features = profile.get("features", {})
    metric_grid([
        ("Predicted annual frequency", number(profile.get("frequency"), 4), "Positive payments per exposure-year."),
        ("Predicted severity (SMU)", number(profile.get("severity")), "Mean positive payment, not aggregate policy loss."),
        ("Two-part pure premium", number(profile.get("two_part_pure_premium")), "Annual positive frequency × positive severity, in SMU."),
        ("Direct Tweedie pure premium", number(profile.get("direct_tweedie_pure_premium")), "Direct annual expected paid loss in SMU; does not identify frequency and severity separately."),
    ])
    if features:
        st.caption(" · ".join(f"{humanize(k)}: {v}" for k, v in features.items()))
    predictions = profile.get("predictions", profile)
    prediction = predictions.get("selected_pure_premium", predictions.get("pure_premium", profile.get("pure_premium")))
    if prediction is None:
        st.info("This example has no saved pure-premium prediction.")
        return
    cols = st.columns(3)
    exposure = cols[0].number_input("Exposure (years)", min_value=0.0, max_value=2.0, value=1.0, step=0.1)
    expense = cols[1].number_input("Expense share of premium", min_value=0.0, max_value=0.8, value=0.20, step=0.01)
    risk = cols[2].number_input("Risk loading on expected loss", min_value=0.0, max_value=0.8, value=0.05, step=0.01)
    cols = st.columns(2)
    profit = cols[0].number_input("Profit share of premium", min_value=0.0, max_value=0.8, value=0.05, step=0.01)
    fixed = cols[1].number_input("Fixed annual cost (source units)", min_value=0.0, max_value=10000.0, value=0.0, step=10.0)
    try:
        result = quote(float(prediction), exposure=exposure, expense=expense, risk=risk, profit=profit, fixed=fixed)
    except ValueError as exc:
        st.error(str(exc))
        return
    table(result)
    st.caption("Annual charged premium = (pure premium × (1 + risk loading) + fixed annual cost) / (1 − expense share − profit share); policy premium equals annual premium × exposure. Expense and profit are shares of final premium; risk loads expected loss. All assumptions are hypothetical; taxes are not estimated. No private policyholder data is requested.")


def pricing(data):
    hero("Pure Premium & Pricing", "Compare annual expected payment models, then explore how explicit hypothetical loadings translate pure premium into an illustrative premium.")
    st.latex(r"\pi(X)=\lambda_{\mathrm{positive}}(X)\,\mu_{\mathrm{positive}}(X),\quad \mathbb{E}[L_i]=e_i\pi(X_i)")
    st.markdown("### Two-part and direct Tweedie models")
    model_comparison(data, "pure_premium")
    st.caption("Tweedie annual loss modeling is exposure weighted. Its mean regression does not separately identify claim frequency and severity without additional assumptions.")
    validation_chart(data, "pure_premium")
    case_study(data, "D")
    st.markdown("### Illustrative premium calculator")
    st.info("Synthetic examples from supported feature combinations. These are educational calculations, not insurance offers or approved tariffs.")
    quote_calculator(data)
    if data.get("pricing"):
        st.markdown("### Saved hypothetical pricing scenarios")
        saved_pricing = data["pricing"]
        quote_keys = ("name", "pure_premium", "annual_premium", "policy_expected_loss", "policy_premium", "expected_loss_ratio")
        if saved_pricing.get("profiles"):
            table([{k: row[k] for k in quote_keys if k in row} for row in saved_pricing["profiles"]], "Pure premium, annual charged premium and policy costs retain source monetary units (SMU); loss ratios are dimensionless.")
        elif saved_pricing.get("scenarios"):
            table(saved_pricing["scenarios"])
        st.caption(saved_pricing.get("note", ""))
    case_study(data, "H")


def validation_chart(data, family):
    validation = data.get("validation", {})
    values = validation.get({"frequency": "frequency_deciles", "severity": "severity_deciles", "pure_premium": "premium_deciles"}[family], validation.get(family, []))
    if isinstance(values, dict):
        values = values.get("deciles", values.get("calibration", []))
    if not isinstance(values, list) or not values:
        return
    frame = pd.DataFrame(values)
    if family == "severity":
        frame = frame.rename(columns={"policies": "claims", "exposure": "claim_weight",
                                      "observed_rate": "observed_mean_payment",
                                      "predicted_rate": "predicted_mean_payment"})
        values = frame.to_dict("records")
    xcol = next((c for c in ("decile", "group", "bin") if c in frame), frame.columns[0])
    observed = next((c for c in ("observed", "observed_rate", "observed_mean_payment", "actual", "observed_frequency", "observed_severity", "observed_pure_premium") if c in frame), None)
    predicted = next((c for c in ("predicted", "predicted_rate", "predicted_mean_payment", "expected", "predicted_frequency", "predicted_severity", "predicted_pure_premium") if c in frame), None)
    if observed and predicted:
        fig = go.Figure()
        for col, label, color in ((observed, "Observed", COLORS[0]), (predicted, "Predicted", COLORS[1])):
            fig.add_trace(go.Scatter(x=frame[xcol].astype(str), y=frame[col], name=label, mode="lines+markers", line={"color": color}))
        chart(fig, f"{humanize(family)} · holdout risk groups", "Mean positive payment (SMU)" if family == "severity" else humanize(family))
    caption = ("Grouped individual positive-payment claims from holdout policies. Each claim has unit claim weight; observed and predicted means divide total payment by claim count, not policy exposure. Parent-policy clustering is retained for uncertainty." if family == "severity" else
               "Grouped holdout policy summaries; exposure weights apply to annual frequency and pure premium. Severity uses positive-claim weights instead of policy exposure.")
    table(values, caption)


def validation(data):
    hero("Model Validation", "Read holdout diagnostics and policy-cluster bootstrap uncertainty alongside the frozen development selection. A random split is not prospective validation.")
    st.markdown("### Frozen selection decision")
    table(data.get("selection", {}))
    st.markdown("### Policy-level bootstrap uncertainty")
    uncertainty = data.get("uncertainty", {})
    st.write(uncertainty.get("method", "No saved uncertainty method."))
    intervals = [{"Measure": humanize(k), "Lower 95% bound": v["lower"], "Upper 95% bound": v["upper"]}
                 for k, v in uncertainty.get("intervals", {}).items()]
    table(intervals)
    paired = [{"Score difference": humanize(k), **v} for k, v in uncertainty.get("paired", {}).items()]
    if paired:
        st.markdown("#### Paired fitted-model comparisons")
        table(paired)
        for target, order in uncertainty.get("comparison_order", {}).items():
            if len(order) == 2:
                st.caption(f"{humanize(target)} difference: {order[0]} minus {order[1]}. Negative deviance differences favor the first model; pointwise intervals are not multiplicity-adjusted.")
    st.caption(f"{uncertainty.get('replicates', 'Unavailable')} policy-cluster resamples. Fixed fitted-model evaluation uncertainty is distinct from refitting uncertainty, process risk and future population shift. Claims belonging to one policy remain clustered.")
    family = st.selectbox("Holdout calibration target", ["frequency", "severity", "pure_premium"], format_func=humanize)
    validation_chart(data, family)
    st.markdown("### Loss concentration and exposure-aware ranking")
    premium_curve(data)
    case_study(data, "E")


@st.cache_data(show_spinner=False, max_entries=6)
def cached_simulation(frequency_values, severity_values, exposure_values, replicates, tail,
                      gamma_shape, lognormal_sigma, frequency_multiplier, severity_multiplier,
                      common_sigma, premium):
    from actuarylab.simulation import simulate_portfolio
    return simulate_portfolio(
        np.asarray(frequency_values), np.asarray(severity_values), np.asarray(exposure_values),
        replicates=replicates, seed=442, gamma_shape=gamma_shape, tail=tail,
        lognormal_sigma=lognormal_sigma, frequency_multiplier=frequency_multiplier,
        severity_multiplier=severity_multiplier, common_sigma=common_sigma, premium=premium,
    )


def show_simulation(result):
    losses = result.get("losses", [])
    metric_grid([
        ("Analytical expected loss", number(result.get("expected_loss"), 0), "SMU; compound model expectation under the submitted assumptions."),
        ("Monte Carlo mean loss", number(result.get("mean"), 0), "SMU; calculated from every simulated portfolio, not the displayed sample."),
        ("95% VaR", number(result.get("var95"), 0), "SMU; inverse empirical CDF of all simulated losses, not regulatory capital."),
        ("95% Expected Shortfall", number(result.get("es95"), 0), "SMU; exact average upper 5% mass of all simulated losses."),
    ])
    with st.expander("All saved risk measures and assumptions"):
        table({k: v for k, v in result.items() if k not in {"losses", "plot_sample_note"}})
    sample_note = result.get("plot_sample_note")
    if sample_note:
        st.caption(sample_note)
        st.caption("Both charts below describe the display sample only. VaR, Expected Shortfall, means and exceedance-of-premium probabilities above retain their saved full-simulation values.")
    else:
        st.caption(f"Charts use all {len(losses):,} losses from this submitted simulation.")
    if len(losses):
        fig = px.histogram(x=losses, nbins=60, color_discrete_sequence=COLORS,
                           labels={"x": "Aggregate loss (source monetary units)", "y": "Simulated portfolios"})
        chart(fig, "Simulated aggregate loss distribution", "Simulated portfolios")
        ordered = np.sort(losses)
        exceedance = 1 - np.arange(1, len(ordered) + 1) / len(ordered)
        fig = go.Figure(go.Scatter(x=ordered, y=exceedance, mode="lines", line={"color": COLORS[0]}, name="Empirical exceedance"))
        fig.update_xaxes(title="Aggregate loss (SMU)")
        fig.update_yaxes(tickformat=".0%")
        chart(fig, "Probability of exceeding an aggregate loss", "Empirical exceedance probability")


def synthetic_portfolio_inputs(cells, policies):
    """Preserve a supplied profile mixture exactly using exposure mass per cell."""
    weights = np.asarray([c["weight"] for c in cells], dtype=float)
    if not np.isfinite(weights).all() or (weights < 0).any() or weights.sum() <= 0:
        raise ValueError("Saved profile weights must be finite, nonnegative and sum to a positive value.")
    weights = weights / weights.sum()
    return (tuple(float(c["frequency"]) for c in cells),
            tuple(float(c["severity"]) for c in cells),
            tuple(float(c["exposure"]) * float(w) * policies for c, w in zip(cells, weights, strict=True)))


def risk_simulator(data):
    hero("Portfolio Risk Simulator", "Simulate aggregate losses from fitted frequency and severity means. Tail choices and shared shocks are assumptions, with bounded workloads and visible Monte Carlo uncertainty.")
    simulation = data.get("simulation", {})
    if simulation.get("scenarios"):
        st.markdown("### Precomputed scenario evidence")
        scenario_rows = [{
            "Scenario": row["name"],
            "Expected loss (SMU)": number(row.get("expected_loss"), 0),
            "MC mean (SMU)": number(row.get("mean"), 0),
            "VaR 95% (SMU)": number(row.get("var95"), 0),
            "ES 95% (SMU)": number(row.get("es95"), 0),
            "Expected loss ratio": (f"{100 * row['expected_loss_ratio']:.2f}%" if row.get("expected_loss_ratio") is not None else "Unavailable"),
        } for row in simulation["scenarios"]]
        table(scenario_rows, "SMU = source monetary units. Displayed money is rounded; detailed saved measures retain full precision. Each summary uses the full recorded simulation count, not the display sample. All portfolios and premium assumptions are hypothetical.")
        saved_index = st.selectbox("Inspect a saved scenario", range(len(simulation["scenarios"])), format_func=lambda i: simulation["scenarios"][i]["name"])
        show_simulation(simulation["scenarios"][saved_index])
        st.caption(simulation.get("portfolio_definition", ""))
        st.caption(simulation.get("tail_warning", ""))
    st.markdown("### Run a bounded synthetic portfolio")
    inputs = data.get("simulation_inputs", {})
    cells = inputs.get("cells", [])
    if not cells:
        st.info("Saved simulation inputs are unavailable.")
        return
    required_parameters = ("gamma_shape", "lognormal_sigma")
    required_cell_fields = ("frequency", "severity", "exposure", "weight")
    if any(key not in inputs for key in required_parameters) or any(any(key not in cell for key in required_cell_fields) for cell in cells):
        st.error("Saved simulation assumptions are incomplete. Regenerate the offline artifact; no replacement assumptions will be supplied.")
        return
    with st.form("simulation"):
        cols = st.columns(3)
        policies = cols[0].number_input("Synthetic portfolio size", min_value=50, max_value=1000, value=500, step=50)
        replicates = cols[1].selectbox("Simulated portfolios", [1000, 2500, 5000], index=1)
        tail = cols[2].selectbox("Severity tail", ["gamma", "lognormal"], format_func=str.capitalize)
        cols = st.columns(3)
        frequency_multiplier = cols[0].slider("Frequency multiplier", min_value=0.5, max_value=2.0, value=1.0, step=0.05)
        severity_multiplier = cols[1].slider("Severity multiplier", min_value=0.5, max_value=2.0, value=1.0, step=0.05)
        common_sigma = cols[2].slider("Shared lognormal frequency shock σ", min_value=0.0, max_value=0.6, value=0.0, step=0.05)
        premium = st.number_input("Hypothetical earned premium per policy (source units)", min_value=1.0, max_value=100000.0, value=500.0, step=25.0)
        run = st.form_submit_button("Simulate portfolio", type="primary")
    st.caption("Normalized synthetic profile weights allocate exposure exactly across saved risk cells (including fractional exposure mass); source policy records are never loaded. Independent compound Poisson baseline. The mean-one shared frequency shock preserves marginal expected loss, but changes process variability. Premium is hypothetical.")
    st.caption(inputs.get("portfolio_definition", "Synthetic portfolio using two-part components."))
    st.caption(f"Gamma shape: {number(inputs.get('gamma_shape'))}; lognormal σ: {number(inputs.get('lognormal_sigma'))}. These are development-calibrated tail approximations, not catastrophe or reinsurance models.")
    if run:
        try:
            f_values, s_values, e_values = synthetic_portfolio_inputs(cells, policies)
            with st.spinner("Simulating bounded aggregate losses…"):
                result = cached_simulation(
                    f_values, s_values, e_values, replicates, tail,
                    inputs["gamma_shape"], inputs["lognormal_sigma"],
                    frequency_multiplier, severity_multiplier, common_sigma, premium * policies,
                )
            st.session_state["simulation_result"] = result
        except ValueError as exc:
            st.error(str(exc))
    if "simulation_result" in st.session_state:
        show_simulation(st.session_state["simulation_result"])
        st.caption("Results correspond to the last submitted assumptions. VaR uses the inverse empirical CDF; Expected Shortfall averages the exact upper-tail mass, including fractional mass at ties. Monte Carlo error does not quantify model or tail-assumption uncertainty.")
    case_study(data, "G")


def governance(data):
    hero("Actuarial Governance & About", "Trace the data, reconciliation choices and model boundaries. Reproducibility and honest limits make the analytical evidence reviewable.")
    st.markdown("### Provenance and attribution")
    st.write("French Motor Third-Party Liability datasets freMTPL2freq and freMTPL2sev, via OpenML and CASdatasets. Historical French motor policies; population transfer to present-day Nordic insurance is unvalidated.")
    st.markdown("[OpenML frequency source](https://www.openml.org/d/41214) · [OpenML severity source](https://www.openml.org/d/41215) · [CASdatasets](https://github.com/dutangc/CASdatasets) · [Source and license record](https://github.com/Priynka-Roy/actuarylab-ai-insurance-pricing-risk/blob/main/docs/DATA_CARD.md)")
    st.markdown("### Data reconciliation")
    table(data.get("audit", {}))
    st.markdown("### Experimental protocol")
    protocol = data.get("protocol", {})
    if isinstance(protocol, dict):
        table(protocol)
    else:
        st.write(protocol)
    st.markdown("### Model explanations")
    explanations = data.get("explainability", {})
    if explanations:
        target = st.selectbox("Explanation", list(explanations), format_func=humanize)
        value = explanations[target]
        if isinstance(value, (dict, list)):
            table(value)
        else:
            st.write(value)
    st.caption("Coefficients, relativities and importance describe fitted statistical associations. Correlated features and sparse categories affect interpretation; none establish causal risk factors.")
    st.markdown("### Responsible pricing")
    st.write("Age, geography, bonus-malus and vehicle attributes can raise legal, ethical and proxy-discrimination questions. Predictive usefulness does not establish permissible use in a real tariff. Group calibration is descriptive and does not itself establish fairness or unlawful discrimination.")
    st.markdown("### Limits of the evidence")
    for limit in data.get("limitations", []):
        st.write(f"• {limit}")
    st.warning("Internal project review is not external actuarial validation or regulatory approval. No insurer sponsored, commissioned or endorsed this educational project.")
    st.markdown("### Reproduce and inspect")
    st.markdown("[GitHub source, methods and tests](https://github.com/Priynka-Roy/actuarylab-ai-insurance-pricing-risk) · [Model card](https://github.com/Priynka-Roy/actuarylab-ai-insurance-pricing-risk/blob/main/docs/MODEL_CARD.md)")
    st.code("python scripts/download_data.py\npython scripts/run_pipeline.py\npython scripts/export_artifacts.py\npython scripts/verify_artifacts.py\nruff check .\npytest", language="bash")
    st.caption("Public app reads saved aggregate JSON. No raw data download, model fitting, or untrusted estimator deserialization occurs at startup. Data and code have distinct licensing; consult the data card.")


def main():
    st.set_page_config(page_title="ActuaryLab AI · Insurance Pricing & Risk", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
    apply_styles()
    with st.sidebar:
        st.markdown("## ActuaryLab AI")
        st.caption("Insurance Pricing, Claims Modeling & Portfolio Risk")
        st.divider()
        page = st.radio("Explore the laboratory", SECTIONS, label_visibility="collapsed")
        st.divider()
        st.caption("PROJECT 04 · HISTORICAL MOTOR INSURANCE")
        st.caption("Exposure-aware models. Transparent assumptions. Reproducible evidence.")
        st.markdown("[View source ↗](https://github.com/Priynka-Roy/actuarylab-ai-insurance-pricing-risk)")
    if not ARTIFACT.exists():
        st.error("The saved analysis artifact is missing. Run the offline pipeline and artifact export before starting this application.")
        st.stop()
    try:
        data = load_dashboard(str(ARTIFACT), ARTIFACT.stat().st_mtime_ns)
    except (OSError, ValueError) as exc:
        st.error(f"The saved analysis artifact could not be read: {exc}")
        st.stop()
    handlers = dict(zip(SECTIONS, (overview, explorer, frequency, severity, pricing, validation, risk_simulator, governance), strict=True))
    handlers[page](data)
    st.divider()
    st.caption("ActuaryLab AI · Educational historical insurance analytics · Source monetary units · No real insurance offers · No regulatory approval")
