# %%  INSTAL PACKAGES
import yfinance as yf
import seaborn as sns
import numpy as np
import pandas as pd

from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt.efficient_frontier import objective_functions
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices


# %% ASSETS
tickers = [ "QQQ", # NASDAQ 100 index
            "IDU", # DOW JONES UTILITIES AVERAGE
            "SDG",  # GLOBAL IMPACT (TESLA, etc)
            "MNA", # IQ MERGER ARBITRAGE ETF
            "SGOL", # GOLD SPOT PRICE
            "CQQQ", # CHINA TECHNOLOGY
            "EWJ", # SOUTH KOREA TECHNOLOGY
            "EWY" ] # JAPAN (TOYOTA, SONY, SOFTBANK, etc)
N = len(tickers)

asset_list=[]
for tick in tickers:
    asset_list.append(yf.Ticker(tick))

# %% BENCHMARK
bm_ticker = "VOO" #S&P500
bmark = yf.Ticker(bm_ticker)

start_date =  "2020-04-01"  # date to start optimization
ptf_date =  "2020-10-29"    # day after the closure
report1_date = "2020-11-12" # day after the closure
report2_date = "2020-11-26" # day after the closre

# Assets
close_data = pd.DataFrame() # Closing Price 
vol_data = pd.DataFrame()  # Volume
for i in range(0,N):
    right = asset_list[i].history(start=start_date, end = report1_date )
    right_close = pd.DataFrame({tickers[i]: right['Close']})
    right_vol = pd.DataFrame({tickers[i]: right['Volume']})
    if (close_data.empty):
        close_data = right_close
        vol_data = right_vol
    else:
        close_data = pd.merge(close_data, right_close, how ='outer', on="Date")
        vol_data = pd.merge(vol_data, right_vol, how ='outer', on="Date")
print("Assets #NaN:\n",close_data.isnull().sum(),"\n") #NaN check

# Benchmark
bm_close = pd.DataFrame({ bm_ticker : bmark.history(start=start_date, end = report1_date)['Close']}) # Closing Price
print("Benchmark1 #NaN:\n", bm_close.isnull().sum(),"\n") #NaN check

# bm_close.to_csv("bm_nov12.csv")
# close_data.to_csv("data_nov12.csv")

print(close_data)

# %% TODAY
sdate = '2020-10-28' 

ctrans = 100.3/100 # Transaction costs 
extraLiquidity = 0.1/100 # Extra liquidity which should not be invested

# %% USD EUR EXCHANGE

usd_eur = yf.Ticker("EUR=X")
USD_EUR_RATE = usd_eur.history(start=sdate)["Close"].loc[sdate] * ctrans
cash = 5e6
cash_USD = cash/ USD_EUR_RATE
start_ptf = cash*(1-extraLiquidity)/ USD_EUR_RATE

# usd_eur.history(start=start_date, end = report1_date)["Close"].to_csv("eur_x.csv")

# %% PORTFOLIO OPTIMIZATION (INFORMATION RATIO)
#Assets return:
a_return = close_data.pct_change().dropna(how="all")
#Benchmark return: 
bm_return = bm_close.pct_change().dropna(how="all")
#Adjusted return:
adj_return = a_return.subtract(bm_return.to_numpy())

#Expected adjusted return
mu = expected_returns.mean_historical_return(adj_return, returns_data=True)
#Sample Variance
Sigma = risk_models.sample_cov(adj_return, returns_data=True)

# %% PTF OPT

from pypfopt import CLA, plotting

cla = CLA(mu, Sigma, weight_bounds=(0.03,1))
cla.max_sharpe()
cla.portfolio_performance(verbose=True)

ax = plotting.plot_efficient_frontier(cla, showfig=True, show_assets=True)

sharpe_pwt=cla.clean_weights()
sharpe_pwt

# %% 
#Print Portfolio Performances
cla.portfolio_performance(verbose=True)

#Post-processing weights
#latest_prices = get_latest_prices(close_data) #latest closing price
latest_prices = close_data.loc[sdate] #2020-10-28 closing price
da = DiscreteAllocation(sharpe_pwt, latest_prices*ctrans, total_portfolio_value=start_ptf)
allocation, leftover = da.lp_portfolio()