# Election Strategy

This folder shows how to turn the ticker summaries from `electionnews` into trade ideas. The output of `electionnews` (candidate -> related stocks with sentiment) is the starting universe.

## Approaches
- **Candidate-linked equity portfolio:** Build a basket of the top positive tickers for each candidate and rebalance as new summaries arrive. Allocation rules and backtests are in `stock_portfolio.ipynb`.
- **Long straddle around catalysts:** For names most closely tied to a candidate, buy a long straddle before key election events (debates, poll releases) to capture volatility regardless of direction. The setup template lives in `Long_Straddle.ipynb`.

## Inputs
- Run `python electionnews/run.py` in the `electionnews` project to refresh `data/summary.csv` (candidate-level positive/negative tickers).
- Copy or read that summary file here to feed the notebooks.

## Running the notebooks
1. Activate the shared env: `source ../pe-env/bin/activate`
2. Open `stock_portfolio.ipynb` or `Long_Straddle.ipynb` and point the data loader to the latest `data/summary.csv` from `election_news`.

Both notebooks assume the candidate-related stocks identified by `election_news` drive the portfolio weights or the option strikes you pick for the long straddle.
