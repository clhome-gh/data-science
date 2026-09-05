import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# --------------------------------------------------
# 1. 기본 화면 설정
# --------------------------------------------------

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")
st.caption("KOBIS 영화관입장권통합전산망 일별 박스오피스")


# --------------------------------------------------
# 2. 한국 시간 기준으로 '어제' 날짜 계산
# --------------------------------------------------
# 배포 서버의 시간이 한국 시간이 아닐 수 있으므로
# 반드시 한국 시간(KST)을 기준으로 날짜를 계산합니다.

KST = ZoneInfo("Asia/Seoul")

now_kst = datetime.now(KST)
yesterday = now_kst.date() - timedelta(days=1)

# KOBIS API가 요구하는 날짜 형식: YYYYMMDD
target_date = yesterday.strftime("%Y%m%d")

# 화면에 보여줄 날짜 형식
display_date = yesterday.strftime("%Y년 %m월 %d일")


# --------------------------------------------------
# 3. KOBIS API에서 박스오피스 가져오기
# --------------------------------------------------
# cache_data를 사용하면 같은 날짜를 다시 조회할 때
# API를 매번 호출하지 않고 약 1시간 동안 저장된 결과를 사용합니다.

@st.cache_data(ttl=3600)
def get_boxoffice(target_dt):
    """
    KOBIS 일별 박스오피스 API를 호출하는 함수입니다.
    target_dt는 YYYYMMDD 형식의 날짜입니다.
    """

    # Streamlit Cloud의 Secrets에서 인증키를 가져옵니다.
    # 실제 인증키는 코드에 직접 작성하지 않습니다.
    api_key = st.secrets["4a3741de944ebaa4c3d4512fd624b8a2"]

    url = (
        "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
        "boxoffice/searchDailyBoxOfficeList.json"
    )

    # API에 보낼 요청값
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

        # HTTP 오류가 발생했는지 확인
        response.raise_for_status()

        # JSON 형식으로 변환
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
                "KOBIS API의 응답을 JSON으로 읽지 못했습니다.\n\n"
                "KOBIS API 서버의 응답 상태나 요청 주소를 확인해 주세요."
            )
        }

    # --------------------------------------------------
    # 4. 인증키 오류 확인
    # --------------------------------------------------
    # KOBIS는 인증키가 잘못되어도 HTTP 상태코드가 200일 수 있습니다.
    # 따라서 faultInfo가 있는지 반드시 확인합니다.

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
                "- Streamlit Cloud의 Secrets에 KOBIS_KEY가 등록되어 있는지\n"
                "- KOBIS_KEY의 값이 정확한지\n"
                "- KOBIS Open API 이용 권한이 있는지"
            )
        }

    # --------------------------------------------------
    # 5. 정상적인 박스오피스 데이터인지 확인
    # --------------------------------------------------

    boxoffice_result = data.get("boxOfficeResult")

    if not boxoffice_result:
        return {
            "success": False,
            "message": (
                "박스오피스 결과(boxOfficeResult)를 찾지 못했습니다.\n\n"
                "KOBIS API 응답 구조가 정상인지 확인해 주세요."
            )
        }

    movie_list = boxoffice_result.get("dailyBoxOfficeList", [])

    # 영화 목록이 비어 있는 경우
    if not movie_list:
        return {
            "success": False,
            "message": (
                f"{target_dt} 날짜의 영화 목록이 비어 있습니다.\n\n"
                "다음 사항을 확인해 주세요.\n"
                "- 조회 날짜에 박스오피스 데이터가 존재하는지\n"
                "- KOBIS API가 해당 날짜의 데이터를 제공하는지\n"
                "- API 응답에 dailyBoxOfficeList가 포함되어 있는지"
            )
        }

    return {
        "success": True,
        "data": movie_list
    }


# --------------------------------------------------
# 6. API 호출
# --------------------------------------------------

result = get_boxoffice(target_date)


# --------------------------------------------------
# 7. API 오류가 발생하면 사용자에게 안내
# --------------------------------------------------

if not result["success"]:
    st.error("박스오피스 정보를 가져오지 못했습니다.")

    # 여러 줄의 안내문을 화면에 표시
    st.warning(result["message"])

    # 오류가 발생했을 때 아래 내용을 실행하지 않도록 종료
    st.stop()


# --------------------------------------------------
# 8. 영화 데이터를 표 형태로 변환
# --------------------------------------------------

movies = result["data"]

df = pd.DataFrame(movies)


# --------------------------------------------------
# 9. 숫자로 변환
# --------------------------------------------------
# KOBIS API에서는 숫자도 문자열로 전달됩니다.
# 그래프와 정렬에 제대로 사용하기 위해 숫자로 변환합니다.

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
# 10. 순위 기준으로 정렬
# --------------------------------------------------

df = df.sort_values("rank")


# --------------------------------------------------
# 11. 조회 날짜 표시
# --------------------------------------------------

st.subheader(f"📅 {display_date}")

st.write(
    f"한국 시간 기준 어제({target_date})의 일별 박스오피스입니다."
)


# --------------------------------------------------
# 12. 1위 영화 확인
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
            "오늘의 관객수",
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
# 13. 관객수 상위 5편 막대그래프
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

# 영화 이름을 인덱스로 설정하면
# Streamlit의 bar_chart에서 영화별 관객수를 쉽게 표시할 수 있습니다.

chart_data = top5[
    ["movieNm", "audiCnt"]
].set_index("movieNm")

st.bar_chart(
    chart_data,
    y="audiCnt"
)


# --------------------------------------------------
# 14. 전체 박스오피스 표
# --------------------------------------------------

st.subheader("🎞️ 전체 박스오피스")

# 사용자에게 보여줄 열만 선택합니다.
display_df = df[
    [
        "rank",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()

# 표의 한글 열 이름으로 변경합니다.
display_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]

# 숫자에 천 단위 쉼표를 표시하기 위한 함수
def format_number(value):
    return f"{value:,}"


# 관객수, 누적관객, 스크린수를 보기 좋게 표시
display_df["관객수"] = display_df["관객수"].apply(format_number)
display_df["누적관객"] = display_df["누적관객"].apply(format_number)
display_df["스크린수"] = display_df["스크린수"].apply(format_number)


# 표 출력
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 15. 하단 안내
# --------------------------------------------------

st.caption(
    "※ 데이터 출처: 영화관입장권통합전산망(KOBIS) 일별 박스오피스 API"
)

st.caption(
    "※ 데이터는 한국 시간 기준 어제 날짜를 조회합니다."
)
