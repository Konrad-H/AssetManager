# %%  INSTAL PACKAGES
import yfinance as yf
import seaborn as sns
import numpy as np
import pandas as pd

from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
from pypfopt import objective_functions
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

# BENCHMARK
bm_ticker = "VOO" #S&P500
bmark = yf.Ticker(bm_ticker)

# %% PRINT ASSET LIST
for i in range(0,N):
    print(asset_list[i].info["shortName"])
print(bmark.info["shortName"])
# %% COLLECTING ASSETS AND BENCHMARK HISTORICAL DATA

# Assets
close_data = pd.DataFrame() # Closing Price 
vol_data = pd.DataFrame()  # Volume
for i in range(0,N):
    right = asset_list[i].history(period="3y")
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
bm_close = pd.DataFrame({ bm_ticker : bmark.history(period="3y")['Close']}) # Closing Price
print("Benchmark1 #NaN:\n", bm_close.isnull().sum(),"\n") #NaN check

# %% TODAY
sdate = '2020-10-28' 

ctrans = 100.3/100 # Transaction costs 
extraLiquidity = 0.1/100 # Extra liquidity which should not be invested
# %% USD EUR EXCHANGE

usd_eur = yf.Ticker("EUR=X")
USD_EUR_RATE = usd_eur.history(period="2y")["Close"].loc[sdate] * ctrans
cash = 5e6
cash_USD = cash/ USD_EUR_RATE
start_ptf = cash*(1-extraLiquidity)/ USD_EUR_RATE

# %% PORTFOLIO OPTIMIZATION (INFORMATION RATIO)
#Assets return:
a_return = close_data['2018-10-28':sdate].pct_change().dropna(how="all")
#Benchmark return: 
bm_return = bm_close['2018-10-28':sdate].pct_change().dropna(how="all")
#Adjusted return:
adj_return = a_return.subtract(bm_return.to_numpy())

#Expected adjusted return
mu = expected_returns.mean_historical_return(adj_return, returns_data=True)
#Sample Variance
Sigma = risk_models.sample_cov(adj_return, returns_data=True)

#Max Sharpe Ratio - Tangent to the Efficient Frontier
ef = EfficientFrontier(mu, Sigma, weight_bounds=(0.01,1)) #weight bounds in negative allows shorting of stocks
#ef.add_objective(objective_functions.L2_reg, gamma=1)
sharpe_pfolio=ef.max_sharpe() #May use add objective to ensure minimum zero weighting to individual stocks
sharpe_pwt=ef.clean_weights()
#print(sharpe_pwt)
# print(np.array(list(sharpe_pwt.values())).sum()) #Check that weights sum to one

#Print Portfolio Performances
ef.portfolio_performance(verbose=True)

#Post-processing weights
#latest_prices = get_latest_prices(close_data) #latest closing price
latest_prices = close_data.loc[sdate] #2020-10-28 closing price
da = DiscreteAllocation(sharpe_pwt, latest_prices*ctrans, total_portfolio_value=start_ptf)
allocation, leftover = da.lp_portfolio()

# %% PORTFOLIO AND BENCHMARK COMPOSITION 
# Portfolio
ptf = pd.DataFrame( columns = ["ticker", "weights", "shares"])
ptf["ticker"] = tickers
ptf["weights"] = sharpe_pwt.values()
ptf["close."+sdate] =close_data.loc[sdate].reset_index(drop=True)
ptf["shares"] = allocation.values()
print(ptf)

# Benchmark
bm_shares = start_ptf/(bm_close.loc[sdate].reset_index(drop=True)*ctrans)

# %% PORTFOLIO AND BENCHMARK HISTORICAL PRICES

# Portfolio
ptf_hist = pd.DataFrame({"Ptf" : np.dot(close_data,ptf["shares"])}, index = close_data.index)

# Benchmark
bm_hist =  pd.DataFrame({bm_ticker : np.dot(bm_close,bm_shares)}, index = bm_close.index)

# %% PLOT HISTORICAL PRICES
all_hist = pd.merge(ptf_hist,bm_hist, left_index = True, right_index = True)

all_hist.plot()

# %% SAVE DATA IN CVS
close_data.to_csv('closed_hist.csv')

# %% ####################################################################################
#### 1ST PERIODICAL VALUATION ###########################################################
#########################################################################################
# %% CHOSEN PORTFOLIO AND BENCHMARK
# Portfolio
ptf = pd.DataFrame()
ptf["ticker"] = tickers
ptf["close."+sdate] =close_data.loc[sdate].reset_index(drop=True)
ptf["shares"] = np.array([12924, 3045, 2263, 10246, 22703, 8010, 3020, 2658])
ptf["weights"] = np.multiply(ptf["shares"].values,ptf["close."+sdate].values)/cash_USD
print(ptf)
liquidity_USD = cash_USD-np.dot(ptf["shares"].values,ptf["close."+sdate].values)*ctrans
ptf_liquidity = pd.DataFrame([["liquidity", liquidity_USD, liquidity_USD/cash_USD]], columns=["ticker", "amount (USD)", "weight"])
print(ptf_liquidity)

# %% PORTFOLIO AND BENCHMARK HISTORICAL PRICES FROM 2020-10-28
# Portfolio

r1date = "2020-11-11"
ptf_hist = pd.DataFrame({"Ptf" : np.dot(close_data.loc["2020-10-28":r1date],ptf["shares"])}, 
                                index = close_data.loc["2020-10-28":r1date].index)
ptf_hist += liquidity_USD

# Benchmark
bm_hist =  pd.DataFrame({bm_ticker : np.dot(bm_close.loc["2020-10-28":r1date],bm_shares)}, 
                                index = bm_close.loc["2020-10-28":r1date].index)

# %% PTF & BM %

# Portfolio
ptf_hist = (ptf_hist/ptf_hist.loc[sdate]-1)*100

# Benchmark
bm_hist =  (bm_hist/bm_hist.loc[sdate]-1)*100

#NB: These returns do not take into account the change USD-EUR, see the file excel for them.
# %% PLOT HISTORICAL PRICES
all_hist = pd.merge(ptf_hist,bm_hist, left_index = True, right_index = True)

all_hist.plot()

# %%
