import plotly.graph_objects as go
from plotly.subplots import make_subplots

def show_dashboard(us_gdp, us_cpi, us_ppi, us_rate, cn_gdp, cn_cpi, cn_ppi, cn_rate):
    fig = make_subplots(rows=4, cols=1, 
                        subplot_titles=('GDP (季度填充月)', 'CPI (同比%)', 'PPI (同比%)', '政策利率 (%)'),
                        shared_xaxes=True, vertical_spacing=0.05)
    
    fig.add_trace(go.Scatter(x=us_gdp.index, y=us_gdp, name='美国GDP', line=dict(color='blue')), row=1, col=1)
    fig.add_trace(go.Scatter(x=cn_gdp.index, y=cn_gdp, name='中国GDP', line=dict(color='red')), row=1, col=1)
    fig.add_trace(go.Scatter(x=us_cpi.index, y=us_cpi, name='美国CPI', line=dict(color='blue')), row=2, col=1)
    fig.add_trace(go.Scatter(x=cn_cpi.index, y=cn_cpi, name='中国CPI', line=dict(color='red')), row=2, col=1)
    fig.add_trace(go.Scatter(x=us_ppi.index, y=us_ppi, name='美国PPI', line=dict(color='blue')), row=3, col=1)
    fig.add_trace(go.Scatter(x=cn_ppi.index, y=cn_ppi, name='中国PPI', line=dict(color='red')), row=3, col=1)
    fig.add_trace(go.Scatter(x=us_rate.index, y=us_rate, name='美国利率', line=dict(color='blue')), row=4, col=1)
    fig.add_trace(go.Scatter(x=cn_rate.index, y=cn_rate, name='中国利率', line=dict(color='red')), row=4, col=1)
    
    fig.update_layout(height=1200, title_text="中美宏观数据对比 (2006-至今)", showlegend=True)
    fig.update_xaxes(title_text="日期")
    return fig
