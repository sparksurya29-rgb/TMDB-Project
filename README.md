# Reel Insights: TMDB Movie Analytics

End-to-end exploratory analysis of the supplied TMDB relational CSV dataset using Pandas, SQLite, SQL, Matplotlib/Seaborn and a Streamlit dashboard.

## Project contents
- `notebooks/01_data_cleaning.ipynb` — source audit, cleaning rules, relational database load and join test.
- `notebooks/02_sql_analysis.ipynb` — all 10 SQL questions from the brief.
- `notebooks/03_pandas_analysis.ipynb` — all 10 Pandas questions from the brief.
- `notebooks/04_visualizations.ipynb` — univariate, bivariate and multivariate charts with written insights.
- `app.py` — three-page Streamlit app: Filters, Dashboard, Query Explorer.
- `data/raw/` — untouched copies of the six supplied CSV files.
- `data/` — cleaned CSV tables and `tmdb_movies.db` SQLite database.
- `sql_queries.json` — the ten saved SQL queries used in Query Explorer.

## Quick start
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the notebooks in Jupyter and run cells top-to-bottom. The notebooks expect `data/` to be available either from the project root or the `notebooks/` folder. The cleaning notebook reads the untouched CSVs from `data/raw/` and regenerates cleaned CSVs and the SQLite database.

## Cleaning decisions
- Exact duplicate rows are removed from each table.
- Orphaned movie references and invalid genre references are removed from bridge/credit/keyword tables.
- `release_date` is parsed as a date for analysis and stored as ISO `YYYY-MM-DD`.
- Budget and revenue zeros are preserved in the data/database because the project brief says they indicate unknown values. Financial analyses that require valid figures exclude zero or missing budget/revenue.
- The source bridge table `movie_genres.csv` does not provide an explicit genre-priority field. The Pandas notebook defines “primary genre” as the first association in source-file order and documents this limitation.
- ROI is `(revenue - budget) / budget`. It is a revenue-based proxy and excludes distribution, marketing, taxes, and other costs; it is not net profit.

## Top five findings from the supplied data
1. **Dataset size:** the source has 2,509 movie rows and 19 genre reference rows. Removing six exact duplicate movie rows leaves 2,503 movie records. The cleaned relational tables contain 6,878 movie-genre associations, 24,902 cast rows, 7,289 crew rows and 41,681 keyword rows after exact duplicate removal.
2. **Financial placeholders matter:** 90 cleaned movie records have zero budget and 102 have zero revenue. Treating these as genuine zeros would distort financial averages and ROI, so financial comparisons exclude them.
3. **Release-year concentration:** 2016 is the most represented release year in the cleaned sample, with 121 movies. This describes this supplied sample, not the entire global film industry.
4. **Revenue leaders:** the top reported revenues include *Avatar* ($2.924B), *Avengers: Endgame* ($2.799B), *Avatar: The Way of Water* ($2.334B), *Titanic* ($2.264B), and *Star Wars: The Force Awakens* ($2.068B).
5. **Genre coverage and ratings:** Drama is the most represented genre (937 distinct movies), followed by Action (808) and Comedy (762). Drama’s average vote rating is about 7.25 in this sample; genre averages overlap because a movie can have multiple genres.

## Recommendations
- Keep a clear distinction between unknown financial values and actual zero-dollar values.
- Use vote counts as context for ratings; a high average based on a small audience may be less stable.
- Use inflation-adjusted revenue and a broader release sample before making cross-decade greenlight or acquisition decisions.
- Interpret actor/director summaries as descriptive associations, not evidence of causal contribution to success.
- Refresh the dataset periodically before using the dashboard for operational decisions.

## Data caveats
The supplied files contain a curated sample, not necessarily all TMDB movies. Reported revenue/budget may be incomplete, financial amounts are not inflation-adjusted, popularity is a platform metric, and genre-level results count multi-genre films in each associated genre. All insights are descriptive rather than causal.

## Open and run in Visual Studio Code

1. Extract the project ZIP file to a folder.
2. Open Visual Studio Code and choose **File → Open Folder**, then select `Reel_Insights_TMDB_Project`.
3. Install the recommended extensions when prompted (Python, Pylance, and Jupyter).
4. Open **Terminal → New Terminal** and create a virtual environment:

   **Windows (PowerShell):**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   python -m streamlit run app.py
   ```

   **macOS / Linux:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   python -m streamlit run app.py
   ```

5. Open the local URL printed in the terminal (usually `http://localhost:8501`).
6. To run a notebook, open `notebooks/01_data_cleaning.ipynb` and select the `.venv` Python interpreter/kernel. Run the notebooks in numeric order.

For Windows, `run_app.bat` can also create the virtual environment, install dependencies, and launch the dashboard automatically. On macOS/Linux, run `./run_app.sh`.

The app uses the included SQLite database at `data/tmdb_movies.db`; keep that file and the `data/` folder in place relative to `app.py`.
