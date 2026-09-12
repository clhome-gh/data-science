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
    
    # 장르 전처리: 세로막대 기호(|)로 여러 개 적힌 경우 첫 번째 장르만 추출
    if 'genre' in df.columns:
        df['genre'] = df['genre'].astype(str).apply(lambda x: x.split('|')[0].strip() if '|' in x else x.strip())
        
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
filtered_df = df[df['nation'].isin(selected_nations)]

# 탭 또는 섹션 구성
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

# 추가 분석 그래프 제공 (도감의 완성도를 높이기 위해)
st.markdown("---")
st.header("2. 총 관객수와 개봉 첫 주 관객수의 관계")

col3, col4 = st.columns([3, 1])

with col3:
    fig_scatter = px.scatter(
        filtered_df,
        x='first_week_audi',
        y='total_audi',
        color='genre',
        hover_name='movieNm',
        labels={'first_week_audi': '개봉 첫 주 관객수', 'total_audi': '총 관객수', 'genre': '장르'},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_scatter.update_layout(margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_scatter, use_container_width=True)

with col4:
    st.markdown("### 📈 상관관계 안내")
    st.markdown("개봉 첫 주 성적이 총 관객수에 미치는 영향을 장르별로 비교할 수 있습니다.")

st.markdown("---")
st.info("💡 **이 그래프로 알 수 있는 것**\n개봉 첫 주의 관객 동원력이 최종 흥행(총 관객수)으로 이어지는 상관관계를 보여주며, 대부분의 영화가 첫 주 성적과 총 관객수 간에 강한 비례 관계를 보인다는 점을 확인할 수 있습니다.")

# 원본 데이터 확인 아코디언
with st.expander("📁 원본 데이터 및 전처리 결과 확인"):
    st.dataframe(filtered_df)
