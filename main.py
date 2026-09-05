import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# ==================================================
# 1. 기본 화면 설정
# ==================================================

st.set_page_config(
    page_title="일별 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 일별 박스오피스")
st.caption("KOBIS 영화관입장권통합전산망")


# ==================================================
# 2. 한국 시간 기준 날짜 계산
# ==================================================

KST = ZoneInfo("Asia/Seoul")

now_kst = datetime.now(KST)

today = now_kst.date()

# 오늘 데이터는 아직 집계 전이므로
# 가장 최근 날짜는 어제입니다.
yesterday = today - timedelta(days=1)


# ==================================================
# 3. 날짜 선택
# ==================================================

selected_date = st.date_input(
    "📅 조회할 날짜",
    value=yesterday,
    max_value=yesterday
)

target_date = selected_date.strftime("%Y%m%d")

display_date = selected_date.strftime(
    "%Y년 %m월 %d일"
)


# ==================================================
# 4. KOBIS API 호출
# ==================================================

@st.cache_data(ttl=3600)
def get_boxoffice(target_dt):

    api_key = st.secrets["KOBIS_KEY"]

    url = (
        "https://www.kobis.or.kr/"
        "kobisopenapi/webservice/rest/boxoffice/"
        "searchDailyBoxOfficeList.json"
    )

    params = {
        "key": api_key,
        "targetDt": target_dt
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "empty": False,
            "message": (
                "KOBIS API에 접속하지 못했습니다.\n\n"
                "다음 사항을 확인해 주세요.\n"
                "• 인터넷 연결 상태\n"
                "• KOBIS API 서버 상태\n"
                "• API 요청 주소\n"
                f"• 오류 내용: {e}"
            )
        }

    except ValueError:

        return {
            "success": False,
            "empty": False,
            "message": (
                "KOBIS API의 응답을 읽지 못했습니다.\n\n"
                "KOBIS API 서버 상태를 확인해 주세요."
            )
        }


    # ==================================================
    # KOBIS 오류 확인
    # ==================================================

    if "faultInfo" in data:

        fault_info = data["faultInfo"]

        error_code = fault_info.get(
            "errorCode",
            ""
        )

        error_message = fault_info.get(
            "message",
            ""
        )

        return {
            "success": False,
            "empty": False,
            "message": (
                "KOBIS API에서 오류를 반환했습니다.\n\n"
                f"오류 코드: {error_code}\n"
                f"오류 내용: {error_message}\n\n"
                "다음 사항을 확인해 주세요.\n"
                "• Streamlit Cloud Secrets에 KOBIS_KEY가 있는지\n"
                "• KOBIS_KEY가 정확한지\n"
                "• KOBIS Open API 사용 권한이 있는지"
            )
        }


    # ==================================================
    # 박스오피스 결과 확인
    # ==================================================

    boxoffice_result = data.get(
        "boxOfficeResult"
    )

    if not boxoffice_result:

        return {
            "success": False,
            "empty": False,
            "message": (
                "박스오피스 결과를 찾지 못했습니다.\n\n"
                "KOBIS API의 응답 내용을 확인해 주세요."
            )
        }


    movie_list = boxoffice_result.get(
        "dailyBoxOfficeList",
        []
    )


    # ==================================================
    # 영화 목록이 없는 경우
    # ==================================================

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


# ==================================================
# 5. 위키백과에서 포스터 자동 검색
# ==================================================

@st.cache_data(ttl=86400)
def get_poster_url(movie_name):

    """
    영화 제목을 이용해서 한국어 위키백과에서
    영화 포스터 이미지를 자동으로 검색합니다.

    별도의 API 키가 필요하지 않습니다.
    """

    search_url = "https://ko.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": movie_name,
        "gsrnamespace": 0,
        "gsrlimit": 5,
        "prop": "pageimages",
        "piprop": "thumbnail",
        "pithumbsize": 500,
        "format": "json",
        "formatversion": 2
    }

    try:

        response = requests.get(
            search_url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "DailyBoxOfficeStreamlit/1.0"
            }
        )

        response.raise_for_status()

        data = response.json()

    except Exception:
        return None


    pages = data.get(
        "query",
        {}
    ).get(
        "pages",
        []
    )


    if not pages:
        return None


    # --------------------------------------------------
    # 1순위: 영화 제목과 정확히 같은 문서
    # --------------------------------------------------

    movie_name_clean = (
        movie_name
        .replace(" ", "")
        .lower()
    )

    for page in pages:

        page_title = page.get(
            "title",
            ""
        )

        page_title_clean = (
            page_title
            .replace(" ", "")
            .lower()
        )

        if page_title_clean == movie_name_clean:

            thumbnail = page.get(
                "thumbnail"
            )

            if thumbnail:

                return thumbnail.get(
                    "source"
                )


    # --------------------------------------------------
    # 2순위: 검색 결과 중 이미지가 있는 문서
    # --------------------------------------------------

    for page in pages:

        thumbnail = page.get(
            "thumbnail"
        )

        if thumbnail:

            return thumbnail.get(
                "source"
            )


    return None


# ==================================================
# 6. KOBIS 데이터 가져오기
# ==================================================

result = get_boxoffice(
    target_date
)


# ==================================================
# 7. 오류 처리
# ==================================================

if not result["success"]:

    if result["empty"]:

        st.info(
            f"📅 {display_date}\n\n"
            "그날은 아직 집계 전입니다."
        )

    else:

        st.error(
            "박스오피스 정보를 가져오지 못했습니다."
        )

        st.warning(
            result["message"]
        )

    st.stop()


# ==================================================
# 8. DataFrame으로 변환
# ==================================================

movies = result["data"]

df = pd.DataFrame(
    movies
)


# ==================================================
# 9. 숫자 데이터를 숫자로 변환
# ==================================================

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


# ==================================================
# 10. 순위순 정렬
# ==================================================

df = df.sort_values(
    "rank"
).reset_index(drop=True)


# ==================================================
# 11. 영화 포스터 자동 검색
# ==================================================

with st.spinner("🎬 영화 포스터를 찾는 중입니다..."):

    df["poster_url"] = df["movieNm"].apply(
        get_poster_url
    )


# ==================================================
# 12. 날짜 표시
# ==================================================

st.subheader(
    f"📅 {display_date}"
)

st.write(
    "선택한 날짜의 일별 박스오피스입니다."
)


# ==================================================
# 13. 1위 영화
# ==================================================

first_movie = df.iloc[0]

st.subheader(
    "🏆 1위 영화"
)

poster_col, info_col = st.columns(
    [1, 2]
)


# --------------------------------------------------
# 1위 포스터
# --------------------------------------------------

with poster_col:

    if first_movie["poster_url"]:

        st.image(
            first_movie["poster_url"],
            width=250
        )

    else:

        st.markdown(
            """
            <div style="
                width:250px;
                height:350px;
                display:flex;
                align-items:center;
                justify-content:center;
                background:#eeeeee;
                border-radius:10px;
                font-size:60px;
            ">
                🎬
            </div>
            """,
            unsafe_allow_html=True
        )


# --------------------------------------------------
# 1위 영화 정보
# --------------------------------------------------

with info_col:

    st.markdown(
        f"# {first_movie['movieNm']}"
    )

    st.write(
        f"개봉일: {first_movie['openDt']}"
    )

    metric1, metric2, metric3 = st.columns(3)

    with metric1:

        st.metric(
            "관객수",
            f"{first_movie['audiCnt']:,}명"
        )

    with metric2:

        st.metric(
            "누적관객",
            f"{first_movie['audiAcc']:,}명"
        )

    with metric3:

        st.metric(
            "스크린수",
            f"{first_movie['scrnCnt']:,}개"
        )


# ==================================================
# 14. 관객수 TOP 5
# ==================================================

st.subheader(
    "📊 관객수 TOP 5"
)

top5 = (
    df.sort_values(
        "audiCnt",
        ascending=False
    )
    .head(5)
    .copy()
)


# --------------------------------------------------
# TOP 5 포스터
# --------------------------------------------------

poster_columns = st.columns(5)

for i, (_, movie) in enumerate(
    top5.iterrows()
):

    with poster_columns[i]:

        if movie["poster_url"]:

            st.image(
                movie["poster_url"],
                use_container_width=True
            )

        else:

            st.markdown(
                """
                <div style="
                    height:250px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    background:#eeeeee;
                    border-radius:8px;
                    font-size:40px;
                ">
                    🎬
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(
            f"**{movie['movieNm']}**"
        )

        st.caption(
            f"{movie['audiCnt']:,}명"
        )


# ==================================================
# 15. TOP 5 막대그래프
# ==================================================

chart_data = (
    top5[
        ["movieNm", "audiCnt"]
    ]
    .set_index("movieNm")
)

st.bar_chart(
    chart_data,
    y="audiCnt"
)


# ==================================================
# 16. 전체 박스오피스
# ==================================================

st.subheader(
    "🎞️ 전체 박스오피스"
)


display_df = df[
    [
        "rank",
        "rankInten",
        "poster_url",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()


# ==================================================
# 17. 순위 변동 화살표
# ==================================================

def make_rank_change(value):

    value = int(value)

    if value > 0:

        return f"🔴 ↑ {value}"

    elif value < 0:

        return f"🔵 ↓ {abs(value)}"

    else:

        return "—"


display_df["rankChange"] = (
    display_df["rankInten"]
    .apply(make_rank_change)
)


# ==================================================
# 18. 표에 사용할 열 선택
# ==================================================

display_df = display_df[
    [
        "rank",
        "rankChange",
        "poster_url",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
]


# ==================================================
# 19. 열 이름 변경
# ==================================================

display_df.columns = [
    "순위",
    "순위 변동",
    "포스터",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]


# ==================================================
# 20. 숫자에 천 단위 쉼표 표시
# ==================================================

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


# ==================================================
# 21. 포스터가 없는 경우 빈 값
# ==================================================

display_df["포스터"] = (
    display_df["포스터"]
    .fillna("")
)


# ==================================================
# 22. 전체 표 출력
# ==================================================

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,

    column_config={

        "포스터": st.column_config.ImageColumn(
            "포스터",
            help="자동으로 검색한 영화 포스터"
        )

    }
)


# ==================================================
# 23. 데이터 출처
# ==================================================

st.divider()

st.caption(
    "※ 박스오피스 데이터: "
    "영화관입장권통합전산망(KOBIS)"
)

st.caption(
    "※ 포스터: 한국어 위키백과에서 영화 제목으로 자동 검색"
)

st.caption(
    "※ 조회 가능한 가장 늦은 날짜는 "
    "한국 시간 기준 어제입니다."
)
