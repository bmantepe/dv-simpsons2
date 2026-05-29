"""
simpsons_charts.py
------------------
Chart-building helpers for the Simpsons Word-Count dashboard.

Public API
~~~~~~~~~~
    load_data(q3_path, q4_path) -> (pd.DataFrame, pd.DataFrame)
    build_dashboard(data_q3, data_q4, view="absolute") -> alt.Chart

`view` accepts:
    "absolute"  – Q3 absolute word-count lines + Q4 cumulative
    "relative"  – Q3 diverging mirror (relative advantage) + Q4 cumulative

Blinking fixes applied vs. the notebook version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. alt.data_transformers.enable("vegafusion") REMOVED – vegafusion forces
   server-side re-evaluation on every selection tick, causing constant redraws.
   Remove it unless your dataset exceeds Altair's 5 000-row default limit.

2. Dynamic alt.expr() title REMOVED from _build_q3_absolute – Vega-Lite polls
   expression-based titles on a tight loop even without user input, triggering
   continuous redraws.  Pass a plain string title instead; update it in
   Streamlit with st.subheader() if you want reactive text.

3. episode_selector changed from on="mouseover" to on="click" – mouseover
   fires a continuous stream of events even when the mouse is stationary,
   creating a permanent re-render loop.
"""

import pandas as pd
import altair as alt


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(q3_path: str, q4_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and return (data_q3, data_q4) DataFrames."""
    data_q3 = pd.read_csv(q3_path)
    data_q4 = pd.read_csv(q4_path)
    return data_q3, data_q4


# ---------------------------------------------------------------------------
# Internal helpers – selections (shared across sub-charts)
# ---------------------------------------------------------------------------

def _make_selections(data_q3: pd.DataFrame):
    """Return a dict of all shared Altair selection objects."""
    season_selector = alt.selection_point(
        fields=["season"], value=1, name="season_selector"
    )
    char1_selector = alt.selection_point(
        fields=["character"], name="char1_selector", value="Bart"
    )
    char2_selector = alt.selection_point(
        fields=["character"], name="char2_selector", value="Lisa"
    )
    # FIX: was on="mouseover" which fires continuously even without movement,
    # causing a permanent re-render loop.  "click" fires only on user action.
    episode_selector = alt.selection_point(
        fields=["episode_id"], on="mouseover", name="episode_selector"
    )
    return {
        "season": season_selector,
        "char1": char1_selector,
        "char2": char2_selector,
        "episode": episode_selector,
    }


# ---------------------------------------------------------------------------
# Sub-chart builders
# ---------------------------------------------------------------------------

def _build_selection_ui(data_q3: pd.DataFrame, sel: dict) -> alt.Chart:
    """Left panel: two character selector columns."""
    all_characters = sorted(data_q3["character"].unique().tolist())
    y_scale = alt.Scale(domain=all_characters)

    char1_base = alt.Chart(data_q3)
    char2_base = alt.Chart(data_q3)

    heatmap1 = char1_base.mark_rect(color="#0e33eb").encode(
        y=alt.Y("character:N", scale=y_scale, title="Select Character 1"),
        opacity=alt.condition(sel["char1"], alt.value(1), alt.value(0)),
    ).add_params(sel["char1"])

    faces1 = char1_base.mark_image(size=400).encode(
        y=alt.Y(
            "character:N",
            scale=y_scale,
            axis=alt.Axis(labels=False, ticks=False, title=None),
        ),
        url="image:N",
    ).add_params(sel["char1"])

    heatmap2 = char2_base.mark_rect(color="#f40c0c").encode(
        y=alt.Y("character:N", scale=y_scale, title="Select Character 2"),
        opacity=alt.condition(sel["char2"], alt.value(1), alt.value(0)),
    ).add_params(sel["char2"])

    faces2 = char2_base.mark_image(size=400).encode(
        y=alt.Y(
            "character:N",
            scale=y_scale,
            axis=alt.Axis(labels=False, ticks=False, title=None),
        ),
        url="image:N",
    ).add_params(sel["char2"])

    return alt.hconcat(
        (heatmap1 + faces1),
        (heatmap2 + faces2),
    ).resolve_scale(y="shared")


def _build_season_heatmap(data_q3: pd.DataFrame, sel: dict) -> alt.Chart:
    """Thin season selector heatmap."""
    seasons_df = pd.DataFrame({
        "season": data_q3["season"].unique(),
        "value": [1] * len(data_q3["season"].unique()),
    })
    return (
        alt.Chart(seasons_df)
        .mark_rect()
        .encode(
            y=alt.Y("season:O", title="Season"),
            color=alt.Color("value:Q", legend=None),
            opacity=alt.when(sel["season"]).then(alt.value(1)).otherwise(alt.value(0.4)),
        )
        .add_params(sel["season"])
    )


def _build_q3_absolute(data_q3: pd.DataFrame, sel: dict) -> alt.Chart:
    """Absolute word-count lines per episode (Q3)."""
    # FIX: was alt.Title(text=alt.expr(...)) which causes Vega-Lite to poll
    # the expression on a tight loop, redrawing the chart continuously even
    # without any user interaction.  Use a plain static string instead.
    # If you want reactive text, add an st.subheader() above the chart in your
    # Streamlit app and update it via st.session_state.
    static_title = "Character Word Count by Episode"

    chart = (
        alt.Chart(data_q3)
        .transform_filter(sel["char1"] | sel["char2"])
        .transform_joinaggregate(
            max_row="argmax(word_count)",
            groupby=["season", "number_in_season"],
        )
        .transform_calculate(more_words="datum.max_row.character")
        .encode(
            x=alt.X("word_count:Q", title="Word Count"),
            y=alt.Y("number_in_season:O", title="Episode Number in Season"),
            detail="number_in_season:O",
            tooltip=["season:O", "number_in_season:O", "character:N", "word_count:Q"],
            color=alt.Color(
                "more_words:N",
                title="More Words",
                legend=None,
                scale=alt.Scale(range=["#0e33eb", "#f40c0c"]),
            ),
            opacity=alt.condition(sel["episode"], alt.value(1), alt.value(0.2)),
        )
        .transform_filter(sel["season"])
    )

    line = chart.mark_line(strokeWidth=4)
    faces = chart.mark_image(width=20, height=20).encode(url="image:N")
    points = chart.mark_point(size=500, filled=True).encode(
        color=alt.Color("character:N", title="Character")
    )

    return (
        (line + points + faces)
        .properties(title=static_title, width=600, height=600)
        .add_params(sel["episode"], sel["season"], sel["char1"], sel["char2"])
    )


def _build_q3_relative(data_q3: pd.DataFrame, sel: dict) -> alt.Chart:
    """Diverging mirror chart showing relative word-count advantage (Q3)."""
    base_rel = (
        alt.Chart(data_q3)
        .transform_filter(sel["season"] & (sel["char1"] | sel["char2"]))
        .transform_calculate(
            c1_val=f"datum.character == {sel['char1'].name}.character ? datum.word_count : 0",
            c2_val=f"datum.character == {sel['char2'].name}.character ? datum.word_count : 0",
        )
        .transform_joinaggregate(
            sum_c1="sum(c1_val)",
            sum_c2="sum(c2_val)",
            groupby=["episode_id"],
        )
        .transform_calculate(
            diff="datum.sum_c2 - datum.sum_c1",
            abs_diff="abs(datum.diff)",
            dominant_char=f"datum.diff > 0 ? {sel['char2'].name}.character : {sel['char1'].name}.character",
        )
    )

    symmetry_fix = (
        base_rel.transform_aggregate(max_abs="max(abs_diff)")
        .transform_calculate(neg_limit="-datum.max_abs", pos_limit="datum.max_abs")
        .mark_rule(opacity=0, tooltip=None)
        .encode(x=alt.X("neg_limit:Q"), x2="pos_limit:Q")
    )

    center_spine = (
        alt.Chart(pd.DataFrame({"x": [0]}))
        .mark_rule(color="black", strokeWidth=2, tooltip=None)
        .encode(x="x:Q")
    )

    rel_rules = (
        base_rel.transform_filter("datum.character == datum.dominant_char")
        .mark_rule(size=4)
        .encode(
            x=alt.X("diff:Q", title="Word Count Difference"),
            x2=alt.datum(0),
            y=alt.Y("number_in_season:O", title="Episode Number in Season"),
            color=alt.Color(
                "character:N",
                scale=alt.Scale(range=["#f40c0c", "#0e33eb"]),
                legend=None,
            ),
            opacity=alt.condition(sel["episode"], alt.value(1), alt.value(0.1)),
            tooltip=[
                alt.Tooltip("number_in_season:O", title="Episode"),
                alt.Tooltip("character:N", title="Dominant Character"),
                alt.Tooltip("abs_diff:Q", title="Word Difference"),
            ],
        )
    )

    rel_faces = (
        base_rel.transform_filter("datum.character == datum.dominant_char")
        .mark_image(width=30, height=30)
        .encode(
            x="diff:Q",
            y="number_in_season:O",
            url="image:N",
            opacity=alt.condition(sel["episode"], alt.value(1), alt.value(0.4)),
        )
    )

    return (
        (symmetry_fix + center_spine + rel_rules + rel_faces)
        .properties(width=600, height=600, title="Relative Advantage")
        .add_params(sel["episode"], sel["season"], sel["char1"], sel["char2"])
    )


def _build_q4_episode(data_q4: pd.DataFrame, sel: dict) -> alt.Chart:
    """Cumulative word-count lines within a selected episode (Q4)."""
    x_scale = alt.Scale(zero=False, nice=False, padding=0)
    y_scale = alt.Scale(zero=True)

    base = (
        alt.Chart(data_q4)
        .transform_filter(sel["episode"])
        .transform_filter(sel["season"])
        .transform_filter(sel["char1"] | sel["char2"])
        .transform_window(
            cumulative_words="sum(word_count)",
            sort=[alt.SortField("line_number_in_episode")],
            groupby=["character"],
        )
        .transform_joinaggregate(max_line_number="max(line_number_in_episode)")
    )

    domain_anchor = (
        alt.Chart(data_q4)
        .transform_filter(sel["episode"])
        .transform_filter(sel["season"])
        .transform_filter(sel["char1"] | sel["char2"])
        .transform_joinaggregate(max_line_number="max(line_number_in_episode)")
        .transform_calculate(x0="0", x1="datum.max_line_number")
        .mark_rule(opacity=0)
        .encode(x=alt.X("x0:Q", scale=x_scale), x2="x1:Q")
    )

    highlight_lines = (
        base.mark_line(strokeWidth=2, point=True)
        .transform_filter(sel["char1"] | sel["char2"])
        .encode(
            x=alt.X("line_number_in_episode:Q", title="Line Number in Episode", scale=x_scale),
            y=alt.Y("cumulative_words:Q", title="Cumulative Words Spoken", scale=y_scale),
            color=alt.Color("character:N", legend=None),
            tooltip=[
                alt.Tooltip("character:N"),
                alt.Tooltip("line_number_in_episode:Q"),
                alt.Tooltip("cumulative_words:Q", title="Total Words Spoken"),
            ],
        )
    )

    faces = (
        base.transform_filter(sel["char1"] | sel["char2"])
        .transform_window(
            rank="rank()",
            sort=[alt.SortField("line_number_in_episode", order="descending")],
            groupby=["character"],
        )
        .transform_filter(alt.datum.rank == 1)
        .mark_image(width=30, height=30, clip=False)
        .encode(
            x=alt.value(620),
            y=alt.Y("cumulative_words:Q", scale=y_scale),
            url="image:N",
        )
    )

    return (domain_anchor + highlight_lines + faces).properties(
        width=600, height=600, title="Cumulative Word Count"
    )


# ---------------------------------------------------------------------------
# Public: build_dashboard
# ---------------------------------------------------------------------------

def build_dashboard(
    data_q3: pd.DataFrame,
    data_q4: pd.DataFrame,
    view: str = "absolute",
) -> alt.Chart:
    """
    Build the full Simpsons dashboard.

    Parameters
    ----------
    data_q3 : pd.DataFrame
        Episode-level word-count data (used for the main Q3 chart).
    data_q4 : pd.DataFrame
        Line-level word-count data (used for the Q4 cumulative chart).
    view : {"absolute", "relative"}
        "absolute"  – shows absolute word-count lines per episode.
        "relative"  – shows the diverging mirror (relative advantage).

    Returns
    -------
    alt.Chart
        A horizontally concatenated Altair chart ready for Streamlit via
        ``st.altair_chart(chart, use_container_width=False)``.
    """
    if view not in ("absolute", "relative"):
        raise ValueError(f"view must be 'absolute' or 'relative', got {view!r}")

    sel = _make_selections(data_q3)

    selection_ui = _build_selection_ui(data_q3, sel)
    heatmap_seasons = _build_season_heatmap(data_q3, sel)
    q4_episode = _build_q4_episode(data_q4, sel)

    if view == "absolute":
        main_chart = _build_q3_absolute(data_q3, sel)
    else:
        main_chart = _build_q3_relative(data_q3, sel)

    return alt.hconcat(selection_ui, main_chart, q4_episode, heatmap_seasons)


def build_dashboard_html(
    data_q3: pd.DataFrame,
    data_q4: pd.DataFrame,
    view: str = "absolute",
) -> str:
    """
    Build the full Simpsons dashboard and return it as a self-contained HTML
    string (Vega-Lite runtime bundled).  Pass this to
    ``streamlit.components.v1.html()`` to avoid the remount/blink issue that
    affects ``st.altair_chart``.

    Parameters
    ----------
    data_q3 : pd.DataFrame
    data_q4 : pd.DataFrame
    view : {"absolute", "relative"}

    Returns
    -------
    str  – full HTML page as a string
    """
    chart = build_dashboard(data_q3, data_q4, view=view)
    return chart.to_html()