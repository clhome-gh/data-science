from pathlib import Path

main_py = '''import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 개봉일: 여덟 자리 숫자 → 날짜
    df["openDt"] = pd.to_datetime(
        df["openDt"].astype(str),
        format="%Y%m%d",
        errors="coerce"
    )

    # 여러 장르가 |로 구분되어 있으면 첫 번째 장르만 사용
    df["genre"] = (
        df["genre"]
        .fillna("미상")
        .astype(str)
        .str.split("|")
        .str[0]
        .str.strip()
    )

    return df

try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오지 못했습니다.")
    st.exception(e)
    st.stop()

# --------------------------------------------------
# ① 장르별 영화 편수
# --------------------------------------------------
st.subheader("① 장르별 영화 편수")

genre_counts = (
    df["genre"]
    .value_counts()
    .rename_axis("genre")
    .reset_index(name="count")
)

genre_counts["ratio"] = genre_counts["count"] / genre_counts["count"].sum()

fig = px.pie(
    genre_counts,
    names="genre",
    values="count",
    hole=0.55,
    title="장르별 영화 편수",
    custom_data=["count", "ratio"]
)

fig.update_traces(
    hovertemplate=(
        "<b>%{label}</b><br>"
        "편수: %{customdata[0]}편<br>"
        "비율: %{customdata[1]:.1%}"
        "<extra></extra>"
    )
)

fig.update_layout(
    height=550,
    margin=dict(t=70, b=30, l=20, r=20)
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("### 이 그래프로 알 수 있는 것")
st.text_input(
    "한 문장으로 작성하세요.",
    placeholder="예: 이 기간에는 어떤 장르의 영화가 많이 개봉했는지 알 수 있다.",
    key="graph1_note",
    label_visibility="collapsed"
)
'''

requirements_txt = '''streamlit
pandas
plotly
'''

Path("/mnt/data/main.py").write_text(main_py, encoding="utf-8")
Path("/mnt/data/requirements.txt").write_text(requirements_txt, encoding="utf-8")

print("파일 생성 완료")
