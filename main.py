import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(
    page_title="서울 일별 평균기온 분포",
    page_icon="🌡️",
    layout="wide"
)

# 제목
st.title("🌡️ 서울의 일별 평균기온 분포")
st.write(
    "서울의 일별 평균기온이 어느 온도 구간에 얼마나 몰려 있는지 "
    "히스토그램으로 확인합니다."
)

# 데이터 주소
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    # 날짜 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 평균기온 숫자 변환
    df["평균기온"] = pd.to_numeric(
        df["평균기온"],
        errors="coerce"
    )

    # 결측값 제거
    df = df.dropna(subset=["날짜", "평균기온"])

    # 연도 추출
    df["연도"] = df["날짜"].dt.year

    return df


df = load_data()

# 사이드바
st.sidebar.header("조회 조건")

min_year = int(df["연도"].min())
max_year = int(df["연도"].max())

start_year, end_year = st.sidebar.slider(
    "조회 기간",
    min_value=min_year,
    max_value=max_year,
    value=(max(min_year, max_year - 99), max_year)
)

# 선택한 기간의 데이터
filtered = df[
    (df["연도"] >= start_year)
    & (df["연도"] <= end_year)
].copy()

# 요약 정보
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "조회 기간",
        f"{start_year}~{end_year}년"
    )

with col2:
    st.metric(
        "관측 일수",
        f"{len(filtered):,}일"
    )

with col3:
    st.metric(
        "평균기온 평균",
        f"{filtered['평균기온'].mean():.1f}℃"
    )

# 히스토그램
st.subheader("일별 평균기온 분포")

fig = px.histogram(
    filtered,
    x="평균기온",
    nbins=30,
    labels={
        "평균기온": "일별 평균기온 (℃)",
        "count": "일수"
    },
    title=f"{start_year}~{end_year}년 서울 일별 평균기온 분포"
)

fig.update_layout(
    xaxis_title="일별 평균기온 (℃)",
    yaxis_title="일수",
    bargap=0.05
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.caption(
    "※ 막대 하나는 일정한 온도 구간을 나타내며, "
    "막대의 높이가 해당 온도 구간에 속하는 날짜의 수입니다."
)

# 데이터 확인
with st.expander("원본 데이터 보기"):
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )
