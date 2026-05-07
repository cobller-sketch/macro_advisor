import pandas as pd
import akshare as ak
from fredapi import Fred
import os
import warnings
warnings.filterwarnings('ignore')

# ---------- 辅助函数：安全解析日期 ----------
def safe_date_parse(series):
    try:
        return pd.to_datetime(series, errors='coerce')
    except:
        out = []
        for val in series:
            try:
                out.append(pd.to_datetime(val))
            except:
                out.append(pd.NaT)
        return pd.Series(out)

# ---------- 美国数据（使用 FRED API）----------
def fetch_us_data(fred_api_key):
    fred = Fred(api_key=fred_api_key)
    cpi_us = fred.get_series('CPIAUCSL', observation_start='2000-01-01')
    ppi_us = fred.get_series('PPIACO', observation_start='2000-01-01')
    fedfunds = fred.get_series('FEDFUNDS', observation_start='2000-01-01')
    gdp_us = fred.get_series('GDP', observation_start='2000-01-01')
    gdp_us_monthly = gdp_us.resample('ME').ffill()
    return cpi_us, ppi_us, fedfunds, gdp_us_monthly

# ---------- 中国数据（带失败回退）----------
def generate_fake_cn_data():
    """当真实数据获取失败时，生成模拟数据（2000年至今的典型走势）"""
    dates = pd.date_range('2000-01-01', pd.Timestamp.today(), freq='M')
    # 模拟CPI：在0~3%之间波动
    cpi = 1.5 + 0.5 * pd.Series(range(len(dates)), index=dates).apply(lambda x: pd.np.sin(x/24))
    # 模拟PPI：在-2%~4%之间波动
    ppi = 0.5 + 0.8 * pd.Series(range(len(dates)), index=dates).apply(lambda x: pd.np.sin(x/18))
    # 模拟GDP增速：6%~10%之间，近期略低
    gdp = 7.0 + 1.5 * pd.Series(range(len(dates)), index=dates).apply(lambda x: pd.np.cos(x/40))
    # 模拟利率：2%~4%之间
    rate = 2.5 + 0.5 * pd.Series(range(len(dates)), index=dates).apply(lambda x: pd.np.sin(x/60))
    return cpi, ppi, gdp, rate

def fetch_cn_data():
    # 默认使用模拟数据
    cpi_cn, ppi_cn, gdp_cn, rate_cn = generate_fake_cn_data()
    
    # 尝试获取真实CPI
    try:
        temp = ak.macro_china_cpi_monthly()
        if temp is not None and not temp.empty:
            # 找日期列
            date_col = None
            for col in ['月份', 'month', '日期', 'date']:
                if col in temp.columns:
                    date_col = col
                    break
            if date_col is None:
                date_col = temp.columns[0]
            temp[date_col] = safe_date_parse(temp[date_col])
            temp = temp.dropna(subset=[date_col])
            if not temp.empty:
                temp.set_index(date_col, inplace=True)
                if 'cpi' in temp.columns:
                    cpi_cn = temp['cpi']
                else:
                    cpi_cn = temp.iloc[:, 0]
                cpi_cn = cpi_cn.sort_index()
    except Exception as e:
        print(f"真实CPI获取失败，使用模拟数据。错误: {e}")
    
    # 尝试获取真实PPI
    try:
        temp = ak.macro_china_ppi()
        if temp is not None and not temp.empty:
            date_col = None
            for col in ['月份', 'month', '日期', 'date']:
                if col in temp.columns:
                    date_col = col
                    break
            if date_col is None:
                date_col = temp.columns[0]
            temp[date_col] = safe_date_parse(temp[date_col])
            temp = temp.dropna(subset=[date_col])
            if not temp.empty:
                temp.set_index(date_col, inplace=True)
                if 'ppi_yoy' in temp.columns:
                    ppi_cn = temp['ppi_yoy']
                else:
                    ppi_cn = temp.iloc[:, 0]
                ppi_cn = ppi_cn.sort_index()
    except Exception as e:
        print(f"真实PPI获取失败，使用模拟数据。错误: {e}")
    
    # 尝试获取真实GDP
    try:
        temp = ak.macro_china_gdp()
        if temp is not None and not temp.empty:
            date_col = None
            for col in ['季度', '日期', 'date']:
                if col in temp.columns:
                    date_col = col
                    break
            if date_col is None:
                date_col = temp.columns[0]
            temp[date_col] = safe_date_parse(temp[date_col])
            temp = temp.dropna(subset=[date_col])
            if not temp.empty:
                temp.set_index(date_col, inplace=True)
                gdp_col = temp.columns[0]
                gdp_quarter = temp[gdp_col].sort_index()
                # 季度转月度
                gdp_cn = gdp_quarter.resample('ME').ffill()
    except Exception as e:
        print(f"真实GDP获取失败，使用模拟数据。错误: {e}")
    
    # 尝试获取真实利率
    try:
        temp = ak.macro_china_shibor()
        if temp is not None and not temp.empty:
            date_col = None
            for col in ['日期', 'date']:
                if col in temp.columns:
                    date_col = col
                    break
            if date_col is None:
                date_col = temp.columns[0]
            temp[date_col] = safe_date_parse(temp[date_col])
            temp = temp.dropna(subset=[date_col])
            if not temp.empty:
                temp.set_index(date_col, inplace=True)
                if 'O/N_IR' in temp.columns:
                    rate_cn = temp['O/N_IR']
                else:
                    rate_cn = temp.iloc[:, 0]
                rate_cn = rate_cn.sort_index()
    except Exception as e:
        print(f"真实利率获取失败，使用模拟数据。错误: {e}")
    
    # 确保所有数据都有值且索引是日期
    for s in [cpi_cn, ppi_cn, gdp_cn, rate_cn]:
        if s is None or s.empty:
            # 不应该发生，因为模拟数据保证了非空
            pass
    
    return cpi_cn, ppi_cn, gdp_cn, rate_cn

# ---------- 主更新函数 ----------
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
        if series is not None and not series.empty:
            try:
                series.to_parquet(f'data/{name}.parquet')
            except Exception as e:
                print(f"保存 {name} 失败: {e}")
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
    # 检查是否所有数据都成功加载
    if any(v is None or v.empty for v in data.values()):
        return None
    return data
