import streamlit as st
import pandas as pd
import requests
import time
import yfinance as yf
from io import BytesIO
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ─────────────────────────────────────────────
# 頁面設定
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="財務規劃系統 Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #f5f7ff !important;
    color: #1a2040 !important;
}
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1.5px solid #dde3f5;
}
html, body, button, input, select, textarea, .stMarkdown, .stText {
    font-family: 'DM Sans', sans-serif !important;
}
h1, h2, h3 { font-family: 'DM Serif Display', serif !important; }

.main-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.4rem;
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}
.section-header {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: #7c3aed;
    letter-spacing: 3px;
    text-transform: uppercase;
    border-left: 3px solid #7c3aed;
    padding-left: 10px;
    margin: 24px 0 12px 0;
}
[data-testid="metric-container"] {
    background: #ffffff !important;
    border: 1.5px solid #e0e7ff !important;
    border-radius: 14px !important;
    padding: 16px 18px !important;
    box-shadow: 0 2px 12px rgba(79,70,229,0.07) !important;
}
[data-testid="metric-container"] label {
    color: #7c8db5 !important;
    font-size: 0.7rem !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    font-family: 'DM Mono', monospace !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #4f46e5 !important;
    font-family: 'DM Serif Display', serif !important;
    font-size: 1.7rem !important;
}
.stButton > button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    box-shadow: 0 4px 14px rgba(79,70,229,0.3) !important;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.85 !important; }
.stTextInput input, .stNumberInput input {
    background: #f8f9ff !important;
    border: 1.5px solid #dde3f5 !important;
    border-radius: 8px !important;
    color: #1a2040 !important;
}
[data-testid="stAlert"] {
    background: #eef2ff !important;
    border: 1px solid #c7d2fe !important;
    border-radius: 10px !important;
    color: #3730a3 !important;
}
[data-testid="stSidebar"] label { color: #5a6a9a !important; font-size: 0.8rem !important; }
hr { border-color: #e0e7ff !important; }
.ai-card {
    background: linear-gradient(135deg, #eef2ff 0%, #f5f0ff 100%);
    border: 1.5px solid #c7d2fe;
    border-radius: 14px;
    padding: 22px 26px;
    line-height: 1.8;
    font-size: 0.93rem;
    color: #1e1b4b;
    white-space: pre-wrap;
    box-shadow: 0 4px 20px rgba(79,70,229,0.08);
}
.ai-badge {
    display: inline-block;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: #fff;
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 2px;
    padding: 3px 10px;
    border-radius: 4px;
    margin-bottom: 10px;
}
.module-card {
    background: #fff;
    border: 1.5px solid #e0e7ff;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 10px rgba(79,70,229,0.05);
}
.gap-badge {
    display: inline-block;
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.8rem;
    font-weight: 600;
}
.ok-badge {
    display: inline-block;
    background: #f0fdf4;
    color: #16a34a;
    border: 1px solid #bbf7d0;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.8rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────
for key in ['run_investment', 'run_health', 'run_insurance', 'run_retirement', 'run_tax']:
    if key not in st.session_state:
        st.session_state[key] = False

# ─────────────────────────────────────────────
# 工具函數
# ─────────────────────────────────────────────
def strip_md(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'#+\s*', '', text)
    return text.strip()

def get_investment_advice(names, p_ret, p_mdd, dca_roi):
    rr = "RR5" if p_mdd < -25 else "RR4" if p_mdd < -15 else "RR3" if p_mdd < -8 else "RR2"
    ret_desc = "表現亮眼" if p_ret > 20 else "穩健成長" if p_ret > 8 else "相對保守"
    mdd_desc = "波動較大，需有心理準備" if p_mdd < -20 else "波動適中" if p_mdd < -10 else "波動相對低"
    dca_desc = "定期定額效果顯著" if dca_roi > p_ret else "單筆投入表現略勝定期定額"
    return f"""【投資組合分析報告】

一、風險收益特性
本組合由 {' / '.join(names)} 組成，歷史加權總報酬率為 {p_ret:.2f}%，{ret_desc}。最大回撤為 {p_mdd:.2f}%，{mdd_desc}，建議投資人應具備 {rr} 等級之風險承受能力。

二、各標的角色
各標的在組合中扮演互補角色，透過不同資產類別的配置，有效分散單一市場風險，兼顧成長性與穩定性。

三、適合投資人輪廓
本組合適合具備 {rr} 風險承受度、投資期間 5 年以上，且能接受短期淨值波動的投資人。建議每季定期檢視組合表現並適時再平衡。

四、注意事項
• 過去績效不代表未來報酬，投資前請充分了解商品風險
• 定期定額報酬率 {dca_roi:.2f}%（{dca_desc}），建議持續執行以平滑成本
• 市場劇烈波動時，切勿因恐慌而中斷投資計畫

五、建議結語
紀律投資、分散配置、長期持有，是累積財富的不二法門。"""

def get_health_advice(monthly_surplus, savings_rate, debt_ratio, emergency_months, net_worth):
    s_comment = "儲蓄率優良，財務紀律良好" if savings_rate >= 20 else "儲蓄率偏低，建議提升至 20% 以上"
    d_comment = "負債比率健康" if debt_ratio <= 40 else "負債比率偏高，應優先還款降低財務風險"
    e_comment = "緊急預備金充足" if emergency_months >= 6 else f"緊急預備金不足（目前 {emergency_months:.1f} 個月），建議累積至 6 個月以上"
    surplus_comment = "月度結餘充裕，可積極投資" if monthly_surplus > 20000 else "月度結餘有限，建議檢視可縮減的支出項目"
    return f"""【財務健診報告】

一、財務健康評估
客戶目前淨資產為 {net_worth/10000:.0f} 萬元，月度結餘 {monthly_surplus:,.0f} 元。{surplus_comment}。整體財務狀況{'健康穩健' if savings_rate >= 20 and debt_ratio <= 40 else '仍有改善空間'}。

二、主要風險與改善建議
• 儲蓄能力：{s_comment}
• 負債管理：{d_comment}
• 緊急準備：{e_comment}

三、資產配置建議
建議將資產依「緊急預備金 → 保障規劃 → 中長期投資」三層次配置。流動資金保留 6 個月生活費，其餘可依風險屬性投入基金或 ETF 等工具。

四、行動計畫
• 短期（3個月）：建立預算記帳習慣，找出可節省項目
• 中期（1年）：提升儲蓄率至 20%，補足緊急預備金
• 長期（3年）：{'加速還款，降低負債比率' if debt_ratio > 40 else '啟動投資計畫，累積退休資產'}

五、總結
財務健康是財富自由的基石，建議每半年進行一次財務健診，持續追蹤改善進度。"""

def get_insurance_advice(age, life_gap, medical_gap, disable_gap, accident_gap):
    gaps = []
    if life_gap > 0: gaps.append(f"壽險缺口 {life_gap} 萬")
    if medical_gap > 0: gaps.append(f"醫療缺口 {medical_gap} 萬")
    if disable_gap > 0: gaps.append(f"失能月給付缺口 ${disable_gap:,}")
    if accident_gap > 0: gaps.append(f"意外險缺口 {accident_gap} 萬")
    gap_str = "、".join(gaps) if gaps else "保障完整，無明顯缺口"
    priority = "失能險 > 醫療實支 > 壽險 > 意外險" if age < 45 else "醫療實支 > 失能險 > 壽險 > 意外險"
    return f"""【保障需求分析報告】

一、保障缺口總覽
經分析，客戶目前保障缺口為：{gap_str}。{'建議儘速補強，以免家庭財務陷入風險。' if gaps else '建議每年定期檢視，確保保障持續有效。'}

二、補強優先順序
依照客戶年齡與家庭狀況，建議補強順序為：{priority}。失能險能在喪失工作能力時維持生活，是現代人最容易忽略卻最重要的保障。

三、建議商品類型
• 壽險：定期壽險 CP 值高，適合有家庭責任的青壯年
• 醫療：實支實付型，可搭配日額型補強住院給付
• 失能：失能扶助險，建議月給付涵蓋家庭基本開銷
• 意外：意外傷害險保費低、保障高，性價比佳

四、預算配置建議
保費支出建議控制在年收入的 10%~15% 以內，優先補強保障型商品，儲蓄型保險次之。

五、注意事項
• 投保前務必詳閱保單條款，了解除外責任
• 建議每 3 年重新檢視保障需求，隨生命階段調整"""

def get_retirement_advice(current_age, retire_age, gap, gap_monthly, total_needed, total_accumulated, expected_return):
    gap_desc = f"缺口 {gap/10000:.0f} 萬，建議每月增加儲蓄 ${gap_monthly:,.0f}" if gap > 0 else "退休準備充足，繼續維持現有計畫"
    years = retire_age - current_age
    return f"""【退休金規劃報告】

一、退休準備充足度
預計退休所需總額為 {total_needed/10000:,.0f} 萬元，目前規劃可累積 {total_accumulated/10000:,.0f} 萬元。{gap_desc}。

二、補足缺口策略
• 增加每月儲蓄：每月多存 ${gap_monthly:,.0f} 元投入退休帳戶
• 提升報酬率：目前設定 {expected_return}%，可考慮適度提高股票型資產比例
• 延後退休：每多工作 1 年，可減少所需資產並增加累積時間
• 開源節流：增加收入來源或降低退休後生活費需求

三、投資配置建議
距退休 {years} 年，{'建議以股票型基金為主（60~80%），債券為輔' if years > 15 else '建議逐步調降股票比例至 40~60%，增加穩定型資產'}，並每年再平衡一次。

四、注意事項
• 通膨侵蝕購買力是退休規劃最大風險，務必納入計算
• 勞保給付視個人年資而異，建議至勞保局試算確認
• 退休金不建議全部放定存，需適度投資以對抗通膨

五、建議結語
退休規劃宜早不宜晚，複利效果在時間拉長後威力驚人，現在開始行動永遠不嫌晚。"""

def get_tax_advice(total_gross, final_tax, eff_rate, use_itemized, dividend_income, filing_status):
    itemized_tip = "已採列舉扣除，建議持續保留醫療、房貸利息等收據" if use_itemized else "目前採標準扣除，若醫療或房貸支出增加，可考慮改列舉"
    div_tip = f"股利所得 {dividend_income:,} 元，已適用 8.5% 股利抵減，節稅效果良好" if dividend_income > 0 else "目前無股利所得"
    return f"""【稅務規劃報告】

一、現況分析
客戶年度綜合所得總額 {total_gross:,} 元，應繳稅額 {final_tax:,.0f} 元，有效稅率 {eff_rate:.2f}%。{itemized_tip}。

二、節稅策略建議
• 保險費：每人每年最高扣除 24,000 元，夫妻合計可達 48,000 元
• 捐贈扣除：對合法機構之捐贈可列舉扣除（上限為綜合所得總額 20%）
• 房貸利息：自住房屋貸款利息最高扣除 300,000 元
• 教育學費：就讀大學以上子女每人扣除 25,000 元

三、股利課稅方式
{div_tip}。股利所得可選擇「合併計稅（8.5% 抵減，上限 8 萬）」或「分離課稅（28%）」，建議每年依實際所得試算選擇有利方式。

四、明年預先規劃
• 年底前確認是否達到各項扣除額上限
• 若有資本利得，可考慮年底前實現損失以抵銷獲利
• {'夫妻合併申報通常較有利，但需每年試算確認' if filing_status == '夫妻合併' else '建議試算夫妻合併vs分開申報，選擇較有利方式'}

五、免責聲明
本試算依現行稅法為基準，實際應納稅額請以國稅局核定為準，重大稅務決策建議諮詢專業會計師。"""

def render_ai(text, badge="系統分析報告"):
    st.markdown(f"""
    <div class="ai-card">
        <div class="ai-badge">{badge}</div><br>
        {text.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PDF 產生器（reportlab）
# ─────────────────────────────────────────────
def build_pdf(client_name, sections: list[dict]) -> bytes:
    """
    sections = [{"title": str, "content": str, "table": pd.DataFrame or None}]
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )

    # 嘗試載入中文字型（若有），否則用內建
    try:
        font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('NotoSans', font_path))
            base_font = 'NotoSans'
        else:
            base_font = 'Helvetica'
    except:
        base_font = 'Helvetica'

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', fontName=base_font, fontSize=20,
                                  textColor=colors.HexColor('#4f46e5'), spaceAfter=6, leading=28)
    sub_style   = ParagraphStyle('Sub',   fontName=base_font, fontSize=10,
                                  textColor=colors.HexColor('#7c8db5'), spaceAfter=14)
    h2_style    = ParagraphStyle('H2',    fontName=base_font, fontSize=13,
                                  textColor=colors.HexColor('#1e1b4b'), spaceBefore=14, spaceAfter=6, leading=18)
    body_style  = ParagraphStyle('Body',  fontName=base_font, fontSize=9,
                                  textColor=colors.HexColor('#1a2040'), leading=15, spaceAfter=8)

    story = []
    # 封面
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("財務規劃報告書", title_style))
    story.append(Paragraph(f"客戶姓名：{client_name}　　製表日期：{time.strftime('%Y/%m/%d')}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#c7d2fe')))
    story.append(Spacer(1, 6*mm))

    for sec in sections:
        story.append(Paragraph(sec['title'], h2_style))
        if sec.get('table') is not None:
            df = sec['table']
            data = [list(df.columns)] + df.values.tolist()
            t = Table(data, repeatRows=1, hAlign='LEFT')
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4f46e5')),
                ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
                ('FONTNAME',   (0,0), (-1,-1), base_font),
                ('FONTSIZE',   (0,0), (-1,-1), 8),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f5f7ff'), colors.white]),
                ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#dde3f5')),
                ('TOPPADDING',    (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING',   (0,0), (-1,-1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 4*mm))
        if sec.get('content'):
            for line in sec['content'].split('\n'):
                if line.strip():
                    story.append(Paragraph(line.strip(), body_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e0e7ff')))

    doc.build(story)
    return buf.getvalue()

# ─────────────────────────────────────────────
# 投資組合函數（保留原有邏輯）
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_fund_data(fund_id, name):
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://fund.cnyes.com/"}
    try:
        res = requests.get(f"https://fund.api.cnyes.com/fund/api/v1/funds/{fund_id}/nav?format=table&page=1",
                           headers=headers, timeout=10)
        nav_items = res.json().get('items', {}).get('data', [])
        if not nav_items: return None
        df_nav = pd.DataFrame(nav_items)
        date_col = next((c for c in ['tradeDate','date','navDate','datetime'] if c in df_nav.columns), None)
        nav_col  = next((c for c in ['nav','nav_price','price'] if c in df_nav.columns), None)
        if not date_col or not nav_col: return None
        # 修正：鉅亨 API 回傳 Unix timestamp（秒），需用 unit='s' 轉換
        raw_date = pd.to_numeric(df_nav[date_col], errors='coerce')
        if raw_date.dropna().iloc[0] > 1e9:
            df_nav['date'] = pd.to_datetime(raw_date, unit='s', errors='coerce')
        else:
            df_nav['date'] = pd.to_datetime(df_nav[date_col], errors='coerce')
        df_nav['nav']  = pd.to_numeric(df_nav[nav_col], errors='coerce')
        df_nav = df_nav.sort_values('date').dropna(subset=['nav'])
    except Exception as e:
        st.error(f"❌ {name} 資料抓取失敗: {e}"); return None

    total_div = 0
    try:
        res_div = requests.get(f"https://fund.api.cnyes.com/fund/api/v1/funds/{fund_id}/dividend",
                               headers=headers, timeout=10).json()
        div_items = res_div.get('items', {}).get('data', [])
        if div_items:
            df_div = pd.DataFrame(div_items)
            div_col = next((c for c in ['totalDistribution','amount'] if c in df_div.columns), df_div.columns[0])
            total_div = pd.to_numeric(df_div[div_col], errors='coerce').sum()
    except Exception as e:
        st.warning(f"⚠️ {name} 配息抓取失敗: {e}")

    if len(df_nav) < 2: return None
    s, e = df_nav['nav'].iloc[0], df_nav['nav'].iloc[-1]
    peak = df_nav['nav'].expanding().max()
    mdd  = ((df_nav['nav'] - peak) / peak).min() * 100
    return {"ID": fund_id, "名稱": name, "最新淨值": round(e,2),
            "累積配息": round(total_div,2),
            "總報酬率(%)": round(((e+total_div-s)/s)*100, 2),
            "最大回撤(%)": round(mdd, 2), "df": df_nav}

@st.cache_data(ttl=3600)
def get_stock_data(stock_id, name):
    try:
        tid = f"{stock_id}.TW" if stock_id.isdigit() or len(stock_id)==4 else stock_id
        df  = yf.Ticker(tid).history(period="2y")
        if df.empty: st.error(f"❌ 找不到: {tid}"); return None
        df = df.reset_index()[['Date','Close']].rename(columns={'Date':'date','Close':'nav'})
        df['date'] = df['date'].dt.tz_localize(None).dt.normalize()
        df = df.sort_values('date').dropna()
        s, e = df['nav'].iloc[0], df['nav'].iloc[-1]
        peak = df['nav'].expanding().max()
        mdd  = ((df['nav'] - peak) / peak).min() * 100
        return {"ID": stock_id, "名稱": name, "最新淨值": round(e,2),
                "累積配息": 0, "總報酬率(%)": round(((e-s)/s)*100,2),
                "最大回撤(%)": round(mdd,2), "df": df}
    except Exception as e:
        st.error(f"❌ {name}: {e}"); return None

def calculate_dca(df_nav, monthly):
    df = df_nav.copy().sort_values('date').set_index('date')
    mdf = df.resample('ME').last().dropna().reset_index()
    if mdf.empty: return pd.DataFrame(), 0, 0, 0
    inv, shares, rows = 0, 0, []
    for _, r in mdf.iterrows():
        inv += monthly; shares += monthly/r['nav']
        val = shares * r['nav']
        rows.append({'日期': r['date'], '累計投入成本': inv, '資產市值': val, '淨利潤': val-inv})
    res = pd.DataFrame(rows).set_index('日期')
    fv  = rows[-1]['資產市值']
    return res, inv, fv, ((fv-inv)/inv)*100


# ═══════════════════════════════════════════════════════
# 共用：從淨值歷史計算年化報酬率（CAGR）
# ═══════════════════════════════════════════════════════
def get_cagr(ticker, ticker_type, dummy_name="標的"):
    """
    直接複用 get_fund_data / get_stock_data 取得完整歷史資料，
    再從 df 計算累積報酬率，作為預設建議值參考。
    回傳 (cagr_or_None, label_str)
    """
    try:
        if ticker_type == "基金":
            data = get_fund_data(ticker, dummy_name)
        else:
            data = get_stock_data(ticker, dummy_name)

        if data is None:
            return None, "查無資料"

        df = data["df"]
        if len(df) < 10:
            return None, "資料不足"

        df = df.sort_values("date")
        start_val = df["nav"].iloc[0]
        end_val   = df["nav"].iloc[-1]
        actual_years = (df["date"].iloc[-1] - df["date"].iloc[0]).days / 365.25

        if start_val <= 0 or actual_years <= 0:
            return None, "計算錯誤"

        cagr = ((end_val / start_val) ** (1 / actual_years) - 1) * 100
        return round(cagr, 2), f"{actual_years:.1f}年CAGR"
    except Exception as e:
        return None, str(e)



# ─────────────────────────────────────────────
# 側邊欄導航
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💼 財務規劃系統")
    st.markdown("---")
    module = st.radio("選擇模組", [
        "📊 投資組合分析",
        "🏥 客戶財務健診",
        "🛡️ 保險需求分析",
        "🏖️ 退休金試算",
        "🧾 稅務規劃",
        "💳 信貸投資套利",
        "🏠 房貸減壓分析",
    ])
    st.markdown("---")
    client_name = st.text_input("客戶姓名", "王小明")
    st.caption(f"製表日期：{time.strftime('%Y/%m/%d')}")

    # ── 免責聲明 ──
    st.markdown("---")
    st.markdown("""
    <div style="
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-left: 3px solid #f97316;
        border-radius: 8px;
        padding: 12px 14px;
        font-size: 0.72rem;
        color: #7c3a00;
        line-height: 1.6;
    ">
        <div style="font-weight:700;letter-spacing:1px;margin-bottom:6px;color:#c2410c;">
            ⚠️ 投資風險聲明
        </div>
        本系統提供之數據與分析報告僅供<strong>參考用途</strong>，不構成任何投資建議或買賣邀約。<br><br>
        • 投資涉及風險，過去績效不代表未來報酬<br>
        • 所有試算結果均為模擬，實際投資結果可能有所不同<br>
        • 本系統不負責因使用本資訊所導致之任何損失<br><br>
        進行任何投資決策前，請諮詢合格之專業財務顧問。
    </div>
    """, unsafe_allow_html=True)

st.markdown(f'<p class="main-title">💼 財務規劃系統 Pro</p>', unsafe_allow_html=True)
st.markdown("---")

# ═══════════════════════════════════════════════════════
# 模組一：投資組合分析（原系統整合）
# ═══════════════════════════════════════════════════════
if module == "📊 投資組合分析":
    st.subheader("📊 投資組合分析")

    with st.sidebar:
        st.markdown("**標的 A**")
        type_a = st.selectbox("類型 A", ["共同基金","股票/ETF"], key="ta")
        f1_id   = st.text_input("代碼 A", "B2abw8B" if type_a=="共同基金" else "2330", key="ia")
        f1_name = st.text_input("名稱 A", "安聯收益成長" if type_a=="共同基金" else "台積電", key="na")
        f1_w    = st.slider("權重 A (%)", 0, 100, 40, key="wa") / 100
        st.markdown("**標的 B**")
        type_b = st.selectbox("類型 B", ["共同基金","股票/ETF"], index=1, key="tb")
        f2_id   = st.text_input("代碼 B", "B090460" if type_b=="共同基金" else "0050", key="ib")
        f2_name = st.text_input("名稱 B", "貝萊德世界科技" if type_b=="共同基金" else "元大台灣50", key="nb")
        f2_w    = st.slider("權重 B (%)", 0, 100, 40, key="wb") / 100
        st.markdown("**標的 C**")
        type_c = st.selectbox("類型 C", ["股票/ETF","共同基金"], key="tc")
        f3_id   = st.text_input("代碼 C", "00878", key="ic")
        f3_name = st.text_input("名稱 C", "國泰永續高股息", key="nc")
        f3_w_r  = st.slider("權重 C (%)", 0, 100, 20, key="wc") / 100
        tw = f1_w+f2_w+f3_w_r
        f1_wn = f1_w/tw if tw>0 else 1/3
        f2_wn = f2_w/tw if tw>0 else 1/3
        f3_wn = f3_w_r/tw if tw>0 else 1/3
        st.markdown(f"<small>正規化：A {f1_wn:.0%} / B {f2_wn:.0%} / C {f3_wn:.0%}</small>", unsafe_allow_html=True)
        monthly_amt = st.number_input("每月定期定額", value=10000, step=1000)

    if st.button("🚀 啟動分析", key="btn_inv"):
        st.session_state.run_investment = True

    if st.session_state.run_investment:
        with st.spinner("抓取資料中..."):
            fetch = {"共同基金": get_fund_data, "股票/ETF": get_stock_data}
            d1 = fetch[type_a](f1_id, f1_name)
            d2 = fetch[type_b](f2_id, f2_name)
            d3 = fetch[type_c](f3_id, f3_name)
        all_d = [x for x in [d1,d2,d3] if x]
        ws_r  = [f1_wn if d1 else 0, f2_wn if d2 else 0, f3_wn if d3 else 0]
        ws    = [w/sum(w2 for x,w2 in zip([d1,d2,d3],ws_r) if x) if x else 0
                 for x,w in zip([d1,d2,d3],ws_r)]
        if len(all_d) < 2:
            st.error("資料不足，請檢查代碼"); st.stop()

        p_ret = sum(x['總報酬率(%)']*w for x,w in zip([d1,d2,d3],ws) if x)
        p_mdd = sum(x['最大回撤(%)']*w for x,w in zip([d1,d2,d3],ws) if x)
        p_div = sum(x['累積配息']*w   for x,w in zip([d1,d2,d3],ws) if x)
        rr    = "RR5" if p_mdd<-25 else "RR4" if p_mdd<-15 else "RR3" if p_mdd<-8 else "RR2"

        st.markdown('<p class="section-header">組合關鍵指標</p>', unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("加權總報酬", f"{p_ret:.2f}%")
        c2.metric("加權最大回撤", f"{p_mdd:.2f}%")
        c3.metric("加權累積配息", f"{p_div:.2f}")
        c4.metric("建議風險等級", rr)

        st.markdown('<p class="section-header">標的對比</p>', unsafe_allow_html=True)
        df_cmp = pd.DataFrame([x for x in [d1,d2,d3] if x]).drop(columns=['df'])
        st.dataframe(df_cmp, use_container_width=True, hide_index=True)

        st.markdown('<p class="section-header">歷史走勢（正規化）</p>', unsafe_allow_html=True)
        nf = {}
        for x in all_d:
            s = x['df'].copy()
            s['date'] = pd.to_datetime(s['date']).dt.normalize()
            s = s.groupby('date')['nav'].last()
            nf[x['名稱']] = (s/s.iloc[0])*100
        st.line_chart(pd.concat(nf, axis=1).dropna(how='all'))

        st.markdown('<p class="section-header">回撤圖</p>', unsafe_allow_html=True)
        if d1:
            dd = d1['df'].copy()
            dd['date'] = pd.to_datetime(dd['date']).dt.normalize()
            dd = dd.groupby('date')['nav'].last()
            st.area_chart((dd - dd.expanding().max()) / dd.expanding().max(), color="#e84040")

        st.markdown('<p class="section-header">定期定額試算</p>', unsafe_allow_html=True)
        pr = d1 or all_d[0]
        dca_df, tc, fv, dca_roi = calculate_dca(pr['df'], monthly_amt)
        col1, col2 = st.columns([1,2])
        with col2:
            fy = st.slider("預測年數", 1, 30, 10)
            er = st.slider("年化報酬率(%)", 0, 20, min(max(int(p_ret),0),20))
        if not dca_df.empty:
            pr_val = fv - tc
            d1c,d2c,d3c,d4c = st.columns(4)
            d1c.metric("總投入", f"${tc:,.0f}")
            d2c.metric("期末價值", f"${fv:,.0f}")
            d3c.metric("盈虧", f"${pr_val:,.0f}", delta=f"{pr_val:,.0f}")
            d4c.metric("DCA 報酬率", f"{dca_roi:.2f}%")
            r = (er/100)/12; n = fy*12
            fval = monthly_amt*(((1+r)**n-1)/r)*(1+r) if r>0 else monthly_amt*n
            st.markdown(f"**🔮 {fy} 年後預期：${fval:,.0f}（年化 {er}%）**")
            st.area_chart(dca_df[['累計投入成本','資產市值']], color=["#4f46e5","#7c3aed"])

        st.markdown('<p class="section-header">系統分析報告</p>', unsafe_allow_html=True)
        advice = get_investment_advice(
            [x['名稱'] for x in all_d], p_ret, p_mdd, dca_roi
        )
        render_ai(advice, "系統分析 · 投資組合")

        pdf_bytes = build_pdf(client_name, [
            {"title": "投資組合摘要", "content": None, "table": df_cmp},
            {"title": "AI 分析報告", "content": strip_md(advice), "table": None},
        ])
        st.download_button("📥 下載 PDF 報告", pdf_bytes,
                           f"投資報告_{client_name}_{time.strftime('%Y%m%d')}.pdf", "application/pdf")

# ═══════════════════════════════════════════════════════
# 模組二：客戶財務健診
# ═══════════════════════════════════════════════════════
elif module == "🏥 客戶財務健診":
    st.subheader("🏥 客戶財務健診報告")
    st.markdown('<p class="section-header">收入與支出</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**💰 月收入來源**")
        salary      = st.number_input("薪資收入（月）", value=80000, step=1000)
        side_income = st.number_input("其他收入（月）", value=5000,  step=1000)
        rental      = st.number_input("租金收入（月）", value=0,     step=1000)
    with col2:
        st.markdown("**💸 月支出項目**")
        living   = st.number_input("生活費（月）", value=30000, step=1000)
        housing  = st.number_input("房貸/房租（月）", value=20000, step=1000)
        insurance_fee = st.number_input("保費（月）", value=5000, step=500)
        other_exp = st.number_input("其他支出（月）", value=10000, step=1000)

    st.markdown('<p class="section-header">資產與負債</p>', unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**🏦 資產**")
        cash        = st.number_input("存款（萬）", value=100, step=10)
        stock_asset = st.number_input("股票/基金（萬）", value=200, step=10)
        real_estate = st.number_input("不動產（萬）", value=1500, step=50)
        other_asset = st.number_input("其他資產（萬）", value=50, step=10)
    with col4:
        st.markdown("**💳 負債**")
        mortgage    = st.number_input("房貸餘額（萬）", value=800, step=50)
        car_loan    = st.number_input("車貸餘額（萬）", value=30, step=10)
        credit_card = st.number_input("信用卡未繳（萬）", value=5, step=1)
        other_debt  = st.number_input("其他負債（萬）", value=0, step=10)

    if st.button("🔍 產生財務健診", key="btn_health"):
        st.session_state.run_health = True

    if st.session_state.run_health:
        total_income  = salary + side_income + rental
        total_expense = living + housing + insurance_fee + other_exp
        monthly_surplus = total_income - total_expense
        total_asset   = (cash + stock_asset + real_estate + other_asset) * 10000
        total_debt    = (mortgage + car_loan + credit_card + other_debt) * 10000
        net_worth     = total_asset - total_debt
        debt_ratio    = (total_debt / total_asset * 100) if total_asset > 0 else 0
        savings_rate  = (monthly_surplus / total_income * 100) if total_income > 0 else 0
        emergency_months = (cash * 10000) / total_expense if total_expense > 0 else 0

        st.markdown('<p class="section-header">財務健診結果</p>', unsafe_allow_html=True)
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("月結餘", f"${monthly_surplus:,.0f}", delta="盈餘" if monthly_surplus>0 else "赤字")
        m2.metric("淨資產", f"${net_worth/10000:,.0f} 萬")
        m3.metric("負債比率", f"{debt_ratio:.1f}%", delta="偏高" if debt_ratio>40 else "健康")
        m4.metric("緊急預備金", f"{emergency_months:.1f} 個月")

        st.markdown('<p class="section-header">收支分析</p>', unsafe_allow_html=True)
        df_income = pd.DataFrame({
            "項目": ["薪資收入","其他收入","租金收入","生活費","房貸/房租","保費","其他支出","月結餘"],
            "金額（元）": [salary, side_income, rental, -living, -housing, -insurance_fee, -other_exp, monthly_surplus]
        })
        st.dataframe(df_income, use_container_width=True, hide_index=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**資產配置**")
            df_asset = pd.DataFrame({"類別":["存款","股票/基金","不動產","其他"],
                                     "金額（萬）":[cash,stock_asset,real_estate,other_asset]})
            st.bar_chart(df_asset.set_index("類別"))
        with col_b:
            st.markdown("**評估指標**")
            indicators = {
                "儲蓄率": (f"{savings_rate:.1f}%", savings_rate >= 20),
                "負債比率": (f"{debt_ratio:.1f}%", debt_ratio <= 40),
                "緊急預備金": (f"{emergency_months:.1f}月", emergency_months >= 6),
                "月度結餘": (f"${monthly_surplus:,.0f}", monthly_surplus > 0),
            }
            for k, (v, ok) in indicators.items():
                badge = '<span class="ok-badge">✓ 健康</span>' if ok else '<span class="gap-badge">⚠ 注意</span>'
                st.markdown(f"**{k}**：{v} {badge}", unsafe_allow_html=True)

        st.markdown('<p class="section-header">系統分析報告</p>', unsafe_allow_html=True)
        advice_h = get_health_advice(monthly_surplus, savings_rate, debt_ratio, emergency_months, net_worth)
        render_ai(advice_h, "系統分析 · 財務健診")

        df_summary = pd.DataFrame({
            "指標": ["月收入","月支出","月結餘","儲蓄率","淨資產","負債比率","緊急預備金"],
            "數值": [f"${total_income:,}", f"${total_expense:,}", f"${monthly_surplus:,}",
                     f"{savings_rate:.1f}%", f"{net_worth/10000:.0f}萬",
                     f"{debt_ratio:.1f}%", f"{emergency_months:.1f}個月"]
        })
        pdf_bytes = build_pdf(client_name, [
            {"title": "財務健診摘要", "content": None, "table": df_summary},
            {"title": "收支明細", "content": None, "table": df_income},
            {"title": "AI 健診建議", "content": strip_md(advice_h), "table": None},
        ])
        st.download_button("📥 下載 PDF 報告", pdf_bytes,
                           f"財務健診_{client_name}_{time.strftime('%Y%m%d')}.pdf", "application/pdf")

# ═══════════════════════════════════════════════════════
# 模組三：保險需求分析
# ═══════════════════════════════════════════════════════
elif module == "🛡️ 保險需求分析":
    st.subheader("🛡️ 保險需求分析")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**基本資料**")
        age         = st.number_input("年齡", value=35, min_value=18, max_value=70)
        gender      = st.selectbox("性別", ["男性","女性"])
        has_spouse  = st.checkbox("已婚", value=True)
        children    = st.number_input("子女數", value=1, min_value=0, max_value=5)
        annual_income = st.number_input("年收入（萬）", value=120, step=10)
        years_to_retire = st.number_input("距退休年數", value=30, step=1)
        # ✅ 新增：房貸負債
        mortgage_debt = st.number_input("房貸餘額（萬）", value=0, step=50, help="壽險需求會加入房貸餘額，確保身故後家人不需承擔負債")
    with col2:
        st.markdown("**現有保障**")
        current_life     = st.number_input("現有壽險保額（萬）", value=500, step=100)
        current_medical  = st.number_input("現有實支實付（萬）", value=30, step=10)
        current_accident = st.number_input("現有意外險（萬）", value=200, step=100)
        current_disable  = st.number_input("現有失能月給付（元）", value=0, step=5000)
        monthly_expense_ins = st.number_input("家庭月支出（元）", value=50000, step=5000)
        # ✅ 新增：失能替代率讓客戶自己調整
        disable_replace_rate = st.slider("失能收入替代率（%）", 40, 80, 60, 5,
            help="失能後每月需要原本支出的多少比例？建議 60%，有房貸可調高至 70~80%") / 100

    if st.button("🔍 計算保障缺口", key="btn_ins"):
        st.session_state.run_insurance = True

    if st.session_state.run_insurance:
        # ✅ 壽險需求 = 年收入 × 剩餘工作年數 × 0.7 + 房貸負債
        life_needed    = int(annual_income * years_to_retire * 0.7) + mortgage_debt
        life_gap       = max(life_needed - current_life, 0)

        # ✅ 醫療：依年齡動態調整建議額度
        if age < 40:
            medical_needed = 50
            medical_note = "（40歲以下建議值）"
        elif age < 55:
            medical_needed = 75
            medical_note = "（40~54歲建議值）"
        else:
            medical_needed = 100
            medical_note = "（55歲以上建議值）"
        medical_gap    = max(medical_needed - current_medical, 0)

        # ✅ 失能：依客戶自訂替代率計算
        disable_needed = int(monthly_expense_ins * disable_replace_rate)
        disable_gap    = max(disable_needed - current_disable, 0)

        # 意外：建議年收入 10 倍
        accident_needed = annual_income * 10
        accident_gap    = max(accident_needed - current_accident, 0)

        st.markdown('<p class="section-header">保障缺口分析</p>', unsafe_allow_html=True)
        g1,g2,g3,g4 = st.columns(4)
        g1.metric("壽險缺口", f"{life_gap} 萬", delta="需補強" if life_gap>0 else "✓ 足夠")
        g2.metric("實支實付缺口", f"{medical_gap} 萬", delta="需補強" if medical_gap>0 else "✓ 足夠")
        g3.metric("失能月給付缺口", f"${disable_gap:,}", delta="需補強" if disable_gap>0 else "✓ 足夠")
        g4.metric("意外險缺口", f"{accident_gap} 萬", delta="需補強" if accident_gap>0 else "✓ 足夠")

        df_ins = pd.DataFrame({
            "險種": ["壽險","醫療實支實付","失能險（月）","意外險"],
            "計算基準": [
                f"年收入{annual_income}萬×{years_to_retire}年×70%+房貸{mortgage_debt}萬",
                f"年齡{age}歲動態建議{medical_note}",
                f"月支出×{int(disable_replace_rate*100)}%替代率",
                f"年收入×10倍"
            ],
            "現有保額": [f"{current_life}萬", f"{current_medical}萬",
                        f"${current_disable:,}", f"{current_accident}萬"],
            "建議保額": [f"{life_needed}萬", f"{medical_needed}萬{medical_note}",
                        f"${disable_needed:,}", f"{accident_needed}萬"],
            "缺口": [f"{life_gap}萬" if life_gap>0 else "✓",
                    f"{medical_gap}萬" if medical_gap>0 else "✓",
                    f"${disable_gap:,}" if disable_gap>0 else "✓",
                    f"{accident_gap}萬" if accident_gap>0 else "✓"],
            "狀態": ["需補強" if x>0 else "足夠" for x in [life_gap, medical_gap, disable_gap, accident_gap]]
        })
        st.dataframe(df_ins, use_container_width=True, hide_index=True)

        st.markdown('<p class="section-header">系統分析報告</p>', unsafe_allow_html=True)
        advice_i = get_insurance_advice(age, life_gap, medical_gap, disable_gap, accident_gap)
        render_ai(advice_i, "系統分析 · 保障需求")

        pdf_bytes = build_pdf(client_name, [
            {"title": "保障缺口分析", "content": None, "table": df_ins},
            {"title": "AI 保障建議", "content": strip_md(advice_i), "table": None},
        ])
        st.download_button("📥 下載 PDF 報告", pdf_bytes,
                           f"保障分析_{client_name}_{time.strftime('%Y%m%d')}.pdf", "application/pdf")

# ═══════════════════════════════════════════════════════
# 模組四：退休金試算
# ═══════════════════════════════════════════════════════
elif module == "🏖️ 退休金試算":
    st.subheader("🏖️ 退休金試算")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**退休規劃參數**")
        current_age    = st.number_input("目前年齡", value=35, min_value=20, max_value=60)
        retire_age     = st.number_input("預計退休年齡", value=65, min_value=50, max_value=75)
        life_expect    = st.number_input("預計壽命", value=90, min_value=70, max_value=100)
        monthly_retire = st.number_input("退休後每月需求（元）", value=50000, step=5000)
        inflation_rate = st.slider("預估通膨率(%)", 1.0, 4.0, 2.0, 0.1)
    with col2:
        st.markdown("**現有退休準備**")
        current_saving   = st.number_input("已累積退休金（萬）", value=100, step=10)
        monthly_save     = st.number_input("每月儲蓄退休金（元）", value=15000, step=1000)
        expected_return  = st.slider("預期年化報酬率(%)", 2.0, 10.0, 5.0, 0.1)
        labor_pension    = st.number_input("預計勞保月領（元）", value=15000, step=1000)
        other_income     = st.number_input("其他退休收入（月）", value=0, step=5000)

    if st.button("🔍 試算退休金缺口", key="btn_retire"):
        st.session_state.run_retirement = True

    if st.session_state.run_retirement:
        years_to_retire = retire_age - current_age
        retire_years    = life_expect - retire_age
        r_monthly = expected_return / 100 / 12
        inf_monthly = inflation_rate / 100 / 12

        # 退休時月支出（通膨調整）
        future_monthly = monthly_retire * ((1 + inflation_rate/100) ** years_to_retire)
        net_monthly_need = max(future_monthly - labor_pension - other_income, 0)

        # 退休所需總額（年金現值）
        if r_monthly > inf_monthly:
            real_r = (r_monthly - inf_monthly)
            total_needed = net_monthly_need * (1 - (1+real_r)**(-retire_years*12)) / real_r
        else:
            total_needed = net_monthly_need * retire_years * 12

        # 累積資產試算
        n = years_to_retire * 12
        future_current = current_saving * 10000 * (1 + expected_return/100) ** years_to_retire
        future_savings  = monthly_save * (((1+r_monthly)**n - 1) / r_monthly) * (1+r_monthly) if r_monthly>0 else monthly_save*n
        total_accumulated = future_current + future_savings
        gap = max(total_needed - total_accumulated, 0)
        gap_monthly = gap / (((1+r_monthly)**n - 1) / r_monthly * (1+r_monthly)) if r_monthly>0 and n>0 else gap/n

        st.markdown('<p class="section-header">退休金試算結果</p>', unsafe_allow_html=True)
        r1,r2,r3,r4 = st.columns(4)
        r1.metric("退休所需總額", f"{total_needed/10000:,.0f} 萬")
        r2.metric("預計累積資產", f"{total_accumulated/10000:,.0f} 萬")
        r3.metric("退休金缺口", f"{gap/10000:,.0f} 萬", delta="需補強" if gap>0 else "✓ 足夠")
        r4.metric("每月需多存", f"${gap_monthly:,.0f}" if gap>0 else "已足夠")

        # 資產累積走勢
        st.markdown('<p class="section-header">資產累積走勢圖</p>', unsafe_allow_html=True)
        years = list(range(0, years_to_retire+1))
        asset_trend = []
        for y in years:
            n_y = y * 12
            fa = current_saving*10000*(1+expected_return/100)**y
            fs = monthly_save*(((1+r_monthly)**n_y-1)/r_monthly)*(1+r_monthly) if r_monthly>0 and n_y>0 else monthly_save*n_y
            asset_trend.append({"年份": f"+{y}年", "累積資產（萬）": (fa+fs)/10000})
        df_trend = pd.DataFrame(asset_trend).set_index("年份")
        st.line_chart(df_trend)

        df_retire = pd.DataFrame({
            "項目": ["退休所需總額","已累積退休金（現值）","退休前預計累積","退休金缺口","每月需多儲蓄"],
            "金額": [f"{total_needed/10000:,.0f}萬",
                    f"{current_saving}萬",
                    f"{total_accumulated/10000:,.0f}萬",
                    f"{gap/10000:,.0f}萬",
                    f"${gap_monthly:,.0f}" if gap>0 else "不需額外增加"]
        })
        st.dataframe(df_retire, use_container_width=True, hide_index=True)

        st.markdown('<p class="section-header">系統分析報告</p>', unsafe_allow_html=True)
        advice_r = get_retirement_advice(current_age, retire_age, gap, gap_monthly, total_needed, total_accumulated, expected_return)
        render_ai(advice_r, "系統分析 · 退休規劃")

        pdf_bytes = build_pdf(client_name, [
            {"title": "退休金試算摘要", "content": None, "table": df_retire},
            {"title": "AI 退休規劃建議", "content": strip_md(advice_r), "table": None},
        ])
        st.download_button("📥 下載 PDF 報告", pdf_bytes,
                           f"退休規劃_{client_name}_{time.strftime('%Y%m%d')}.pdf", "application/pdf")

# ═══════════════════════════════════════════════════════
# 模組五：稅務規劃（綜所稅 + 海外收入 + 遺產贈與稅）
# ═══════════════════════════════════════════════════════
elif module == "🧾 稅務規劃":
    st.subheader("🧾 稅務規劃")

    # 子分頁
    tax_tab1, tax_tab2, tax_tab3 = st.tabs(["📋 綜合所得稅", "🌏 海外收入分析", "🏛️ 遺產與贈與稅"])

    # ── Tab 1：綜合所得稅 ──────────────────────────────────
    with tax_tab1:
        st.markdown("**國內所得資料（年）**")
        col1, col2 = st.columns(2)
        with col1:
            salary_income   = st.number_input("薪資所得（元）", value=1200000, step=10000, key="t1_sal")
            dividend_income = st.number_input("國內股利所得（元）", value=100000, step=10000, key="t1_div")
            rental_income   = st.number_input("租賃所得（元）", value=0, step=10000, key="t1_rent")
            other_income_t  = st.number_input("其他所得（元）", value=0, step=10000, key="t1_other")
        with col2:
            filing_status = st.selectbox("申報方式", ["單身","夫妻合併","夫妻分開"], key="t1_fs")
            dependents    = st.number_input("撫養人數", value=1, min_value=0, max_value=10, key="t1_dep")
            has_elderly   = st.checkbox("撫養70歲以上長輩", value=False, key="t1_eld")
            life_insurance_ded = st.number_input("人壽保險費（元）", value=60000, step=1000, key="t1_ins")
            medical_ded   = st.number_input("醫療費用（元）", value=0, step=1000, key="t1_med")
            mortgage_ded  = st.number_input("房貸利息（元）", value=120000, step=10000, key="t1_mor")

        if st.button("🔍 試算綜合所得稅", key="btn_tax"):
            st.session_state.run_tax = True

        if st.session_state.run_tax:
            SALARY_DED   = 218000
            STANDARD_DED_SINGLE  = 124000
            STANDARD_DED_MARRIED = 248000
            PERSONAL_EXEMPT = 92000

            num_persons = 1 if filing_status=="單身" else 2
            total_exempt = PERSONAL_EXEMPT * (num_persons + dependents)
            if has_elderly:
                total_exempt += PERSONAL_EXEMPT * 0.5

            salary_special_ded = min(salary_income, SALARY_DED)
            standard_ded = STANDARD_DED_MARRIED if filing_status=="夫妻合併" else STANDARD_DED_SINGLE
            itemized_ded = min(life_insurance_ded, 24000) + medical_ded + min(mortgage_ded, 300000)
            deduction = max(standard_ded, itemized_ded)
            use_itemized = itemized_ded > standard_ded

            total_gross = salary_income + dividend_income + rental_income + other_income_t
            net_income  = max(total_gross - total_exempt - salary_special_ded - deduction, 0)

            brackets = [(560000,0.05),(1260000,0.12),(2520000,0.20),(4720000,0.30),(float('inf'),0.40)]
            prev, tax = 0, 0
            for limit, rate in brackets:
                if net_income <= 0: break
                taxable = min(net_income, limit) - prev
                if taxable <= 0:
                    prev = limit; continue
                tax += taxable * rate
                prev = limit
                if net_income <= limit: break

            div_credit = min(dividend_income * 0.085, 80000)
            final_tax  = max(tax - div_credit, 0)
            eff_rate   = final_tax / total_gross * 100 if total_gross > 0 else 0

            st.markdown('<p class="section-header">試算結果</p>', unsafe_allow_html=True)
            t1,t2,t3,t4 = st.columns(4)
            t1.metric("綜合所得總額", f"${total_gross:,.0f}")
            t2.metric("綜合所得淨額", f"${net_income:,.0f}")
            t3.metric("應繳所得稅", f"${final_tax:,.0f}")
            t4.metric("有效稅率", f"{eff_rate:.2f}%")

            df_tax = pd.DataFrame({
                "項目": ["綜合所得總額","免稅額","薪資特別扣除","扣除額（標準/列舉）",
                        "股利可抵減稅額","綜合所得淨額","應繳稅額","有效稅率"],
                "金額": [f"${total_gross:,}", f"${total_exempt:,.0f}", f"${salary_special_ded:,.0f}",
                        f"${deduction:,.0f}（{'列舉' if use_itemized else '標準'}）",
                        f"${div_credit:,.0f}", f"${net_income:,.0f}",
                        f"${final_tax:,.0f}", f"{eff_rate:.2f}%"]
            })
            st.dataframe(df_tax, use_container_width=True, hide_index=True)

            if use_itemized:
                st.success(f"✅ 採列舉扣除額 ${itemized_ded:,.0f}，比標準扣除 ${standard_ded:,.0f} 省更多")
            else:
                st.info(f"ℹ️ 採標準扣除額 ${standard_ded:,.0f}（列舉 ${itemized_ded:,.0f} 較低）")

            st.markdown('<p class="section-header">系統分析報告</p>', unsafe_allow_html=True)
            advice_t = get_tax_advice(total_gross, final_tax, eff_rate, use_itemized, dividend_income, filing_status)
            render_ai(advice_t, "系統分析 · 綜合所得稅")

            pdf_bytes_t = build_pdf(client_name, [
                {"title": "綜合所得稅試算明細", "content": None, "table": df_tax},
                {"title": "節稅建議", "content": strip_md(advice_t), "table": None},
            ])
            st.download_button("📥 下載 PDF 報告", pdf_bytes_t,
                               f"綜所稅_{client_name}_{time.strftime('%Y%m%d')}.pdf", "application/pdf")

    # ── Tab 2：海外收入分析 ────────────────────────────────
    with tax_tab2:
        st.markdown("""
        <div style="background:#eef2ff;border:1px solid #c7d2fe;border-radius:10px;padding:12px 16px;
                    font-size:0.82rem;color:#3730a3;margin-bottom:16px;">
        📌 <b>台灣海外收入課稅說明：</b>台灣採「最低稅負制（AMT）」，海外收入超過 <b>100 萬元</b> 須計入基本所得額，
        基本所得額超過 <b>750 萬元</b> 才需繳納 20% 基本稅額，且與一般所得稅擇高課徵。
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**海外收入（年）**")
            overseas_salary   = st.number_input("海外薪資所得（元）", value=0, step=10000, key="os_sal",
                                                 help="在海外工作取得的薪資，須申報但有免稅額")
            overseas_dividend = st.number_input("海外股利／基金配息（元）", value=0, step=10000, key="os_div",
                                                 help="美股、ETF、海外基金配息等")
            overseas_rental   = st.number_input("海外租金收入（元）", value=0, step=10000, key="os_rent",
                                                 help="在海外持有房產的租金收入")
            overseas_capital  = st.number_input("海外資本利得（元）", value=0, step=10000, key="os_cap",
                                                 help="賣出海外股票、基金等的獲利")
        with col2:
            st.markdown("**國內所得（供比較用）**")
            domestic_income_cmp = st.number_input("國內年所得合計（元）", value=1200000, step=10000, key="dom_inc")
            st.markdown("**已繳海外稅款**")
            overseas_tax_paid = st.number_input("已在海外繳納稅款（元）", value=0, step=10000, key="os_tax",
                                                  help="如美國預扣稅（withholding tax）等，可用來扣抵台灣稅額")

        if st.button("🔍 分析海外收入稅務", key="btn_overseas"):
            st.session_state["run_overseas"] = True

        if st.session_state.get("run_overseas"):
            total_overseas = overseas_salary + overseas_dividend + overseas_rental + overseas_capital

            # 最低稅負制（AMT）計算
            AMT_EXEMPT      = 7500000   # 基本所得額免稅 750 萬
            AMT_RATE        = 0.20      # 基本稅率 20%
            OVERSEAS_EXEMPT = 1000000   # 海外收入免稅門檻 100 萬

            # 計入基本所得額的海外收入（超過 100 萬部分）
            overseas_taxable = max(total_overseas - OVERSEAS_EXEMPT, 0)
            basic_income     = domestic_income_cmp + overseas_taxable

            # 基本稅額
            basic_tax_base = max(basic_income - AMT_EXEMPT, 0)
            basic_tax      = basic_tax_base * AMT_RATE

            # 一般稅額估算（簡化）
            brackets = [(560000,0.05),(1260000,0.12),(2520000,0.20),(4720000,0.30),(float('inf'),0.40)]
            prev, normal_tax = 0, 0
            net_dom = max(domestic_income_cmp - 92000 - min(domestic_income_cmp, 218000) - 124000, 0)
            for limit, rate in brackets:
                if net_dom <= 0: break
                taxable = min(net_dom, limit) - prev
                if taxable > 0:
                    normal_tax += taxable * rate
                prev = limit
                if net_dom <= limit: break

            # 擇高課徵，扣掉已繳海外稅
            final_amt = max(basic_tax - normal_tax, 0)
            additional_tax = max(final_amt - overseas_tax_paid, 0)
            total_tax_burden = normal_tax + additional_tax
            eff_rate_overseas = total_tax_burden / (domestic_income_cmp + total_overseas) * 100 if (domestic_income_cmp + total_overseas) > 0 else 0

            st.markdown('<p class="section-header">海外收入稅務分析</p>', unsafe_allow_html=True)

            # KPI
            o1,o2,o3,o4 = st.columns(4)
            o1.metric("海外收入合計", f"${total_overseas:,.0f}")
            o2.metric("計入基本所得額", f"${overseas_taxable:,.0f}",
                      delta="超過100萬門檻" if overseas_taxable > 0 else "未達門檻免計入")
            o3.metric("最低稅負額", f"${basic_tax:,.0f}",
                      delta="需額外繳納" if additional_tax > 0 else "低於一般稅額")
            o4.metric("綜合有效稅率", f"{eff_rate_overseas:.2f}%")

            # 各類海外收入對比表
            df_overseas = pd.DataFrame({
                "收入類型": ["海外薪資", "海外股利/配息", "海外租金", "海外資本利得", "合計"],
                "金額（元）": [f"${overseas_salary:,}", f"${overseas_dividend:,}",
                              f"${overseas_rental:,}", f"${overseas_capital:,}",
                              f"${total_overseas:,}"],
                "台灣課稅方式": [
                    "併入綜合所得稅，可扣除海外已繳稅",
                    "計入最低稅負制基本所得額",
                    "計入最低稅負制基本所得額",
                    "計入最低稅負制基本所得額",
                    "—"
                ],
                "注意事項": [
                    "需申報，海外工作滿183天可能免稅",
                    "美股配息通常已扣30%預扣稅",
                    "需申報，可扣除費用後計稅",
                    "台灣對海外資本利得課20%最低稅負",
                    "—"
                ]
            })
            st.dataframe(df_overseas, use_container_width=True, hide_index=True)

            # 國內 vs 海外收入結構圖
            st.markdown('<p class="section-header">國內外收入結構比較</p>', unsafe_allow_html=True)
            df_structure = pd.DataFrame({
                "類別": ["國內所得", "海外薪資", "海外股利/配息", "海外租金", "海外資本利得"],
                "金額（萬）": [
                    domestic_income_cmp/10000,
                    overseas_salary/10000,
                    overseas_dividend/10000,
                    overseas_rental/10000,
                    overseas_capital/10000
                ]
            }).set_index("類別")
            st.bar_chart(df_structure)

            # 節稅提示
            st.markdown('<p class="section-header">海外稅務節稅要點</p>', unsafe_allow_html=True)
            tips = []
            if total_overseas < 1000000:
                tips.append("✅ 海外收入未達 100 萬免稅門檻，目前**無需計入最低稅負**，建議維持在此範圍內")
            else:
                tips.append(f"⚠️ 海外收入 ${total_overseas:,} 已超過 100 萬門檻，需計入基本所得額 ${overseas_taxable:,}")
            if overseas_dividend > 0:
                tips.append("💡 美股配息通常已預扣 30% 美國稅，可向台灣國稅局申請扣抵，避免重複課稅")
            if overseas_capital > 0:
                tips.append("💡 海外資本利得可考慮分批實現，避免單年度基本所得額超過 750 萬")
            if overseas_salary > 0:
                tips.append("💡 海外工作連續滿 183 天可能符合非居住者身份，建議諮詢會計師確認申報方式")
            for tip in tips:
                st.markdown(tip)

            pdf_bytes_o = build_pdf(client_name, [
                {"title": "海外收入稅務分析", "content": None, "table": df_overseas},
                {"title": "國內外收入結構", "content": f"國內所得：${domestic_income_cmp:,}\n海外收入合計：${total_overseas:,}\n最低稅負額：${basic_tax:,.0f}\n綜合有效稅率：{eff_rate_overseas:.2f}%", "table": None},
            ])
            st.download_button("📥 下載 PDF 報告", pdf_bytes_o,
                               f"海外收入稅務_{client_name}_{time.strftime('%Y%m%d')}.pdf", "application/pdf")

    # ── Tab 3：遺產與贈與稅 ───────────────────────────────
    with tax_tab3:
        st.markdown("""
        <div style="background:#eef2ff;border:1px solid #c7d2fe;border-radius:10px;padding:12px 16px;
                    font-size:0.82rem;color:#3730a3;margin-bottom:16px;">
        📌 <b>2024年遺產稅：</b>免稅額 <b>1,333 萬元</b>，稅率 10%/15%/20% 三級累進。
        <b>贈與稅：</b>每人每年免稅額 <b>244 萬元</b>，超過部分 10%/15%/20% 累進課徵。
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**遺產試算**")
            total_estate      = st.number_input("遺產總額（萬）", value=3000, step=100,
                                                  help="含不動產、存款、股票、保險、其他資產")
            estate_debt       = st.number_input("負債（萬）", value=500, step=50,
                                                  help="房貸、其他債務可從遺產中扣除")
            funeral_expense   = st.number_input("喪葬費扣除（萬）", value=123, step=10,
                                                  help="2024年固定扣除額 123 萬")
            num_heirs         = st.number_input("繼承人數（直系血親）", value=2, min_value=0, max_value=10,
                                                  help="每位直系血親繼承人可扣除 50 萬")
            has_disabled_heir = st.checkbox("繼承人有身心障礙者", value=False,
                                              help="身心障礙者繼承人可額外扣除 693 萬")
        with col2:
            st.markdown("**贈與稅試算（每年）**")
            gift_amount       = st.number_input("贈與總額（萬）", value=0, step=50,
                                                  help="每人每年 244 萬免稅額")
            gift_persons      = st.number_input("贈與人數（夫妻各自均可贈與）", value=1, min_value=1, max_value=2,
                                                  help="夫妻各自有 244 萬免稅額，合計可達 488 萬/年")
            st.markdown("**保險節稅規劃**")
            life_insurance_value = st.number_input("人壽保險死亡給付（萬）", value=0, step=100,
                                                     help="指定受益人之壽險死亡給付，每位受益人免稅額 3,330 萬")

        if st.button("🔍 試算遺產與贈與稅", key="btn_estate"):
            st.session_state["run_estate"] = True

        if st.session_state.get("run_estate"):
            # ── 遺產稅計算 ──
            ESTATE_EXEMPT    = 1333   # 免稅額 萬
            HEIR_DED         = 50     # 每位直系血親 萬
            DISABLED_DED     = 693    # 身障繼承人 萬
            SPOUSE_DED       = 553    # 配偶扣除額 萬（簡化，若有配偶）

            net_estate = total_estate - estate_debt - funeral_expense
            estate_deduction = (HEIR_DED * num_heirs) + (DISABLED_DED if has_disabled_heir else 0)
            taxable_estate = max(net_estate - ESTATE_EXEMPT - estate_deduction, 0)

            # 遺產稅三級累進（萬為單位）
            estate_brackets = [(5000, 0.10), (10000, 0.15), (float('inf'), 0.20)]
            prev_e, estate_tax = 0, 0
            for limit, rate in estate_brackets:
                if taxable_estate <= 0: break
                taxable = min(taxable_estate, limit) - prev_e
                if taxable > 0:
                    estate_tax += taxable * rate
                prev_e = limit
                if taxable_estate <= limit: break

            # 壽險免稅額
            insurance_exempt_per = 3330  # 每位受益人萬
            insurance_exempt_total = min(life_insurance_value, insurance_exempt_per)
            effective_estate_after_ins = max(taxable_estate - max(life_insurance_value - insurance_exempt_total, 0) * 0, taxable_estate)

            # ── 贈與稅計算 ──
            GIFT_EXEMPT_PER = 244  # 每人每年免稅額 萬
            total_gift_exempt = GIFT_EXEMPT_PER * gift_persons
            taxable_gift = max(gift_amount - total_gift_exempt, 0)

            gift_brackets = [(2500, 0.10), (5000, 0.15), (float('inf'), 0.20)]
            prev_g, gift_tax = 0, 0
            for limit, rate in gift_brackets:
                if taxable_gift <= 0: break
                taxable = min(taxable_gift, limit) - prev_g
                if taxable > 0:
                    gift_tax += taxable * rate
                prev_g = limit
                if taxable_gift <= limit: break

            # ── 顯示結果 ──
            st.markdown('<p class="section-header">遺產稅試算</p>', unsafe_allow_html=True)
            e1,e2,e3,e4 = st.columns(4)
            e1.metric("遺產淨額", f"{net_estate:,.0f} 萬")
            e2.metric("課稅遺產淨額", f"{taxable_estate:,.0f} 萬")
            e3.metric("應納遺產稅", f"{estate_tax:,.0f} 萬",
                      delta="需規劃節稅" if estate_tax > 0 else "免稅")
            e4.metric("遺產稅率級距",
                      "20%" if taxable_estate > 10000 else "15%" if taxable_estate > 5000 else "10%" if taxable_estate > 0 else "免稅")

            df_estate = pd.DataFrame({
                "項目": ["遺產總額","負債扣除","喪葬費扣除","遺產免稅額（1,333萬）",
                         f"繼承人扣除（{num_heirs}人×50萬）",
                         "身障繼承人加扣" if has_disabled_heir else "身障加扣（無）",
                         "課稅遺產淨額","應納遺產稅"],
                "金額（萬）": [
                    f"{total_estate:,}", f"-{estate_debt:,}", f"-{funeral_expense:,}",
                    f"-{ESTATE_EXEMPT:,}", f"-{HEIR_DED * num_heirs:,}",
                    f"-{DISABLED_DED}" if has_disabled_heir else "0",
                    f"{taxable_estate:,.0f}", f"{estate_tax:,.0f}"
                ]
            })
            st.dataframe(df_estate, use_container_width=True, hide_index=True)

            st.markdown('<p class="section-header">贈與稅試算</p>', unsafe_allow_html=True)
            g1,g2,g3 = st.columns(3)
            g1.metric("贈與總額", f"{gift_amount:,} 萬")
            g2.metric(f"免稅額（{gift_persons}人×244萬）", f"{total_gift_exempt:,} 萬")
            g3.metric("應納贈與稅", f"{gift_tax:,.0f} 萬",
                      delta="需注意" if gift_tax > 0 else "免稅")

            # ── 壽險節稅分析 ──
            if life_insurance_value > 0:
                st.markdown('<p class="section-header">壽險節稅分析</p>', unsafe_allow_html=True)
                st.info(f"""
                💡 **壽險死亡給付節稅效果**
                - 指定受益人的壽險給付 **不計入遺產**，每位受益人享有 **3,330 萬免稅額**
                - 您設定的壽險保額 **{life_insurance_value:,} 萬**，可讓受益人免稅領取
                - 若改用遺產繼承，同等金額需繳納遺產稅約 **{min(life_insurance_value * 0.10, life_insurance_value * 0.20):,.0f} 萬**
                - 建議以保險規劃傳承，節稅效果顯著 ✅
                """)

            # ── 遺產 vs 逐年贈與比較 ──
            st.markdown('<p class="section-header">遺產稅 vs 逐年贈與規劃比較</p>', unsafe_allow_html=True)
            years_plan = 10
            gift_per_year = GIFT_EXEMPT_PER * 2  # 夫妻各自贈與
            total_gift_10y = gift_per_year * years_plan
            remaining_estate = max(total_estate - total_gift_10y, 0)
            remaining_net = max(remaining_estate - estate_debt - funeral_expense - ESTATE_EXEMPT - estate_deduction, 0)
            prev_r, remaining_tax = 0, 0
            for limit, rate in estate_brackets:
                if remaining_net <= 0: break
                taxable = min(remaining_net, limit) - prev_r
                if taxable > 0:
                    remaining_tax += taxable * rate
                prev_r = limit
                if remaining_net <= limit: break

            df_compare = pd.DataFrame({
                "方案": ["現在全部留遺產", f"夫妻各自每年贈與{gift_per_year}萬（持續{years_plan}年）"],
                "稅負（萬）": [f"{estate_tax:,.0f}", f"{remaining_tax:,.0f}"],
                "可移轉財產（萬）": [
                    f"{total_estate - estate_tax:,.0f}",
                    f"{total_estate - remaining_tax:,.0f}"
                ],
                "節稅效果": ["基準", f"可節省約 {max(estate_tax - remaining_tax, 0):,.0f} 萬"]
            })
            st.dataframe(df_compare, use_container_width=True, hide_index=True)

            # 節稅建議文字
            st.markdown('<p class="section-header">節稅規劃建議</p>', unsafe_allow_html=True)
            advice_estate = f"""【遺產與贈與稅規劃報告】

一、遺產稅現況
客戶遺產總額 {total_estate:,} 萬元，扣除負債與各項扣除後，課稅遺產淨額為 {taxable_estate:,.0f} 萬元，應納遺產稅約 {estate_tax:,.0f} 萬元。{"目前遺產規模已達須積極規劃節稅的門檻。" if estate_tax > 0 else "目前遺產規模在免稅範圍內，暫無遺產稅壓力。"}

二、逐年贈與規劃
夫妻各自每年可贈與 244 萬（合計 488 萬）且免稅。持續 10 年可移轉 {gift_per_year * years_plan:,} 萬資產，有效降低未來遺產稅基，預計可節省遺產稅約 {max(estate_tax - remaining_tax, 0):,.0f} 萬元。

三、壽險節稅策略
{"指定受益人的壽險給付不計入遺產，每位受益人享有 3,330 萬免稅額，是最有效的傳承工具之一。建議將部分資產轉換為壽險保額，兼顧保障與節稅。" if life_insurance_value == 0 else f"現有壽險保額 {life_insurance_value:,} 萬，可讓受益人免稅傳承，節稅效果顯著。建議持續維持並適時調高保額。"}

四、建議優先行動
• 每年善用夫妻各 244 萬贈與免稅額，儘早移轉資產
• 考慮以不動產信託規劃，減少遺產糾紛
• 壽險受益人務必指定，避免給付計入遺產
• 每 3 年重新評估遺產規模，適時調整規劃

五、免責聲明
本試算依現行稅法，實際稅額以國稅局核定為準。重大稅務決策請諮詢專業會計師或律師。"""

            render_ai(advice_estate, "系統分析 · 遺產規劃")

            pdf_bytes_e = build_pdf(client_name, [
                {"title": "遺產稅試算", "content": None, "table": df_estate},
                {"title": "方案比較", "content": None, "table": df_compare},
                {"title": "節稅規劃建議", "content": strip_md(advice_estate), "table": None},
            ])
            st.download_button("📥 下載 PDF 報告", pdf_bytes_e,
                               f"遺產規劃_{client_name}_{time.strftime('%Y%m%d')}.pdf", "application/pdf")


# ═══════════════════════════════════════════════════════
# 模組六：信貸投資套利試算
# ═══════════════════════════════════════════════════════
elif module == "💳 信貸投資套利":
    st.subheader("💳 信貸投資套利試算")
    st.markdown("""
    <div style="background:#eef2ff;border:1px solid #c7d2fe;border-radius:10px;padding:12px 16px;
                font-size:0.82rem;color:#3730a3;margin-bottom:16px;">
    📌 <b>套利原理：</b>向銀行借取低利率信貸，將資金投入預期報酬率較高的基金或ETF，賺取利差。
    此策略有風險，市場報酬不保證，虧損時仍需還款。請審慎評估風險承受度。
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**信貸條件**")
        loan_amount = st.number_input("貸款金額（元）", value=1000000, step=50000, key="cl_amt")
        loan_rate   = st.slider("信貸年利率（%）", 1.0, 8.0, 2.5, 0.1, key="cl_rate")
        loan_years  = st.number_input("貸款年期（年）", value=7, min_value=1, max_value=10, key="cl_yr")
    with col2:
        st.markdown("**投資設定**")
        inv_amount  = st.number_input("實際投資金額（元）", value=1000000, step=50000, key="cl_inv",
                                       help="通常等於貸款金額")
        st.markdown("**投資標的配置（1～3個，比例合計需為100%）**")
        cl_num = st.radio("標的數量", [1, 2, 3], index=1, horizontal=True, key="cl_num")
        defaults_cl_name = ["006208 富邦台50", "安聯收益成長", "統一奔騰基金"]
        defaults_cl_type = ["ETF/股票", "基金", "基金"]
        defaults_cl_id   = ["006208", "B2abw8B", "B090460"]
        defaults_cl_pct  = [50, 50, 0] if cl_num == 2 else ([100, 0, 0] if cl_num == 1 else [40, 30, 30])
        cl_targets = []
        for i in range(cl_num):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            with c1: t = st.text_input(f"標的{i+1}名稱", value=defaults_cl_name[i], key=f"cl_t{i}")
            with c2: tid = st.text_input(f"代碼{i+1}", value=defaults_cl_id[i], key=f"cl_tid{i}")
            with c3: ttype = st.selectbox(f"類型{i+1}", ["ETF/股票","基金"], index=["ETF/股票","基金"].index(defaults_cl_type[i]), key=f"cl_tt{i}", label_visibility="collapsed")
            with c4: p = st.number_input(f"比例{i+1}%", value=defaults_cl_pct[i], min_value=0, max_value=100, key=f"cl_p{i}", label_visibility="collapsed")
            cl_targets.append((t, tid, ttype, p))

        total_cl_pct = sum(x[3] for x in cl_targets)
        if total_cl_pct == 100:
            st.success(f"✅ 比例合計 {total_cl_pct}%")
        else:
            st.warning(f"⚠️ 比例合計 {total_cl_pct}%，請調整至 100%")

    if total_cl_pct == 100:
        # ── 各標的設定：區分配息型 vs 成長型 ──
        st.markdown('<p class="section-header">標的報酬率設定</p>', unsafe_allow_html=True)
        st.caption("配息型：有月配息現金流（如安聯收益成長）；成長型：只有資產增值（如0050 ETF）")
        cagr_results = []
        weighted_return  = 0   # 加權報酬率（計算資產終值）
        monthly_dividend = 0   # 配息型每月配息總額

        for name, tid, ttype, pct in cl_targets:
            ctype = "基金" if ttype == "基金" else "股票"
            cagr, label = get_cagr(tid, ctype)
            if cagr is None:
                suggested = 7.0
                cagr_display = "無法取得"
            else:
                suggested = round(max(min(cagr, 12.0), 0.0), 1)
                cagr_display = f"{cagr:.2f}%"
                if cagr > 15:
                    st.warning(f"⚠️ {name} 近3年CAGR {cagr:.1f}% 偏高，已建議保守值 {suggested}%")
                elif cagr < 0:
                    st.warning(f"⚠️ {name} 近3年CAGR {cagr:.1f}% 為負值，建議手動輸入合理預期值")

            c1, c2 = st.columns([4, 1])
            with c1:
                exp = st.number_input(
                    f"{name}（{tid}）近3年CAGR：{cagr_display} — 預期年化報酬率（%）",
                    value=float(suggested), min_value=0.0, max_value=30.0, step=0.5,
                    key=f"cl_exp_{tid}"
                )
            with c2:
                is_dividend = st.selectbox(
                    "類型", ["配息型", "成長型"],
                    index=0 if ttype == "基金" else 1,
                    key=f"cl_div_{tid}",
                    label_visibility="collapsed"
                )
            cagr_results.append((name, tid, pct, cagr_display, exp, is_dividend))
            weighted_return += exp * pct / 100
            if is_dividend == "配息型":
                monthly_dividend += (inv_amount * pct / 100) * (exp / 100 / 12)

        df_cagr = pd.DataFrame({
            "標的": [x[0] for x in cagr_results],
            "代碼": [x[1] for x in cagr_results],
            "比例": [f"{x[2]}%" for x in cagr_results],
            "近3年CAGR": [x[3] for x in cagr_results],
            "預期報酬率": [f"{x[4]:.1f}%" for x in cagr_results],
            "類型": [x[5] for x in cagr_results],
        })
        st.dataframe(df_cagr, use_container_width=True, hide_index=True)
        st.info(f"組合加權報酬率：**{weighted_return:.2f}%**　｜　配息型月現金流：**${monthly_dividend:,.0f}**")

        # 套利計算
        r_monthly = loan_rate / 100 / 12
        n_months  = loan_years * 12
        monthly_payment = loan_amount * r_monthly / (1 - (1 + r_monthly) ** (-n_months))
        total_payment   = monthly_payment * n_months
        total_interest  = total_payment - loan_amount
        final_inv_val   = inv_amount * (1 + weighted_return/100) ** loan_years
        net_profit  = final_inv_val - total_payment
        arb_spread  = weighted_return - loan_rate

        st.markdown('<p class="section-header">套利試算結果</p>', unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("每月還款額", f"${monthly_payment:,.0f}")
        k2.metric("利率差（套利空間）", f"{arb_spread:.1f}%",
                  delta="正套利" if arb_spread > 0 else "負套利，不建議")
        k3.metric(f"{loan_years}年後投資終值", f"${final_inv_val:,.0f}")
        k4.metric("扣除還款後淨利", f"${net_profit:,.0f}",
                  delta="獲利" if net_profit > 0 else "虧損")

        # ── 走勢圖：依使用者設定的預期報酬率與貸款條件 ──
        st.markdown('<p class="section-header">資產 vs 負債走勢（依設定條件）</p>', unsafe_allow_html=True)
        st.caption("藍線：投資資產（依上方設定的預期報酬率複利成長）；紅線：信貸負債餘額（依利率逐月遞減）")
        trend_data = []
        for y in range(loan_years + 1):
            paid_months = y * 12
            if r_monthly > 0 and paid_months > 0:
                remaining_debt = loan_amount * (1+r_monthly)**paid_months - monthly_payment * ((1+r_monthly)**paid_months-1) / r_monthly
            else:
                remaining_debt = loan_amount
            remaining_debt = max(remaining_debt, 0)
            inv_val = inv_amount * (1 + weighted_return/100) ** y
            trend_data.append({"年份": y, "投資資產價值": inv_val, "信貸負債餘額": remaining_debt})
        df_trend = pd.DataFrame(trend_data).set_index("年份")
        df_trend.index.name = "年（第N年）"
        st.line_chart(df_trend, color=["#4f46e5","#e84040"])

        df_credit = pd.DataFrame({
            "項目": ["貸款金額","信貸年利率","貸款年期","每月還款額",
                     "總還款金額","總利息支出","組合加權報酬率",
                     f"{loan_years}年後投資終值","套利淨利潤","建議"],
            "數值": [f"${loan_amount:,}", f"{loan_rate}%", f"{loan_years}年",
                    f"${monthly_payment:,.0f}", f"${total_payment:,.0f}",
                    f"${total_interest:,.0f}", f"{weighted_return:.2f}%",
                    f"${final_inv_val:,.0f}", f"${net_profit:,.0f}",
                    "✅ 正套利，可考慮執行" if arb_spread > 2 else
                    "⚠️ 利差偏小，需謹慎評估" if arb_spread > 0 else "❌ 負套利，不建議"]
        })
        st.dataframe(df_credit, use_container_width=True, hide_index=True)

        advice_credit = f"""【信貸投資套利分析報告】

一、套利空間評估
信貸利率 {loan_rate}%，組合加權年化報酬率 {weighted_return:.2f}%（依各標的近3年實際CAGR加權），
利差為 {arb_spread:.1f}%。{"具備正套利空間。" if arb_spread > 0 else "目前不具備套利空間，不建議執行。"}

二、現金流壓力分析
每月需還款 ${monthly_payment:,.0f}，{loan_years}年共還款 ${total_payment:,.0f}，其中利息 ${total_interest:,.0f}。
建議此金額不超過月收入的 30%。

三、風險提醒
• 上述CAGR為過去績效，不代表未來報酬
• 信貸到期仍需還款，無論投資盈虧
• 建議選擇波動較低的標的降低風險
• 緊急預備金需維持 6 個月生活費不可動用

四、免責聲明
本試算僅供參考，請在充分了解風險後再做決策。"""

        st.markdown('<p class="section-header">系統分析報告</p>', unsafe_allow_html=True)
        render_ai(advice_credit, "系統分析 · 信貸套利")

        pdf_bytes_c = build_pdf(client_name, [
            {"title": "標的報酬率", "content": None, "table": df_cagr},
            {"title": "信貸套利試算", "content": None, "table": df_credit},
            {"title": "分析報告", "content": strip_md(advice_credit), "table": None},
        ])
        st.download_button("📥 下載 PDF 報告", pdf_bytes_c,
                           f"信貸套利_{client_name}_{time.strftime('%Y%m%d')}.pdf", "application/pdf")


# ═══════════════════════════════════════════════════════
# 模組七：房貸減壓分析
# ═══════════════════════════════════════════════════════
elif module == "🏠 房貸減壓分析":
    st.subheader("🏠 房貸減壓套利分析")
    st.markdown("""
    <div style="background:#eef2ff;border:1px solid #c7d2fe;border-radius:10px;padding:12px 16px;
                font-size:0.82rem;color:#3730a3;margin-bottom:16px;">
    📌 <b>策略說明：</b>透過轉增貸或理財型房貸，將部分房屋淨值變現投入市場，
    以投資配息補貼房貸月付款，改善每月現金流壓力。
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**1. 原房貸狀況**")
        orig_loan_bal = st.number_input("原房貸餘額（萬）", value=800, step=50, key="hl_bal")
        orig_monthly  = st.number_input("原每月還款額（元）", value=32000, step=1000, key="hl_pay")
        st.markdown("**2. 轉增貸 / 新房貸方案**")
        st.markdown("**本利攤還型**")
        hc1, hc2, hc3 = st.columns(3)
        with hc1: new_loan_a  = st.number_input("金額（萬）", value=800, step=50, key="hl_a_amt")
        with hc2: new_rate_a  = st.number_input("利率（%）", value=2.1, step=0.1, key="hl_a_rate", format="%.1f")
        with hc3: new_years_a = st.number_input("年期", value=30, step=1, key="hl_a_yr")
        st.markdown("**理財型（寬限期）**")
        hd1, hd2, hd3 = st.columns(3)
        with hd1: new_loan_b  = st.number_input("金額（萬）", value=0, step=50, key="hl_b_amt")
        with hd2: new_rate_b  = st.number_input("利率（%）", value=2.5, step=0.1, key="hl_b_rate", format="%.1f")
        with hd3: new_years_b = st.number_input("寬限年期", value=5, step=1, key="hl_b_yr")
    with col2:
        st.markdown("**3. 投資設定**")
        st.caption("請在各標的欄位填入實際投入金額，系統自動加總")
        st.markdown("**投資標的（1～3個，比例合計需為100%）**")
        hl_num = st.radio("標的數量", [1, 2, 3], index=1, horizontal=True, key="hl_num")
        defaults_hl_name = ["006208 富邦台50", "安聯收益成長", "統一奔騰基金"]
        defaults_hl_type = ["ETF/股票", "基金", "基金"]
        defaults_hl_id   = ["006208", "B2abw8B", "B090460"]
        defaults_hl_pct  = [50, 50, 0] if hl_num == 2 else ([100, 0, 0] if hl_num == 1 else [40, 30, 30])
        hl_targets = []
        for i in range(hl_num):
            h1, h2, h3, h4 = st.columns([2, 1, 1, 1])
            with h1: t = st.text_input(f"標的{i+1}名稱", value=defaults_hl_name[i], key=f"hl_t{i}")
            with h2: tid = st.text_input(f"代碼{i+1}", value=defaults_hl_id[i], key=f"hl_tid{i}")
            with h3: ttype = st.selectbox(f"類型{i+1}", ["ETF/股票","基金"], index=["ETF/股票","基金"].index(defaults_hl_type[i]), key=f"hl_tt{i}", label_visibility="collapsed")
            with h4: p = st.number_input(f"比例{i+1}%", value=defaults_hl_pct[i], min_value=0, max_value=100, key=f"hl_p{i}", label_visibility="collapsed")
            hl_targets.append((t, tid, ttype, p))
        inv_total_hl = 0  # 佔位用，實際金額由各標的 inv_this 決定

        total_hl_pct = sum(x[3] for x in hl_targets)
        if total_hl_pct == 100:
            st.success(f"✅ 比例合計 {total_hl_pct}%")
        else:
            st.warning(f"⚠️ 比例合計 {total_hl_pct}%，請調整至 100%")

    if total_hl_pct == 100:
        # ── 各標的設定：區分配息型 vs 成長型 ──
        st.markdown('<p class="section-header">標的報酬率設定</p>', unsafe_allow_html=True)
        st.caption("請分別設定各標的的年化報酬率與類型（配息型可產生每月現金流；成長型只有資產增值）")

        hl_cagr_results = []
        hl_growth_return   = 0   # 成長型加權報酬率（用於資產終值）
        hl_dividend_income = 0   # 配息型每月配息總額

        for name, tid, ttype, pct in hl_targets:
            ctype = "基金" if ttype == "基金" else "股票"
            cagr, label = get_cagr(tid, ctype)
            if cagr is None:
                suggested = 6.0
                cagr_display = "無法取得"
            else:
                suggested = round(max(min(cagr, 12.0), 0.0), 1)
                cagr_display = f"{cagr:.2f}%"
                if cagr > 15:
                    st.warning(f"⚠️ {name} 近3年CAGR {cagr:.1f}% 偏高，已建議保守值 {suggested}%")
                elif cagr < 0:
                    st.warning(f"⚠️ {name} 近3年CAGR {cagr:.1f}% 為負值，建議手動輸入合理預期值")

            r1, r2, r3 = st.columns([3, 1, 1])
            with r1:
                exp = st.number_input(
                    f"{name}（{tid}）近3年CAGR：{cagr_display} — 預期年化報酬率（%）",
                    value=float(suggested), min_value=0.0, max_value=30.0, step=0.5,
                    key=f"hl_exp_{tid}"
                )
            with r2:
                is_dividend = st.selectbox(
                    "類型", ["配息型", "成長型"],
                    index=0 if ttype == "基金" else 1,
                    key=f"hl_div_{tid}",
                    help="配息型：有月配息；成長型：無配息只有增值"
                )
            with r3:
                inv_this = st.number_input(
                    "投入（萬）",
                    value=int(100 * pct / 100) if pct > 0 else 0,
                    min_value=0, step=50,
                    key=f"hl_inv_{tid}",
                    label_visibility="visible"
                )

            hl_cagr_results.append((name, tid, pct, cagr_display, exp, is_dividend, inv_this))

            # 成長型：貢獻到整體資產終值報酬率
            hl_growth_return += exp * pct / 100

            # 配息型：貢獻月配息
            if is_dividend == "配息型":
                hl_dividend_income += (inv_this * 10000) * (exp / 100 / 12)

        # 整體資產終值用加權報酬率
        hl_weighted_return = hl_growth_return
        inv_total_actual = sum(x[6] for x in hl_cagr_results)  # 實際總投資（萬）

        df_hl_cagr = pd.DataFrame({
            "標的": [x[0] for x in hl_cagr_results],
            "代碼": [x[1] for x in hl_cagr_results],
            "比例": [f"{x[2]}%" for x in hl_cagr_results],
            "近3年CAGR": [x[3] for x in hl_cagr_results],
            "預期報酬率": [f"{x[4]:.1f}%" for x in hl_cagr_results],
            "類型": [x[5] for x in hl_cagr_results],
            "投入（萬）": [x[6] for x in hl_cagr_results],
        })
        st.dataframe(df_hl_cagr, use_container_width=True, hide_index=True)
        st.info(f"配息型每月預估現金流：**${hl_dividend_income:,.0f}**　｜　投資組合加權報酬率：**{hl_weighted_return:.2f}%**")

        # ── 月付計算 ──
        r_a = new_rate_a / 100 / 12
        n_a = new_years_a * 12
        monthly_a = (new_loan_a*10000)*r_a/(1-(1+r_a)**(-n_a)) if r_a>0 and n_a>0 else 0

        # 理財型：寬限期只付利息，寬限期後本利攤還
        r_b = new_rate_b / 100 / 12
        monthly_b_interest = (new_loan_b*10000) * r_b if new_loan_b > 0 else 0
        n_b_after = max((new_years_a - new_years_b) * 12, 0)
        monthly_b_full = (new_loan_b*10000)*r_b/(1-(1+r_b)**(-n_b_after)) if r_b>0 and n_b_after>0 and new_loan_b>0 else 0

        total_new_monthly_grace = monthly_a + monthly_b_interest   # 寬限期內
        total_new_monthly_after = monthly_a + monthly_b_full        # 寬限期後
        monthly_diff_grace = orig_monthly - total_new_monthly_grace
        monthly_diff_after = orig_monthly - total_new_monthly_after

        # 現金流改善 = 月付節省 + 配息收入
        net_flow_grace = monthly_diff_grace + hl_dividend_income
        net_flow_after = monthly_diff_after + hl_dividend_income
        inv_final_10y  = (inv_total_actual * 10000) * (1 + hl_weighted_return/100) ** 10

        st.markdown('<p class="section-header">房貸減壓試算結果</p>', unsafe_allow_html=True)

        # 原房貸 vs 新方案比較
        st.markdown("**月付款比較**")
        cmp1, cmp2, cmp3 = st.columns(3)
        cmp1.metric("原房貸月付", f"${orig_monthly:,}")
        cmp2.metric("新方案（寬限期內）", f"${total_new_monthly_grace:,.0f}",
                    delta=f"{'節省' if monthly_diff_grace>=0 else '增加'} ${abs(monthly_diff_grace):,.0f}")
        cmp3.metric("新方案（寬限期後）", f"${total_new_monthly_after:,.0f}",
                    delta=f"{'節省' if monthly_diff_after>=0 else '增加'} ${abs(monthly_diff_after):,.0f}")

        st.markdown("**現金流改善（含配息）**")
        h1c, h2c, h3c, h4c = st.columns(4)
        h1c.metric("配息型月現金流", f"${hl_dividend_income:,.0f}",
                   help="配息型標的每月預估配息收入")
        h2c.metric("寬限期現金流改善", f"${net_flow_grace:,.0f}",
                   delta="✓ 減壓" if net_flow_grace>0 else "⚠ 負擔增加")
        h3c.metric("寬限期後現金流改善", f"${net_flow_after:,.0f}",
                   delta="✓ 減壓" if net_flow_after>0 else "⚠ 負擔增加")
        h4c.metric("10年後投資終值", f"${inv_final_10y:,.0f}")

        # ── 走勢圖：30年（含寬限期切換）──
        st.markdown('<p class="section-header">資產 vs 房貸負債走勢（30年）</p>', unsafe_allow_html=True)
        st.caption("藍線：投資資產複利成長；紅線：房貸負債餘額（寬限期後本金開始下降）")
        cf_data = []
        for y in range(31):
            inv_val = (inv_total_actual * 10000) * (1 + hl_weighted_return/100) ** y
            paid_m  = y * 12

            # 本利攤還負債
            if r_a > 0 and paid_m > 0:
                rem_a2 = (new_loan_a*10000)*(1+r_a)**paid_m - monthly_a*((1+r_a)**paid_m-1)/r_a
            else:
                rem_a2 = new_loan_a * 10000
            rem_a2 = max(rem_a2, 0)

            # 理財型：寬限期內本金不動，寬限期後開始攤還
            if new_loan_b > 0:
                grace_months = new_years_b * 12
                if paid_m <= grace_months:
                    rem_b2 = new_loan_b * 10000
                else:
                    extra_m = paid_m - grace_months
                    rem_b2 = (new_loan_b*10000)*(1+r_b)**extra_m - monthly_b_full*((1+r_b)**extra_m-1)/r_b if r_b>0 else new_loan_b*10000
                    rem_b2 = max(rem_b2, 0)
            else:
                rem_b2 = 0

            cf_data.append({"年": y, "投資資產": inv_val, "房貸負債": rem_a2 + rem_b2})

        df_cf = pd.DataFrame(cf_data).set_index("年")
        st.line_chart(df_cf, color=["#4f46e5","#e84040"])

        # ── 明細表 ──
        df_house = pd.DataFrame({
            "項目": ["原房貸月付", "新方案月付（本利攤）",
                     f"理財型月付（寬限期 {new_years_b} 年內）",
                     f"理財型月付（寬限期後）",
                     "寬限期現金流改善（含配息）", "寬限期後現金流改善（含配息）",
                     "配息型月配息", "總投資金額", "10年後投資終值"],
            "金額": [
                f"${orig_monthly:,}",
                f"${monthly_a:,.0f}",
                f"${monthly_b_interest:,.0f}（只付利息）",
                f"${monthly_b_full:,.0f}（本利攤還）",
                f"${net_flow_grace:,.0f}",
                f"${net_flow_after:,.0f}",
                f"${hl_dividend_income:,.0f}",
                f"${inv_total_actual*10000:,}",
                f"${inv_final_10y:,.0f}"
            ]
        })
        st.dataframe(df_house, use_container_width=True, hide_index=True)

        advice_house = f"""【房貸減壓套利分析報告】

一、策略概述
原房貸月付 ${orig_monthly:,} 元。新方案月付 ${total_new_monthly:,.0f} 元，
{"每月節省 $" + f"{abs(monthly_diff):,.0f}" if monthly_diff>=0 else "月付增加 $" + f"{abs(monthly_diff):,.0f}"}。

二、投資配息補貼效果
投資 {inv_total_actual} 萬，組合加權報酬率 {hl_weighted_return:.2f}%（依各標的近3年實際CAGR），
預估每月配息 ${inv_monthly_income:,.0f}，每月現金流淨改善 ${net_monthly_flow:,.0f} 元。

三、長期展望
10年後投資終值預估 ${inv_final_10y:,.0f} 元。

四、風險提醒
• CAGR為過去績效，不代表未來表現
• 理財型寬限期結束後月付將大幅增加，需提前規劃
• 轉增貸會增加房屋抵押風險

五、免責聲明
本試算依過去數據估算，實際結果以市場表現為準。"""

        st.markdown('<p class="section-header">系統分析報告</p>', unsafe_allow_html=True)
        render_ai(advice_house, "系統分析 · 房貸減壓")

        pdf_bytes_h = build_pdf(client_name, [
            {"title": "標的報酬率", "content": None, "table": df_hl_cagr},
            {"title": "房貸減壓試算", "content": None, "table": df_house},
            {"title": "分析報告", "content": strip_md(advice_house), "table": None},
        ])
        st.download_button("📥 下載 PDF 報告", pdf_bytes_h,
                           f"房貸減壓_{client_name}_{time.strftime('%Y%m%d')}.pdf", "application/pdf")
