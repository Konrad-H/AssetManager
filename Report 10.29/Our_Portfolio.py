# %%  INSTAL PACKAGES

import yfinance as yf
import matplotlib.pyplot as plt
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
                "EWJ" ] # JAPAN (TOYOTA, SONY, SOFTBANK, etc)
N = len(tickers)
weights = np.ones(N)/N # TRIVIAL WEIGHTS


asset_list=[]
for tick in tickers:
    asset_list.append(yf.Ticker(tick))

last_close = np.zeros(N)
shares = np.zeros(N)

# %% 

usd_eur = yf.Ticker("EUR=X")
USD_EUR_RATE = usd_eur.info["previousClose"]

start_ptf = 5000000/ USD_EUR_RATE

# %% Print Asset List

for i in range(0,N):
    print(asset_list[i].info["shortName"])
    print(asset_list[i].recommendations)
# %% Creating Historical Data

close_data = pd.DataFrame()
vol_data = pd.DataFrame()

for i in range(0,N):
    right = asset_list[i].history(period="2y")
    right_close = pd.DataFrame(pd.DataFrame({tickers[i]: right['Close']}))
    right_vol =  pd.DataFrame(pd.DataFrame({tickers[i]: right['Volume']}))
    if (close_data.empty):
        close_data = right_close
        vol_data = right_vol
    else:
        close_data = pd.merge(close_data, right_close, how ='outer', on="Date")
        vol_data = pd.merge(vol_data, right_vol, how ='outer', on="Date")


# %% Create my portfolio
ptf = pd.DataFrame( columns = ["ticker", "weights", "shares"])
ptf["ticker"] = tickers
ptf["weights"] = weights
ptf["close.2020-10-28"] =close_data.loc['2020-10-28'].reset_index(drop=True)
ptf["shares"] = start_ptf * weights / ptf["close.2020-10-28"]
ptf

# %% Calculate the historical price

ptf_hist = pd.DataFrame({"close" : np.dot(close_data,ptf["shares"])}, index = close_data.index)
sns.lineplot(x = ptf_hist.index, y = ptf_hist["close"] )

# %%

