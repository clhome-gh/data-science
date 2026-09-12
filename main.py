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

@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_csv(DATA_URL)

    # 날짜를 실제 날짜형으로 변환
    df["날짜"] = pd.to_datetime(
        df["날짜"].astype(str).str.strip(),
        format="%Y%m%d",
        errors="coerce"
    )

    # 숫자형으로 변환
    number_cols = [
        "순위", "영화코드", "일관객",
        "누적관객", "스크린수", "상영횟수"
    ]

    for col in number_cols:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", ""),
            errors="coerce"
        )

    # 필요한 데이터가 없는 행 제거
    df = df.dropna(subset=["날짜", "영화명", "일관객"])

    return df.sort_values(["날짜", "순위"]).reset_index(drop=True)


try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오지 못했습니다.")
    st.code(str(e))
    st.stop()

st.info(f"총 {df['날짜'].nunique()}일의 데이터를 불러왔습니다.")

# ==================================================
# 그래프 1
# ==================================================

st.divider()
st.header("📈 그래프 1. 영화별 일관객 변화")

movie_list = sorted(df["영화명"].unique())

selected_movie = st.selectbox(
    "영화를 선택하세요.",
    movie_list,
    key="movie_select"
)

movie_df = (
    df[df["영화명"] == selected_movie]
    .sort_values("날짜")
)

fig1 = px.line(
    movie_df,
    x="날짜",
    y="일관객",
    markers=True,
    title=f"「{selected_movie}」의 날짜별 일관객 변화",
    labels={
        "날짜": "날짜",
        "일관객": "일관객 수(명)"
    }
)

fig1.update_traces(
    hovertemplate=(
        "날짜: %{x|%Y-%m-%d}"
        "<br>일관객: %{y:,}명"
        "<extra></extra>"
    )
)

fig1.update_layout(
    hovermode="closest",
    xaxis_title="날짜",
    yaxis_title="일관객 수(명)"
)

st.plotly_chart(fig1, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것:**")
st.text_input(
    "그래프 1 해석 문구",
    placeholder="예: 시간이 지나면서 영화의 일관객 수가 어떻게 변하는지 알 수 있다.",
    key="graph1_note"
)

# ==================================================
# 그래프 2
# ==================================================

st.divider()
st.header("📊 그래프 2. 기간 내 일관객 합계 TOP 5")

# 영화별 기간 전체 일관객 합계 계산
movie_total = (
    df.groupby("영화명", as_index=False)["일관객"]
    .sum()
    .sort_values("일관객", ascending=False)
)

top5 = movie_total.head(5).copy()
top5_movies = top5["영화명"].tolist()

# TOP 5 영화 목록을 먼저 보여줌
st.write("**이 기간 일관객 합계 TOP 5 영화**")

top5_display = top5.copy()
top5_display.index = range(1, len(top5_display) + 1)
top5_display.columns = ["영화명", "기간 일관객 합계"]

st.dataframe(
    top5_display.style.format(
        {"기간 일관객 합계": "{:,.0f}명"}
    ),
    use_container_width=True
)

# TOP 5 영화의 날짜별 일관객 데이터
top5_df = df[df["영화명"].isin(top5_movies)].copy()

# 같은 날짜/영화가 여러 행이면 합산
top5_daily = (
    top5_df
    .groupby(["날짜", "영화명"], as_index=False)["일관객"]
    .sum()
    .sort_values(["날짜", "영화명"])
)

# 날짜 × 영화 형태로 변환
# 해당 날짜에 TOP 5 영화가 10위권 밖이면 값이 없으므로 0으로 채우지 않음
# → 실제 데이터가 없는 것을 관객 0명으로 오해하지 않도록 함
top5_wide = (
    top5_daily
    .pivot(index="날짜", columns="영화명", values="일관객")
    .sort_index()
    .reset_index()
)

# Plotly가 확실하게 각 영화를 하나의 선으로 인식하도록 다시 세로형으로 변환
top5_plot = top5_wide.melt(
    id_vars="날짜",
    value_vars=top5_movies,
    var_name="영화명",
    value_name="일관객"
).dropna(subset=["일관객"])

fig2 = px.line(
    top5_plot,
    x="날짜",
    y="일관객",
    color="영화명",
    markers=False,
    title="기간 내 일관객 합계 TOP 5 영화의 날짜별 일관객",
    labels={
        "날짜": "날짜",
        "일관객": "일관객 수(명)",
        "영화명": "영화"
    },
    category_orders={"영화명": top5_movies}
)

fig2.update_traces(
    hovertemplate=(
        "영화: %{fullData.name}"
        "<br>날짜: %{x|%Y-%m-%d}"
        "<br>일관객: %{y:,}명"
        "<extra></extra>"
    )
)

fig2.update_layout(
    hovermode="closest",
    xaxis_title="날짜",
    yaxis_title="일관객 수(명)",
    legend_title="영화",
    legend=dict(
        itemclick="toggle",
        itemdoubleclick="toggleothers"
    )
)

st.plotly_chart(fig2, use_container_width=True)

st.caption("범례의 영화 이름을 클릭하면 해당 영화의 선을 켜거나 끌 수 있습니다.")

st.markdown("**이 그래프로 알 수 있는 것:**")
st.text_input(
    "그래프 2 해석 문구",
    placeholder="예: 일관객 합계가 큰 영화들의 흥행 시기와 관객 변화 양상을 비교할 수 있다.",
    key="graph2_note"
)

# ==================================================
# 그래프 3 추가 공간
# ==================================================

st.divider()
st.header("📊 그래프 3. 앞으로 추가할 그래프")

st.caption(
    "여기에 다음 그래프를 추가할 수 있습니다. "
    "예: 누적관객 변화, 순위 변화, 스크린 수와 일관객의 관계 등"
)

st.markdown("**이 그래프로 알 수 있는 것:**")
st.text_input(
    "그래프 3 해석 문구",
    placeholder="추가할 그래프의 의미를 적어 보세요.",
    key="graph3_note"
)
