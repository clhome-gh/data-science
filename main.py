import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide"
)

# 타이틀
st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")
st.markdown("KOBIS 박스오피스 데이터를 바탕으로 영화의 다양한 분포와 관계를 시각적으로 탐색하는 대시보드입니다.")

# 데이터 로드 캐시 함수
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)
    
    # 장르 전처리: 결측치를 빈 문자열로 채우고, 문자열로 변환한 뒤 첫 번째 장르만 추출
    if 'genre' in df.columns:
        df['genre'] = df['genre'].fillna('기타').astype(str)
        df['genre'] = df['genre'].apply(lambda x: x.split('|')[0].strip() if '|' in x else x.strip())
        
    # 기타 결측치 및 데이터 타입 정제
    df['total_audi'] = pd.to_numeric(df['total_audi'], errors='coerce').fillna(0)
    df['movieNm'] = df['movieNm'].fillna('알 수 없음')
    df['nation'] = df['nation'].fillna('기타')
    
    return df

# 데이터 불러오기
try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 사이드바 설정 (필터 기능 추가)
st.sidebar.header("🔍 데이터 필터")
selected_nations = st.sidebar.multiselect(
    "제작 국가 선택",
    options=df['nation'].dropna().unique(),
    default=df['nation'].dropna().unique()
)

# 필터 적용
filtered_df = df[df['nation'].isin(selected_nations)].copy()

# 데이터가 비어있을 경우 예외 처리
if filtered_df.empty:
    st.warning("선택된 조건에 해당하는 데이터가 없습니다. 사이드바에서 필터를 다시 선택해 주세요.")
    st.stop()

# -------------------------------------------------------------
# 1. 장르별 영화 편수 분포 (도넛 그래프)
# -------------------------------------------------------------
st.markdown("---")
st.header("1. 장르별 영화 편수 분포")

col1, col2 = st.columns([3, 1])

with col1:
    # 장르별 편수 집계
    genre_counts = filtered_df['genre'].value_counts().reset_index()
    genre_counts.columns = ['genre', 'count']
    
    # 플롯리 도넛 그래프 생성
    fig_genre = px.pie(
        genre_counts,
        names='genre',
        values='count',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_genre.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>편수: %{value}편<br>비율: %{percent}<extra></extra>'
    )
    fig_genre.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_genre, use_container_width=True)

with col2:
    st.markdown("### 📊 데이터 요약")
    st.metric("총 영화 편수", f"{len(filtered_df)}편")
    st.metric("고유 장르 수", f"{filtered_df['genre'].nunique()}개")
    st.markdown(f"**선택된 국가:** {', '.join(selected_nations) if selected_nations else '없음'}")

# '이 그래프로 알 수 있는 것' 구역 나누기
st.markdown("---")
st.info("💡 **이 그래프로 알 수 있는 것**\n전체 박스오피스 상위권 영화 중 특정 장르(예: 드라마, 액션 등)가 차지하는 비중을 한눈에 파악할 수 있으며, 관객들의 선호도가 집중되는 주력 장르 경향을 확인할 수 있습니다.")

# -------------------------------------------------------------
# 2. 장르별 영화 트리맵 (총 관객수 기준)
# -------------------------------------------------------------
st.markdown("---")
st.header("2. 장르 및 영화별 총 관객수 분포 트리맵")

# 트리맵 시각화를 위한 포맷팅
filtered_df['total_audi_str'] = filtered_df['total_audi'].apply(lambda x: f"{int(x):,}명")

fig_treemap = px.treemap(
    filtered_df,
    path=['genre', 'movieNm'],
    values='total_audi',
    color='total_audi',
    color_continuous_scale='Blues',
    hover_data={'total_audi_str': True, 'total_audi': False}
)

fig_treemap.update_traces(
    hovertemplate='<b>장르:</b> %{parent}<br><b>영화명:</b> %{label}<br><b>총 관객수:</b> %{customdata[0]}<extra></extra>'
)
fig_treemap.update_layout(
    margin=dict(t=20, b=20, l=20, r=20),
    height=550
)

st.plotly_chart(fig_treemap, use_container_width=True)

# '이 그래프로 알 수 있는 것' 구역 나누기
st.markdown("---")
st.info("💡 **이 그래프로 알 수 있는 것**\n각 장르 영역 안에서 어떤 영화가 가장 많은 관객을 동원했는지 면적(총 관객수)을 통해 직관적으로 비교할 수 있으며, 특정 장르의 흥행 파워와 블록버스터 영화들의 분포를 한눈에 파악할 수 있습니다.")

# 원본 데이터 확인 아코디언
with st.expander("📁 원본 데이터 및 전처리 결과 확인"):
    st.dataframe(filtered_df.drop(columns=['total_audi_str']))
