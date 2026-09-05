import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="서울 연평균 기온 변화",
    page_icon="🌡️",
    layout="wide"
)

# 제목
st.title("🌡️ 서울의 100년간 연평균 기온 변화")
st.write("1907년 이후 서울의 일별 기온 데이터를 이용해 연평균 기온의 변화를 살펴봅니다.")

# 데이터 주소
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    # 날짜를 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 기온 데이터를 숫자형으로 변환
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    # 날짜 또는 평균기온이 없는 행 제거
    df = df.dropna(subset=["날짜", "평균기온"])

    return df


df = load_data()

# 연도 추출
df["연도"] = df["날짜"].dt.year

# 연도별 평균기온 계산
annual_temp = (
    df.groupby("연도")["평균기온"]
    .mean()
    .reset_index()
)

annual_temp.columns = ["연도", "연평균기온"]

# 100년 구간 선택
min_year = int(annual_temp["연도"].min())
max_year = int(annual_temp["연도"].max())

st.sidebar.header("조회 기간")

start_year, end_year = st.sidebar.slider(
    "연도 선택",
    min_value=min_year,
    max_value=max_year,
    value=(max(min_year, max_year - 99), max_year)
)

filtered = annual_temp[
    (annual_temp["연도"] >= start_year)
    & (annual_temp["연도"] <= end_year)
].copy()

# 주요 정보
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "조회 시작 연도",
        f"{start_year}년"
    )

with col2:
    st.metric(
        "조회 종료 연도",
        f"{end_year}년"
    )

with col3:
    if len(filtered) > 0:
        highest_year = filtered.loc[
            filtered["연평균기온"].idxmax(), "연도"
        ]
        highest_temp = filtered["연평균기온"].max()

        st.metric(
            "가장 따뜻했던 해",
            f"{int(highest_year)}년",
            f"{highest_temp:.1f}℃"
        )

# 그래프
st.subheader("연평균 기온 변화")

chart_data = filtered.set_index("연도")

st.line_chart(
    chart_data,
    y="연평균기온",
    x_label="연도",
    y_label="연평균 기온 (℃)"
)

st.caption(
    "※ 연평균 기온은 해당 연도의 일평균 기온을 평균하여 계산했습니다."
)

# 데이터 표
with st.expander("연도별 연평균 기온 데이터 보기"):
    display_data = filtered.copy()
    display_data["연평균기온"] = display_data["연평균기온"].round(2)

    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True
    )
