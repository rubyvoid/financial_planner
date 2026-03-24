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
# 模組五：稅務規劃
# ═══════════════════════════════════════════════════════
elif module == "🧾 稅務規劃":
    st.subheader("🧾 稅務規劃（台灣綜合所得稅）")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**所得資料（年）**")
        salary_income   = st.number_input("薪資所得（元）", value=1200000, step=10000)
        dividend_income = st.number_input("股利所得（元）", value=100000, step=10000)
        rental_income   = st.number_input("租賃所得（元）", value=0, step=10000)
        other_income_t  = st.number_input("其他所得（元）", value=0, step=10000)
    with col2:
        st.markdown("**扣除額**")
        filing_status = st.selectbox("申報方式", ["單身","夫妻合併","夫妻分開"])
        dependents    = st.number_input("撫養人數", value=1, min_value=0, max_value=10)
        has_elderly   = st.checkbox("撫養70歲以上長輩", value=False)
        life_insurance_ded = st.number_input("人壽保險費（元）", value=60000, step=1000)
        medical_ded   = st.number_input("醫療費用（元）", value=0, step=1000)
        mortgage_ded  = st.number_input("房貸利息（元）", value=120000, step=10000)

    if st.button("🔍 試算所得稅", key="btn_tax"):
        st.session_state.run_tax = True

    if st.session_state.run_tax:
        # 2024年台灣綜合所得稅參數
        BASIC_EXEMPT = 92000       # 基本免稅額
        SALARY_DED   = 218000      # 薪資特別扣除額
        STANDARD_DED_SINGLE  = 124000
        STANDARD_DED_MARRIED = 248000
        PERSONAL_EXEMPT = 92000

        # 免稅額
        num_persons = 1 if filing_status=="單身" else 2
        total_exempt = PERSONAL_EXEMPT * num_persons
        total_exempt += PERSONAL_EXEMPT * dependents
        if has_elderly:
            total_exempt += PERSONAL_EXEMPT * 0.5  # 加倍扣除

        # 薪資特扣
        salary_special_ded = min(salary_income, SALARY_DED)

        # 標準 vs 列舉
        standard_ded = STANDARD_DED_MARRIED if filing_status=="夫妻合併" else STANDARD_DED_SINGLE
        itemized_ded = min(life_insurance_ded, 24000) + medical_ded + mortgage_ded
        deduction = max(standard_ded, itemized_ded)
        use_itemized = itemized_ded > standard_ded

        total_gross = salary_income + dividend_income + rental_income + other_income_t
        net_income  = max(total_gross - total_exempt - salary_special_ded - deduction, 0)

        # 累進稅率（2024）
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

        # 股利可抵減（8.5%，上限8萬）
        div_credit = min(dividend_income * 0.085, 80000)
        final_tax  = max(tax - div_credit, 0)
        eff_rate   = final_tax / total_gross * 100 if total_gross > 0 else 0

        st.markdown('<p class="section-header">稅務試算結果</p>', unsafe_allow_html=True)
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
            st.success(f"✅ 採**列舉扣除額** ${itemized_ded:,.0f}，比標準扣除 ${standard_ded:,.0f} 多省 ${(itemized_ded-standard_ded)*0.12:,.0f} 稅金")
        else:
            st.info(f"ℹ️ 採**標準扣除額** ${standard_ded:,.0f}（列舉 ${itemized_ded:,.0f} 較低）")

        st.markdown('<p class="section-header">系統分析報告</p>', unsafe_allow_html=True)
        advice_t = get_tax_advice(total_gross, final_tax, eff_rate, use_itemized, dividend_income, filing_status)
        render_ai(advice_t, "系統分析 · 稅務規劃")

        pdf_bytes = build_pdf(client_name, [
            {"title": "稅務試算明細", "content": None, "table": df_tax},
            {"title": "AI 節稅建議", "content": strip_md(advice_t), "table": None},
        ])
        st.download_button("📥 下載 PDF 報告", pdf_bytes,
                           f"稅務規劃_{client_name}_{time.strftime('%Y%m%d')}.pdf", "application/pdf")
