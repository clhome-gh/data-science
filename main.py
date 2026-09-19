import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from scipy.stats import linregress

# 페이지 설정
st.set_page_config(page_title="서울 기온 예측기", page_icon="🌡️", layout="wide")

st.title("🌡️ 서울 기온 예측기")
st.markdown("서울의 과거 기온 데이터를 바탕으로 연도별 평균기온의 추세를 분석하고 회귀 직선을 통해 미래 기온을 예측합니다.")

@st.cache_data
def load_and_preprocess_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"
    df = pd.read_csv(url, encoding="utf-8")
    
    # 열 이름 공백 제거
    df.columns = df.columns.str.strip()
    
    # 날짜 데이터 처리 및 연도 추출
    df['날짜'] = pd.to_datetime(df['날짜'])
    df['연도'] = df['날짜'].dt.year
    
    # 1. 수업 기준 기간: 2025년까지 필터링
    df_filtered = df[df['연도'] <= 2025].copy()
    
    # 평균기온 결측치 제거
    df_filtered = df_filtered.dropna(subset=['평균기온'])
    
    # 2. 관측일이 300일 미만인 해 제외
    year_counts = df_filtered.groupby('연도').size()
    valid_years = year_counts[year_counts >= 300].index
    df_filtered = df_filtered[df_filtered['연도'].isin(valid_years)]
    
    # 연도별 평균기온 계산
    yearly_df = df_filtered.groupby('연도')['평균기온'].mean().reset_index()
    
    return yearly_df

# 데이터 로드
try:
    yearly_df = load_and_preprocess_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 3. 1908년부터 지난 연수를 독립 변수로 설정 (X = 연도 - 1908)
yearly_df['지난연수'] = yearly_df['연도'] - 1908

# 회귀 분석 수행 (경사 및 절편, 상관계수 계산)
slope, intercept, r_value, p_value, std_err = linregress(yearly_df['지난연수'], yearly_df['평균기온'])
corr_coef = r_value

# 회귀 직선 값 계산
yearly_df['회귀예측'] = slope * yearly_df['지난연수'] + intercept

# 기본 통계 정보 추출
start_year = int(yearly_df['연도'].min())
end_year = int(yearly_df['연도'].max())
num_years = len(yearly_df)

# 화면에 정보 표시 (개수, 시작 연도, 끝 연도)
col1, col2, col3 = st.columns(3)
col1.metric("회귀선 생성에 사용된 해의 개수", f"{num_years}년")
col2.metric("시작 연도", f"{start_year}년")
col3.metric("끝 연도", f"{end_year}년")

st.markdown("---")

# 4. Plotly 시각화 (가로축에 연도를 그대로 표시)
fig = go.Figure()

# 연평균기온 산점도
fig.add_trace(go.Scatter(
    x=yearly_df['연도'],
    y=yearly_df['평균기온'],
    mode='markers',
    name='연평균기온 (실측)',
    marker=dict(color='royalblue', size=6)
))

# 회귀 직선
fig.add_trace(go.Scatter(
    x=yearly_df['연도'],
    y=yearly_df['회귀예측'],
    mode='lines',
    name='회귀 직선',
    line=dict(color='firebrick', width=2)
))

fig.update_layout(
    title="서울 연도별 평균기온 및 회귀 직선 추세",
    xaxis_title="연도",
    yaxis_title="평균기온 (°C)",
    hovermode="x unified",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# 상관계수 표시
st.info(f"📊 **상관계수 (r):** {corr_coef:.4f} (연도와 평균기온 간의 선형 상관관계)")

st.markdown("---")

# 5. 슬라이더를 통한 연도별 예상 기온 확인 (범위: 1900 ~ 2100)
st.subheader("🔮 특정 연도 기온 예측하기")
selected_year = st.slider("조회할 연도를 선택하세요", min_value=1900, max_value=2100, value=2026, step=1)

# 선택된 연도의 예상 기온 계산
selected_elapsed = selected_year - 1908
predicted_temp = slope * selected_elapsed + intercept

# 강조된 예상 기온 표시
st.markdown(
    f"""
    <div style="background-color: #f0f2f6; padding: 25px; border-radius: 10px; text-align: center;">
        <h3 style="margin-bottom: 10px; color: #31333F;">📅 {selected_year}년 예상 평균기온</h3>
        <h1 style="color: #ff4b4b; font-size: 52px; margin-top: 0;">{predicted_temp:.2f} °C</h1>
    </div>
    """,
    unsafe_allow_html=True
)
