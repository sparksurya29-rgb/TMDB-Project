from pathlib import Path
import base64
import json
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Reel Insights | TMDB", page_icon="🎬", layout="wide")
ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "tmdb_movies.db"
QUERIES_PATH = ROOT / "sql_queries.json"

# Original local SVG wallpaper: no internet connection is required.
WALLPAPER = r'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1000" viewBox="0 0 1600 1000">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#30206b"/><stop offset=".42" stop-color="#075b78"/><stop offset=".72" stop-color="#8a2b70"/><stop offset="1" stop-color="#e47738"/></linearGradient><radialGradient id="glow"><stop stop-color="#ffdc73" stop-opacity=".62"/><stop offset=".45" stop-color="#ff5f9e" stop-opacity=".28"/><stop offset="1" stop-color="#e8793e" stop-opacity="0"/></radialGradient></defs>
<rect width="1600" height="1000" fill="url(#bg)"/><circle cx="1250" cy="230" r="520" fill="url(#glow)"/><circle cx="180" cy="850" r="500" fill="#21d4c2" opacity=".42"/>
<g transform="rotate(-18 800 500)" opacity=".16" fill="none" stroke="#fff0a8" stroke-width="4"><rect x="-200" y="160" width="2100" height="180" rx="28"/><rect x="-200" y="660" width="2100" height="180" rx="28"/></g>
<g fill="#fff7d6" opacity=".24">''' + ''.join(f'<rect x="{x}" y="{y}" width="44" height="26" rx="5"/>' for y in (195,695) for x in range(0,1600,100)) + r'''</g>
<g fill="none" stroke="#c6f7ff" stroke-width="3" opacity=".24"><circle cx="1280" cy="690" r="220"/><circle cx="1280" cy="690" r="170"/><circle cx="1280" cy="690" r="120"/><circle cx="310" cy="300" r="140"/></g></svg>'''
wallpaper_uri = "data:image/svg+xml;base64," + base64.b64encode(WALLPAPER.encode("utf-8")).decode("ascii")
st.markdown(f"""
<style>
/* Keep the colourful wallpaper visible around the app, not over the content. */
.stApp {{
  background: url('{wallpaper_uri}') center / cover fixed;
  color: #20233a;
}}
[data-testid="stAppViewContainer"] {{ background: transparent; }}
[data-testid="stHeader"] {{ background: rgba(255,255,255,.86); }}
/* High-contrast, nearly opaque content surface improves readability. */
[data-testid="stMainBlockContainer"] {{
  background: rgba(255,255,255,.94);
  border: 1px solid rgba(255,255,255,.8);
  border-radius: 22px;
  padding: 1.5rem 2rem 2.5rem 2rem;
  margin-top: 1rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 12px 36px rgba(31, 20, 67, .20);
  color: #20233a;
}}
[data-testid="stSidebar"] {{
  background: linear-gradient(165deg, #38256f, #087f8c, #9c347c);
  border-right: 1px solid rgba(255,255,255,.4);
}}
[data-testid="stSidebar"] * {{ color: #ffffff; }}
[data-testid="stMetric"] {{
  background: linear-gradient(135deg, #fff0f5, #e6fbff);
  border: 1px solid #d7dff5; padding: 14px 16px; border-radius: 16px;
  box-shadow: 0 6px 18px rgba(37, 48, 90, .09);
}}
[data-testid="stMetric"] label, [data-testid="stMetric"] [data-testid="stMetricLabel"] {{ color: #41435f !important; }}
[data-testid="stMetricValue"], [data-testid="stMetricDelta"] {{ color: #25244b !important; }}
[data-testid="stVerticalBlockBorderWrapper"] {{
  background: rgba(255,255,255,.88); border: 1px solid #e1e5f0;
  border-radius: 16px;
}}
.stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
.stTabs [data-baseweb="tab"] {{
  background: linear-gradient(100deg, #ffe1ec, #d9f8f6);
  color: #292449; border: 1px solid #d9dff0; border-radius: 10px 10px 0 0; padding: 9px 15px;
}}
.stButton > button, [data-testid="stDownloadButton"] button {{
  background: linear-gradient(100deg, #e94f88, #7655dc, #079da8); color: white;
  border: 0; border-radius: 10px; font-weight: 650;
}}
.stButton > button:hover, [data-testid="stDownloadButton"] button:hover {{
  border: 1px solid #4d3d93; color: white; filter: brightness(1.08);
}}
[data-testid="stDataFrame"] {{ border: 1px solid #d9dfed; border-radius: 12px; overflow: hidden; }}
[data-baseweb="select"] > div, [data-baseweb="input"] > div {{ border-radius: 9px; }}
/* Force readable dark text on the light content surface. */
[data-testid="stMainBlockContainer"] h1,
[data-testid="stMainBlockContainer"] h2,
[data-testid="stMainBlockContainer"] h3,
[data-testid="stMainBlockContainer"] p,
[data-testid="stMainBlockContainer"] label,
[data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] {{ color: #25243f; }}
[data-testid="stMainBlockContainer"] h1,
[data-testid="stMainBlockContainer"] h2,
[data-testid="stMainBlockContainer"] h3 {{ text-shadow: none; }}
</style>
""", unsafe_allow_html=True)

if not DB.exists():
    st.error(f"Database not found: {DB}. Make sure data/tmdb_movies.db is inside the project folder.")
    st.stop()
if not QUERIES_PATH.exists():
    st.error(f"SQL query file not found: {QUERIES_PATH}")
    st.stop()
QUERIES = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))

@st.cache_data(show_spinner="Loading TMDB data…")
def load_table(table_name: str) -> pd.DataFrame:
    allowed = {"movies", "genres", "movie_genres", "cast", "crew", "movie_keywords"}
    if table_name not in allowed:
        raise ValueError("Unknown database table")
    with sqlite3.connect(DB) as conn:
        return pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)

movies = load_table("movies")
genres = load_table("genres")
movie_genres_raw = load_table("movie_genres")
cast = load_table("cast")
crew = load_table("crew")
keywords = load_table("movie_keywords")
movies["release_date"] = pd.to_datetime(movies["release_date"], errors="coerce")
movies["release_year"] = movies["release_date"].dt.year
movies["release_decade"] = (movies["release_year"] // 10 * 10).astype("Int64")
movie_genres = movie_genres_raw.merge(genres, on="genre_id", how="left")

valid_years = movies["release_year"].dropna()
yr_min = int(valid_years.min()) if not valid_years.empty else 1900
yr_max = int(valid_years.max()) if not valid_years.empty else 2030

# Persistent shared filters
st.session_state.setdefault("selected_genres", [])
st.session_state.setdefault("year_range", (yr_min, yr_max))
st.session_state.setdefault("min_rating", 0.0)
st.session_state.setdefault("selected_language", "All")

st.title("🎬 Reel Insights")
st.caption("TMDB movie analytics · SQL · Pandas · 10 interactive visualizations")

with st.sidebar:
    st.markdown("## 🎞️ TMDB Analysis")
    page = st.radio("Menu", ["Home", "Filters", "Dashboard", "Queries"], label_visibility="collapsed")
    st.divider()
    st.header("Global filters")
    genre_options = sorted(genres["genre_name"].dropna().astype(str).unique().tolist())
    st.multiselect("Genres (any selected)", genre_options, key="selected_genres")
    st.slider("Release year", min_value=yr_min, max_value=yr_max, key="year_range")
    st.slider("Minimum rating", min_value=0.0, max_value=10.0, step=0.1, key="min_rating")
    languages = ["All"] + sorted(movies["original_language"].dropna().astype(str).unique().tolist())
    st.selectbox("Original language", languages, key="selected_language"), 
    st.divider()
    st.caption("Filters apply to the Dashboard and Queries pages.")

filtered = movies.copy()
if st.session_state.selected_genres:
    eligible_ids = movie_genres.loc[movie_genres.genre_name.isin(st.session_state.selected_genres), "movie_id"].unique()
    filtered = filtered[filtered.movie_id.isin(eligible_ids)]
filtered = filtered[
    filtered.release_year.between(st.session_state.year_range[0], st.session_state.year_range[1], inclusive="both")
    & (filtered.vote_average.fillna(0) >= st.session_state.min_rating)
]
if st.session_state.selected_language != "All":
    filtered = filtered[filtered.original_language == st.session_state.selected_language]
filtered_ids = set(filtered.movie_id.tolist())
filtered_genres = movie_genres[movie_genres.movie_id.isin(filtered_ids)].copy()
filtered_cast = cast[cast.movie_id.isin(filtered_ids)].copy()
filtered_keywords = keywords[keywords.movie_id.isin(filtered_ids)].copy()

if page == "Home":
    st.header("Welcome to Reel Insights")
    st.write("Explore movie performance, audience ratings, genre trends, cast credits, and keyword patterns. Use the sidebar filters to refine your analysis.")
    a, b, c, d = st.columns(4)
    a.metric("Movies in dataset", f"{movies.movie_id.nunique():,}")
    b.metric("Genres", f"{genres.genre_name.nunique():,}")
    c.metric("Cast credits", f"{len(cast):,}")
    d.metric("Mean rating", f"{movies.vote_average.mean():.2f}/10")
    st.subheader("Explore the application")
    st.markdown("- **Filters:** choose genre, release years, minimum rating and language.\n- **Dashboard:** explore 10 visualizations based on your selected filters.\n- **Queries:** run any of the 10 project SQL questions and inspect the result dataframe and chart.")
    st.info("Financial figures reported as zero are treated as unknown placeholders and excluded from budget/revenue comparisons.")

elif page == "Filters":
    st.header("🎛️ Filters")
    st.write("Adjust the shared filters in the sidebar. Your selection is applied to Dashboard and Queries.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Matching movies", f"{len(filtered):,}")
    c2.metric("Year window", f"{st.session_state.year_range[0]}–{st.session_state.year_range[1]}")
    c3.metric("Minimum rating", f"{st.session_state.min_rating:.1f}/10")
    cols = ["title", "release_date", "original_language", "vote_average", "vote_count", "popularity", "budget", "revenue"]
    st.dataframe(filtered[cols].sort_values("popularity", ascending=False), use_container_width=True, hide_index=True)
    st.caption("Budget and revenue values of zero are retained as unknown placeholders; they are not interpreted as free movies.")

elif page == "Dashboard":
    st.header("📊 Dashboard — 10 Visualizations")
    st.caption(f"Showing {len(filtered):,} movies matching the current filters.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Movies", f"{filtered.movie_id.nunique():,}")
    c2.metric("Genres represented", f"{filtered_genres.genre_name.nunique():,}")
    c3.metric("Distinct actors", f"{filtered_cast.person_id.nunique():,}")
    c4.metric("Average rating", f"{filtered.vote_average.mean():.2f}/10" if not filtered.empty else "—")

    tab1, tab2, tab3 = st.tabs(["Commercial performance", "Audience & releases", "Genre & correlations"])
    with tab1:
        left, right = st.columns(2)
        with left:
            st.subheader("1. Top 10 movies by revenue")
            rev = filtered[filtered.revenue > 0].nlargest(10, "revenue").sort_values("revenue")
            if not rev.empty:
                st.plotly_chart(px.bar(rev, x="revenue", y="title", orientation="h", labels={"revenue":"Revenue (USD)","title":"Movie"}, title="Top grossing movies", hover_data=["release_year","vote_average"]), use_container_width=True)
            else: st.info("No positive revenue values match these filters.")
        with right:
            st.subheader("2. Genre distribution")
            gd = filtered_genres.groupby("genre_name").movie_id.nunique().reset_index(name="movies").sort_values("movies", ascending=False)
            if not gd.empty: st.plotly_chart(px.pie(gd, names="genre_name", values="movies", hole=.42, title="Movies by genre"), use_container_width=True)
            else: st.info("No genre associations for this selection.")
        st.subheader("3. Budget vs revenue")
        fin = filtered[(filtered.budget > 0) & (filtered.revenue > 0)].copy()
        if not fin.empty:
            st.plotly_chart(px.scatter(fin, x="budget", y="revenue", color="original_language", hover_name="title", size="vote_count", log_x=True, log_y=True, labels={"budget":"Budget (USD)","revenue":"Revenue (USD)","vote_count":"Votes"}, title="Reported budget compared with reported revenue"), use_container_width=True)
        else: st.info("No movies with positive budget and revenue match these filters.")
    with tab2:
        left, right = st.columns(2)
        with left:
            st.subheader("4. Runtime distribution")
            runtime = filtered.loc[filtered.runtime.between(1, 500), ["runtime"]]
            if not runtime.empty: st.plotly_chart(px.histogram(runtime, x="runtime", nbins=30, marginal="box", title="Movie runtime in minutes"), use_container_width=True)
            else: st.info("No valid runtime values in this selection.")
        with right:
            st.subheader("5. Rating distribution")
            ratings = filtered.loc[filtered.vote_average.between(0, 10), ["vote_average"]]
            if not ratings.empty: st.plotly_chart(px.histogram(ratings, x="vote_average", nbins=25, title="Audience rating distribution", labels={"vote_average":"Rating (0–10)"}), use_container_width=True)
            else: st.info("No ratings available for this selection.")
        st.subheader("6. Movie releases by year")
        yearly = filtered.dropna(subset=["release_year"]).groupby("release_year").movie_id.nunique().reset_index(name="movies")
        if not yearly.empty: st.plotly_chart(px.bar(yearly, x="release_year", y="movies", title="Number of movies released per year", labels={"release_year":"Release year","movies":"Movies"}), use_container_width=True)
        else: st.info("No release-year values in this selection.")
        st.subheader("7. Popularity vs vote count")
        popularity = filtered[(filtered.popularity >= 0) & (filtered.vote_count >= 0)]
        if not popularity.empty: st.plotly_chart(px.scatter(popularity, x="vote_count", y="popularity", color="vote_average", hover_name="title", log_x=True, title="Audience engagement and TMDB popularity", labels={"vote_count":"Vote count (log scale)","popularity":"Popularity score","vote_average":"Rating"}), use_container_width=True)
        else: st.info("No popularity/vote data in this selection.")
    with tab3:
        st.subheader("8. Average rating by genre")
        rating_genres = filtered_genres.merge(filtered[["movie_id", "vote_average"]], on="movie_id", how="inner")
        rating_genres = rating_genres.groupby("genre_name").agg(avg_rating=("vote_average", "mean"), movie_count=("movie_id", "nunique")).reset_index().sort_values("avg_rating", ascending=False)
        if not rating_genres.empty: st.plotly_chart(px.bar(rating_genres, x="genre_name", y="avg_rating", color="movie_count", title="Average rating by genre", labels={"genre_name":"Genre","avg_rating":"Average rating","movie_count":"Movies"}), use_container_width=True)
        else: st.info("No genre ratings available.")
        st.subheader("9. Genre revenue by release decade")
        genre_decade = filtered_genres.merge(filtered[["movie_id", "revenue", "release_decade"]], on="movie_id", how="inner")
        genre_decade = genre_decade[genre_decade.revenue > 0].groupby(["genre_name", "release_decade"]).revenue.mean().reset_index(name="avg_revenue")
        if not genre_decade.empty:
            genre_decade["release_decade"] = genre_decade["release_decade"].astype(str) + "s"
            st.plotly_chart(px.density_heatmap(genre_decade, x="release_decade", y="genre_name", z="avg_revenue", histfunc="avg", title="Average reported revenue by genre and decade", labels={"release_decade":"Release decade","genre_name":"Genre","avg_revenue":"Average revenue (USD)"}), use_container_width=True)
        else: st.info("No positive revenue values for the genre/decade heatmap.")

    if not filtered.empty:
        genre_revenue = filtered_genres.merge(filtered[["movie_id", "revenue"]], on="movie_id", how="inner")
        genre_revenue = genre_revenue[genre_revenue.revenue > 0].groupby("genre_name").revenue.mean().sort_values(ascending=False)
        if not genre_revenue.empty:
            st.success(f"Insight: **{genre_revenue.index[0]}** has the highest average reported revenue in this filtered selection (${genre_revenue.iloc[0]:,.0f}). Multi-genre movies contribute to each associated genre.")

else:  # Queries
    st.header("🧮 SQL Query Explorer")
    st.write("Select one of the 10 SQL questions. Each query displays its SQL, result dataframe, chart, and a brief interpretation.")
    query_names = [q["name"] for q in QUERIES]
    selected_query = st.selectbox("Choose a saved query", query_names)
    query_item = next(q for q in QUERIES if q["name"] == selected_query)
    with st.expander("View SQL statement"):
        st.code(query_item["sql"], language="sql")
    # Execute each query against a temporary, filtered copy of movie-linked tables.
    with sqlite3.connect(DB) as conn:
        ids = [int(x) for x in filtered.movie_id.tolist()]
        conn.execute("PRAGMA temp_store = MEMORY")
        for table in ("movies", "movie_genres", "cast", "crew", "movie_keywords"):
            if ids:
                placeholders = ",".join("?" for _ in ids)
                conn.execute(f'CREATE TEMP TABLE "{table}" AS SELECT * FROM main."{table}" WHERE movie_id IN ({placeholders})', ids)
            else:
                conn.execute(f'CREATE TEMP TABLE "{table}" AS SELECT * FROM main."{table}" WHERE 0')
        result = pd.read_sql_query(query_item["sql"], conn)
    st.subheader(f"Result dataframe · {len(result):,} row(s)")
    st.dataframe(result, use_container_width=True, hide_index=True)
    if not result.empty:
        st.download_button("Download query results as CSV", result.to_csv(index=False).encode("utf-8-sig"), file_name="reel_insights_query_results.csv", mime="text/csv")
        numeric_cols = result.select_dtypes(include="number").columns.tolist()
        non_numeric_cols = [c for c in result.columns if c not in numeric_cols]
        st.subheader("Query visualization")
        if numeric_cols:
            chart_x = st.selectbox("Chart category / X-axis", non_numeric_cols or result.columns.tolist(), key="query_chart_x")
            chart_y = st.selectbox("Chart value / Y-axis", numeric_cols, index=len(numeric_cols)-1, key="query_chart_y")
            chart_type = st.selectbox("Chart type", ["Bar", "Line", "Scatter", "Pie"], key="query_chart_type")
            chart_data = result.head(100).copy()
            if chart_type == "Bar": fig = px.bar(chart_data, x=chart_x, y=chart_y, title=selected_query)
            elif chart_type == "Line": fig = px.line(chart_data, x=chart_x, y=chart_y, markers=True, title=selected_query)
            elif chart_type == "Scatter": fig = px.scatter(chart_data, x=chart_x, y=chart_y, title=selected_query)
            else: fig = px.pie(chart_data.head(25), names=chart_x, values=chart_y, title=selected_query)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("This query has no numeric columns to chart. The dataframe above contains the full result.")
        st.info(f"Insight: the selected query returned {len(result):,} row(s). Interpret the chart alongside the full dataframe; some joins can legitimately produce multiple rows per movie or person.")
    else:
        st.info("No rows matched this query and the current filters. Try broadening the sidebar filters.")
