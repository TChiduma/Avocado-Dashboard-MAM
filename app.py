from dash import Dash, dcc, html, Input, Output, State, callback_context
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from data_loader import load_data

df = load_data()
df["date"] = pd.to_datetime(df["date"])

COLORS = {
    "bg": "#0E0E0E",
    "navbar": "#151515",
    "card": "#1C1C1C",
    "accent": "#7AC74F",       # avocado green
    "accent_soft": "#264027",
    "text": "#F5F5F5",
    "muted": "#A0A0A0",
    "border": "#333333",
}

GLOBAL_STYLE = {
    "fontFamily": "'Quicksand', sans-serif",
    "backgroundColor": COLORS["bg"],
    "color": COLORS["text"],
    "minHeight": "100vh",
}

AVOCADO_COLORS = ["#7AC74F", "#A3B18A", "#D4A373", "#CB997E", "#6B705C"]

def dark_mode_style_component():
    # CSS is loaded automatically from assets/custom.css
    return html.Div()


def format_number(n):
    try:
        if n is None or (isinstance(n, float) and np.isnan(n)):
            return "–"
        n = float(n)
    except (ValueError, TypeError):
        return "–"

    abs_n = abs(n)
    if abs_n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    elif abs_n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    elif abs_n >= 1_000:
        return f"{n / 1_000:.2f}K"
    else:
        return f"{n:.2f}"


def format_change_kpi(change, is_currency=True):
    if change is None or (isinstance(change, float) and np.isnan(change)):
        return html.Span("–", style={"color": COLORS["text"]})
    prefix = "$" if is_currency else ""
    val_str = f"{prefix}{abs(change):.2f}" if is_currency else format_number(abs(change))
    if change > 0.0001:
        return html.Span(
            f"▲ +{val_str}",
            style={
                "color": "#7AC74F",
                "backgroundColor": "rgba(122, 199, 79, 0.16)",
                "padding": "3px 8px",
                "borderRadius": "6px",
                "fontWeight": "700",
                "fontSize": "19px",
                "letterSpacing": "-0.3px",
            },
        )
    elif change < -0.0001:
        return html.Span(
            f"▼ -{val_str}",
            style={
                "color": "#FF6B6B",
                "backgroundColor": "rgba(255, 107, 107, 0.16)",
                "padding": "3px 8px",
                "borderRadius": "6px",
                "fontWeight": "700",
                "fontSize": "19px",
                "letterSpacing": "-0.3px",
            },
        )
    else:
        return html.Span(
            f"• {val_str}",
            style={
                "color": COLORS["muted"],
                "backgroundColor": "rgba(255, 255, 255, 0.06)",
                "padding": "3px 8px",
                "borderRadius": "6px",
                "fontWeight": "600",
                "fontSize": "19px",
            },
        )


def apply_fig_theme(fig, title=None):
    fig.update_layout(
        paper_bgcolor=COLORS["card"],
        plot_bgcolor=COLORS["card"],
        font=dict(
            family="'Quicksand', sans-serif",
            color=COLORS["text"],
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
        ),
        transition=dict(duration=350, easing="cubic-in-out"),
        hoverlabel=dict(
            bgcolor="#151515",
            font_size=13,
            font_family="'Quicksand', sans-serif",
            bordercolor="#7AC74F",
        ),
    )
    if title is not None:
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(color=COLORS["accent"], size=18),
            )
        )
    fig.update_xaxes(
        gridcolor=COLORS["border"],
        zerolinecolor=COLORS["border"],
    )
    fig.update_yaxes(
        gridcolor=COLORS["border"],
        zerolinecolor=COLORS["border"],
    )
    return fig


def apply_avocado_colors(fig):
    for i, trace in enumerate(fig.data):
        color = AVOCADO_COLORS[i % len(AVOCADO_COLORS)]
        if hasattr(trace, "line") and trace.line is not None:
            trace.line.color = color
        if hasattr(trace, "marker") and trace.marker is not None:
            trace.marker.color = color
    return fig


def empty_figure(message="No data for selected filters."):
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(color=COLORS["muted"]),
    )
    apply_fig_theme(fig)
    return fig


def collapsible_info_box(title, bullets, default_open=False):
    return html.Details(
        className="page-info-box",
        open=default_open,
        children=[
            html.Summary(
                children=[
                    html.Span("▶", className="toggle-icon"),
                    html.Span("💡", style={"fontSize": "13px"}),
                    html.Span(title),
                    html.Span("(click to toggle guide)", style={"color": COLORS["muted"], "fontSize": "11px", "fontWeight": "400", "marginLeft": "auto"}),
                ],
            ),
            html.Ul(
                style={
                    "margin": "10px 0 2px 0",
                    "paddingLeft": "20px",
                    "color": COLORS["muted"],
                    "fontSize": "12.5px",
                    "lineHeight": "1.65",
                },
                children=[html.Li(bullet) for bullet in bullets],
            ),
        ],
    )


def drilldown_badge(text="● Click point to drill down"):
    return html.Div(
        style={
            "display": "flex",
            "justifyContent": "flex-end",
            "marginBottom": "-36px",
            "position": "relative",
            "zIndex": 8,
            "paddingRight": "18px",
            "pointerEvents": "none",
        },
        children=[
            html.Span(
                text,
                className="status-badge",
                style={
                    "fontSize": "11px",
                    "padding": "3px 10px",
                    "margin": 0,
                    "backgroundColor": "rgba(122, 199, 79, 0.14)",
                    "border": "1px solid rgba(122, 199, 79, 0.35)",
                    "boxShadow": "0 2px 10px rgba(0,0,0,0.3)",
                },
            ),
        ],
    )


def is_active(pathname, target):
    return pathname == target or (pathname in [None, "/"] and target == "/")


def navbar(pathname="/"):
    def link(path, label):
        active = is_active(pathname, path)
        style = {
            "marginLeft": "8px",
            "marginRight": "8px",
            "cursor": "pointer",
            "textDecoration": "none",
            "fontSize": "14px",
        }
        if active:
            style.update(
                {
                    "color": COLORS["accent"],
                    "backgroundColor": COLORS["accent_soft"],
                    "fontWeight": "600",
                    "padding": "6px 10px",
                    "borderRadius": "8px",
                }
            )
        else:
            style.update(
                {
                    "color": COLORS["muted"],
                    "backgroundColor": "transparent",
                    "fontWeight": "400",
                }
            )
        return dcc.Link(label, href=path, style=style)

    return html.Div(
        id="navbar",
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "padding": "0 28px",
            "height": "68px",
            "backgroundColor": "rgba(21, 21, 21, 0.9)",
            "backdropFilter": "blur(12px)",
            "-webkitBackdropFilter": "blur(12px)",
            "borderBottom": f"1px solid {COLORS['border']}",
            "position": "sticky",
            "top": 0,
            "zIndex": 999,
        },
        children=[
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "10px"},
                children=[
                    html.Img(
                        src="/assets/avocado_mascot.svg",
                        alt="Avocado Mascot",
                        style={
                            "height": "38px",
                            "width": "38px",
                            "display": "inline-block",
                            "verticalAlign": "middle",
                            "filter": "drop-shadow(0 2px 6px rgba(0, 0, 0, 0.4))",
                        },
                    ),
                    html.Span(
                        "Avocado Dashboard",
                        style={
                            "color": COLORS["accent"],
                            "fontWeight": "800",
                            "fontSize": "23px",
                            "letterSpacing": "-0.5px",
                        },
                    ),
                ],
            ),
            html.Div(
                style={"display": "flex", "alignItems": "center"},
                children=[
                    link("/", "Overview"),
                    link("/markets", "Markets"),
                    link("/trends", "Trends"),
                    link("/comparison", "Comparison"),
                    link("/data", "Data"),
                ],
            ),
        ],
    )


def overview_layout():
    regions = sorted(df["region"].dropna().unique())
    types = sorted(df["type"].dropna().unique())

    return html.Div(
        style={"padding": "24px"},
        children=[
            html.H2(
                "Market Overview",
                style={
                    "color": COLORS["accent"],
                    "fontWeight": "700",
                    "marginBottom": "8px",
                },
            ),
            html.P(
                "Explore overall avocado prices, volumes, and key metrics across regions and types.",
                style={"color": COLORS["muted"], "marginBottom": "12px"},
            ),
            html.Div(
                html.Span(f"● {len(df):,} weekly records • {df['region'].nunique()} US markets • {df['date'].min().year}–{df['date'].max().year}", className="status-badge"),
                style={"marginBottom": "16px"},
            ),
            collapsible_info_box(
                "Executive Market Overview & KPI Guide",
                [
                    "Macro Trends: Track aggregate market volume and price evolution across the full United States dataset.",
                    "Dynamic KPIs: Volume, Average Price, Top Region, Volatility, and Latest Daily Change recompute dynamically based on your filter selection.",
                    "Multi-Dimensional Filtering: Filter by date range, specific regions, or avocado varieties (Conventional / Organic) to focus the scope.",
                ],
                default_open=False,
            ),
            html.Div(
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "16px",
                    "marginBottom": "24px",
                },
                children=[
                    html.Div(
                        children=[
                            html.Label(
                                "Date range",
                                style={"color": COLORS["muted"], "fontSize": "12px"},
                            ),
                            dcc.DatePickerRange(
                                id="date-range",
                                start_date=df["date"].min().date(),
                                end_date=df["date"].max().date(),
                                display_format="YYYY-MM-DD",
                            ),
                        ],
                    ),
                    html.Div(
                        style={"minWidth": "200px"},
                        children=[
                            html.Label(
                                "Regions",
                                style={"color": COLORS["muted"], "fontSize": "12px"},
                            ),
                            dcc.Dropdown(
                                id="region-dropdown",
                                options=[{"label": r, "value": r} for r in regions],
                                multi=True,
                                placeholder="All regions",
                            ),
                        ],
                    ),
                    html.Div(
                        style={"minWidth": "200px"},
                        children=[
                            html.Label(
                                "Types",
                                style={"color": COLORS["muted"], "fontSize": "12px"},
                            ),
                            dcc.Dropdown(
                                id="type-checklist",
                                options=[{"label": t, "value": t} for t in types],
                                multi=True,
                                placeholder="All types",
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                id="kpi-container",
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "16px",
                    "marginBottom": "24px",
                },
            ),
            html.Div(
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "24px",
                },
                children=[
                    html.Div(
                        style={"flex": "1 1 400px"},
                        children=[
                            drilldown_badge(),
                            dcc.Loading(
                                dcc.Graph(
                                    id="price-over-time",
                                    style={"height": "420px"},
                                ),
                                type="dot",
                                color=COLORS["accent"],
                            ),
                        ],
                    ),
                    html.Div(
                        style={"flex": "1 1 400px"},
                        children=[
                            drilldown_badge(),
                            dcc.Loading(
                                dcc.Graph(
                                    id="volume-over-time",
                                    style={"height": "420px"},
                                ),
                                type="dot",
                                color=COLORS["accent"],
                            ),
                        ],
                    ),
                ],
            ),
            dcc.Loading(
                html.Div(id="overview-drilldown-container"),
                type="dot",
                color=COLORS["accent"],
            ),
            dcc.Store(id="overview-selected-week", data=None),
        ],
    )

def markets_layout():
    regions = sorted(df["region"].dropna().unique())

    return html.Div(
        style={"padding": "24px"},
        children=[
            html.H2(
                "Markets",
                style={
                    "color": COLORS["accent"],
                    "fontWeight": "700",
                    "marginBottom": "8px",
                },
            ),
            html.P(
                "Visualize average prices and total volumes across US markets.",
                style={"color": COLORS["muted"], "marginBottom": "12px"},
            ),
            html.Div(
                html.Span("● 54 US Metropolitan & Regional Markets • Volume & Price Distribution", className="status-badge"),
                style={"marginBottom": "16px"},
            ),
            collapsible_info_box(
                "Regional Heatmap Guide",
                [
                    "Proportional Sizing: Treemap tile area scales directly with market size—Total Volume for sales capacity and Average Price for valuation.",
                    "Concise Metric Shorthand: Values inside heatmaps are cleanly abbreviated (e.g. 4.84B, 120M, $1.80) for rapid scanning without clutter.",
                    "Market Filtering: Use the Regions filter below to isolate specific metropolitan areas or compare targeted territories.",
                ],
                default_open=False,
            ),

            # NEW REGION FILTER
            html.Div(
                style={"marginBottom": "16px"},
                children=[
                    html.Label(
                        "Regions",
                        style={"color": COLORS["muted"], "fontSize": "12px"},
                    ),
                    dcc.Dropdown(
                        id="market-region-filter",
                        options=[{"label": r, "value": r} for r in regions],
                        multi=True,
                        placeholder="All regions",
                    ),
                ],
            ),

            html.Div(
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "24px",
                },
                children=[
                    html.Div(
                        style={"flex": "1 1 400px"},
                        children=[
                            dcc.Loading(
                                dcc.Graph(
                                    id="market-volume-treemap",
                                    style={"height": "420px"},
                                ),
                                type="dot",
                                color=COLORS["accent"],
                            )
                        ],
                    ),
                    html.Div(
                        style={"flex": "1 1 400px"},
                        children=[
                            dcc.Loading(
                                dcc.Graph(
                                    id="market-price-treemap",
                                    style={"height": "420px"},
                                ),
                                type="dot",
                                color=COLORS["accent"],
                            )
                        ],
                    ),
                ],
            ),
        ],
    )


def trends_layout():
    types = sorted(df["type"].dropna().unique())

    return html.Div(
        style={"padding": "24px"},
        children=[
            html.H2(
                "Trends",
                style={
                    "color": COLORS["accent"],
                    "fontWeight": "700",
                    "marginBottom": "8px",
                },
            ),
            html.P(
                "Analyze rolling price trends and volatility over time.",
                style={"color": COLORS["muted"], "marginBottom": "12px"},
            ),
            html.Div(
                html.Span("● Rolling moving averages & daily volatility indicators", className="status-badge"),
                style={"marginBottom": "16px"},
            ),
            collapsible_info_box(
                "Moving Average Smoothing & Volatility Guide",
                [
                    "Rolling Window Control: Adjust the slider (2 to 20 days) to smooth out short-term fluctuations and uncover sustained price trends.",
                    "Organic vs. Conventional Spread: Compare price trajectories across avocado types to inspect premium margins over multi-year cycles.",
                    "Daily Price Volatility: Evaluates standard deviation of daily prices across regions, highlighting periods of market supply shocks.",
                ],
                default_open=False,
            ),
            html.Div(
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "16px",
                    "marginBottom": "24px",
                },
                children=[
                    html.Div(
                        children=[
                            html.Label(
                                "Date range",
                                style={"color": COLORS["muted"], "fontSize": "12px"},
                            ),
                            dcc.DatePickerRange(
                                id="t-date-range",
                                start_date=df["date"].min().date(),
                                end_date=df["date"].max().date(),
                                display_format="YYYY-MM-DD",
                            ),
                        ],
                    ),
                    html.Div(
                        style={"minWidth": "200px"},
                        children=[
                            html.Label(
                                "Types",
                                style={"color": COLORS["muted"], "fontSize": "12px"},
                            ),
                            dcc.Dropdown(
                                id="t-type-checklist",
                                options=[{"label": t, "value": t} for t in types],
                                multi=True,
                                placeholder="All types",
                            ),
                        ],
                    ),
                    html.Div(
                        style={"flex": "1 1 320px", "minWidth": "280px"},
                        children=[
                            html.Label(
                                "Rolling window (days)",
                                style={"color": COLORS["muted"], "fontSize": "12px"},
                            ),
                            dcc.Slider(
                                id="rolling-window",
                                min=2,
                                max=20,
                                step=1,
                                value=8,
                                marks={i: str(i) for i in range(2, 21, 2)},
                                updatemode="mouseup",
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "24px",
                },
                children=[
                    html.Div(
                        style={"flex": "1 1 400px"},
                        children=[
                            drilldown_badge(),
                            dcc.Loading(
                                dcc.Graph(
                                    id="rolling-chart",
                                    style={"height": "400px"},
                                ),
                                type="dot",
                                color=COLORS["accent"],
                            ),
                        ],
                    ),
                    html.Div(
                        style={"flex": "1 1 400px"},
                        children=[
                            drilldown_badge(),
                            dcc.Loading(
                                dcc.Graph(
                                    id="volatility-chart",
                                    style={"height": "400px"},
                                ),
                                type="dot",
                                color=COLORS["accent"],
                            ),
                        ],
                    ),
                ],
            ),
            dcc.Loading(
                html.Div(id="trends-drilldown-container"),
                type="dot",
                color=COLORS["accent"],
            ),
            dcc.Store(id="trends-selected-week", data=None),
        ],
    )


def comparison_layout():
    regions = sorted(df["region"].dropna().unique())
    types = sorted(df["type"].dropna().unique())
    default_type = "conventional" if "conventional" in types else (types[0] if types else None)

    return html.Div(
        style={"padding": "24px"},
        children=[
            html.H2(
                "Comparison",
                style={
                    "color": COLORS["accent"],
                    "fontWeight": "700",
                    "marginBottom": "8px",
                },
            ),
            html.P(
                "Compare prices and volumes between two regions.",
                style={"color": COLORS["muted"], "marginBottom": "12px"},
            ),
            html.Div(
                html.Span("● Multi-market differential & spread comparison", className="status-badge"),
                style={"marginBottom": "16px"},
            ),
            collapsible_info_box(
                "Regional Comparison & Data Notes",
                [
                    "Dataset Consistency: Both selected regions record weekly metrics for Conventional and Organic avocados concurrently.",
                    "All Types (Combined): Automatically sums conventional and organic units into true market volume, and calculates the combined weekly mean price.",
                    "Specific Types: Choose 'Conventional' or 'Organic' to benchmark identical product categories 1-to-1 between markets.",
                ],
                default_open=False,
            ),
            html.Div(
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "16px",
                    "marginBottom": "24px",
                },
                children=[
                    html.Div(
                        style={"minWidth": "200px"},
                        children=[
                            html.Label(
                                "Region 1",
                                style={"color": COLORS["muted"], "fontSize": "12px"},
                            ),
                            dcc.Dropdown(
                                id="comp-region-1",
                                options=[{"label": r, "value": r} for r in regions],
                                placeholder="Select region 1",
                            ),
                        ],
                    ),
                    html.Div(
                        style={"minWidth": "200px"},
                        children=[
                            html.Label(
                                "Region 2",
                                style={"color": COLORS["muted"], "fontSize": "12px"},
                            ),
                            dcc.Dropdown(
                                id="comp-region-2",
                                options=[{"label": r, "value": r} for r in regions],
                                placeholder="Select region 2",
                            ),
                        ],
                    ),
                    html.Div(
                        style={"minWidth": "200px"},
                        children=[
                            html.Label(
                                "Type",
                                style={"color": COLORS["muted"], "fontSize": "12px"},
                            ),
                            dcc.Dropdown(
                                id="comp-type",
                                options=[
                                    {"label": "All types (combined)", "value": "all"},
                                    {"label": "Conventional", "value": "conventional"},
                                    {"label": "Organic", "value": "organic"},
                                ],
                                value="all",
                                clearable=False,
                            ),
                        ],
                    ),
                    html.Div(
                        children=[
                            html.Label(
                                "Date range",
                                style={"color": COLORS["muted"], "fontSize": "12px"},
                            ),
                            dcc.DatePickerRange(
                                id="comp-date-range",
                                start_date=df["date"].min().date(),
                                end_date=df["date"].max().date(),
                                display_format="YYYY-MM-DD",
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                id="comp-kpis",
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "16px",
                    "marginBottom": "24px",
                },
            ),
            html.Div(
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "24px",
                },
                children=[
                    html.Div(
                        style={"flex": "1 1 400px"},
                        children=[
                            drilldown_badge(),
                            dcc.Loading(
                                dcc.Graph(
                                    id="comp-price-chart",
                                    style={"height": "400px"},
                                ),
                                type="dot",
                                color=COLORS["accent"],
                            ),
                        ],
                    ),
                    html.Div(
                        style={"flex": "1 1 400px"},
                        children=[
                            drilldown_badge(),
                            dcc.Loading(
                                dcc.Graph(
                                    id="comp-volume-chart",
                                    style={"height": "400px"},
                                ),
                                type="dot",
                                color=COLORS["accent"],
                            ),
                        ],
                    ),
                ],
            ),
            dcc.Loading(
                html.Div(id="comp-drilldown-container"),
                type="dot",
                color=COLORS["accent"],
            ),
            dcc.Store(id="comp-selected-week", data=None),
        ],
    )


def data_layout():
    regions = sorted(df["region"].dropna().unique())
    types = sorted(df["type"].dropna().unique())

    return html.Div(
        style={"padding": "24px"},
        children=[
            html.H2(
                "Data",
                style={
                    "color": COLORS["accent"],
                    "fontWeight": "700",
                    "marginBottom": "8px",
                },
            ),
            html.P(
                "Inspect the underlying avocado dataset with filters.",
                style={"color": COLORS["muted"], "marginBottom": "12px"},
            ),
            html.Div(
                html.Span("● Raw weekly observations • Instant CSV export", className="status-badge"),
                style={"marginBottom": "16px"},
            ),
            collapsible_info_box(
                "Raw Data Inspection & Export Guide",
                [
                    "Search & Dynamic Filter: Refine by region, type, and date range; the table updates in real time to match exact query criteria.",
                    "Instant CSV Export: Click '⬇ Export Filtered CSV' to download your current filtered dataset for offline spreadsheet or econometric modeling.",
                    "Render Performance: For optimal responsiveness, the table previews the latest 150 matching records with clean, formatted currency and volume counts.",
                ],
                default_open=False,
            ),
            html.Div(
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "16px",
                    "marginBottom": "24px",
                },
                children=[
                    html.Div(
                        style={"minWidth": "200px"},
                        children=[
                            html.Label(
                                "Regions",
                                style={"color": COLORS["muted"], "fontSize": "12px"},
                            ),
                            dcc.Dropdown(
                                id="data-region",
                                options=[{"label": r, "value": r} for r in regions],
                                multi=True,
                                placeholder="All regions",
                            ),
                        ],
                    ),
                    html.Div(
                        style={"minWidth": "200px"},
                        children=[
                            html.Label(
                                "Type",
                                style={"color": COLORS["muted"], "fontSize": "12px"},
                            ),
                            dcc.Dropdown(
                                id="data-type",
                                options=[{"label": t, "value": t} for t in types],
                                placeholder="All types",
                            ),
                        ],
                    ),
                    html.Div(
                        children=[
                            html.Label(
                                "Date range",
                                style={"color": COLORS["muted"], "fontSize": "12px"},
                            ),
                            dcc.DatePickerRange(
                                id="data-date-range",
                                start_date=df["date"].min().date(),
                                end_date=df["date"].max().date(),
                                display_format="YYYY-MM-DD",
                            ),
                        ],
                    ),
                    html.Div(
                        style={"display": "flex", "alignItems": "flex-end"},
                        children=[
                            html.Button(
                                "⬇ Export Filtered CSV",
                                id="btn-download-csv",
                                style={
                                    "backgroundColor": COLORS["accent_soft"],
                                    "color": COLORS["accent"],
                                    "border": f"1px solid {COLORS['accent']}",
                                    "borderRadius": "8px",
                                    "padding": "9px 16px",
                                    "fontWeight": "600",
                                    "fontSize": "13px",
                                    "cursor": "pointer",
                                    "height": "38px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "6px",
                                },
                            ),
                            dcc.Download(id="download-dataframe-csv"),
                        ],
                    ),
                ],
            ),
            dcc.Loading(
                html.Div(
                    id="data-table-container",
                    style={
                        "maxHeight": "520px",
                        "overflowY": "auto",
                        "border": f"1px solid {COLORS['border']}",
                        "borderRadius": "12px",
                        "padding": "12px",
                        "backgroundColor": COLORS["card"],
                    },
                ),
                type="dot",
                color=COLORS["accent"],
            ),
        ],
    )


app = Dash(__name__)
server = app.server

app.layout = html.Div(
    style=GLOBAL_STYLE,
    children=[
        dcc.Location(id="url"),
        html.Link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;600;700&display=swap",
        ),
        dark_mode_style_component(),
        navbar("/"),
        html.Div(id="page-content"),
    ],
)


@app.callback(
    [Output("navbar", "children"), Output("page-content", "children")],
    Input("url", "pathname"),
)
def display_page(pathname):
    nav = navbar(pathname).children

    if pathname in [None, "/"]:
        page = overview_layout()
    elif pathname == "/markets":
        page = markets_layout()
    elif pathname == "/trends":
        page = trends_layout()
    elif pathname == "/comparison":
        page = comparison_layout()
    elif pathname == "/data":
        page = data_layout()
    else:
        page = html.Div(
            style={"padding": "24px"},
            children=[
                html.H2(
                    "404 - Page not found",
                    style={"color": COLORS["text"], "fontWeight": "700"},
                ),
                html.P(
                    "The page you requested does not exist.",
                    style={"color": COLORS["muted"]},
                ),
            ],
        )

    return nav, page


@app.callback(
    [
        Output("price-over-time", "figure"),
        Output("volume-over-time", "figure"),
        Output("kpi-container", "children"),
    ],
    [
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("region-dropdown", "value"),
        Input("type-checklist", "value"),
    ],
)
def update_overview(start_date, end_date, regions, types):
    mask = pd.Series(True, index=df.index)
    if start_date is not None:
        mask &= (df["date"] >= pd.to_datetime(start_date))
    if end_date is not None:
        mask &= (df["date"] <= pd.to_datetime(end_date))
    if regions:
        mask &= df["region"].isin(regions)
    if types:
        mask &= df["type"].isin(types)

    dff = df[mask]
    if dff.empty:
        return empty_figure(), empty_figure(), []

    grouped = (
        dff.groupby(["date", "type"])["average_price"]
        .mean()
        .reset_index()
        .sort_values("date")
    )

    fig = px.line(
        grouped,
        x="date",
        y="average_price",
        color="type",
        labels={"average_price": "Average price", "date": "Date", "type": "Type"},
        color_discrete_sequence=AVOCADO_COLORS,
    )
    fig.update_traces(
        mode="lines+markers",
        marker=dict(size=4),
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Avg Price: <b>$%{y:.2f}</b><br><span style='font-size:11px;color:#7AC74F'>👆 Click point to inspect week</span><extra>%{fullData.name}</extra>",
    )
    apply_fig_theme(fig, title="Average price over time")

    grouped_vol = (
        dff.groupby(["date", "type"])["total_volume"]
        .sum()
        .reset_index()
        .sort_values("date")
    )

    fig_vol = px.line(
        grouped_vol,
        x="date",
        y="total_volume",
        color="type",
        labels={"total_volume": "Total volume", "date": "Date", "type": "Type"},
        color_discrete_sequence=AVOCADO_COLORS,
    )
    fig_vol.update_traces(
        mode="lines+markers",
        marker=dict(size=4),
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Total Volume: <b>%{y:,.0f} units</b><br><span style='font-size:11px;color:#7AC74F'>👆 Click point to inspect week</span><extra>%{fullData.name}</extra>",
    )
    apply_fig_theme(fig_vol, title="Total volume over time")

    total_volume = dff["total_volume"].sum()
    avg_price = dff["average_price"].mean()

    region_volume = (
        dff.groupby("region")["total_volume"].sum().reset_index().sort_values("total_volume", ascending=False)
    )
    top_region = region_volume["region"].iloc[0] if not region_volume.empty else None

    daily_mean = (
        dff.groupby("date")["average_price"].mean().sort_index()
    )
    daily_diff = daily_mean.diff()
    volatility = daily_diff.std() if len(daily_diff.dropna()) > 0 else None
    latest_change = daily_diff.iloc[-1] if len(daily_diff.dropna()) > 0 else None

    def kpi_card(title, value, subtitle=None, badge=None):
        return html.Div(
            className="kpi-card",
            style={
                "backgroundColor": COLORS["card"],
                "borderRadius": "16px",
                "border": f"1px solid {COLORS['border']}",
                "padding": "14px 18px",
                "minWidth": "200px",
                "flex": "1 1 180px",
                "cursor": "default",
            },
            children=[
                html.Div(
                    style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "4px"},
                    children=[
                        html.Span(
                            title,
                            style={
                                "color": COLORS["muted"],
                                "fontSize": "11.5px",
                                "fontWeight": "600",
                                "letterSpacing": "0.4px",
                                "textTransform": "uppercase",
                            },
                        ),
                        html.Span(badge, style={"fontSize": "14px"}) if badge else None,
                    ],
                ),
                html.Div(
                    value,
                    style={
                        "color": COLORS["text"],
                        "fontSize": "22px",
                        "fontWeight": "700",
                    },
                ),
                html.Div(
                    subtitle or "",
                    style={
                        "color": COLORS["accent"] if "change" in title.lower() or "volatility" in title.lower() else COLORS["muted"],
                        "fontSize": "11px",
                        "marginTop": "4px",
                    },
                ),
            ],
        )

    kpis = [
        kpi_card("Total volume", format_number(total_volume), "Units sold across selection", "📦"),
        kpi_card("Average price", f"${avg_price:.2f}" if avg_price else "–", "Mean price per avocado", "🥑"),
        kpi_card("Top region by volume", top_region if top_region else "–", "Highest volume market", "🏆"),
        kpi_card("Price volatility", f"${volatility:.3f}" if volatility else "–", "Std. dev. of daily shifts", "📈"),
        kpi_card("Latest daily change", format_change_kpi(latest_change, is_currency=True), "vs previous day", "⚡"),
    ]

    return fig, fig_vol, kpis


@app.callback(
    Output("overview-selected-week", "data"),
    [
        Input("price-over-time", "clickData"),
        Input("volume-over-time", "clickData"),
    ],
    prevent_initial_call=True,
)
def store_overview_selected_week(price_click, vol_click):
    try:
        trig_id = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else None
    except Exception:
        trig_id = None
    click_data = price_click if trig_id == "price-over-time" else (vol_click if trig_id == "volume-over-time" else (price_click or vol_click))
    if not click_data or not click_data.get("points"):
        return None
    point = click_data["points"][0]
    clicked_raw = point.get("x")
    if not clicked_raw:
        return None
    return str(clicked_raw)[:10]


@app.callback(
    Output("overview-drilldown-container", "children"),
    [
        Input("overview-selected-week", "data"),
        Input("region-dropdown", "value"),
        Input("type-checklist", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_overview_drilldown(selected_week, regions, types, start_date, end_date):
    if not selected_week:
        return html.Div(
            style={
                "backgroundColor": COLORS["card"],
                "border": f"1px dashed {COLORS['border']}",
                "borderRadius": "16px",
                "padding": "24px 28px",
                "textAlign": "center",
                "marginTop": "24px",
            },
            children=[
                html.Div("👆", style={"fontSize": "26px", "marginBottom": "6px"}),
                html.Div(
                    "Interactive Weekly Market Breakdown",
                    style={"color": COLORS["accent"], "fontWeight": "700", "fontSize": "16px", "marginBottom": "4px"},
                ),
                html.Div(
                    "Click on any data point along the price or volume trend lines above to inspect a detailed market-by-market volume & price breakdown for that exact week.",
                    style={"color": COLORS["muted"], "fontSize": "13px"},
                ),
            ],
        )

    date_str = str(selected_week)[:10]
    try:
        target_date = pd.to_datetime(date_str)
    except Exception:
        return html.Div("Invalid date.")

    if (start_date and target_date < pd.to_datetime(start_date)) or (end_date and target_date > pd.to_datetime(end_date)):
        return html.Div(
            style={
                "backgroundColor": COLORS["card"],
                "border": f"1px dashed {COLORS['border']}",
                "borderRadius": "16px",
                "padding": "24px 28px",
                "textAlign": "center",
                "marginTop": "24px",
            },
            children=[
                html.Div("📅", style={"fontSize": "26px", "marginBottom": "6px"}),
                html.Div(
                    f"Selected week ({date_str}) is outside current date filters",
                    style={"color": COLORS["accent"], "fontWeight": "700", "fontSize": "16px", "marginBottom": "4px"},
                ),
                html.Div(
                    "Widen your date filter range or click a data point on the chart above to inspect a new week.",
                    style={"color": COLORS["muted"], "fontSize": "13px"},
                ),
            ],
        )

    week_df = df[df["date"] == target_date]
    if regions:
        week_df = week_df[week_df["region"].isin(regions)]
    if types:
        week_df = week_df[week_df["type"].isin(types)]

    if week_df.empty:
        return html.Div(
            style={"padding": "20px", "textAlign": "center", "color": COLORS["muted"]},
            children=f"No matching regional records found for the week of {date_str} with the current filter selection.",
        )

    date_formatted = target_date.strftime("%B %d, %Y")
    total_vol = week_df["total_volume"].sum()
    avg_price = week_df["average_price"].mean()
    n_markets = week_df["region"].nunique()

    # 1. Top 10 regions by volume
    vol_by_reg = (
        week_df.groupby("region")["total_volume"]
        .sum()
        .reset_index()
        .sort_values("total_volume", ascending=False)
        .head(10)
        .sort_values("total_volume", ascending=True)
    )
    vol_by_reg["vol_formatted"] = vol_by_reg["total_volume"].map(format_number)

    fig_bar_vol = px.bar(
        vol_by_reg,
        x="total_volume",
        y="region",
        orientation="h",
        text="vol_formatted",
        labels={"total_volume": "Total Volume", "region": "Market"},
        color_discrete_sequence=[COLORS["accent"]],
    )
    fig_bar_vol.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#0E0E0E", size=12, family="'Quicksand', sans-serif"),
        marker=dict(line=dict(width=1, color="#121212")),
        hovertemplate="<b>%{y}</b><br>Volume: %{x:,.0f} units (%{text})<extra></extra>",
    )
    apply_fig_theme(fig_bar_vol, title="Top 10 Markets by Volume")
    fig_bar_vol.update_layout(height=360, margin=dict(l=10, r=20, t=50, b=30), xaxis_title="", yaxis_title="")

    # 2. Top 10 regions by price
    price_by_reg = (
        week_df.groupby("region")["average_price"]
        .mean()
        .reset_index()
        .sort_values("average_price", ascending=False)
        .head(10)
        .sort_values("average_price", ascending=True)
    )
    price_by_reg["price_formatted"] = price_by_reg["average_price"].map(lambda p: f"${p:.2f}")

    fig_bar_price = px.bar(
        price_by_reg,
        x="average_price",
        y="region",
        orientation="h",
        text="price_formatted",
        labels={"average_price": "Average Price", "region": "Market"},
        color_discrete_sequence=["#D4A373"],
    )
    fig_bar_price.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#0E0E0E", size=12, family="'Quicksand', sans-serif"),
        marker=dict(line=dict(width=1, color="#121212")),
        hovertemplate="<b>%{y}</b><br>Avg Price: $%{x:.2f}<extra></extra>",
    )
    apply_fig_theme(fig_bar_price, title="Top 10 Markets by Average Price")
    fig_bar_price.update_layout(height=360, margin=dict(l=10, r=20, t=50, b=30), xaxis_title="", yaxis_title="")

    top_vol_reg = vol_by_reg.iloc[-1]["region"]
    top_price_reg = price_by_reg.iloc[-1]["region"]

    return html.Div(
        style={
            "backgroundColor": COLORS["card"],
            "borderRadius": "18px",
            "border": f"1px solid {COLORS['accent']}",
            "padding": "24px",
            "marginTop": "24px",
            "boxShadow": "0 8px 30px rgba(0,0,0,0.35)",
        },
        children=[
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "flex-start",
                    "flexWrap": "wrap",
                    "gap": "12px",
                    "marginBottom": "18px",
                    "borderBottom": f"1px solid {COLORS['border']}",
                    "paddingBottom": "14px",
                },
                children=[
                    html.Div(
                        children=[
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "gap": "8px"},
                                children=[
                                    html.Span("📅", style={"fontSize": "20px"}),
                                    html.H3(
                                        "Weekly Market Breakdown",
                                        style={
                                            "color": COLORS["accent"],
                                            "margin": 0,
                                            "fontWeight": "800",
                                            "fontSize": "19px",
                                        },
                                    ),
                                    html.Span(f"● Week of {date_formatted}", className="status-badge", style={"fontSize": "11px", "padding": "3px 10px"}),
                                ],
                            ),
                            html.P(
                                f"Regional price and volume distributions across {n_markets} reporting markets for sales commencing {date_formatted}.",
                                style={"color": COLORS["muted"], "margin": "4px 0 0 0", "fontSize": "12.5px"},
                            ),
                        ],
                    ),
                    html.Span(
                        "💡 Click any other date point above to change the breakdown week",
                        style={
                            "color": COLORS["muted"],
                            "fontSize": "11.5px",
                            "fontStyle": "italic",
                            "alignSelf": "center",
                        },
                    ),
                ],
            ),
            html.Div(
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "14px",
                    "marginBottom": "20px",
                },
                children=[
                    html.Div(
                        style={
                            "backgroundColor": "rgba(255,255,255,0.03)",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "12px",
                            "padding": "10px 16px",
                            "flex": "1 1 160px",
                        },
                        children=[
                            html.Div("TOTAL WEEKLY VOLUME", style={"color": COLORS["muted"], "fontSize": "10px", "fontWeight": "700"}),
                            html.Div(f"{format_number(total_vol)} units", style={"color": COLORS["text"], "fontSize": "18px", "fontWeight": "700", "marginTop": "2px"}),
                        ],
                    ),
                    html.Div(
                        style={
                            "backgroundColor": "rgba(255,255,255,0.03)",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "12px",
                            "padding": "10px 16px",
                            "flex": "1 1 160px",
                        },
                        children=[
                            html.Div("NATIONAL AVERAGE PRICE", style={"color": COLORS["muted"], "fontSize": "10px", "fontWeight": "700"}),
                            html.Div(f"${avg_price:.2f}", style={"color": COLORS["accent"], "fontSize": "18px", "fontWeight": "700", "marginTop": "2px"}),
                        ],
                    ),
                    html.Div(
                        style={
                            "backgroundColor": "rgba(255,255,255,0.03)",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "12px",
                            "padding": "10px 16px",
                            "flex": "1 1 160px",
                        },
                        children=[
                            html.Div("TOP VOLUME MARKET", style={"color": COLORS["muted"], "fontSize": "10px", "fontWeight": "700"}),
                            html.Div(top_vol_reg, style={"color": COLORS["text"], "fontSize": "16px", "fontWeight": "700", "marginTop": "2px"}),
                        ],
                    ),
                    html.Div(
                        style={
                            "backgroundColor": "rgba(255,255,255,0.03)",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "12px",
                            "padding": "10px 16px",
                            "flex": "1 1 160px",
                        },
                        children=[
                            html.Div("HIGHEST PRICED MARKET", style={"color": COLORS["muted"], "fontSize": "10px", "fontWeight": "700"}),
                            html.Div(top_price_reg, style={"color": COLORS["text"], "fontSize": "16px", "fontWeight": "700", "marginTop": "2px"}),
                        ],
                    ),
                ],
            ),
            html.Div(
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "20px",
                },
                children=[
                    html.Div(
                        style={"flex": "1 1 450px"},
                        children=[
                            drilldown_badge(f"● Week of {date_formatted}"),
                            dcc.Graph(figure=fig_bar_vol, config={"displayModeBar": False}),
                        ],
                    ),
                    html.Div(
                        style={"flex": "1 1 450px"},
                        children=[
                            drilldown_badge(f"● Week of {date_formatted}"),
                            dcc.Graph(figure=fig_bar_price, config={"displayModeBar": False}),
                        ],
                    ),
                ],
            ),
        ],
    )


@app.callback(
    [
        Output("market-volume-treemap", "figure"),
        Output("market-price-treemap", "figure"),
    ],
    Input("market-region-filter", "value"),
)
def update_markets(regions):
    if regions:
        dff = df[df["region"].isin(regions)]
    else:
        dff = df

    if dff.empty:
        return empty_figure(), empty_figure()

    grouped = dff.groupby("region").agg(
        avg_price=("average_price", "mean"),
        total_volume=("total_volume", "sum"),
    ).reset_index()

    grouped["vol_short"] = grouped["total_volume"].map(format_number)
    grouped["price_short"] = grouped["avg_price"].map(lambda p: f"${p:.2f}")

    # Treemap by volume
    fig_volume_treemap = px.treemap(
        grouped,
        path=["region"],
        values="total_volume",
        color="total_volume",
        color_continuous_scale="Greens",
        custom_data=["vol_short"],
    )
    fig_volume_treemap.update_traces(
        texttemplate="<b>%{label}</b><br><span style='font-size:14px; font-weight:700;'>%{customdata[0]}</span>",
        hovertemplate="<b>%{label}</b><br>Total Volume: <b>%{value:,.0f} units</b> (%{customdata[0]})<extra></extra>",
        marker=dict(pad=dict(t=8, l=4, r=4, b=4), line=dict(width=1.5, color="#121212")),
    )
    apply_fig_theme(fig_volume_treemap, title="Regional Market Heatmap (Total Volume)")

    # Treemap by price
    fig_price_treemap = px.treemap(
        grouped,
        path=["region"],
        values="avg_price",
        color="avg_price",
        color_continuous_scale="Viridis",
        custom_data=["price_short"],
    )
    fig_price_treemap.update_traces(
        texttemplate="<b>%{label}</b><br><span style='font-size:14px; font-weight:700;'>%{customdata[0]}</span>",
        hovertemplate="<b>%{label}</b><br>Average Price: <b>$%{value:.2f}</b><extra></extra>",
        marker=dict(pad=dict(t=8, l=4, r=4, b=4), line=dict(width=1.5, color="#121212")),
    )
    apply_fig_theme(fig_price_treemap, title="Regional Price Heatmap")

    return fig_volume_treemap, fig_price_treemap


@app.callback(
    [
        Output("rolling-chart", "figure"),
        Output("volatility-chart", "figure"),
    ],
    [
        Input("t-date-range", "start_date"),
        Input("t-date-range", "end_date"),
        Input("t-type-checklist", "value"),
        Input("rolling-window", "value"),
    ],
)
def update_trends(start_date, end_date, types, window):
    mask = pd.Series(True, index=df.index)
    if start_date is not None:
        mask &= (df["date"] >= pd.to_datetime(start_date))
    if end_date is not None:
        mask &= (df["date"] <= pd.to_datetime(end_date))
    if types:
        mask &= df["type"].isin(types)

    dff = df[mask]
    if dff.empty:
        return empty_figure(), empty_figure()

    dff = dff.sort_values("date")

    # Rolling average price per type
    rolling_base = (
        dff.groupby(["type", "date"])["average_price"]
        .mean()
        .reset_index()
    )

    rolling_base["rolling_price"] = (
        rolling_base.groupby("type")["average_price"]
        .rolling(window=window)
        .mean()
        .reset_index(level=0, drop=True)
    )

    fig_rolling = px.line(
        rolling_base,
        x="date",
        y="rolling_price",
        color="type",
        labels={"rolling_price": "Rolling average price", "date": "Date", "type": "Type"},
        color_discrete_sequence=AVOCADO_COLORS,
    )
    fig_rolling.update_traces(
        mode="lines+markers",
        marker=dict(size=4),
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Rolling Avg Price: <b>$%{y:.2f}</b><br><span style='font-size:11px;color:#7AC74F'>👆 Click point to inspect week</span><extra>%{fullData.name}</extra>",
    )
    apply_fig_theme(fig_rolling, title=f"Rolling average price ({window}-day window)")

    # Volatility: std of daily price across regions per type
    vol_df = (
        dff.groupby(["type", "date"])["average_price"]
        .agg(["mean", "std"])
        .reset_index()
        .rename(columns={"std": "volatility"})
    )

    fig_vol = px.line(
        vol_df,
        x="date",
        y="volatility",
        color="type",
        labels={"volatility": "Price volatility (std)", "date": "Date", "type": "Type"},
        color_discrete_sequence=AVOCADO_COLORS,
    )
    fig_vol.update_traces(
        mode="lines+markers",
        marker=dict(size=4),
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Daily Volatility (Std): <b>$%{y:.3f}</b><br><span style='font-size:11px;color:#7AC74F'>👆 Click point to inspect week</span><extra>%{fullData.name}</extra>",
    )
    apply_fig_theme(fig_vol, title="Daily price volatility by type")

    return fig_rolling, fig_vol


@app.callback(
    Output("trends-selected-week", "data"),
    [
        Input("rolling-chart", "clickData"),
        Input("volatility-chart", "clickData"),
    ],
    prevent_initial_call=True,
)
def store_trends_selected_week(rolling_click, vol_click):
    try:
        trig_id = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else None
    except Exception:
        trig_id = None
    click_data = rolling_click if trig_id == "rolling-chart" else (vol_click if trig_id == "volatility-chart" else (rolling_click or vol_click))
    if not click_data or not click_data.get("points"):
        return None
    point = click_data["points"][0]
    clicked_raw = point.get("x")
    if not clicked_raw:
        return None
    return str(clicked_raw)[:10]


@app.callback(
    Output("trends-drilldown-container", "children"),
    [
        Input("trends-selected-week", "data"),
        Input("t-type-checklist", "value"),
        Input("t-date-range", "start_date"),
        Input("t-date-range", "end_date"),
    ],
)
def update_trends_drilldown(selected_week, types, start_date, end_date):
    if not selected_week:
        return html.Div(
            style={
                "backgroundColor": COLORS["card"],
                "border": f"1px dashed {COLORS['border']}",
                "borderRadius": "16px",
                "padding": "24px 28px",
                "textAlign": "center",
                "marginTop": "24px",
            },
            children=[
                html.Div("👆", style={"fontSize": "26px", "marginBottom": "6px"}),
                html.Div(
                    "Interactive Weekly Market Breakdown",
                    style={"color": COLORS["accent"], "fontWeight": "700", "fontSize": "16px", "marginBottom": "4px"},
                ),
                html.Div(
                    "Click on any data point along the rolling price or volatility lines above to inspect a detailed market-by-market volume & price breakdown for that exact week.",
                    style={"color": COLORS["muted"], "fontSize": "13px"},
                ),
            ],
        )

    date_str = str(selected_week)[:10]
    try:
        target_date = pd.to_datetime(date_str)
    except Exception:
        return html.Div("Invalid date.")

    if (start_date and target_date < pd.to_datetime(start_date)) or (end_date and target_date > pd.to_datetime(end_date)):
        return html.Div(
            style={
                "backgroundColor": COLORS["card"],
                "border": f"1px dashed {COLORS['border']}",
                "borderRadius": "16px",
                "padding": "24px 28px",
                "textAlign": "center",
                "marginTop": "24px",
            },
            children=[
                html.Div("📅", style={"fontSize": "26px", "marginBottom": "6px"}),
                html.Div(
                    f"Selected week ({date_str}) is outside current date filters",
                    style={"color": COLORS["accent"], "fontWeight": "700", "fontSize": "16px", "marginBottom": "4px"},
                ),
                html.Div(
                    "Widen your date filter range or click a data point on the chart above to inspect a new week.",
                    style={"color": COLORS["muted"], "fontSize": "13px"},
                ),
            ],
        )

    week_df = df[df["date"] == target_date]
    if types:
        week_df = week_df[week_df["type"].isin(types)]

    if week_df.empty:
        return html.Div(
            style={"padding": "20px", "textAlign": "center", "color": COLORS["muted"]},
            children=f"No matching records found for the week of {date_str} with the current filter selection.",
        )

    date_formatted = target_date.strftime("%B %d, %Y")
    total_vol = week_df["total_volume"].sum()
    avg_price = week_df["average_price"].mean()
    n_markets = week_df["region"].nunique()

    # 1. Top 10 regions by volume
    vol_by_reg = (
        week_df.groupby("region")["total_volume"]
        .sum()
        .reset_index()
        .sort_values("total_volume", ascending=False)
        .head(10)
        .sort_values("total_volume", ascending=True)
    )
    vol_by_reg["vol_formatted"] = vol_by_reg["total_volume"].map(format_number)

    fig_bar_vol = px.bar(
        vol_by_reg,
        x="total_volume",
        y="region",
        orientation="h",
        text="vol_formatted",
        labels={"total_volume": "Total Volume", "region": "Market"},
        color_discrete_sequence=[COLORS["accent"]],
    )
    fig_bar_vol.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#0E0E0E", size=12, family="'Quicksand', sans-serif"),
        marker=dict(line=dict(width=1, color="#121212")),
        hovertemplate="<b>%{y}</b><br>Volume: %{x:,.0f} units (%{text})<extra></extra>",
    )
    apply_fig_theme(fig_bar_vol, title="Top 10 Markets by Volume")
    fig_bar_vol.update_layout(
        height=360,
        margin=dict(l=10, r=20, t=50, b=30),
        xaxis_title="",
        yaxis_title="",
    )

    # 2. Top 10 regions by average price
    price_by_reg = (
        week_df.groupby("region")["average_price"]
        .mean()
        .reset_index()
        .sort_values("average_price", ascending=False)
        .head(10)
        .sort_values("average_price", ascending=True)
    )
    price_by_reg["price_formatted"] = price_by_reg["average_price"].map(lambda p: f"${p:.2f}")

    fig_bar_price = px.bar(
        price_by_reg,
        x="average_price",
        y="region",
        orientation="h",
        text="price_formatted",
        labels={"average_price": "Average Price", "region": "Market"},
        color_discrete_sequence=["#D4A373"],
    )
    fig_bar_price.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#0E0E0E", size=12, family="'Quicksand', sans-serif"),
        marker=dict(line=dict(width=1, color="#121212")),
        hovertemplate="<b>%{y}</b><br>Avg Price: $%{x:.2f}<extra></extra>",
    )
    apply_fig_theme(fig_bar_price, title="Top 10 Markets by Average Price")
    fig_bar_price.update_layout(
        height=360,
        margin=dict(l=10, r=20, t=50, b=30),
        xaxis_title="",
        yaxis_title="",
    )

    top_vol_reg = vol_by_reg.iloc[-1]["region"]
    top_price_reg = price_by_reg.iloc[-1]["region"]

    return html.Div(
        style={
            "backgroundColor": COLORS["card"],
            "borderRadius": "18px",
            "border": f"1px solid {COLORS['accent']}",
            "padding": "24px",
            "marginTop": "24px",
            "boxShadow": "0 8px 30px rgba(0,0,0,0.35)",
        },
        children=[
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "flex-start",
                    "flexWrap": "wrap",
                    "gap": "12px",
                    "marginBottom": "18px",
                    "borderBottom": f"1px solid {COLORS['border']}",
                    "paddingBottom": "14px",
                },
                children=[
                    html.Div(
                        children=[
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "gap": "8px"},
                                children=[
                                    html.Span("📅", style={"fontSize": "20px"}),
                                    html.H3(
                                        "Weekly Market Breakdown",
                                        style={
                                            "color": COLORS["accent"],
                                            "margin": 0,
                                            "fontWeight": "800",
                                            "fontSize": "19px",
                                        },
                                    ),
                                    html.Span(f"● Week of {date_formatted}", className="status-badge", style={"fontSize": "11px", "padding": "3px 10px"}),
                                ],
                            ),
                            html.P(
                                f"Regional price and volume distributions across {n_markets} reporting markets for sales commencing {date_formatted}.",
                                style={"color": COLORS["muted"], "margin": "4px 0 0 0", "fontSize": "12.5px"},
                            ),
                        ],
                    ),
                    html.Span(
                        "💡 Click any other date point above to change the breakdown week",
                        style={
                            "color": COLORS["muted"],
                            "fontSize": "11.5px",
                            "fontStyle": "italic",
                            "alignSelf": "center",
                        },
                    ),
                ],
            ),
            html.Div(
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "14px",
                    "marginBottom": "20px",
                },
                children=[
                    html.Div(
                        style={
                            "backgroundColor": "rgba(255,255,255,0.03)",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "12px",
                            "padding": "10px 16px",
                            "flex": "1 1 160px",
                        },
                        children=[
                            html.Div("TOTAL WEEKLY VOLUME", style={"color": COLORS["muted"], "fontSize": "10px", "fontWeight": "700"}),
                            html.Div(f"{format_number(total_vol)} units", style={"color": COLORS["text"], "fontSize": "18px", "fontWeight": "700", "marginTop": "2px"}),
                        ],
                    ),
                    html.Div(
                        style={
                            "backgroundColor": "rgba(255,255,255,0.03)",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "12px",
                            "padding": "10px 16px",
                            "flex": "1 1 160px",
                        },
                        children=[
                            html.Div("NATIONAL AVERAGE PRICE", style={"color": COLORS["muted"], "fontSize": "10px", "fontWeight": "700"}),
                            html.Div(f"${avg_price:.2f}", style={"color": COLORS["accent"], "fontSize": "18px", "fontWeight": "700", "marginTop": "2px"}),
                        ],
                    ),
                    html.Div(
                        style={
                            "backgroundColor": "rgba(255,255,255,0.03)",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "12px",
                            "padding": "10px 16px",
                            "flex": "1 1 160px",
                        },
                        children=[
                            html.Div("TOP VOLUME MARKET", style={"color": COLORS["muted"], "fontSize": "10px", "fontWeight": "700"}),
                            html.Div(top_vol_reg, style={"color": COLORS["text"], "fontSize": "16px", "fontWeight": "700", "marginTop": "2px"}),
                        ],
                    ),
                    html.Div(
                        style={
                            "backgroundColor": "rgba(255,255,255,0.03)",
                            "border": f"1px solid {COLORS['border']}",
                            "borderRadius": "12px",
                            "padding": "10px 16px",
                            "flex": "1 1 160px",
                        },
                        children=[
                            html.Div("HIGHEST PRICED MARKET", style={"color": COLORS["muted"], "fontSize": "10px", "fontWeight": "700"}),
                            html.Div(top_price_reg, style={"color": COLORS["text"], "fontSize": "16px", "fontWeight": "700", "marginTop": "2px"}),
                        ],
                    ),
                ],
            ),
            html.Div(
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "20px",
                },
                children=[
                    html.Div(
                        style={"flex": "1 1 450px"},
                        children=[
                            drilldown_badge(f"● Week of {date_formatted}"),
                            dcc.Graph(figure=fig_bar_vol, config={"displayModeBar": False}),
                        ],
                    ),
                    html.Div(
                        style={"flex": "1 1 450px"},
                        children=[
                            drilldown_badge(f"● Week of {date_formatted}"),
                            dcc.Graph(figure=fig_bar_price, config={"displayModeBar": False}),
                        ],
                    ),
                ],
            ),
        ],
    )


@app.callback(
    [
        Output("comp-price-chart", "figure"),
        Output("comp-volume-chart", "figure"),
        Output("comp-kpis", "children"),
    ],
    [
        Input("comp-region-1", "value"),
        Input("comp-region-2", "value"),
        Input("comp-type", "value"),
        Input("comp-date-range", "start_date"),
        Input("comp-date-range", "end_date"),
    ],
)
def update_comparison(region1, region2, comp_type, start_date, end_date):
    mask = pd.Series(True, index=df.index)
    if start_date is not None:
        mask &= (df["date"] >= pd.to_datetime(start_date))
    if end_date is not None:
        mask &= (df["date"] <= pd.to_datetime(end_date))
    if comp_type and comp_type != "all":
        mask &= (df["type"] == comp_type)
        type_label = comp_type.title()
        type_sub = f" • {type_label}"
    else:
        type_label = "All types combined"
        type_sub = " • Combined types"

    dff = df[mask]

    if not region1 or not region2:
        return empty_figure("Select both regions to compare."), empty_figure("Select both regions to compare."), []

    dff1 = dff[dff["region"] == region1]
    dff2 = dff[dff["region"] == region2]

    if dff1.empty or dff2.empty:
        return empty_figure("No data for selected regions."), empty_figure("No data for selected regions."), []

    # Aggregate by date so that when "All types" (or both types) are selected,
    # total volume is the combined sum for that date, and price is the combined average price!
    dff1_agg = (
        dff1.groupby("date")
        .agg(
            average_price=("average_price", "mean"),
            total_volume=("total_volume", "sum"),
        )
        .reset_index()
        .sort_values("date")
    )

    dff2_agg = (
        dff2.groupby("date")
        .agg(
            average_price=("average_price", "mean"),
            total_volume=("total_volume", "sum"),
        )
        .reset_index()
        .sort_values("date")
    )

    # Price comparison
    fig_price = go.Figure()
    fig_price.add_trace(
        go.Scatter(
            x=dff1_agg["date"],
            y=dff1_agg["average_price"],
            mode="lines+markers",
            marker=dict(size=4),
            name=region1,
            line=dict(color=AVOCADO_COLORS[0], width=2.5),
            hovertemplate=f"<b>{region1}</b>: $%{{y:.2f}}<br><span style='font-size:11px;color:#7AC74F'>👆 Click to inspect week</span><extra></extra>",
        )
    )
    fig_price.add_trace(
        go.Scatter(
            x=dff2_agg["date"],
            y=dff2_agg["average_price"],
            mode="lines+markers",
            marker=dict(size=4),
            name=region2,
            line=dict(color=AVOCADO_COLORS[1], width=2.5),
            hovertemplate=f"<b>{region2}</b>: $%{{y:.2f}}<br><span style='font-size:11px;color:#7AC74F'>👆 Click to inspect week</span><extra></extra>",
        )
    )
    apply_fig_theme(fig_price, title=f"Average price comparison ({type_label})")

    # Volume comparison
    fig_volume = go.Figure()
    fig_volume.add_trace(
        go.Scatter(
            x=dff1_agg["date"],
            y=dff1_agg["total_volume"],
            mode="lines+markers",
            marker=dict(size=4),
            name=region1,
            line=dict(color=AVOCADO_COLORS[0], width=2.5),
            hovertemplate=f"<b>{region1}</b>: %{{y:,.0f}} units<br><span style='font-size:11px;color:#7AC74F'>👆 Click to inspect week</span><extra></extra>",
        )
    )
    fig_volume.add_trace(
        go.Scatter(
            x=dff2_agg["date"],
            y=dff2_agg["total_volume"],
            mode="lines+markers",
            marker=dict(size=4),
            name=region2,
            line=dict(color=AVOCADO_COLORS[1], width=2.5),
            hovertemplate=f"<b>{region2}</b>: %{{y:,.0f}} units<br><span style='font-size:11px;color:#7AC74F'>👆 Click to inspect week</span><extra></extra>",
        )
    )
    apply_fig_theme(fig_volume, title=f"Total volume comparison ({type_label})")

    avg_price_1 = dff1["average_price"].mean()
    avg_price_2 = dff2["average_price"].mean()
    price_diff = avg_price_1 - avg_price_2

    vol_1 = dff1["total_volume"].sum()
    vol_2 = dff2["total_volume"].sum()
    vol_diff = vol_1 - vol_2

    def comp_kpi(title, value, subtitle=None):
        return html.Div(
            className="kpi-card",
            style={
                "backgroundColor": COLORS["card"],
                "borderRadius": "16px",
                "border": f"1px solid {COLORS['border']}",
                "padding": "14px 18px",
                "minWidth": "190px",
                "flex": "1 1 170px",
            },
            children=[
                html.Div(
                    title,
                    style={
                        "color": COLORS["muted"],
                        "fontSize": "11.5px",
                        "fontWeight": "600",
                        "letterSpacing": "0.3px",
                        "textTransform": "uppercase",
                        "marginBottom": "4px",
                    },
                ),
                html.Div(
                    value,
                    style={
                        "color": COLORS["text"],
                        "fontSize": "20px",
                        "fontWeight": "700",
                    },
                ),
                html.Div(
                    subtitle or "",
                    style={
                        "color": COLORS["accent"] if "diff" in title.lower() else COLORS["muted"],
                        "fontSize": "11px",
                        "marginTop": "4px",
                    },
                ),
            ],
        )

    kpis = [
        comp_kpi(f"{region1} avg price", f"${avg_price_1:.2f}" if pd.notna(avg_price_1) else "–", f"Mean price{type_sub}"),
        comp_kpi(f"{region2} avg price", f"${avg_price_2:.2f}" if pd.notna(avg_price_2) else "–", f"Mean price{type_sub}"),
        comp_kpi("Price difference", format_change_kpi(price_diff, is_currency=True), f"{region1} vs {region2}"),
        comp_kpi(f"{region1} total volume", format_number(vol_1) if pd.notna(vol_1) else "–", f"Total units{type_sub}"),
        comp_kpi(f"{region2} total volume", format_number(vol_2) if pd.notna(vol_2) else "–", f"Total units{type_sub}"),
        comp_kpi("Volume difference", format_change_kpi(vol_diff, is_currency=False), f"{region1} vs {region2}"),
    ]

    return fig_price, fig_volume, kpis


@app.callback(
    Output("comp-selected-week", "data"),
    [
        Input("comp-price-chart", "clickData"),
        Input("comp-volume-chart", "clickData"),
    ],
    prevent_initial_call=True,
)
def store_comp_selected_week(price_click, vol_click):
    try:
        trig_id = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else None
    except Exception:
        trig_id = None
    click_data = price_click if trig_id == "comp-price-chart" else (vol_click if trig_id == "comp-volume-chart" else (price_click or vol_click))
    if not click_data or not click_data.get("points"):
        return None
    point = click_data["points"][0]
    clicked_raw = point.get("x")
    if not clicked_raw:
        return None
    return str(clicked_raw)[:10]


@app.callback(
    Output("comp-drilldown-container", "children"),
    [
        Input("comp-selected-week", "data"),
        Input("comp-region-1", "value"),
        Input("comp-region-2", "value"),
        Input("comp-type", "value"),
        Input("comp-date-range", "start_date"),
        Input("comp-date-range", "end_date"),
    ],
)
def update_comp_drilldown(selected_week, region1, region2, comp_type, start_date, end_date):
    if not region1 or not region2:
        return html.Div()

    if not selected_week:
        return html.Div(
            style={
                "backgroundColor": COLORS["card"],
                "border": f"1px dashed {COLORS['border']}",
                "borderRadius": "16px",
                "padding": "24px 28px",
                "textAlign": "center",
                "marginTop": "24px",
            },
            children=[
                html.Div("👆", style={"fontSize": "26px", "marginBottom": "6px"}),
                html.Div(
                    "Interactive Head-to-Head Weekly Drilldown",
                    style={"color": COLORS["accent"], "fontWeight": "700", "fontSize": "16px", "marginBottom": "4px"},
                ),
                html.Div(
                    f"Click any point on the price or volume charts above to view a direct side-by-side bar comparison between {region1} and {region2} for that specific week.",
                    style={"color": COLORS["muted"], "fontSize": "13px"},
                ),
            ],
        )

    date_str = str(selected_week)[:10]
    try:
        target_date = pd.to_datetime(date_str)
    except Exception:
        return html.Div()

    if (start_date and target_date < pd.to_datetime(start_date)) or (end_date and target_date > pd.to_datetime(end_date)):
        return html.Div(
            style={
                "backgroundColor": COLORS["card"],
                "border": f"1px dashed {COLORS['border']}",
                "borderRadius": "16px",
                "padding": "24px 28px",
                "textAlign": "center",
                "marginTop": "24px",
            },
            children=[
                html.Div("📅", style={"fontSize": "26px", "marginBottom": "6px"}),
                html.Div(
                    f"Selected week ({date_str}) is outside current date filters",
                    style={"color": COLORS["accent"], "fontWeight": "700", "fontSize": "16px", "marginBottom": "4px"},
                ),
                html.Div(
                    "Widen your date filter range or click a data point on the chart above to inspect a new week.",
                    style={"color": COLORS["muted"], "fontSize": "13px"},
                ),
            ],
        )

    date_formatted = target_date.strftime("%B %d, %Y")

    mask = (df["date"] == target_date) & (df["region"].isin([region1, region2]))
    if comp_type and comp_type != "all":
        mask &= (df["type"] == comp_type)
        type_str = comp_type.title()
    else:
        type_str = "All Types Combined"

    week_sub = df[mask]
    if week_sub.empty:
        return html.Div(
            style={"padding": "20px", "textAlign": "center", "color": COLORS["muted"]},
            children=f"No matching records for week of {date_str} with current filter selection.",
        )

    agg = week_sub.groupby("region").agg(
        avg_price=("average_price", "mean"),
        total_volume=("total_volume", "sum"),
    ).reset_index()

    r1_data = agg[agg["region"] == region1]
    r2_data = agg[agg["region"] == region2]

    p1 = r1_data["avg_price"].iloc[0] if not r1_data.empty else 0
    p2 = r2_data["avg_price"].iloc[0] if not r2_data.empty else 0
    v1 = r1_data["total_volume"].iloc[0] if not r1_data.empty else 0
    v2 = r2_data["total_volume"].iloc[0] if not r2_data.empty else 0

    p_diff = p1 - p2
    v_diff = v1 - v2

    # Head-to-head bar for price
    fig_bar_price = px.bar(
        agg,
        x="region",
        y="avg_price",
        text=agg["avg_price"].map(lambda p: f"${p:.2f}"),
        color="region",
        color_discrete_sequence=[AVOCADO_COLORS[0], AVOCADO_COLORS[1]],
        labels={"avg_price": "Average Price", "region": "Region"},
    )
    fig_bar_price.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#0E0E0E", size=13, family="'Quicksand', sans-serif"),
        marker=dict(line=dict(width=1, color="#121212")),
        hovertemplate="<b>%{x}</b>: $%{y:.2f}<extra></extra>",
    )
    apply_fig_theme(fig_bar_price, title=f"Average Price: {region1} vs {region2}")
    fig_bar_price.update_layout(height=320, showlegend=False, xaxis_title="", yaxis_title="")

    # Head-to-head bar for volume
    fig_bar_vol = px.bar(
        agg,
        x="region",
        y="total_volume",
        text=agg["total_volume"].map(format_number),
        color="region",
        color_discrete_sequence=[AVOCADO_COLORS[0], AVOCADO_COLORS[1]],
        labels={"total_volume": "Total Volume", "region": "Region"},
    )
    fig_bar_vol.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#0E0E0E", size=13, family="'Quicksand', sans-serif"),
        marker=dict(line=dict(width=1, color="#121212")),
        hovertemplate="<b>%{x}</b>: %{y:,.0f} units (%{text})<extra></extra>",
    )
    apply_fig_theme(fig_bar_vol, title=f"Total Volume: {region1} vs {region2}")
    fig_bar_vol.update_layout(height=320, showlegend=False, xaxis_title="", yaxis_title="")

    return html.Div(
        style={
            "backgroundColor": COLORS["card"],
            "borderRadius": "18px",
            "border": f"1px solid {COLORS['accent']}",
            "padding": "24px",
            "marginTop": "24px",
            "boxShadow": "0 8px 30px rgba(0,0,0,0.35)",
        },
        children=[
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "flexWrap": "wrap",
                    "gap": "12px",
                    "marginBottom": "16px",
                    "borderBottom": f"1px solid {COLORS['border']}",
                    "paddingBottom": "12px",
                },
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "8px"},
                        children=[
                            html.Span("⚔️", style={"fontSize": "20px"}),
                            html.H3(
                                f"Head-to-Head Weekly Breakdown ({type_str})",
                                style={"color": COLORS["accent"], "margin": 0, "fontWeight": "800", "fontSize": "18px"},
                            ),
                            html.Span(f"● Week of {date_formatted}", className="status-badge", style={"fontSize": "11px", "padding": "3px 10px"}),
                        ],
                    ),
                    html.Span("Click any other date on the charts above to switch weeks", style={"color": COLORS["muted"], "fontSize": "11.5px", "fontStyle": "italic"}),
                ],
            ),
            html.Div(
                style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "20px"},
                children=[
                    html.Div(
                        style={"backgroundColor": "rgba(255,255,255,0.03)", "border": f"1px solid {COLORS['border']}", "borderRadius": "12px", "padding": "10px 16px", "flex": "1 1 180px"},
                        children=[
                            html.Div("PRICE SPREAD (REG 1 − REG 2)", style={"color": COLORS["muted"], "fontSize": "10px", "fontWeight": "700"}),
                            html.Div(f"{'+' if p_diff > 0 else ''}${p_diff:.2f}", style={"color": COLORS["accent"] if p_diff >= 0 else "#FF6B6B", "fontSize": "18px", "fontWeight": "700", "marginTop": "2px"}),
                        ],
                    ),
                    html.Div(
                        style={"backgroundColor": "rgba(255,255,255,0.03)", "border": f"1px solid {COLORS['border']}", "borderRadius": "12px", "padding": "10px 16px", "flex": "1 1 180px"},
                        children=[
                            html.Div("VOLUME SPREAD (REG 1 − REG 2)", style={"color": COLORS["muted"], "fontSize": "10px", "fontWeight": "700"}),
                            html.Div(f"{'+' if v_diff > 0 else ''}{format_number(v_diff)} units", style={"color": COLORS["accent"] if v_diff >= 0 else "#FF6B6B", "fontSize": "18px", "fontWeight": "700", "marginTop": "2px"}),
                        ],
                    ),
                ],
            ),
            html.Div(
                style={"display": "flex", "flexWrap": "wrap", "gap": "20px"},
                children=[
                    html.Div(
                        style={"flex": "1 1 420px"},
                        children=[
                            drilldown_badge(f"● Week of {date_formatted}"),
                            dcc.Graph(figure=fig_bar_price, config={"displayModeBar": False}),
                        ],
                    ),
                    html.Div(
                        style={"flex": "1 1 420px"},
                        children=[
                            drilldown_badge(f"● Week of {date_formatted}"),
                            dcc.Graph(figure=fig_bar_vol, config={"displayModeBar": False}),
                        ],
                    ),
                ],
            ),
        ],
    )


@app.callback(
    Output("data-table-container", "children"),
    [
        Input("data-region", "value"),
        Input("data-type", "value"),
        Input("data-date-range", "start_date"),
        Input("data-date-range", "end_date"),
    ],
)
def update_data_table(regions, data_type, start_date, end_date):
    mask = pd.Series(True, index=df.index)
    if start_date is not None:
        mask &= (df["date"] >= pd.to_datetime(start_date))
    if end_date is not None:
        mask &= (df["date"] <= pd.to_datetime(end_date))
    if regions:
        mask &= df["region"].isin(regions)
    if data_type:
        mask &= (df["type"] == data_type)

    dff = df[mask]
    if dff.empty:
        return html.Div(
            "No data matching selected filters.",
            style={"color": COLORS["muted"], "padding": "16px", "textAlign": "center"},
        )

    total_records = len(dff)
    display_limit = 150
    dff_display = dff.sort_values("date", ascending=False).head(display_limit).copy()
    dff_display["date"] = dff_display["date"].dt.strftime("%Y-%m-%d")
    dff_display["average_price"] = dff_display["average_price"].map(lambda p: f"${p:.2f}")
    dff_display["total_volume"] = dff_display["total_volume"].map(lambda v: f"{v:,.0f}")

    table = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=[f"<b>{col.replace('_', ' ').title()}</b>" for col in dff_display.columns],
                    fill_color=COLORS["navbar"],
                    font=dict(color=COLORS["text"], size=12, family="'Quicksand', sans-serif"),
                    height=36,
                    align="left",
                ),
                cells=dict(
                    values=[dff_display[col] for col in dff_display.columns],
                    fill_color=COLORS["card"],
                    font=dict(color=COLORS["text"], size=11.5, family="'Quicksand', sans-serif"),
                    height=28,
                    align="left",
                ),
            )
        ]
    )
    table.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=COLORS["card"],
        plot_bgcolor=COLORS["card"],
    )

    info_banner = html.Div(
        f"Displaying latest {min(total_records, display_limit):,} of {total_records:,} matching records. (Filters above refine this view)",
        style={
            "color": COLORS["muted"],
            "fontSize": "12.5px",
            "marginBottom": "10px",
            "fontStyle": "italic",
        },
    )

    return html.Div([info_banner, dcc.Graph(figure=table, style={"height": "480px"})])


@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download-csv", "n_clicks"),
    [
        State("data-region", "value"),
        State("data-type", "value"),
        State("data-date-range", "start_date"),
        State("data-date-range", "end_date"),
    ],
    prevent_initial_call=True,
)
def download_csv(n_clicks, regions, data_type, start_date, end_date):
    mask = pd.Series(True, index=df.index)
    if start_date is not None:
        mask &= (df["date"] >= pd.to_datetime(start_date))
    if end_date is not None:
        mask &= (df["date"] <= pd.to_datetime(end_date))
    if regions:
        mask &= df["region"].isin(regions)
    if data_type:
        mask &= (df["type"] == data_type)
    dff = df[mask].sort_values("date")
    return dcc.send_data_frame(dff.to_csv, "avocado_filtered_data.csv", index=False)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("RENDER") is None
    app.run(host="0.0.0.0", port=port, debug=debug)
