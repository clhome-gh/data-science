import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="데이터 탐색",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 데이터 탐색 및 시각화")
st.markdown("뇌졸중 데이터셋의 주요 변수 분포와 특성을 탐색하는 페이지입니다.")

@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/stroke.csv"
    df = pd.read_csv(url, encoding='utf-8')
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 데 실패했습니다: {e}")
    st.stop()

# 1. 나이와 평균 혈당 히스토그램 두 개 나란히
st.subheader("📊 1. 나이와 평균 혈당 분포")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**나이(age) 분포**")
    fig_age = px.histogram(df, x="age", nbins=30, title="나이 히스토그램", labels={"age": "나이", "count": "사람 수"})
    st.plotly_chart(fig_age, use_container_width=True)

with col2:
    st.markdown("**평균 혈당(avg_glucose_level) 분포**")
    fig_glucose = px.histogram(df, x="avg_glucose_level", nbins=30, title="평균 혈당 히스토그램", labels={"avg_glucose_level": "평균 혈당", "count": "사람 수"})
    st.plotly_chart(fig_glucose, use_container_width=True)

st.markdown("---")

# 2. 뇌졸중 여부에 따른 나이와 평균 혈당 상자그림 및 평균값 표
st.subheader("📈 2. 뇌졸중 여부에 따른 나이 및 평균 혈당 비교")

df['stroke_str'] = df['stroke'].astype(str).replace({'0': '정상 (0)', '1': '뇌졸중 (1)'})

col1, col2 = st.columns(2)

with col1:
    fig_box_age = px.box(df, x="stroke_str", y="age", title="뇌졸중 여부에 따른 나이 비교", labels={"stroke_str": "뇌졸중 여부", "age": "나이"})
    st.plotly_chart(fig_box_age, use_container_width=True)

with col2:
    fig_box_glucose = px.box(df, x="stroke_str", y="avg_glucose_level", title="뇌졸중 여부에 따른 평균 혈당 비교", labels={"stroke_str": "뇌졸중 여부", "avg_glucose_level": "평균 혈당"})
    st.plotly_chart(fig_box_glucose, use_container_width=True)

mean_summary = df.groupby('stroke_str')[['age', 'avg_glucose_level']].mean().reset_index()
mean_summary.columns = ['뇌졸중 여부', '평균 나이', '평균 혈당']
st.markdown("**[두 무리의 평균값 비교 표]**")
st.dataframe(mean_summary, use_container_width=True)

st.markdown("---")

# 3. 고혈압 및 심장병 여부에 따른 뇌졸중 비율 막대그래프
st.subheader("📊 3. 질환(고혈압, 심장병)과 뇌졸중 비율")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**고혈압(hypertension)에 따른 뇌졸중 비율**")
    hyp_stroke = df.groupby('hypertension')['stroke'].mean().reset_index()
    hyp_stroke['hypertension_str'] = hyp_stroke['hypertension'].map({0: '고혈압 없음 (0)', 1: '고혈압 있음 (1)'})
    hyp_stroke['stroke_percent'] = hyp_stroke['stroke'] * 100
    fig_hyp = px.bar(hyp_stroke, x='hypertension_str', y='stroke_percent', text_auto='.2f%',
                     title="고혈압 여부에 따른 뇌졸중 비율", labels={'hypertension_str': '고혈압 여부', 'stroke_percent': '뇌졸중 비율 (%)'})
    st.plotly_chart(fig_hyp, use_container_width=True)

with col2:
    st.markdown("**심장병(heart_disease)에 따른 뇌졸중 비율**")
    heart_stroke = df.groupby('heart_disease')['stroke'].mean().reset_index()
    heart_stroke['heart_disease_str'] = heart_stroke['heart_disease'].map({0: '심장병 없음 (0)', 1: '심장병 있음 (1)'})
    heart_stroke['stroke_percent'] = heart_stroke['stroke'] * 100
    fig_heart = px.bar(heart_stroke, x='heart_disease_str', y='stroke_percent', text_auto='.2f%',
                     title="심장병 여부에 따른 뇌졸중 비율", labels={'heart_disease_str': '심장병 여부', 'stroke_percent': '뇌졸중 비율 (%)'})
    st.plotly_chart(fig_heart, use_container_width=True)

st.markdown("---")

# 4. bmi가 비어 있는 사람들 vs 전체 뇌졸중 비율 비교 표
st.subheader("📉 4. BMI 결측치 인원 및 뇌졸중 비율 비교")

total_count = len(df)
total_stroke_ratio = df['stroke'].mean() * 100

bmi_null_df = df[df['bmi'].isnull()]
bmi_null_count = len(bmi_null_df)
bmi_null_stroke_ratio = (bmi_null_df['stroke'].mean() * 100) if bmi_null_count > 0 else 0

comparison_data = pd.DataFrame({
    "구분": ["전체 데이터", "BMI 결측치 데이터"],
    "인원 수 (명)": [total_count, bmi_null_count],
    "뇌졸중 비율 (%)": [round(total_stroke_ratio, 2), round(bmi_null_stroke_ratio, 2)]
})

st.dataframe(comparison_data, use_container_width=True)

st.markdown("---")

# 5. 흡연 상태(smoking_status) 값마다 사람 수 세기 표
st.subheader("🚬 5. 흡연 상태(smoking_status)별 인원수")

smoking_counts = df['smoking_status'].value_counts().reset_index()
smoking_counts.columns = ['흡연 상태 (smoking_status)', '인원 수 (명)']
st.dataframe(smoking_counts, use_container_width=True)
