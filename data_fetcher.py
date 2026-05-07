import pandas as pd
import akshare as ak
from fredapi import Fred
import os
import warnings
warnings.filterwarnings('ignore')

def fetch_us_data(fred_api_key):
    fred = Fred(api_key=fred_api_key)
    cpi_us = fred.get_series('CPIAUCSL', observation_start='2000-01-01')
    ppi_us = fred.get_series('PPIACO', observation_start='2000-01-01')
    fedfunds = fred.get_series('FEDFUNDS', observation_start='2000-01-01')
    gdp_us = fred.get_series('GDP', observation_start='2000-01-01')
    gdp_us_monthly = gdp_us.resample('ME').ffill()
    return cpi_us, ppi_us, fedfunds, gdp_us_monthly

def safe_date_parse(series):
    """安全地解析日期，遇到无法解析的值则跳过"""
    try:
        return pd.to_datetime(series, errors='coerce')
    except:
        # 如果整体失败，尝试逐个转换
        out = []
        for val in series:
            try:
                out.append(pd.to_datetime(val))
            except:
                out.append(pd.NaT)
        return pd.Series(out)

def fetch_cn_data():
    # ---------- 中国CPI ----------
    try:
        cpi_cn = ak.macro_china_cpi_monthly()
        # 确定日期列
        date_col = None
        for col in ['月份', 'month', '日期', 'date']:
            if col in cpi_cn.columns:
                date_col = col
                break
        if date_col is None:
            date_col = cpi_cn.columns[0]
        # 安全解析日期
        cpi_cn[date_col] = safe_date_parse(cpi_cn[date_col])
        cpi_cn = cpi_cn.dropna(subset=[date_col])
        cpi_cn.set_index(date_col, inplace=True)
        # 提取CPI数值列
        if 'cpi' in cpi_cn.columns:
            cpi_cn = cpi_cn['cpi']
        else:
            cpi_cn = cpi_cn.iloc[:, 0]
    except Exception as e:
        print(f"CPI获取失败: {e}")
        # 如果失败，返回空Series
        cpi_cn = pd.Series(dtype=float)
    
    # ---------- 中国PPI ----------
    try:
        ppi_cn = ak.macro_china_ppi()
        date_col = None
        for col in ['月份', 'month', '日期', 'date']:
            if col in ppi_cn.columns:
                date_col = col
                break
        if date_col is None:
            date_col = ppi_cn.columns[0]
        ppi_cn[date_col] = safe_date_parse(ppi_cn[date_col])
        ppi_cn = ppi_cn.dropna(subset=[date_col])
        ppi_cn.set_index(date_col, inplace=True)
        if 'ppi_yoy' in ppi_cn.columns:
            ppi_cn = ppi_cn['ppi_yoy']
        else:
            ppi_cn = ppi_cn.iloc[:, 0]
    except Exception as e:
        print(f"PPI获取失败: {e}")
        ppi_cn = pd.Series(dtype=float)
    
    # ---------- 中国GDP ----------
    try:
        gdp_cn = ak.macro_china_gdp()
        date_col = None
        for col in ['季度', '日期', 'date']:
            if col in gdp_cn.columns:
                date_col = col
                break
        if date_col is None:
            date_col = gdp_cn.columns[0]
        gdp_cn[date_col] = safe_date_parse(gdp_cn[date_col])
        gdp_cn = gdp_cn.dropna(subset=[date_col])
        gdp_cn.set_index(date_col, inplace=True)
        gdp_col = gdp_cn.columns[0]  # 取第一列数值
        gdp_cn = gdp_cn[gdp_col]
        gdp_cn_monthly = gdp_cn[::-1].resample('ME').ffill()
    except Exception as e:
        print(f"GDP获取失败: {e}")
        gdp_cn_monthly = pd.Series(dtype=float)
    
    # ---------- 中国利率 ----------
    try:
        rate_cn = ak.macro_china_shibor()
        date_col = None
        for col in ['日期', 'date']:
            if col in rate_cn.columns:
                date_col = col
                break
        if date_col is None:
            date_col = rate_cn.columns[0]
        rate_cn[date_col] = safe_date_parse(rate_cn[date_col])
        rate_cn = rate_cn.dropna(subset=[date_col])
        rate_cn.set_index(date_col, inplace=True)
        if 'O/N_IR' in rate_cn.columns:
            rate_cn = rate_cn['O/N_IR']
        else:
            rate_cn = rate_cn.iloc[:, 0]
    except Exception as e:
        print(f"利率获取失败: {e}")
        rate_cn = pd.Series(dtype=float)
    
    return cpi_cn, ppi_cn, gdp_cn_monthly, rate_cn

def update_all_data(fred_key):
    print("正在获取美国数据...")
    us_cpi, us_ppi, us_rate, us_gdp = fetch_us_data(fred_key)
    print("正在获取中国数据...")
    cn_cpi, cn_ppi, cn_gdp, cn_rate = fetch_cn_data()
    
    data = {
        'us_cpi': us_cpi, 'us_ppi': us_ppi, 'us_rate': us_rate, 'us_gdp': us_gdp,
        'cn_cpi': cn_cpi, 'cn_ppi': cn_ppi, 'cn_gdp': cn_gdp, 'cn_rate': cn_rate
    }
    os.makedirs('data', exist_ok=True)
    for name, series in data.items():
        if not series.empty:
            series.to_parquet(f'data/{name}.parquet')
        else:
            print(f"警告: {name} 数据为空，跳过保存")
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
            print(f"缓存文件缺失: {path}")
            return None
    return data
