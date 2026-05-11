"""Octa Financial Control — Charts (all Plotly, all HTML-exportable)."""
import plotly.graph_objects as go

D = {
    "bg":"#0f1421","bg2":"#1a2235","bg3":"#232f45",
    "text":"#e2e8f0","muted":"#8899b0","accent":"#00BCD4",
    "accent2":"#FF6B35","success":"#6fcf97","warning":"#f6cc52",
    "danger":"#fc8181","border":"rgba(255,255,255,0.09)",
}

CAT_COLORS = {
    "personnel":            "#00BCD4",
    "travel":               "#6fcf97",
    "equipment":            "#f6cc52",
    "other_goods_services": "#FF6B35",
    "subcontracting":       "#9b59b6",
    "third_parties":        "#3498db",
    "overhead":             "#8899b0",
}

CAT_LABELS = {
    "personnel":            "Personnel",
    "travel":               "Travel",
    "equipment":            "Equipment",
    "other_goods_services": "Other Goods",
    "subcontracting":       "Subcontracting",
    "third_parties":        "Third Parties",
    "overhead":             "Overhead",
}


def _layout(fig, title="", height=380):
    fig.update_layout(
        title=dict(text=title, font=dict(color=D["text"], size=13)) if title else None,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=height, margin=dict(l=10, r=10, t=100 if title else 20, b=50),
        font=dict(color=D["text"], size=11),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=D["text"], size=10),
                    orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", color=D["text"]),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", color=D["text"]),
    )
    return fig


def fig_to_html(fig, title=""):
    if title:
        fig.update_layout(title=dict(text=title))
    return fig.to_html(full_html=True, include_plotlyjs=True,
                       config={"responsive": True, "scrollZoom": True})


# ── 1. Budget consumption gauge per partner ───────────────────────────────────
def chart_budget_gauge(planned, actual, title="Budget Consumed"):
    pct   = round(actual / planned * 100, 1) if planned else 0
    color = D["success"] if pct < 75 else (D["warning"] if pct < 95 else D["danger"])
    fig   = go.Figure(go.Indicator(
        mode   = "gauge+number",
        value  = pct,
        number = {"suffix": "%", "font": {"color": D["text"], "size": 34}},
        gauge  = {
            "axis":      {"range": [0, 100], "tickcolor": D["muted"],
                          "tickfont": {"color": D["muted"], "size": 10}},
            "bar":       {"color": color, "thickness": 0.72},
            "bgcolor":   "rgba(0,0,0,0)",
            "borderwidth": 0,
            "threshold": {"line": {"color": D["danger"], "width": 3},
                          "thickness": 0.8, "value": 90},
        },
        title = {"text": f"<b>{title}</b><br>€{actual:,.0f} of €{planned:,.0f}",
                 "font": {"color": D["muted"], "size": 11}},
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=260, margin=dict(l=20,r=20,t=50,b=10),
                      font=dict(color=D["text"]))
    return fig


# ── 2. Planned vs actual by category (grouped bar) ───────────────────────────
def chart_by_category(by_cat: dict, title="Budget by Cost Category"):
    cats    = [k for k in CAT_LABELS if k in by_cat]
    labels  = [CAT_LABELS.get(c, c) for c in cats]
    planned = [by_cat[c].get("planned", 0) for c in cats]
    actual  = [by_cat[c].get("actual",  0) for c in cats]
    solid   = [CAT_COLORS.get(c, D["muted"]) for c in cats]

    # Faded planned bars — all as explicit rgba() strings
    FADED = {
        "personnel":            "rgba(0,188,212,0.33)",
        "travel":               "rgba(111,207,151,0.33)",
        "equipment":            "rgba(246,204,82,0.33)",
        "other_goods_services": "rgba(255,107,53,0.33)",
        "subcontracting":       "rgba(155,89,182,0.33)",
        "third_parties":        "rgba(52,152,219,0.33)",
        "overhead":             "rgba(136,153,176,0.33)",
    }
    faded = [FADED.get(c, "rgba(136,153,176,0.33)") for c in cats]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Planned", x=labels, y=planned,
        marker_color=faded,
        hovertemplate="%{x}<br>Planned: €%{y:,.0f}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        name="Actual", x=labels, y=actual,
        marker_color=solid,
        hovertemplate="%{x}<br>Actual: €%{y:,.0f}<extra></extra>"
    ))
    fig.update_layout(barmode="group", xaxis_tickangle=-20,
                      yaxis_title="Amount (€)")
    return _layout(fig, title, 400)


# ── 3. Spending by category (donut) ──────────────────────────────────────────
def chart_spending_donut(by_cat: dict, title="Actual Spending by Category"):
    cats   = [k for k in CAT_LABELS if k in by_cat and by_cat[k].get("actual",0)>0]
    labels = [CAT_LABELS.get(c,c) for c in cats]
    values = [by_cat[c].get("actual",0) for c in cats]
    colors = [CAT_COLORS.get(c, D["muted"]) for c in cats]
    if not values:
        return go.Figure()
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.6,
        marker=dict(colors=colors, line=dict(color=D["bg"], width=2)),
        textfont=dict(color=D["text"]),
        hovertemplate="%{label}<br>€%{value:,.0f} (%{percent})<extra></extra>",
    ))
    return _layout(fig, title, 340)


# ── 4. Partner comparison bar ─────────────────────────────────────────────────
def chart_partner_comparison(partner_summaries: list,
                              title="Budget by Partner — Planned vs Actual"):
    if not partner_summaries:
        return go.Figure()
    names   = [p["short_name"] or p["partner_name"][:20] for p in partner_summaries]
    planned = [p["planned"] for p in partner_summaries]
    actual  = [p["actual"]  for p in partner_summaries]
    colors  = []
    for p in partner_summaries:
        pct = p["pct_spent"]
        colors.append(D["success"] if pct<75 else (D["warning"] if pct<95 else D["danger"]))

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Planned", x=names, y=planned,
                         marker_color="rgba(0,188,212,0.35)",
                         hovertemplate="%{x}<br>Planned: €%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(name="Actual",  x=names, y=actual,
                         marker_color=colors,
                         hovertemplate="%{x}<br>Actual: €%{y:,.0f}<extra></extra>"))
    fig.update_layout(barmode="group", yaxis_title="Amount (€)")
    return _layout(fig, title, 380)


# ── 5. WP spending breakdown (stacked bar) ────────────────────────────────────
def chart_wp_breakdown(matrix: dict, wps: list, partner_id: int = None,
                        title="Spending by Work Package"):
    """
    Stacked bar per WP. If partner_id given, shows that partner only.
    Otherwise sums all partners.
    """
    from config import CAT_KEYS
    wp_labels, wp_planned, wp_actual = [], [], []
    wp_map = {w["wp_id"]: w.get("wp_number","") for w in wps}

    # Collect per-WP totals
    wid_totals = {}
    for pid, wps_data in matrix.items():
        if partner_id and pid != partner_id:
            continue
        for wid, cats in wps_data.items():
            if wid not in wid_totals:
                wid_totals[wid] = {"planned":0,"actual":0}
            for cat in CAT_KEYS:
                d = cats.get(cat,{})
                wid_totals[wid]["planned"] += d.get("planned",0)
                wid_totals[wid]["actual"]  += d.get("actual",0)

    for wid, totals in sorted(wid_totals.items(), key=lambda x: wp_map.get(x[0],"")):
        wp_labels.append(wp_map.get(wid, f"WP{wid}"))
        wp_planned.append(totals["planned"])
        wp_actual.append(totals["actual"])

    if not wp_labels:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Planned", x=wp_labels, y=wp_planned,
                         marker_color="rgba(0,188,212,0.35)",
                         hovertemplate="%{x}<br>Planned: €%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(name="Actual", x=wp_labels, y=wp_actual,
                         marker_color=D["accent"],
                         hovertemplate="%{x}<br>Actual: €%{y:,.0f}<extra></extra>"))
    fig.update_layout(barmode="group", yaxis_title="Amount (€)")
    return _layout(fig, title, 380)


# ── 6. Burn rate / forecast line chart ───────────────────────────────────────
def chart_burn_rate(snapshots: list, total_planned: float,
                    title="Budget Burn Rate Over Time"):
    if not snapshots:
        return go.Figure()
    periods = [s["reporting_period"] for s in snapshots]
    spent   = [float(s.get("total_spent",0)) for s in snapshots]
    # Cumulative
    cum_spent = []
    running = 0
    for s in spent:
        running += s
        cum_spent.append(running)

    fig = go.Figure()
    # Budget ceiling
    fig.add_trace(go.Scatter(
        x=periods, y=[total_planned]*len(periods),
        mode="lines", name="Total Budget",
        line=dict(color=D["danger"], dash="dash", width=2),
        hovertemplate="Period %{x}<br>Budget ceiling: €%{y:,.0f}<extra></extra>",
    ))
    # Actual cumulative spend
    fig.add_trace(go.Scatter(
        x=periods, y=cum_spent,
        mode="lines+markers", name="Cumulative Spent",
        line=dict(color=D["accent"], width=3),
        marker=dict(size=8, color=D["accent"]),
        fill="tozeroy", fillcolor="rgba(0,188,212,0.12)",
        hovertemplate="Period %{x}<br>Spent to date: €%{y:,.0f}<extra></extra>",
    ))
    # Forecast: linear projection
    if len(periods) >= 2 and periods[-1] > 0:
        rate = cum_spent[-1] / periods[-1]   # avg per period
        max_p = max(periods[-1] + 4, 8)
        fc_periods = list(range(periods[-1], max_p+1))
        fc_values  = [cum_spent[-1] + rate*(i-periods[-1]) for i in fc_periods]
        fig.add_trace(go.Scatter(
            x=fc_periods, y=fc_values,
            mode="lines", name="Forecast",
            line=dict(color=D["warning"], dash="dot", width=2),
            hovertemplate="Period %{x}<br>Forecast: €%{y:,.0f}<extra></extra>",
        ))

    fig.update_layout(xaxis_title="Reporting Period",
                      yaxis_title="Cumulative Amount (€)")
    return _layout(fig, title, 380)


# ── 7. Deviation waterfall chart ─────────────────────────────────────────────
def chart_deviation(by_cat: dict, title="Variance — Actual vs Planned"):
    cats   = [k for k in CAT_LABELS if k in by_cat]
    labels = [CAT_LABELS.get(c,c) for c in cats]
    deltas = [by_cat[c].get("actual",0) - by_cat[c].get("planned",0) for c in cats]
    colors = [D["danger"] if d > 0 else D["success"] for d in deltas]

    fig = go.Figure(go.Bar(
        x=labels, y=deltas,
        marker_color=colors, marker_line_width=0,
        hovertemplate="%{x}<br>Variance: €%{y:,.0f}<extra></extra>",
        text=[f"€{d:+,.0f}" for d in deltas],
        textposition="outside",
        textfont=dict(color=D["text"], size=10),
    ))
    fig.add_hline(y=0, line_color="rgba(255,255,255,0.3)", line_width=1)
    fig.update_layout(yaxis_title="Variance (€) — negative = under budget",
                      xaxis_tickangle=-15)
    return _layout(fig, title, 360)
