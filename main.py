# maruti_ads_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(layout="wide", page_title="Maruti Ads Performance Demo")

# ------------------ Helpers ------------------
def safe_num(s):
    if pd.isna(s):
        return np.nan
    if isinstance(s, (int, float, np.number)):
        return float(s)
    s = str(s).strip()
    # remove rupee symbol, commas, spaces
    s = s.replace('₹', '').replace('Rs', '').replace(',', '').replace(' ', '')
    # percent handling
    if s.endswith('%'):
        try:
            return float(s.replace('%',''))
        except:
            return np.nan
    try:
        return float(s)
    except:
        return np.nan

def col_fuzzy_match(cols, candidates):
    cols_low = {c.lower().strip(): c for c in cols}
    for cand in candidates:
        c = cand.lower().strip()
        if c in cols_low:
            return cols_low[c]
    # substring match
    for c_low, orig in cols_low.items():
        for cand in candidates:
            if cand.lower().strip() in c_low or c_low in cand.lower().strip():
                return orig
    return None

def coerce_numeric_cols(df, candidate_names):
    for name in candidate_names:
        if name in df.columns:
            df[name] = df[name].map(safe_num)
    return df

def load_sample_sheets():
    # builds the sample sheets from user's provided data
    sheets = {}
    sheets['Campaign Summary'] = pd.DataFrame({
        'Campaign': ['Brand – Exact','Brand – Phrase','Model A – Non-Brand','Model B – Non-Brand','SUV Segment – Generic','Hatchback Segment – Generic','Competitor Conquesting','Finance / EMI Queries','Service / Test Drive'],
        'Impressions':[480000,720000,1200000,900000,2100000,1500000,800000,600000,350000],
        'Clicks':[57600,57600,60000,40500,63000,52500,20000,24000,17500],
        'CTR':['12%','8%','5%','4.5%','3%','3.5%','2.5%','4%','5%'],
        'Avg CPC':[12,10,22,25,30,18,35,28,20],
        'Spend':[691200,576000,1320000,1012500,1890000,945000,700000,672000,350000],
        'Conversions':[3456,2304,1800,1012,1260,1312,300,1200,2625],
        'CVR':['6%','4%','3%','2.5%','2%','2.5%','1.5%','5%','15%'],
        'CPA':[200,250,733,999,1500,720,2333,560,133]
    })

    sheets['Model A Keywords'] = pd.DataFrame({
        'Keyword':['best sedan under 10 lakhs','Model A price','Model A mileage','Model A vs Model B'],
        'Impressions':[320000,210000,150000,100000],
        'Clicks':[9600,16800,7500,3000],
        'CTR':['3%','8%','5%','3%'],
        'CPC':[24,18,16,30],
        'Spend':[230400,302400,120000,90000],
        'Conversions':[264,588,285,150],
        'CVR':['2.75%','3.5%','3.8%','5%'],
        'CPA':[873,514,421,600]
    })

    sheets['SUV Keywords'] = pd.DataFrame({
        'Keyword':['best SUV India 2025','compact SUV price','SUV under 12 lakhs','SUV comparison 2025'],
        'Impressions':[450000,310000,220000,150000],
        'Clicks':[13500,9300,6600,3000],
        'CTR':['3%','3%','3%','2%'],
        'CPC':[32,28,30,35],
        'Spend':[432000,260400,198000,105000],
        'Conversions':[270,186,198,96],
        'CVR':['2%','2%','3%','3.2%'],
        'CPA':[1600,1400,1000,1094]
    })

    sheets['Landing Pages'] = pd.DataFrame({
        'Landing Page':['/model-a','/model-b','/test-drive','/financing-emi'],
        'Sessions':[42000,31500,18000,22500],
        'Bounce':['52%','58%','38%','42%'],
        'Avg Time':['1:35','1:20','2:05','1:50'],
        'Leads':[960,720,1980,1125],
        'Conv Rate':['2.3%','2.2%','11%','5%']
    })

    sheets['Campaign Summary 2'] = pd.DataFrame({
        'Campaign':['Brand','Hatchbacks','Sedans (Dzire)','SUVs','MPV (Ertiga)','Finance/EMI'],
        'Impressions':[3200000,4500000,2000000,3800000,1900000,1200000],
        'Clicks':[352000,225000,96000,121600,76000,48000],
        'CTR':['11%','5%','4.8%','3.2%','4%','4%'],
        'Avg CPC':[11,22,24,30,26,28],
        'Cost':[3872000,4950000,2304000,3648000,1976000,1344000],
        'Conversions':[22880,6525,3072,3648,2660,2400],
        'CVR':['6.5%','2.9%','3.2%','3%','3.5%','5%'],
        'CPA':[169,758,750,1000,743,560],
        'Conv Value':[11440000,3262500,1536000,2553600,1729000,1440000],
        'ROAS':[2.96,0.66,0.67,0.7,0.87,1.07],
        'Search IS':['82%','75%','70%','68%','72%','60%'],
        'Lost IS (Budget)':['10%','18%','22%','25%','20%','30%'],
        'Bid Strategy':['Maximize Conversions','tCPA','Maximize Clicks','tCPA','Maximize Conversions','tCPA']
    })

    sheets['Ad Group Summary'] = pd.DataFrame({
        'Campaign':['Hatchbacks','Hatchbacks','Hatchbacks','Hatchbacks','Sedans','Sedans','SUV','SUV','SUV','MPV','MPV','Finance','Finance'],
        'Ad Group':['Swift Price','Swift Mileage','Baleno Price','WagonR Comparison','Dzire Price','Dzire Mileage','Brezza Variants','Grand Vitara Price','Fronx Comparison','Ertiga Price','Ertiga CNG','EMI Calculator','Loan Eligibility'],
        'Impressions':[1200000,900000,1000000,700000,900000,700000,1200000,1000000,600000,1000000,900000,700000,500000],
        'Clicks':[54000,40500,45000,28000,43200,31500,36000,30000,18000,40000,36000,28000,20000],
        'CTR':['4.5%','4.5%','4.5%','4%','4.8%','4.5%','3%','3%','3%','4%','4%','4%','4%'],
        'CPC':[21,20,23,18,22,24,29,32,30,25,27,26,30],
        'Cost':[1134000,810000,1035000,504000,950400,756000,1044000,960000,540000,1000000,972000,728000,600000],
        'Conversions':[1350,1012,1125,700,1296,882,1080,900,540,1400,1260,1400,1000],
        'CVR':['2.5%','2.5%','2.5%','2.5%','3%','2.8%','3%','3%','3%','3.5%','3.5%','5%','5%'],
        'CPA':[840,800,920,720,733,857,967,1067,1000,714,771,520,600]
    })

    sheets['Keyword Performance'] = pd.DataFrame({
        'Keyword':['swift on road price','swift mileage','best hatchback 2025','baleno price','wagonr vs alto','dzire on road price','brezza price','brezza vs venue','grand vitara mileage','ertiga cng price','emi calculator car'],
        'Match Type':['Exact','Phrase','Broad','Exact','Phrase','Exact','Exact','Exact','Phrase','Phrase','Broad'],
        'Impressions':[500000,350000,420000,600000,300000,450000,550000,400000,350000,500000,400000],
        'Clicks':[27500,15750,12600,30000,12000,23400,16500,12000,10500,20000,16000],
        'CTR':['5.5%','4.5%','3%','5%','4%','5.2%','3%','3%','3%','4%','4%'],
        'CPC':[22,20,24,23,18,24,30,29,32,27,26],
        'Cost':[605000,315000,302400,690000,216000,561600,495000,348000,336000,540000,416000],
        'QS':[8,7,6,8,7,8,7,6,6,7,6],
        'Conv':[825,525,336,900,300,702,495,360,315,700,800],
        'CVR':['3%','3.3%','2.7%','3%','2.5%','3%','3%','3%','3%','3.5%','5%'],
        'CPA':[733,600,900,767,720,800,1000,967,1067,771,520],
        'IS':['78%','74%','66%','72%','69%','71%','65%','63%','59%','70%','55%'],
        'Lost IS (Rank)':['12%','15%','22%','18%','20%','19%','24%','27%','29%','21%','30%']
    })

    sheets['Search Terms Report'] = pd.DataFrame({
        'Search Term':['swift mileage real user review','baleno price delhi 2025','best car under 10 lakhs for family','brezza zxi vs venue sx','ertiga cng 7 seater mileage','car emi calculator online'],
        'Keyword Triggered':['swift mileage','baleno price','best hatchback 2025','brezza vs venue','ertiga cng price','emi calculator car'],
        'Impressions':[120000,150000,200000,90000,110000,160000],
        'Clicks':[5400,7500,6000,2700,4400,6400],
        'CTR':['4.5%','5%','3%','3%','4%','4%'],
        'Conv':[170,260,180,81,154,320],
        'CPA':[620,750,900,930,700,520],
        'Conversion Type':['Brochure','Test Drive','Lead','Test Drive','Brochure','Lead']
    })

    sheets['Device Performance'] = pd.DataFrame({
        'Device':['Mobile','Desktop','Tablet'],
        'Impressions':[9000000,2300000,300000],
        'Clicks':[405000,92000,13500],
        'CTR':['4.5%','4%','4.5%'],
        'CPC':[24,26,22],
        'Cost':[9720000,2392000,297000],
        'Conversions':[12150,2760,540],
        'CVR':['3%','3%','4%'],
        'CPA':[800,867,550]
    })

    sheets['Location Performance'] = pd.DataFrame({
        'City':['Delhi','Mumbai','Bangalore','Chennai','Hyderabad','Pune','Ahmedabad','Kolkata','Jaipur','Lucknow'],
        'Impressions':[1200000,950000,900000,700000,650000,500000,450000,400000,300000,280000],
        'Clicks':[60000,45600,40500,30100,27300,22500,18900,16000,12000,11200],
        'CTR':['5%','4.8%','4.5%','4.3%','4.2%','4.5%','4.2%','4%','4%','4%'],
        'CPC':[26,25,27,23,24,22,20,21,19,18],
        'Cost':[1560000,1140000,1093500,692300,655200,495000,378000,336000,228000,201600],
        'Conversions':[1920,1420,1350,1053,1040,855,700,600,450,420],
        'CVR':['3.2%','3.1%','3.3%','3.5%','3.8%','3.8%','3.7%','3.8%','3.7%','3.8%'],
        'CPA':[812,803,810,657,630,579,540,560,507,480]
    })

    sheets['Weekly Trends'] = pd.DataFrame({
        'Week':['Week 1','Week 2','Week 3','Week 4'],
        'Impressions':[3200000,3400000,3600000,3700000],
        'Clicks':[148000,154000,162000,166000],
        'Cost':[1790000,1850000,1940000,2010000],
        'Conversions':[3800,3950,4200,4350]
    })

    sheets['Landing Page 2'] = sheets['Landing Pages'].copy()

    sheets['Conversion Type'] = pd.DataFrame({
        'Conversion Type':['Test Drive','Brochure','Dealer Call','WhatsApp Lead'],
        'Count':[9800,11200,5400,2800],
        'Value per Conversion':[800,300,600,400],
        'Total Value':[9800*800,11200*300,5400*600,2800*400]
    })

    return sheets

# ------------------ Load sheets (upload optional) ------------------
st.title("Maruti Google Ads Performance")
uploaded = st.file_uploader("Upload Google Ads Data Excel", type=['xlsx','xls'])

if uploaded is None:
    sheets = load_sample_sheets()
else:
    # read all sheets but do not display their names
    xls = pd.ExcelFile(uploaded)
    sheets = {}
    for name in xls.sheet_names:
        try:
            sheets[name] = pd.read_excel(xls, sheet_name=name)
        except Exception:
            pass

# ------------------ Utility: find sheet by keywords ------------------
def find_sheet(names):
    for k in sheets.keys():
        kn = k.lower()
        for keyword in names:
            if keyword in kn:
                return k
    return None

# Choose relevant sheets (best-effort)
camp_sheet = find_sheet(['campaign summary 2','campaign summary','campaigns']) or list(sheets.keys())[0]
model_a_kw_sheet = find_sheet(['model a','model a keywords','model a keyword']) or find_sheet(['keyword'])
suv_kw_sheet = find_sheet(['suv keywords','suv']) or None
landing_sheet = find_sheet(['landing page 2','landing pages','landing page']) or None
adgroup_sheet = find_sheet(['ad group','adgroup']) or None
kw_perf_sheet = find_sheet(['keyword performance','keyword performance']) or None
sqr_sheet = find_sheet(['search terms','search terms report','sqr']) or None
device_sheet = find_sheet(['device performance','device']) or None
loc_sheet = find_sheet(['location performance','location']) or None
weekly_sheet = find_sheet(['weekly trends','weekly']) or None
conv_type_sheet = find_sheet(['conversion type','conversion types']) or None

# Helper to coerce sheet to numeric where appropriate
def clean_df(df):
    df = df.copy()
    # coerce percent columns and rupee columns intelligently
    for c in df.columns:
        # try convert using safe_num
        coerced = df[c].map(safe_num)
        # if more than 50% numeric after coercion, replace
        if coerced.notna().sum() / max(1, len(coerced)) > 0.5:
            df[c] = coerced
    return df

# Clean all sheets
for k in list(sheets.keys()):
    sheets[k] = clean_df(sheets[k])

# ------------------ Build unified campaign-level df for analytics ------------------
camp_df = sheets.get(camp_sheet, pd.DataFrame()).copy()
# normalize column names to simple tokens
camp_df.columns = [str(c).strip() for c in camp_df.columns]

# common column name candidates
impr_col = col_fuzzy_match(camp_df.columns, ['impressions','impr'])
clicks_col = col_fuzzy_match(camp_df.columns, ['clicks'])
spend_col = col_fuzzy_match(camp_df.columns, ['cost','spend','amount','cost_(₹)','cost_₹','cost_(rs)'])
conv_col = col_fuzzy_match(camp_df.columns, ['conversions','conv'])
conv_value_col = col_fuzzy_match(camp_df.columns, ['conv value','conversion value','conv_value','conv_value_(₹)','conv value (₹)'])
campaign_name_col = col_fuzzy_match(camp_df.columns, ['campaign','campaign name'])

# fallback if not in camp_df try Campaign Summary (original if present)
if spend_col is None:
    # try other sheet variants
    for alt in ['Campaign Summary','Campaign Summary 2']:
        df_temp = sheets.get(alt)
        if isinstance(df_temp, pd.DataFrame):
            spend_col = col_fuzzy_match(df_temp.columns, ['cost','spend','amount'])
            if spend_col:
                # copy totals into camp_df if needed (but don't overwrite)
                pass

# safe values
camp_df['impressions'] = camp_df[impr_col] if impr_col in camp_df.columns else camp_df.get('Impressions', 0)
camp_df['clicks'] = camp_df[clicks_col] if clicks_col in camp_df.columns else camp_df.get('Clicks', 0)
camp_df['spend'] = camp_df[spend_col] if spend_col in camp_df.columns else camp_df.get('Spend', camp_df.get('Cost', 0))
camp_df['conversions'] = camp_df[conv_col] if conv_col in camp_df.columns else camp_df.get('Conversions', 0)
camp_df['conv_value'] = camp_df[conv_value_col] if conv_value_col in camp_df.columns else camp_df.get('Conv Value', camp_df.get('Conv Value (₹)', 0))
camp_df['campaign'] = camp_df[campaign_name_col] if campaign_name_col in camp_df.columns else camp_df.iloc[:,0].astype(str)

# calculated metrics
camp_df['ctr_pct'] = (camp_df['clicks'] / camp_df['impressions']) * 100
camp_df['avg_cpc'] = np.where(camp_df['clicks']>0, camp_df['spend'] / camp_df['clicks'], np.nan)
camp_df['cvr_pct'] = np.where(camp_df['clicks']>0, camp_df['conversions'] / camp_df['clicks'] * 100, np.nan)
camp_df['cpa'] = np.where(camp_df['conversions']>0, camp_df['spend'] / camp_df['conversions'], np.nan)
camp_df['roas'] = np.where(camp_df['spend']>0, camp_df['conv_value'] / camp_df['spend'], np.nan)

# ------------------ Overview KPIs ------------------
st.header("Overview KPIs")
col1, col2, col3, col4, col5 = st.columns(5)
total_impr = int(camp_df['impressions'].sum())
total_clicks = int(camp_df['clicks'].sum())
total_spend = float(camp_df['spend'].sum())
total_conv = int(camp_df['conversions'].sum()) if camp_df['conversions'].notna().any() else 0
total_conv_value = float(camp_df['conv_value'].sum()) if 'conv_value' in camp_df.columns else np.nan
col1.metric("Impressions", f"{total_impr:,}")
col2.metric("Clicks", f"{total_clicks:,}")
col3.metric("Spend (₹)", f"{int(total_spend):,}")
col4.metric("Conversions", f"{total_conv:,}")
col5.metric("ROAS", f"{(total_conv_value/total_spend):.2f}" if total_spend>0 and not np.isnan(total_conv_value) else "N/A")

st.markdown("---")

# ------------------ 1) Where are we spending money ------------------
st.subheader("Money Spending — Spend distribution & hotspots")
fig = px.bar(camp_df.sort_values('spend', ascending=False), x='campaign', y='spend', title='Campaign Spend (₹)')
st.plotly_chart(fig, use_container_width=True)
fig_pie = px.pie(camp_df, names='campaign', values='spend', title='Spend share by Campaign')
st.plotly_chart(fig_pie, use_container_width=True)

# Top spend by adgroup if sheet exists
if adgroup_sheet and isinstance(sheets.get(adgroup_sheet), pd.DataFrame):
    ag = clean_df(sheets[adgroup_sheet])
    # detect cost and conversions similar way
    ag_cost = col_fuzzy_match(ag.columns, ['cost','cost_(₹)','cost_₹','cost'])
    ag_conv = col_fuzzy_match(ag.columns, ['conversions','conv'])
    ag_name = col_fuzzy_match(ag.columns, ['ad group','ad_group','adgroup'])
    if ag_cost:
        ag['cost'] = ag[ag_cost].map(safe_num)
        top_ag = ag.sort_values('cost', ascending=False).head(10)
        st.markdown("Top Ad Groups by Spend")
        st.plotly_chart(px.bar(top_ag, x=ag_name or ag.columns[0], y='cost'), use_container_width=True)

# ------------------ 2) What's working vs wasting budget ------------------
st.subheader("Efficiency & Waste Reports")
# Campaign efficiency scatter (spend vs conversions) and color by ROAS
fig = px.scatter(camp_df, x='spend', y='conversions', size='impressions', color='roas',
                 hover_name='campaign', title='Spend vs Conversions (bubble=size impressions, color=ROAS)')
st.plotly_chart(fig, use_container_width=True)

# Wasted: high spend but low conversions or very high CPA
median_spend = camp_df['spend'].median()
waste_df = camp_df[(camp_df['spend'] > median_spend) & ((camp_df['conversions']==0) | (camp_df['cpa'] > camp_df['cpa'].median()*1.5))]
if not waste_df.empty:
    st.markdown("**Wasted campaigns (high spend & poor conversion/CPA)**")
    st.dataframe(waste_df[['campaign','spend','conversions','cpa','roas']].sort_values('spend', ascending=False))
else:
    st.write("No obvious wasted campaigns found by rule (high spend & poor conversion).")

# Keyword waste
kw = None
for candidate in [model_a_kw_sheet, suv_kw_sheet, kw_perf_sheet]:
    if candidate and isinstance(sheets.get(candidate), pd.DataFrame):
        kw = clean_df(sheets[candidate])
        break
if kw is not None:
    kw_cols = kw.columns
    k_cost = col_fuzzy_match(kw_cols, ['spend','cost','cost_(₹)'])
    k_conv = col_fuzzy_match(kw_cols, ['conversions','conv'])
    k_kw = col_fuzzy_match(kw_cols, ['keyword','search term','keyword_'])
    if k_cost:
        kw['cost'] = kw[k_cost].map(safe_num)
    if k_conv:
        kw['conversions'] = kw[k_conv].map(safe_num)
    if k_kw is None:
        kw['keyword'] = kw.iloc[:,0].astype(str)
    else:
        kw['keyword'] = kw[k_kw].astype(str)
    # display top wasted keywords
    wasted_kw = kw[(kw['cost']> kw['cost'].median()) & (kw.get('conversions',0)==0)]
    if not wasted_kw.empty:
        st.markdown("**Wasted Keywords (high spend + zero conversions)**")
        st.dataframe(wasted_kw[['keyword','cost']].sort_values('cost', ascending=False).head(20))
    # Keyword funnel
    if 'Impressions' in kw.columns or 'Impressions' in kw.columns or 'impressions' in kw.columns:
        # try using 'Clicks' and 'Impressions' columns if present
        imp_col = col_fuzzy_match(kw.columns, ['impressions'])
        clicks_col = col_fuzzy_match(kw.columns, ['clicks'])
        conv_col_kw = col_fuzzy_match(kw.columns, ['conversions','conv'])
        if imp_col and clicks_col:
            funnel = kw[[k_kw or kw.columns[0], imp_col, clicks_col, conv_col_kw]].rename(columns={imp_col:'Impressions', clicks_col:'Clicks', conv_col_kw:'Conversions'})
            funnel = funnel.fillna(0)
            st.markdown("Keyword Funnel (sample top 10 by impressions)")
            st.dataframe(funnel.sort_values('Impressions', ascending=False).head(10))

# ------------------ 3) Where should we increase/decrease investment? ------------------
st.subheader("Increase or Decrease investment — Actionable suggestions")
# Scale candidates: high ROAS and relatively lower spend
scale_candidates = camp_df[(camp_df['roas'] > camp_df['roas'].median()) & (camp_df['spend'] < camp_df['spend'].median())]
reduce_candidates = camp_df[(camp_df['roas'] < camp_df['roas'].median()) & (camp_df['spend'] > camp_df['spend'].median())]

st.markdown("**Recommend Increase Budget** (high ROAS, underfunded)")
if not scale_candidates.empty:
    st.dataframe(scale_candidates[['campaign','spend','roas','conversions']].sort_values('roas', ascending=False))
else:
    st.write("No immediate scale candidates found by the simple rule.")

st.markdown("**Recommend Decrease / Pause** (low ROAS, high spend)")
if not reduce_candidates.empty:
    st.dataframe(reduce_candidates[['campaign','spend','roas','conversions']].sort_values('spend', ascending=False))
else:
    st.write("No immediate reduce candidates found by the simple rule.")

# ------------------ 4) What changes will improve ROAS ------------------
st.subheader("Changes will improve ROAS — actions")
st.write("""
- Improve landing page conversion rates for campaigns with high spend & low CVR (see Landing Page section).  
- Pause or convert to negative keywords any high-spend keywords with zero conversions.  
- Reallocate budget to campaigns showing ROAS > median and low lost IS.  
- Test creative/CTA for campaigns with high impressions but low CTR.
""")

# ------------------ Device & Location ------------------
st.markdown("---")
st.subheader("Device & Location Performance")
if device_sheet and isinstance(sheets.get(device_sheet), pd.DataFrame):
    dev = clean_df(sheets[device_sheet])
    dev_cost_col = col_fuzzy_match(dev.columns, ['cost','spend'])
    dev_name_col = col_fuzzy_match(dev.columns, ['device'])
    if dev_cost_col and dev_name_col:
        dev['cost'] = dev[dev_cost_col].map(safe_num)
        fig = px.pie(dev, names=dev_name_col, values='cost', title='Spend share by Device')
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(dev)
else:
    st.info("Device performance sheet not found in uploaded file (using sample data).")

if loc_sheet and isinstance(sheets.get(loc_sheet), pd.DataFrame):
    loc = clean_df(sheets[loc_sheet])
    # map columns
    loc_cost_col = col_fuzzy_match(loc.columns, ['cost','cost_(₹)','cost_₹'])
    loc_name_col = col_fuzzy_match(loc.columns, ['city','location','city_name'])
    if loc_cost_col and loc_name_col:
        loc['cost'] = loc[loc_cost_col].map(safe_num)
        fig = px.choropleth(loc.sort_values('cost', ascending=False).head(20), locations=loc_name_col, color='cost', locationmode='country names' if loc_name_col.lower()=='country' else None, title='Top City Spend (top 20)')
        # fallback: use bar chart when mapping to map fails
        st.plotly_chart(px.bar(loc.sort_values('cost', ascending=False).head(20), x=loc_name_col, y='cost', title='Top Cities by Spend'), use_container_width=True)
    st.dataframe(loc)
else:
    st.info("Location performance sheet not found in uploaded file (using sample data).")

# ------------------ Weekly Trends ------------------
# st.markdown("---")
# st.subheader("Weekly Time Series & Trend")
# if weekly_sheet and isinstance(sheets.get(weekly_sheet), pd.DataFrame):
#     w = clean_df(sheets[weekly_sheet])
#     # normalize week -> index
#     w.columns = [c.strip() for c in w.columns]
#     # coerce numeric
#     for c in w.columns:
#         w[c] = w[c].map(safe_num) if w[c].dtype==object else w[c]
#     st.dataframe(w)
#     # line plots
#     plot_cols = [c for c in ['Impressions','Clicks','Cost','Conversions'] if c in w.columns or c.lower() in [x.lower() for x in w.columns]]
#     if plot_cols:
#         # try to map by lower
#         col_map = {c: next((col for col in w.columns if col.lower().startswith(c.lower())), None) for c in ['Impressions','Clicks','Cost','Conversions']}
#         ycols = [col_map[c] for c in col_map if col_map[c]]
#         fig = px.line(w, x=w.columns[0], y=ycols, title="Weekly trends")
#         st.plotly_chart(fig, use_container_width=True)
# else:
#     # if not provided, build trend from campaign summary totals across the 4-week sample if present
#     if 'Weekly Trends' in sheets:
#         w = clean_df(sheets['Weekly Trends'])
#         st.dataframe(w)
#         fig = px.line(w, x='Week', y=['Impressions','Clicks','Cost','Conversions'], title='Weekly Trends (sample)')
#         st.plotly_chart(fig, use_container_width=True)

# ------------------ Landing Page Analysis ------------------
st.markdown("---")
st.subheader("Landing Page Performance & Funnel")

# ---- SAFE SHEET DETECTION ----
possible_sheet_names = [
    landing_sheet,
    "Landing Pages",
    "Landing Page 2",
    "Landing",
    "LP"
]

possible_sheet_names = [name for name in possible_sheet_names if name]  # remove None

lp = None
for name in possible_sheet_names:
    if name in sheets:
        lp = sheets[name]
        break

# ---- PROCESS IF FOUND ----
if isinstance(lp, pd.DataFrame):

    lp = clean_df(lp)

    # fuzzy match helper
    def fuzzy(col_list, patterns):
        from difflib import get_close_matches
        for p in patterns:
            match = get_close_matches(p.lower(), [c.lower() for c in col_list], n=1, cutoff=0.6)
            if match:
                # return original column name (case preserved)
                return [c for c in col_list if c.lower() == match[0]][0]
        return None

    # find relevant columns dynamically
    lp_name = fuzzy(lp.columns, ["landing page", "landing", "url", "page", "destination"])
    sess_col = fuzzy(lp.columns, ["sessions", "visits", "traffic"])
    leads_col = fuzzy(lp.columns, ["leads", "conversions", "form submits", "signups"])
    bounce_col = fuzzy(lp.columns, ["bounce", "bounce rate"])
    conv_rate_col = fuzzy(lp.columns, ["conv rate", "conversion rate", "lead cvr"])

    # ---- FUNNEL VISUALIZATION ----
    if sess_col and leads_col and lp_name:

        funnel_df = lp[[lp_name, sess_col, leads_col]].copy()
        funnel_df.columns = ["Landing Page", "Sessions", "Leads"]
        funnel_df["Conversion Rate"] = (funnel_df["Leads"] / funnel_df["Sessions"] * 100).replace([np.inf, np.nan], 0)

        st.dataframe(
            funnel_df.sort_values("Sessions", ascending=False),
            use_container_width=True
        )

        # Chart 1: Sessions vs Leads
        fig = px.bar(
            funnel_df.sort_values("Sessions", ascending=False),
            x="Landing Page",
            y=["Sessions", "Leads"],
            barmode="group",
            title="🔍 Landing Page Traffic vs Leads"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Chart 2: Conversion Rate by Landing Page
        fig2 = px.line(
            funnel_df.sort_values("Conversion Rate", ascending=False),
            x="Landing Page",
            y="Conversion Rate",
            markers=True,
            title="Landing Page Conversion Rate Trend"
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Chart 3: Pareto - 80/20 of LPs driving leads
        fig3 = px.treemap(
            funnel_df,
            path=["Landing Page"],
            values="Leads",
            title="🌳 Which Landing Pages Generate the Most Leads?"
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Insights
        best = funnel_df.sort_values("Conversion Rate", ascending=False).head(1)
        worst = funnel_df.sort_values("Conversion Rate", ascending=True).head(1)

        st.success(f"**Top Landing Page:** `{best.iloc[0]['Landing Page']}` ({best.iloc[0]['Conversion Rate']:.2f}% CR)")
        st.error(f"Fix Low Performing Page: `{worst.iloc[0]['Landing Page']}` ({worst.iloc[0]['Conversion Rate']:.2f}% CR)")

    else:
        st.warning("⚠ Could not detect required columns (Landing Page / Sessions / Leads). Showing raw sheet.")
        st.dataframe(lp, use_container_width=True)

else:
    st.info("Landing Page sheet not found in uploaded file.")


# ------------------ Search Terms & Conversion Types ------------------
st.markdown("---")
st.subheader("Search Terms & Conversion Types")
if sqr_sheet and isinstance(sheets.get(sqr_sheet), pd.DataFrame):
    sqr = clean_df(sheets[sqr_sheet])
    st.dataframe(sqr.sort_values(col_fuzzy_match(sqr.columns, ['Impressions','impressions']), ascending=False).head(50))
else:
    st.info("Search Terms sheet not found.")

if conv_type_sheet and isinstance(sheets.get(conv_type_sheet), pd.DataFrame):
    convs = clean_df(sheets[conv_type_sheet])
    st.dataframe(convs)
    total_value = convs['Total Value'].map(safe_num).sum() if 'Total Value' in convs.columns else np.nan
    st.metric("Total Conversion Value (₹)", f"{int(total_value):,}" if not np.isnan(total_value) else "N/A")

# ------------------ Export combined CSV ------------------
st.markdown("---")
st.subheader("Export")
try:
    combined = pd.concat([clean_df(s) for s in sheets.values()], sort=False)
    buf = BytesIO()
    combined.to_csv(buf, index=False)
    buf.seek(0)
    st.download_button("Download combined CSV", data=buf, file_name="maruti_ads_combined.csv", mime="text/csv")
except Exception as e:
    st.warning("Could not prepare combined CSV: " + str(e))
