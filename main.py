import streamlit as st
import pandas as pd
import plotly.express as px

# ==================================================
# 영화 데이터 그래프 도감 1 - 시간
# ==================================================

st.set_page_config(
    page_title="영화 데이터 그래프 도감 1 - 시간",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감 1 - 시간")
st.caption("KOBIS 일별 박스오피스 데이터를 시간의 흐름에 따라 살펴봅니다.")

# ==================================================
# 1. 데이터 불러오기
# ==================================================

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 날짜 열을 진짜 날짜형으로 변환
    df["날짜"] = pd.to_datetime(
        df["날짜"].astype(str),
        format="%Y%m%d",
        errors="coerce"
    )

    # 숫자 열을 숫자형으로 변환
    numeric_columns = [
        "순위",
        "영화코드",
        "일관객",
        "누적관객",
        "스크린수",
        "상영횟수"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.sort_values(["날짜", "순위"]).reset_index(drop=True)


try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오지 못했습니다.")
    st.code(str(e))
    st.stop()


# ==================================================
# 2. 데이터 기본 정보
# ==================================================

st.info(
    f"총 {df['날짜'].nunique()}일의 일별 박스오피스 데이터를 불러왔습니다."
)

st.divider()


# ==================================================
# 그래프 구역 1. 시간에 따른 일관객 변화
# ==================================================

st.header("📈 그래프 1. 영화별 일관객 변화")

movie_list = sorted(
    df["영화명"].dropna().unique().tolist()
)

selected_movie = st.selectbox(
    "영화를 선택하세요.",
    movie_list,
    index=0
)

movie_df = (
    df[df["영화명"] == selected_movie]
    .sort_values("날짜")
    .copy()
)

fig = px.line(
    movie_df,
    x="날짜",
    y="일관객",
    markers=True,
    title=f"「{selected_movie}」의 날짜별 일관객 변화",
    labels={
        "날짜": "날짜",
        "일관객": "일관객 수"
    }
)

fig.update_traces(
    hovertemplate="날짜: %{x|%Y-%m-%d}<br>일관객: %{y:,}명<extra></extra>"
)

fig.update_layout(
    hovermode="x unified",
    xaxis_title="날짜",
    yaxis_title="일관객 수(명)"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.markdown("**이 그래프로 알 수 있는 것:**")
st.text_input(
    "그래프 1 해석 문구",
    placeholder="예: 개봉 직후 관객 수가 높고 시간이 지나면서 감소하는 경향을 볼 수 있다.",
    key="graph1_note"
)


# ==================================================
# 앞으로 그래프를 추가할 공간
# ==================================================

st.divider()

st.header("📊 그래프 2. 앞으로 추가할 그래프")

st.caption(
    "여기에 다음 그래프를 추가할 수 있습니다. "
    "예: 누적관객 변화, 순위 변화, 스크린 수와 일관객의 관계 등"
)

st.markdown("**이 그래프로 알 수 있는 것:**")
st.text_input(
    "그래프 2 해석 문구",
    placeholder="추가할 그래프의 의미를 적어 보세요.",
    key="graph2_note"
)


st.divider()

st.header("📊 그래프 3. 앞으로 추가할 그래프")

st.caption("다음 분석 그래프를 추가할 수 있는 구역입니다.")

st.markdown("**이 그래프로 알 수 있는 것:**")
st.text_input(
    "그래프 3 해석 문구",
    placeholder="추가할 그래프의 의미를 적어 보세요.",
    key="graph3_note"
)
st.caption(
    "※ 조회 가능한 가장 최근 날짜는 한국 시간 기준 어제입니다."
)
