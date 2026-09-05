import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# --------------------------------------------------
# 1. 기본 화면 설정
# --------------------------------------------------

st.set_page_config(
    page_title="박스오피스 조회",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 일별 박스오피스")
st.caption("KOBIS 영화관입장권통합전산망 일별 박스오피스")


# --------------------------------------------------
# 2. 한국 시간 기준 날짜 계산
# --------------------------------------------------
# 배포 서버가 한국 시간이 아닐 수도 있기 때문에
# 반드시 한국 시간(KST)을 기준으로 오늘 날짜를 계산합니다.

KST = ZoneInfo("Asia/Seoul")

now_kst = datetime.now(KST)
today = now_kst.date()

# 오늘 영화 데이터는 아직 집계 전이므로
# 가장 최근에 조회할 수 있는 날짜는 '어제'입니다.
yesterday = today - timedelta(days=1)


# --------------------------------------------------
# 3. 달력에서 조회 날짜 선택
# --------------------------------------------------
# 사용자가 달력에서 원하는 날짜를 선택합니다.
# 가장 늦은 날짜는 어제입니다.

selected_date = st.date_input(
    "📅 조회할 날짜를 선택하세요",
    value=yesterday,
    max_value=yesterday
)

# KOBIS API가 요구하는 YYYYMMDD 형식으로 변환
target_date = selected_date.strftime("%Y%m%d")

# 화면에 표시할 날짜
display_date = selected_date.strftime("%Y년 %m월 %d일")


# --------------------------------------------------
# 4. KOBIS API 호출 함수
# --------------------------------------------------
# 같은 날짜를 다시 조회하면 약 1시간 동안
# 저장된 결과를 사용하도록 캐시합니다.

@st.cache_data(ttl=3600)
def get_boxoffice(target_dt):

    # Streamlit Cloud Secrets에서 인증키를 가져옵니다.
    # 실제 인증키는 코드에 작성하지 않습니다.
    api_key = st.secrets["KOBIS_KEY"]

    url = (
        "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
        "boxoffice/searchDailyBoxOfficeList.json"
    )

    params = {
        "key": api_key,
        "targetDt": target_dt
    }

    try:
        # KOBIS API 요청
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        # HTTP 오류 확인
        response.raise_for_status()

        # JSON 데이터로 변환
        data = response.json()

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "message": (
                "KOBIS API에 접속하지 못했습니다.\n\n"
                "다음 사항을 확인해 주세요.\n"
                "- 인터넷 연결 상태\n"
                "- KOBIS API 서버 상태\n"
                "- API 요청 주소가 올바른지\n"
                f"- 요청 오류: {e}"
            )
        }

    except ValueError:

        return {
            "success": False,
            "message": (
                "KOBIS API의 응답을 읽지 못했습니다.\n\n"
                "KOBIS API 서버의 응답 상태를 확인해 주세요."
            )
        }


    # --------------------------------------------------
    # 5. KOBIS 오류(faultInfo) 확인
    # --------------------------------------------------
    # 인증키가 잘못되어도 HTTP 상태코드는 200일 수 있으므로
    # faultInfo가 있는지 별도로 확인합니다.

    if "faultInfo" in data:

        fault_info = data["faultInfo"]

        fault_code = fault_info.get("errorCode", "")
        fault_message = fault_info.get("message", "")

        return {
            "success": False,
            "message": (
                "KOBIS API에서 오류를 반환했습니다.\n\n"
                f"오류 코드: {fault_code}\n"
                f"오류 내용: {fault_message}\n\n"
                "다음 사항을 확인해 주세요.\n"
                "- Streamlit Cloud Secrets에 KOBIS_KEY가 등록되어 있는지\n"
                "- KOBIS_KEY가 정확한지\n"
                "- KOBIS Open API 이용 권한이 있는지"
            )
        }


    # --------------------------------------------------
    # 6. 박스오피스 결과 확인
    # --------------------------------------------------

    boxoffice_result = data.get("boxOfficeResult")

    if not boxoffice_result:

        return {
            "success": False,
            "message": (
                "박스오피스 결과를 찾지 못했습니다.\n\n"
                "KOBIS API 응답을 확인해 주세요."
            )
        }


    movie_list = boxoffice_result.get(
        "dailyBoxOfficeList",
        []
    )


    # --------------------------------------------------
    # 7. 영화 목록이 비어 있는 경우
    # --------------------------------------------------
    # 사용자가 요구한 문구를 표시하기 위해
    # 별도의 상태값을 반환합니다.

    if not movie_list:

        return {
            "success": False,
            "empty": True,
            "message": "그날은 아직 집계 전입니다."
        }


    return {
        "success": True,
        "empty": False,
        "data": movie_list
    }


# --------------------------------------------------
# 8. 선택한 날짜의 데이터 가져오기
# --------------------------------------------------

result = get_boxoffice(target_date)


# --------------------------------------------------
# 9. API 오류 또는 데이터 없음 처리
# --------------------------------------------------

if not result["success"]:

    if result.get("empty", False):

        # 영화 목록이 비어 있는 경우
        st.info(
            f"📅 {display_date}\n\n"
            "그날은 아직 집계 전입니다."
        )

    else:

        # API 오류가 발생한 경우
        st.error(
            "박스오피스 정보를 가져오지 못했습니다."
        )

        st.warning(result["message"])

    # 더 이상 아래 코드를 실행하지 않습니다.
    st.stop()


# --------------------------------------------------
# 10. 영화 데이터를 DataFrame으로 변환
# --------------------------------------------------

movies = result["data"]

df = pd.DataFrame(movies)


# --------------------------------------------------
# 11. 숫자 데이터를 실제 숫자로 변환
# --------------------------------------------------
# KOBIS에서는 숫자도 문자열로 전달됩니다.
# 따라서 정렬과 그래프에 사용하기 전에 숫자로 변환합니다.

number_columns = [
    "rank",
    "rankInten",
    "audiCnt",
    "audiAcc",
    "scrnCnt",
    "showCnt"
]

for column in number_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0).astype(int)


# --------------------------------------------------
# 12. 순위순으로 정렬
# --------------------------------------------------

df = df.sort_values("rank")


# --------------------------------------------------
# 13. 선택한 날짜 표시
# --------------------------------------------------

st.subheader(f"📅 {display_date}")

st.write(
    "선택한 날짜의 일별 박스오피스입니다."
)


# --------------------------------------------------
# 14. 1위 영화 표시
# --------------------------------------------------

if len(df) > 0:

    first_movie = df.iloc[0]

    st.subheader("🏆 1위 영화")

    st.markdown(
        f"## 🎬 {first_movie['movieNm']}"
    )


    # --------------------------------------------------
    # 지표 카드 3개
    # --------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "관객수",
            f"{first_movie['audiCnt']:,}명"
        )

    with col2:

        st.metric(
            "누적 관객수",
            f"{first_movie['audiAcc']:,}명"
        )

    with col3:

        st.metric(
            "스크린 수",
            f"{first_movie['scrnCnt']:,}개"
        )


# --------------------------------------------------
# 15. 관객수 상위 5편 막대그래프
# --------------------------------------------------

st.subheader("📊 관객수 상위 5편")

top5 = (
    df.sort_values(
        "audiCnt",
        ascending=False
    )
    .head(5)
    .copy()
)

chart_data = top5[
    ["movieNm", "audiCnt"]
].set_index("movieNm")

st.bar_chart(
    chart_data,
    y="audiCnt"
)


# --------------------------------------------------
# 16. 전체 박스오피스 표 만들기
# --------------------------------------------------

st.subheader("🎞️ 전체 박스오피스")


# 표에 사용할 데이터만 복사합니다.
display_df = df[
    [
        "rank",
        "rankInten",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()


# --------------------------------------------------
# 17. 순위 변동 화살표 만들기
# --------------------------------------------------
# rankInten은 전날 대비 순위 변화입니다.
#
# 양수 → 순위가 오른 영화 → 🔺 빨간색
# 음수 → 순위가 내려간 영화 → 🔻 파란색
# 0    → 순위 변화 없음 → -
#
# 여기서는 표 안에서 색깔을 표현하기 위해
# HTML을 사용합니다.

def make_rank_change(value):

    value = int(value)

    if value > 0:
        return f"🔴 ↑ {value}"

    elif value < 0:
        return f"🔵 ↓ {abs(value)}"

    else:
        return "-"


display_df["rankChange"] = (
    display_df["rankInten"]
    .apply(make_rank_change)
)


# --------------------------------------------------
# 18. 표의 열 이름 변경
# --------------------------------------------------

display_df = display_df[
    [
        "rank",
        "rankChange",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
]

display_df.columns = [
    "순위",
    "순위 변동",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]


# --------------------------------------------------
# 19. 숫자에 천 단위 쉼표 표시
# --------------------------------------------------

display_df["관객수"] = (
    display_df["관객수"]
    .apply(lambda x: f"{x:,}")
)

display_df["누적관객"] = (
    display_df["누적관객"]
    .apply(lambda x: f"{x:,}")
)

display_df["스크린수"] = (
    display_df["스크린수"]
    .apply(lambda x: f"{x:,}")
)


# --------------------------------------------------
# 20. 최종 표 출력
# --------------------------------------------------

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 21. 데이터 출처 안내
# --------------------------------------------------

st.caption(
    "※ 데이터 출처: 영화관입장권통합전산망(KOBIS) "
    "일별 박스오피스 API"
)

st.caption(
    "※ 조회 가능한 가장 최근 날짜는 한국 시간 기준 어제입니다."
)
