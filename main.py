스트림릿 앱(main.py)을 새로 만들어 줘. 제목은 '영화 데이터 그래프 도감 2 - 분포와 관계'.
- 데이터는 이 주소에서 불러와:
  https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv
  1년간 박스오피스 10위권에 든 영화 가운데 이 기간에 개봉한 216편의 요약표야. 열은
  movieCd(영화코드) · movieNm(영화명) · openDt(개봉일, 여덟 자리 숫자) ·
  genre(장르 - 세로막대 기호로 여러 개 적힌 영화는 첫 번째 장르만 써) · nation(제작 국가) ·
  first_scrn(개봉일 스크린수) · first_show(개봉일 상영횟수) · first_week_audi(개봉 첫 주 관객) ·
  total_audi(총 관객) · days_in_top10(10위권에 머문 날수).
- 첫 그래프: 장르별 영화 편수를 플롯리 도넛 그래프로 보여 줘. 조각에 마우스를 올리면 편수와 비율이 보이게.
- 그래프마다 아래에 '이 그래프로 알 수 있는 것' 한 문장을 넣을 자리를 만들고, 구역을 나눠 줘.
- 필요한 라이브러리 목록(requirements.txt)도 같이 줘. 버전 숫자 없이 이름만.

It seems like I can’t do more advanced data analysis right now. Please try again later. 

왜 안되?

아까는 코드 내용의 문제가 아니라, 내가 파일을 만들어 주는 도구 호출이 일시적으로 제한되어 실패한 것이야.

즉,

main.py 코드 자체가 잘못돼서 실패한 것 ❌
네 GitHub 데이터 주소가 문제인 것 ❌
Streamlit이나 Plotly 문제인 것 ❌
파일 생성 도구의 일시적인 오류 ⭕

그래서 내가 임의로 다운로드 파일을 만들어서 링크를 줄 수도 없었어.

다시 요청해 주면 main.py와 requirements.txt를 실제 파일로 생성해서 바로 받을 수 있게 해줄게.

광고
스트림릿 앱(main.py)을 새로 만들어 줘. 제목은 '영화 데이터 그래프 도감 2 - 분포와 관계'.
- 데이터는 이 주소에서 불러와:
  https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv
  1년간 박스오피스 10위권에 든 영화 가운데 이 기간에 개봉한 216편의 요약표야. 열은
  movieCd(영화코드) · movieNm(영화명) · openDt(개봉일, 여덟 자리 숫자) ·
  genre(장르 - 세로막대 기호로 여러 개 적힌 영화는 첫 번째 장르만 써) · nation(제작 국가) ·
  first_scrn(개봉일 스크린수) · first_show(개봉일 상영횟수) · first_week_audi(개봉 첫 주 관객) ·
  total_audi(총 관객) · days_in_top10(10위권에 머문 날수).
- 첫 그래프: 장르별 영화 편수를 플롯리 도넛 그래프로 보여 줘. 조각에 마우스를 올리면 편수와 비율이 보이게.
- 그래프마다 아래에 '이 그래프로 알 수 있는 것' 한 문장을 넣을 자리를 만들고, 구역을 나눠 줘.
- 필요한 라이브러리 목록(requirements.txt)도 같이 줘. 버전 숫자 없이 이름만.

It seems like I can’t do more advanced data analysis right now. Please try again later. 

그러면 파일 형태로 만들어줄수는 있을까?

지금은 파일 생성 도구가 일시적으로 제한되어 있어서 실제 .py와 .txt 파일을 만들어 첨부할 수는 없어.

대신 다음 요청에서 도구가 정상화되면 바로 아래 두 파일 형태로 만들어 줄 수 있어.

main.py — 네가 요청한 Streamlit 앱 전체 코드
requirements.txt — streamlit, pandas, plotly

파일 생성이 가능해지면 다운로드 링크까지 포함해서 한 번에 줄게.

광고

Sponsored options
Ad
Sponsored options
Ad
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
