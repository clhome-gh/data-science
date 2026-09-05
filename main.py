import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(
    page_title="서울 최저기온과 최고기온",
    page_icon="🌡️",
    layout="wide"
)

# 제목
st.title("🌡️ 서울의 최저기온과 최고기온 관계")
st.write(
    "날마다 측정된 최저기온과 최고기온의 관계를 "
    "산점도로 확인합니다."
)

# 데이터 주소
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    # 날짜 변환
    df["날짜"] = pd.to_datetime(
        df["날짜"],
        errors="coerce"
    )

    # 기온 데이터를 숫자로 변환
    for column in ["최저기온", "최고기온"]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # 필요한 데이터가 없는 행 제거
    df = df.dropna(
        subset=["날짜", "최저기온", "최고기온"]
    )

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
    상관계수 = filtered["최저기온"].corr(
        filtered["최고기온"]
    )

    st.metric(
        "상관계수",
        f"{상관계수:.2f}"
    )

# 산점도
st.subheader("일별 최저기온과 최고기온의 관계")

fig = px.scatter(
    filtered,
    x="최저기온",
    y="최고기온",
    hover_data=["날짜"],
    labels={
        "최저기온": "최저기온 (℃)",
        "최고기온": "최고기온 (℃)"
    },
    title=f"{start_year}~{end_year}년 서울 일별 기온 관계"
)

fig.update_traces(
    marker={
        "size": 5,
        "opacity": 0.5
    }
)

fig.update_layout(
    xaxis_title="최저기온 (℃)",
    yaxis_title="최고기온 (℃)"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.caption(
    "※ 점 하나는 하루를 나타냅니다. "
    "점이 오른쪽 위로 모일수록 최저기온과 최고기온이 함께 높아지는 경향을 의미합니다."
)

# 데이터 보기
with st.expander("분석에 사용된 데이터 보기"):
    st.dataframe(
        filtered[
            ["날짜", "최저기온", "최고기온"]
        ],
        use_container_width=True,
        hide_index=True
    )
