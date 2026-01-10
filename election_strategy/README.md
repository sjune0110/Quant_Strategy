# Election Strategy

This folder shows how to turn the ticker summaries from `electionnews` into trade ideas. The output of `electionnews` (candidate -> related stocks with sentiment) is the starting universe.

## Structure
- `data/`: `polldata.csv` and `events.csv` generated from `poll.ipynb`.
- `strategy/`: Notebooks `stock_portfolio.ipynb` and `Long_Straddle.ipynb` for portfolios/option setups.
- `poll.ipynb`: Builds the polling/election date datasets into `data/`.

## Inputs
- Run `python electionnews/run.py` in the `electionnews` project to refresh `data/summary.csv` (candidate-level positive/negative tickers).
- Copy or read that summary file here to feed the notebooks.

## Running the notebooks
1. Activate the shared env: `source ../pe-env/bin/activate`
2. From this folder, run `poll.ipynb` to regenerate `data/polldata.csv` and `data/events.csv`.
3. Open `strategy/stock_portfolio.ipynb` or `strategy/Long_Straddle.ipynb`. They read `data/polldata.csv` and expect `electionnews/data/summary.csv` for candidate/stock inputs.

Both notebooks assume the candidate-related stocks identified by `election_news` drive the portfolio weights or the option strikes you pick for the long straddle.
