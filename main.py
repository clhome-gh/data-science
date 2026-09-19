import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import math


# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="영화 유형 나누기",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 유형 나누기")


# -----------------------------
# 데이터 불러오기
# -----------------------------
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/main/data/"
    "kobis_movies.csv"
)


@st.cache_data
def load_data():

    df = pd.read_csv(DATA_URL, encoding="utf-8")

    # 숫자로 변환
    numeric_columns = [
        "first_scrn",
        "first_show",
        "first_date",
        "peak",
        "first_week_audi",
        "total_audi",
        "days_in_top10"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # -------------------------
    # 분석에 사용할 속성 생성
    # -------------------------

    # 스크린 수 → 상용로그
    df["스크린 수"] = df["first_scrn"].apply(
        lambda x: math.log10(x) if pd.notna(x) and x > 0 else float("nan")
    )

    # 누적 관객 → 상용로그
    df["누적 관객"] = df["total_audi"].apply(
        lambda x: math.log10(x) if pd.notna(x) and x > 0 else float("nan")
    )

    # 10위권 일수 → 그대로 사용
    df["10위권 일수"] = df["days_in_top10"]

    # 롱런 지수 = 누적 관객 / 첫 주 관객
    # 20을 넘으면 20으로 제한
    df["롱런 지수"] = (
        df["total_audi"] / df["first_week_audi"]
    ).clip(upper=20)

    return df


try:
    all_df = load_data()

except Exception as e:
    st.error(
        f"데이터를 불러오는 중 문제가 발생했습니다.\n\n{e}"
    )
    st.stop()


# -----------------------------
# 사용할 속성
# -----------------------------
FEATURES = [
    "스크린 수",
    "누적 관객",
    "10위권 일수",
    "롱런 지수"
]


# -----------------------------
# 결측치 및 첫 주 관객 0 제거
# -----------------------------
df = all_df.dropna(
    subset=FEATURES + ["first_week_audi"]
).copy()

df = df[
    df["first_week_audi"] > 0
].copy()


# -----------------------------
# 전체 편수 / 묶은 편수
# -----------------------------
st.write(
    f"전체 편수: **{len(all_df):,}편**"
    f"　|　"
    f"묶은 편수: **{len(df):,}편**"
)


# -----------------------------
# 군집화 속성 선택
# -----------------------------
selected_features = st.multiselect(
    "묶는 데 사용할 속성을 고르세요.",
    options=FEATURES,
    default=FEATURES
)


if len(selected_features) < 2:

    st.warning(
        "묶는 데 사용할 속성을 두 개 이상 골라 주세요."
    )

    st.stop()


# -----------------------------
# 선택한 속성 표준화
# -----------------------------
X = df[selected_features]

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


# -----------------------------
# K-평균 군집화
# -----------------------------
kmeans = KMeans(
    n_clusters=3,
    random_state=42,
    n_init=10
)

df["군집번호"] = kmeans.fit_predict(X_scaled)


# -----------------------------
# 누적 관객 평균을 기준으로
# ㉮ → ㉯ → ㉰ 순서 결정
# -----------------------------
cluster_order = (
    df.groupby("군집번호")["total_audi"]
    .mean()
    .sort_values(ascending=False)
    .index
    .tolist()
)


cluster_names = {
    cluster: ["㉮", "㉯", "㉰"][i]
    for i, cluster in enumerate(cluster_order)
}


df["묶음"] = df["군집번호"].map(cluster_names)


# -----------------------------
# 2차원 산점도
# -----------------------------
st.subheader("2차원 산점도")


col1, col2 = st.columns(2)


with col1:

    x_2d = st.selectbox(
        "가로축 속성",
        FEATURES,
        index=0
    )


with col2:

    y_2d = st.selectbox(
        "세로축 속성",
        FEATURES,
        index=1
    )


fig_2d = px.scatter(
    df,
    x=x_2d,
    y=y_2d,
    color="묶음",
    hover_name="movieNm",
    hover_data={
        "묶음": True
    },
    category_orders={
        "묶음": ["㉮", "㉯", "㉰"]
    }
)

fig_2d.update_traces(
    marker={
        "size": 7
    }
)

fig_2d.update_layout(
    legend_title="묶음"
)

st.plotly_chart(
    fig_2d,
    use_container_width=True
)


# -----------------------------
# 3차원 산점도
# -----------------------------
st.subheader("3차원 산점도")


if len(selected_features) < 3:

    st.info(
        "묶는 데 사용할 속성을 세 개 이상 골라야 "
        "3차원 산점도를 표시할 수 있습니다."
    )

else:

    col1, col2, col3 = st.columns(3)


    with col1:

        x_3d = st.selectbox(
            "x축 속성",
            FEATURES,
            index=0,
            key="x_3d"
        )


    with col2:

        y_3d = st.selectbox(
            "y축 속성",
            FEATURES,
            index=1,
            key="y_3d"
        )


    with col3:

        z_3d = st.selectbox(
            "z축 속성",
            FEATURES,
            index=2,
            key="z_3d"
        )


    fig_3d = px.scatter_3d(
        df,
        x=x_3d,
        y=y_3d,
        z=z_3d,
        color="묶음",
        hover_name="movieNm",
        hover_data={
            "묶음": True
        },
        category_orders={
            "묶음": ["㉮", "㉯", "㉰"]
        }
    )


    fig_3d.update_traces(
        marker={
            "size": 3
        }
    )


    fig_3d.update_layout(
        legend_title="묶음"
    )


    st.plotly_chart(
        fig_3d,
        use_container_width=True
    )


# -----------------------------
# 묶음별 평균
# -----------------------------
st.subheader("묶음별 편수와 속성 평균")


summary = (
    df.groupby("묶음")
    .agg(
        편수=("movieNm", "count"),
        스크린_수_평균=("first_scrn", "mean"),
        누적_관객_평균=("total_audi", "mean"),
        십위권_일수_평균=("days_in_top10", "mean"),
        롱런_지수_평균=("롱런 지수", "mean")
    )
    .reindex(["㉮", "㉯", "㉰"])
    .reset_index()
)


summary.columns = [
    "묶음",
    "편수",
    "스크린 수 평균",
    "누적 관객 평균",
    "10위권 일수 평균",
    "롱런 지수 평균"
]


st.dataframe(
    summary.style.format(
        {
            "편수": "{:,.0f}",
            "스크린 수 평균": "{:,.1f}",
            "누적 관객 평균": "{:,.0f}",
            "10위권 일수 평균": "{:,.1f}",
            "롱런 지수 평균": "{:,.2f}"
        }
    ),
    use_container_width=True,
    hide_index=True
)


# -----------------------------
# 묶음별 누적 관객 TOP 5
# -----------------------------
st.subheader("묶음별 누적 관객 상위 5편")


for group in ["㉮", "㉯", "㉰"]:

    st.markdown(f"### {group}")

    top_movies = (
        df[df["묶음"] == group]
        .sort_values(
            "total_audi",
            ascending=False
        )
        .head(5)
    )

    if len(top_movies) == 0:

        st.write(
            "해당 묶음에 영화가 없습니다."
        )

    else:

        for i, movie in enumerate(
            top_movies["movieNm"],
            start=1
        ):

            st.write(
                f"{i}. {movie}"
            )
