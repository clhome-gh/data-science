import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------
# 페이지 설정
# ---------------------------------------
st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")

st.write(
    "1년간 박스오피스 10위권에 든 영화 가운데 "
    "이 기간에 개봉한 216편의 데이터를 살펴봅니다."
)

# ---------------------------------------
# 데이터 주소
# ---------------------------------------
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "main/data/kobis_movies.csv"
)


# ---------------------------------------
# 데이터 불러오기
# ---------------------------------------
@st.cache_data
def load_data():

    df = pd.read_csv(DATA_URL)

    # 개봉일 처리
    df["openDt"] = pd.to_datetime(
        df["openDt"].astype(str).str.strip(),
        format="%Y%m%d",
        errors="coerce"
    )

    # -----------------------------------
    # 장르 처리
    # -----------------------------------
    # NaN, 숫자형 등 어떤 값이 들어와도
    # 안전하게 문자열로 변환
    df["genre"] = df["genre"].apply(
        lambda x:
            "미상"
            if pd.isna(x)
            else str(x).split("|")[0].strip()
    )

    # 빈 장르 처리
    df.loc[df["genre"] == "", "genre"] = "미상"

    return df


# ---------------------------------------
# 데이터 불러오기
# ---------------------------------------
try:
    df = load_data()

except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.exception(e)
    st.stop()


# ---------------------------------------
# 데이터 확인
# ---------------------------------------
st.success(f"총 {len(df)}편의 영화 데이터를 불러왔습니다.")


# =======================================
# 그래프 1
# 장르별 영화 편수
# =======================================

st.subheader("① 장르별 영화 편수")

genre_counts = (
    df["genre"]
    .value_counts()
    .reset_index()
)

genre_counts.columns = ["genre", "count"]

# 비율 계산
genre_counts["ratio"] = (
    genre_counts["count"] /
    genre_counts["count"].sum()
)


# ---------------------------------------
# 도넛 그래프
# ---------------------------------------
fig = px.pie(
    genre_counts,
    names="genre",
    values="count",
    hole=0.55,
    title="장르별 영화 편수"
)

# 마우스를 올렸을 때
# 장르 / 편수 / 비율 표시
fig.update_traces(
    customdata=genre_counts[["count", "ratio"]],
    hovertemplate=(
        "<b>%{label}</b><br>"
        "편수: %{customdata[0]}편<br>"
        "비율: %{customdata[1]:.1%}"
        "<extra></extra>"
    )
)

fig.update_layout(
    height=550,
    margin=dict(
        t=70,
        b=30,
        l=20,
        r=20
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ---------------------------------------
# 그래프 설명 영역
# ---------------------------------------
st.markdown("---")

st.markdown("### 📝 이 그래프로 알 수 있는 것")

st.text_input(
    "내용을 입력하세요.",
    placeholder=(
        "예: 이 기간에는 어떤 장르의 영화가 "
        "가장 많이 개봉했는지 알 수 있다."
    ),
    key="graph1_note",
    label_visibility="collapsed"
)
