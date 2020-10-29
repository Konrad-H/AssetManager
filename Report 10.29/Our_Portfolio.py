# %%  INSTAL PACKAGES

import yfinance as yf
import seaborn as sns
import numpy as np
import pandas as pd

# %% Ticker List

tickers = [ "QQQ", # NASDAQ 100 index
                "IDU", # DOW JONES UTILITIES AVERAGE
                "SDG",  # GLOBAL IMPACT (TESLA, etc)
                "MNA", # IQ MERGER ARBITRAGE ETF
                "SGOL", # GOLD SPOT PRICE
                "CQQQ", # CHINA TECHNOLOGY
                "EWJ",
                "EWY" ] # JAPAN (TOYOTA, SONY, SOFTBANK, etc)
N = len(tickers)

asset_list=[]
for tick in tickers:
    asset_list.append(yf.Ticker(tick))

# %% BENCHMARK
bm_ticker = "VOO"
bm2_ticker = "ACWI"
bmark = yf.Ticker(bm_ticker)
bmark2 = yf.Ticker(bm2_ticker)

# %% Print Asset List

for i in range(0,N):
    print(asset_list[i].info["shortName"])
    print(asset_list[i].recommendations)
# %% Creating Historical Data

close_data = pd.DataFrame()
vol_data = pd.DataFrame()

for i in range(0,N):
    right = asset_list[i].history(period="2y")
    right_close = pd.DataFrame({tickers[i]: right['Close']})
    right_vol = pd.DataFrame({tickers[i]: right['Volume']})
    if (close_data.empty):
        close_data = right_close
        vol_data = right_vol
    else:
        close_data = pd.merge(close_data, right_close, how ='outer', on="Date")
        vol_data = pd.merge(vol_data, right_vol, how ='outer', on="Date")


bm_close = pd.DataFrame({ bm_ticker : bmark.history(period="2y")['Close']})
bm2_close = pd.DataFrame({ bm2_ticker :  bmark2.history(period="2y")['Close']})

# %% TODAY
sdate = '2020-10-28'
sdate = '2020-09-03' # DELETE THIS

ctrans = 100.3/100
# %% TODAY 

usd_eur = yf.Ticker("EUR=X")
USD_EUR_RATE = usd_eur.history(period="2y")["Close"].loc[sdate] * ctrans

start_ptf = 5000000/ USD_EUR_RATE 


# %% Create my portfolio

weights = np.ones(N)/N # TRIVIAL WEIGHTS

ptf = pd.DataFrame( columns = ["ticker", "weights", "shares"])
ptf["ticker"] = tickers
ptf["weights"] = weights
ptf["close."+sdate] =close_data.loc[sdate].reset_index(drop=True)
ptf["shares"] = start_ptf * weights / (ptf["close."+sdate]*ctrans)
ptf

bm_shares = start_ptf/(bm_close.loc[sdate].reset_index(drop=True)*ctrans)
bm2_shares = start_ptf/(bm2_close.loc[sdate].reset_index(drop=True)*ctrans)


# %% Calculate the historical price

ptf_hist = pd.DataFrame({"Ptf" : np.dot(close_data,ptf["shares"])}, index = close_data.index)

# possible BenchMarks
bm_hist =  pd.DataFrame({bm_ticker : np.dot(bm_close,bm_shares)}, index = bm_close.index)
bm2_hist =  pd.DataFrame({bm2_ticker : np.dot(bm2_close,bm2_shares)}, index = bm2_close.index)


# %%

all_hist = pd.merge(ptf_hist,bm_hist, left_index = True, right_index = True)
all_hist = pd.merge(all_hist,bm2_hist, left_index = True, right_index = True)

all_hist.plot()

# %%

close_data.to_csv('closed_hist.csv')
# %%
