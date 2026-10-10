import streamlit as st
import pandas as pd
import plotly.express as px

# Define pages using st.Page
home_page = st.Page("main.py", title="홈", icon="🧠", default=True)
explore_page = st.Page("pages/1_탐색.py", title="데이터 탐색", icon="🔍")
model_page = st.Page("pages/2_분류_모델.py", title="분류 모델", icon="🤖")

# Setup navigation (Include all pages!)
pg = st.navigation([home_page, explore_page, model_page])

# Page configuration
st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🧠",
    layout="wide"
)

# Run the selected page content
if pg.title == "홈":
    # Title
    st.title("🧠 뇌졸중 예측 실습실")
    st.markdown("환자의 건강 지표를 바탕으로 뇌졸중 발생 가능성을 탐색하고 예측하는 실습실입니다.")

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

    # 1. Metric Cards
    total_people = len(df)
    num_columns = len(df.columns)
    stroke_count = int(df['stroke'].sum()) if 'stroke' in df.columns else 0
    stroke_ratio = (stroke_count / total_people) * 100 if total_people > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("전체 사람 수", f"{total_people:,} 명")
    col2.metric("열 개수", f"{num_columns} 개")
    col3.metric("뇌졸중(1) 환자 수", f"{stroke_count:,} 명")
    col4.metric("뇌졸중 비율", f"{stroke_ratio:.2f}%")

    st.markdown("---")

    # 2. Metadata Table with Editable Korean Meaning (Pre-filled)
    st.subheader("📋 데이터셋 열 정보")
    st.markdown("아래 표의 **우리말 뜻** 칸을 확인하고 교재를 참고하여 수정해 보세요.")

    default_meanings = {
        "id": "환자 고유 ID",
        "gender": "성별",
        "age": "나이",
        "hypertension": "고혈압 여부 (0: 없음, 1: 있음)",
        "heart_disease": "심장병 여부 (0: 없음, 1: 있음)",
        "ever_married": "결혼 여부",
        "work_type": "직업 유형",
        "Residence_type": "거주지 유형",
        "avg_glucose_level": "평균 혈당 수치",
        "bmi": "체질량지수 (BMI)",
        "smoking_status": "흡연 상태",
        "stroke": "뇌졸중 발생 여부 (0: 정상, 1: 뇌졸중)"
    }

    columns_info = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        null_count = int(df[col].isnull().sum())
        korean_meaning = default_meanings.get(col, "")
        columns_info.append({
            "열 이름 (Column)": col,
            "우리말 뜻": korean_meaning,
            "값의 종류 (Dtype)": dtype,
            "빈 값 개수 (Nulls)": null_count
        })

    meta_df = pd.DataFrame(columns_info)

    # Editable dataframe for Korean meaning
    edited_meta_df = st.data_editor(
        meta_df,
        column_config={
            "열 이름 (Column)": st.column_config.TextColumn(disabled=True),
            "우리말 뜻": st.column_config.TextColumn("우리말 뜻 (수정 가능)", required=False),
            "값의 종류 (Dtype)": st.column_config.TextColumn(disabled=True),
            "빈 값 개수 (Nulls)": st.column_config.NumberColumn(disabled=True)
        },
        hide_index=True,
        use_container_width=True
    )

    st.markdown("---")

    # 3. First 5 Rows Preview
    st.subheader("🔍 데이터 미리보기 (상위 5행)")
    st.dataframe(df.head(), use_container_width=True)

    st.markdown("---")

    # 4. Data Source Information Section
    st.subheader("📌 데이터 출처 및 참고")
    st.text_area("데이터 출처", value="출처: 모듈 데이터 / Kaggle Stroke Prediction Dataset", height=100)
else:
    pg.run()
