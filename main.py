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
        "순위",
        "영화코드",
        "일관객",
        "누적관객",
        "스크린수",
        "상영횟수"
    ]

    for col in number_cols:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", ""),
            errors="coerce"
        )

    # 필요한 데이터가 없는 행 제거
    df = df.dropna(
        subset=["날짜", "영화명", "일관객"]
    )

    return df.sort_values(
        ["날짜", "순위"]
    ).reset_index(drop=True)


# ==================================================
# 데이터 불러오기 오류 처리
# ==================================================

try:
    df = load_data()

except Exception as e:
    st.error("데이터를 불러오지 못했습니다.")
    st.code(str(e))
    st.stop()


st.info(
    f"총 {df['날짜'].nunique()}일의 데이터를 불러왔습니다."
)


# ==================================================
# 그래프 1
# ==================================================

st.divider()
st.header("📈 그래프 1. 영화별 일관객 변화")

movie_list = sorted(
    df["영화명"].unique()
)

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

st.plotly_chart(
    fig1,
    use_container_width=True
)

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

movie_total = (
    df.groupby(
        "영화명",
        as_index=False
    )["일관객"]
    .sum()
    .sort_values(
        "일관객",
        ascending=False
    )
)

top5 = movie_total.head(5).copy()

top5_movies = top5["영화명"].tolist()


# --------------------------------------------------
# TOP 5 영화 목록
# --------------------------------------------------

st.write("**이 기간 일관객 합계 TOP 5 영화**")

top5_display = top5.copy()

top5_display.index = range(
    1,
    len(top5_display) + 1
)

top5_display.columns = [
    "영화명",
    "기간 일관객 합계"
]

st.dataframe(
    top5_display.style.format(
        {
            "기간 일관객 합계": "{:,.0f}명"
        }
    ),
    use_container_width=True
)


# --------------------------------------------------
# TOP 5 영화의 날짜별 일관객 데이터
# --------------------------------------------------

top5_df = df[
    df["영화명"].isin(top5_movies)
].copy()

top5_daily = (
    top5_df
    .groupby(
        ["날짜", "영화명"],
        as_index=False
    )["일관객"]
    .sum()
    .sort_values(
        ["날짜", "영화명"]
    )
)

top5_wide = (
    top5_daily
    .pivot(
        index="날짜",
        columns="영화명",
        values="일관객"
    )
    .sort_index()
    .reset_index()
)

top5_plot = (
    top5_wide
    .melt(
        id_vars="날짜",
        value_vars=top5_movies,
        var_name="영화명",
        value_name="일관객"
    )
    .dropna(subset=["일관객"])
)


# --------------------------------------------------
# 그래프 2 생성
# --------------------------------------------------

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
    category_orders={
        "영화명": top5_movies
    }
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

st.plotly_chart(
    fig2,
    use_container_width=True
)

st.caption(
    "범례의 영화 이름을 클릭하면 해당 영화의 선을 켜거나 끌 수 있습니다."
)

st.markdown("**이 그래프로 알 수 있는 것:**")

st.text_input(
    "그래프 2 해석 문구",
    placeholder="예: 일관객 합계가 큰 영화들의 흥행 시기와 관객 변화 양상을 비교할 수 있다.",
    key="graph2_note"
)


# ==================================================
# 그래프 3
# 날짜별 10위권 일관객 합계
# ==================================================

st.divider()
st.header("📊 그래프 3. 날짜별 10위권 일관객 합계")

st.caption(
    "각 날짜의 박스오피스 1위부터 10위까지의 "
    "일관객을 모두 더해 날짜별 전체 관객 규모를 보여줍니다."
)

# 1~10위 데이터만 선택
top10_df = df[
    df["순위"] <= 10
].copy()

# 날짜별 10위권 일관객 합계
daily_top10 = (
    top10_df
    .groupby(
        "날짜",
        as_index=False
    )["일관객"]
    .sum()
    .sort_values("날짜")
)


# --------------------------------------------------
# 그래프 3 생성
# --------------------------------------------------

fig3 = px.area(
    daily_top10,
    x="날짜",
    y="일관객",
    title="날짜별 10위권 영화의 일관객 합계",
    labels={
        "날짜": "날짜",
        "일관객": "10위권 일관객 합계(명)"
    }
)

fig3.update_traces(
    hovertemplate=(
        "날짜: %{x|%Y-%m-%d}"
        "<br>10위권 일관객 합계: %{y:,}명"
        "<extra></extra>"
    )
)


# --------------------------------------------------
# 합계가 가장 큰 3일
# --------------------------------------------------

top3_days = (
    daily_top10
    .nlargest(
        3,
        "일관객"
    )
)

for _, row in top3_days.iterrows():

    fig3.add_annotation(
        x=row["날짜"],
        y=row["일관객"],
        text=(
            f"{row['날짜'].strftime('%Y-%m-%d')}"
            f"<br>{row['일관객']:,.0f}명"
        ),
        showarrow=True,
        arrowhead=2,
        ax=0,
        ay=-55
    )


fig3.update_layout(
    hovermode="x unified",
    xaxis_title="날짜",
    yaxis_title="10위권 일관객 합계(명)"
)

st.plotly_chart(
    fig3,
    use_container_width=True
)


# --------------------------------------------------
# TOP 3 날짜 표
# --------------------------------------------------

st.write("**10위권 일관객 합계가 가장 높았던 3일**")

top3_display = top3_days.copy()

top3_display["날짜"] = (
    top3_display["날짜"]
    .dt.strftime("%Y-%m-%d")
)

top3_display = top3_display.rename(
    columns={
        "날짜": "날짜",
        "일관객": "10위권 일관객 합계"
    }
)

top3_display = top3_display[
    ["날짜", "10위권 일관객 합계"]
]

st.dataframe(
    top3_display.style.format(
        {
            "10위권 일관객 합계": "{:,.0f}명"
        }
    ),
    use_container_width=True,
    hide_index=True
)

st.markdown("**이 그래프로 알 수 있는 것:**")

st.text_input(
    "그래프 3 해석 문구",
    placeholder="예: 날짜별로 상위 10개 영화의 전체 관객 규모가 어떻게 변화했는지 알 수 있다.",
    key="graph3_note"
)


# ==================================================
# 그래프 4
# 기간 내 일관객 합계 TOP 10
# ==================================================

st.divider()
st.header("📊 그래프 4. 기간 내 일관객 합계 TOP 10")

st.caption(
    "영화별로 이 기간의 일관객을 모두 더해 TOP 10을 선정합니다. "
    "마우스를 올리면 10위권에 든 날수도 확인할 수 있습니다."
)


# --------------------------------------------------
# 영화별 기간 일관객 합계
# --------------------------------------------------

movie_total_all = (
    df.groupby(
        "영화명",
        as_index=False
    )["일관객"]
    .sum()
)


# --------------------------------------------------
# 영화별 10위권 진입 일수
# --------------------------------------------------

top10_entry_days = (
    df[df["순위"] <= 10]
    .groupby("영화명")["날짜"]
    .nunique()
    .reset_index(
        name="10위권 진입 일수"
    )
)


# --------------------------------------------------
# 두 데이터 합치기
# --------------------------------------------------

movie_top10 = movie_total_all.merge(
    top10_entry_days,
    on="영화명",
    how="left"
)

movie_top10["10위권 진입 일수"] = (
    movie_top10["10위권 진입 일수"]
    .fillna(0)
    .astype(int)
)


# --------------------------------------------------
# 일관객 합계 TOP 10
# --------------------------------------------------

top10_movies = (
    movie_top10
    .sort_values(
        "일관객",
        ascending=False
    )
    .head(10)
    .copy()
)


# --------------------------------------------------
# 가로 막대그래프
# --------------------------------------------------

fig4 = px.bar(
    top10_movies,
    x="일관객",
    y="영화명",
    orientation="h",
    title="기간 내 일관객 합계 TOP 10",
    labels={
        "일관객": "기간 일관객 합계(명)",
        "영화명": "영화"
    }
)

# 관객이 많은 영화가 위쪽에 오도록 설정
fig4.update_yaxes(
    categoryorder="total ascending"
)


# --------------------------------------------------
# 마우스를 올렸을 때 표시
# --------------------------------------------------

fig4.update_traces(
    customdata=top10_movies[
        ["10위권 진입 일수"]
    ].values,

    hovertemplate=(
        "영화: %{y}"
        "<br>기간 일관객 합계: %{x:,}명"
        "<br>10위권 진입 일수: %{customdata[0]}일"
        "<extra></extra>"
    )
)

fig4.update_layout(
    xaxis_title="기간 일관객 합계(명)",
    yaxis_title="영화",
    hovermode="closest"
)

st.plotly_chart(
    fig4,
    use_container_width=True
)


st.markdown("**이 그래프로 알 수 있는 것:**")

st.text_input(
    "그래프 4 해석 문구",
    placeholder="예: 기간 동안 관객을 많이 모은 영화와 10위권에 오래 머문 영화를 비교할 수 있다.",
    key="graph4_note"
)


# ==================================================
# 그래프 5
# 월 × 요일별 일관객 합계 히트맵
# ==================================================

st.divider()
st.header("🔥 그래프 5. 월 × 요일별 일관객 합계")

st.caption(
    "날짜에서 월과 요일을 추출하여, "
    "월별·요일별 전체 일관객 합계를 히트맵으로 보여줍니다. "
    "색이 진할수록 관객이 많은 것을 의미합니다."
)


# --------------------------------------------------
# 월과 요일 추출
# --------------------------------------------------

month_weekday_df = df.copy()

# 월 추출
month_weekday_df["월"] = (
    month_weekday_df["날짜"].dt.month
)

# 요일 추출
weekday_map = {
    0: "월요일",
    1: "화요일",
    2: "수요일",
    3: "목요일",
    4: "금요일",
    5: "토요일",
    6: "일요일"
}

month_weekday_df["요일"] = (
    month_weekday_df["날짜"]
    .dt.dayofweek
    .map(weekday_map)
)


# --------------------------------------------------
# 월 × 요일별 일관객 합계
# --------------------------------------------------

month_weekday_total = (
    month_weekday_df
    .groupby(
        ["월", "요일"],
        as_index=False
    )["일관객"]
    .sum()
)


# --------------------------------------------------
# 요일 순서 지정
# --------------------------------------------------

weekday_order = [
    "월요일",
    "화요일",
    "수요일",
    "목요일",
    "금요일",
    "토요일",
    "일요일"
]


# --------------------------------------------------
# 히트맵용 데이터 형태로 변환
# --------------------------------------------------

heatmap_data = (
    month_weekday_total
    .pivot(
        index="월",
        columns="요일",
        values="일관객"
    )
)


# 월 순서
heatmap_data = heatmap_data.sort_index()


# 요일 순서
heatmap_data = heatmap_data.reindex(
    columns=weekday_order
)


# --------------------------------------------------
# 히트맵 생성
# --------------------------------------------------

fig5 = px.imshow(
    heatmap_data,
    labels={
        "x": "요일",
        "y": "월",
        "color": "일관객 합계"
    },
    x=weekday_order,
    y=heatmap_data.index,
    text_auto=".0f",
    aspect="auto",
    title="월 × 요일별 일관객 합계"
)


# --------------------------------------------------
# 마우스를 올렸을 때 표시
# --------------------------------------------------

fig5.update_traces(
    hovertemplate=(
        "%{y}월 %{x}"
        "<br>일관객 합계: %{z:,}명"
        "<extra></extra>"
    )
)


# --------------------------------------------------
# 그래프 레이아웃
# --------------------------------------------------

fig5.update_layout(
    xaxis_title="요일",
    yaxis_title="월",
    coloraxis_colorbar_title="일관객"
)

st.plotly_chart(
    fig5,
    use_container_width=True
)


# --------------------------------------------------
# 그래프 5 해석
# --------------------------------------------------

st.markdown("**이 그래프로 알 수 있는 것:**")

st.text_input(
    "그래프 5 해석 문구",
    placeholder="예: 어떤 월과 요일에 영화 관객이 많이 몰렸는지 한눈에 비교할 수 있다.",
    key="graph5_note"
)
