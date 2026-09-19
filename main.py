import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import math


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="영화 유형 나누기",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 유형 나누기")


# =========================================================
# 데이터 주소
# =========================================================
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/main/data/"
    "kobis_movies.csv"
)


# =========================================================
# 사용할 속성
# =========================================================
FEATURES = [
    "스크린 수",
    "누적 관객",
    "10위권 일수",
    "롱런 지수"
]


# 묶음 표시 기호
CLUSTER_SYMBOLS = [
    "㉮",
    "㉯",
    "㉰",
    "㉱",
    "㉲",
    "㉳",
    "㉴"
]


# =========================================================
# 데이터 불러오기
# =========================================================
@st.cache_data
def load_data():

    df = pd.read_csv(
        DATA_URL,
        encoding="utf-8"
    )

    # 숫자로 변환할 열
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

    # -----------------------------------------------------
    # 1. 스크린 수
    # 상용로그
    # -----------------------------------------------------
    df["스크린 수"] = df["first_scrn"].apply(
        lambda x:
        math.log10(x)
        if pd.notna(x) and x > 0
        else float("nan")
    )

    # -----------------------------------------------------
    # 2. 누적 관객
    # 상용로그
    # -----------------------------------------------------
    df["누적 관객"] = df["total_audi"].apply(
        lambda x:
        math.log10(x)
        if pd.notna(x) and x > 0
        else float("nan")
    )

    # -----------------------------------------------------
    # 3. 10위권 일수
    # 그대로 사용
    # -----------------------------------------------------
    df["10위권 일수"] = df["days_in_top10"]

    # -----------------------------------------------------
    # 4. 롱런 지수
    # 누적 관객 / 첫 주 관객
    # 최대 20
    # -----------------------------------------------------
    df["롱런 지수"] = (
        df["total_audi"] /
        df["first_week_audi"]
    ).clip(upper=20)

    return df


# =========================================================
# 데이터 불러오기
# =========================================================
try:

    all_df = load_data()

except Exception as e:

    st.error(
        f"데이터를 불러오는 중 문제가 발생했습니다.\n\n{e}"
    )

    st.stop()


# =========================================================
# 분석 대상 데이터 만들기
# =========================================================
df = all_df.dropna(
    subset=FEATURES + ["first_week_audi"]
).copy()

# 첫 주 관객이 0인 영화 제외
df = df[
    df["first_week_audi"] > 0
].copy()


# =========================================================
# 전체 편수 / 묶은 편수
# =========================================================
st.write(
    f"전체 편수: **{len(all_df):,}편**"
    f"　|　"
    f"묶은 편수: **{len(df):,}편**"
)


# =========================================================
# 묶음 수 선택
# =========================================================
st.subheader("묶음 수 정하기")

cluster_count = st.selectbox(
    "묶을 영화 유형의 수를 고르세요.",
    options=list(range(2, 8)),
    index=1
)


# =========================================================
# 묶음에 사용할 속성 선택
# =========================================================
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


# =========================================================
# 선택한 속성 표준화
# =========================================================
X = df[selected_features]

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


# =========================================================
# 선택한 묶음 수로 K-평균 실행
# =========================================================
kmeans = KMeans(
    n_clusters=cluster_count,
    random_state=42,
    n_init=10
)

df["군집번호"] = kmeans.fit_predict(X_scaled)


# =========================================================
# 누적 관객 평균이 높은 묶음부터
# ㉮, ㉯, ㉰ ... 부여
# =========================================================
cluster_order = (
    df.groupby("군집번호")["total_audi"]
    .mean()
    .sort_values(ascending=False)
    .index
    .tolist()
)


cluster_names = {
    cluster: CLUSTER_SYMBOLS[i]
    for i, cluster in enumerate(cluster_order)
}


df["묶음"] = df["군집번호"].map(
    cluster_names
)


# 현재 묶음 순서
current_symbols = CLUSTER_SYMBOLS[:cluster_count]


# =========================================================
# 2차원 산점도
# =========================================================
st.subheader("2차원 산점도")


col1, col2 = st.columns(2)


with col1:

    x_2d = st.selectbox(
        "가로축 속성",
        FEATURES,
        index=0,
        key="x_2d"
    )


with col2:

    y_2d = st.selectbox(
        "세로축 속성",
        FEATURES,
        index=1,
        key="y_2d"
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
        "묶음": current_symbols
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


# =========================================================
# 3차원 산점도
# =========================================================
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
            "묶음": current_symbols
        }
    )


    # 점을 작게 표시
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


# =========================================================
# 묶음별 편수와 네 속성의 평균
# =========================================================
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
    .reindex(current_symbols)
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


# =========================================================
# 묶음별 누적 관객 상위 5편
# =========================================================
st.subheader("묶음별 누적 관객 상위 5편")


for group in current_symbols:

    st.markdown(
        f"### {group}"
    )

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


# =========================================================
# 묶음 수에 따른 중심에서의 거리 제곱합
# =========================================================
st.subheader("묶음 수에 따른 거리 제곱합")


# 1~7개의 묶음에 대해 각각 K-평균 실행
sse_values = []


for k in range(1, 8):

    kmeans_test = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    kmeans_test.fit(X_scaled)

    # 각 점에서 자신이 속한 중심까지의
    # 거리 제곱의 합
    sse_values.append(
        kmeans_test.inertia_
    )


# =========================================================
# 엘보 그래프
# =========================================================
fig_elbow = go.Figure()


fig_elbow.add_trace(
    go.Scatter(
        x=list(range(1, 8)),
        y=sse_values,
        mode="lines+markers",
        name="거리 제곱합"
    )
)


# 현재 선택한 묶음 수에 세로선
fig_elbow.add_vline(
    x=cluster_count,
    line_dash="dash",
    annotation_text=f"현재 선택: {cluster_count}개",
    annotation_position="top"
)


fig_elbow.update_layout(
    xaxis_title="묶음 수",
    yaxis_title="중심에서의 거리 제곱합",
    xaxis=dict(
        tickmode="linear",
        dtick=1
    ),
    showlegend=False
)


st.plotly_chart(
    fig_elbow,
    use_container_width=True
)


# =========================================================
# 거리 제곱합 표
# =========================================================
sse_table = []


for i in range(7):

    k = i + 1

    current_value = sse_values[i]


    if i == 0:

        reduction = None

    else:

        reduction = (
            sse_values[i - 1]
            - current_value
        )


    sse_table.append(
        {
            "묶음 수": k,
            "거리 제곱합": current_value,
            "바로 앞 값에서 감소한 값": reduction
        }
    )


sse_df = pd.DataFrame(
    sse_table
)


st.dataframe(
    sse_df.style.format(
        {
            "묶음 수": "{:,.0f}",
            "거리 제곱합": "{:,.2f}",
            "바로 앞 값에서 감소한 값": (
                lambda x:
                "" if pd.isna(x)
                else f"{x:,.2f}"
            )
        }
    ),
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 선택한 묶음 수의 실루엣 점수
# =========================================================
silhouette = silhouette_score(
    X_scaled,
    df["군집번호"]
)


st.write(
    f"현재 선택한 묶음 수 **{cluster_count}개**의 "
    f"실루엣 점수: **{silhouette:.3f}**"
)


st.caption(
    "실루엣 점수는 -1에서 1 사이의 값이며, "
    "1에 가까울수록 묶음이 서로 뚜렷하게 나뉘어 있음을 의미합니다."
)
