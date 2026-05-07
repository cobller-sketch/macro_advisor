import pandas as pd
import akshare as ak
from fredapi import Fred
import os

def fetch_us_data(fred_api_key):
    fred = Fred(api_key=fred_api_key)
    cpi_us = fred.get_series('CPIAUCSL', observation_start='2000-01-01')
    ppi_us = fred.get_series('PPIACO', observation_start='2000-01-01')
    fedfunds = fred.get_series('FEDFUNDS', observation_start='2000-01-01')
    gdp_us = fred.get_series('GDP', observation_start='2000-01-01')
    gdp_us_monthly = gdp_us.resample('ME').ffill()
    return cpi_us, ppi_us, fedfunds, gdp_us_monthly

def fetch_cn_data():
    # 中国CPI
    cpi_cn = ak.macro_china_cpi_monthly()
    # 自动识别列名
    if '月份' in cpi_cn.columns:
        date_col = '月份'
    elif 'month' in cpi_cn.columns:
        date_col = 'month'
    elif '日期' in cpi_cn.columns:
        date_col = '日期'
    else:
        # 如果都没找到，默认用第一列
        date_col = cpi_cn.columns[0]
    cpi_cn[date_col] = pd.to_datetime(cpi_cn[date_col])
    cpi_cn.set_index(date_col, inplace=True)
    cpi_cn = cpi_cn['cpi'] if 'cpi' in cpi_cn.columns else cpi_cn.iloc[:, 0]
    
    # 中国PPI
    ppi_cn = ak.macro_china_ppi()
    if '月份' in ppi_cn.columns:
        date_col = '月份'
    elif 'month' in ppi_cn.columns:
        date_col = 'month'
    elif '日期' in ppi_cn.columns:
        date_col = '日期'
    else:
        date_col = ppi_cn.columns[0]
    ppi_cn[date_col] = pd.to_datetime(ppi_cn[date_col])
    ppi_cn.set_index(date_col, inplace=True)
    ppi_cn = ppi_cn['ppi_yoy'] if 'ppi_yoy' in ppi_cn.columns else ppi_cn.iloc[:, 0]
    
    # 中国GDP
    gdp_cn = ak.macro_china_gdp()
    if '季度' in gdp_cn.columns:
        date_col = '季度'
    elif '日期' in gdp_cn.columns:
        date_col = '日期'
    else:
        date_col = gdp_cn.columns[0]
    gdp_cn[date_col] = pd.to_datetime(gdp_cn[date_col])
    gdp_cn.set_index(date_col, inplace=True)
    # 取绝对值列（可能是第一列）
    gdp_col = gdp_cn.columns[0]
    gdp_cn_monthly = gdp_cn[gdp_col][::-1].resample('ME').ffill()
    
    # 中国利率（隔夜Shibor）
    rate_cn = ak.macro_china_shibor()
    if '日期' in rate_cn.columns:
        date_col = '日期'
    elif 'date' in rate_cn.columns:
        date_col = 'date'
    else:
        date_col = rate_cn.columns[0]
    rate_cn[date_col] = pd.to_datetime(rate_cn[date_col])
    rate_cn.set_index(date_col, inplace=True)
    # 取隔夜利率列
    if 'O/N_IR' in rate_cn.columns:
        rate_cn = rate_cn['O/N_IR']
    else:
        rate_cn = rate_cn.iloc[:, 0]
    
    return cpi_cn, ppi_cn, gdp_cn_monthly, rate_cn

def update_all_data(fred_key):
    us_cpi, us_ppi, us_rate, us_gdp = fetch_us_data(fred_key)
    cn_cpi, cn_ppi, cn_gdp, cn_rate = fetch_cn_data()
    data = {
        'us_cpi': us_cpi, 'us_ppi': us_ppi, 'us_rate': us_rate, 'us_gdp': us_gdp,
        'cn_cpi': cn_cpi, 'cn_ppi': cn_ppi, 'cn_gdp': cn_gdp, 'cn_rate': cn_rate
    }
    os.makedirs('data', exist_ok=True)
    for name, series in data.items():
        series.to_parquet(f'data/{name}.parquet')
    return data

def load_cached_data():
    if not os.path.exists('data'):
        return None
    data = {}
    for name in ['us_cpi', 'us_ppi', 'us_rate', 'us_gdp', 'cn_cpi', 'cn_ppi', 'cn_gdp', 'cn_rate']:
        path = f'data/{name}.parquet'
        if os.path.exists(path):
            data[name] = pd.read_parquet(path)
        else:
            return None
    return data
