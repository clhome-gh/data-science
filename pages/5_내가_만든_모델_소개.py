import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="내가 만든 모델 소개",
    page_icon="📝",
    layout="wide"
)

st.title("📝 내가 만든 모델 소개 및 보고서 작성")
st.markdown("머신러닝 실습을 통해 학습한 모델의 특성과 성능을 정리하고 보고서 형태로 확인하는 페이지입니다.")

# Tabs: 1. 채우기 화면 (Editor), 2. 한 장으로 모아 보기 (Summary Report)
tab1, tab2 = st.tabs(["✍️ 내용 채우기", "📄 한 장으로 모아 보기 (보고서)"])

with tab1:
    st.subheader("1. 모델 요약 서식 작성")
    q1 = st.text_area("1. 무슨 데이터입니까?", placeholder="예: 뇌졸중 환자의 건강 지표 및 의료 기록 데이터셋", height=100)
    q2 = st.text_area("2. 무엇을 보고 맞힙니까?", placeholder="예: 나이, 평균 혈당, 고혈압, 심장병 등의 입력 속성", height=100)
    q3 = st.text_area("3. 무엇을 고쳤습니까?", placeholder="예: 클래스 가중치(balanced weight) 조정 및 결측치 처리", height=100)
    q4 = st.text_area("4. 이 모델을 검진센터가 사용해도 됩니까?", placeholder="예: 보조 지표로는 활용 가능하나 단독 진단용으로는 주의 필요", height=100)
    q5 = st.text_area("5. 이 모델이 못 하는 것 한 가지", placeholder="예: 환자의 미세한 생활 습관 변화나 정서적 요인까지는 예측 불가", height=100)

    st.markdown("---")
    st.subheader("2. 전·후 성능 지표 비교 손수 입력 표")
    st.markdown("앞 페이지에서 확인한 값을 아래 빈 표에 손으로 직접 입력해 보세요.")

    empty_data = [
        {"평가지표": "정확도 (Accuracy)", "고치기 전": "", "고친 뒤": ""},
        {"평가지표": "재현율 (Recall)", "고치기 전": "", "고친 뒤": ""},
        {"평가지표": "F1 점수", "고치기 전": "", "고친 뒤": ""},
        {"평가지표": "찾아낸 환자 (TP)", "고치기 전": "", "고친 뒤": ""},
        {"평가지표": "헛짚은 사람 (FP)", "고치기 전": "", "고친 뒤": ""}
    ]
    
    empty_df = pd.DataFrame(empty_data)
    
    if "user_table" not in st.session_state:
        st.session_state["user_table"] = empty_df

    edited_table = st.data_editor(
        st.session_state["user_table"],
        column_config={
            "평가지표": st.column_config.TextColumn(disabled=True),
            "고치기 전": st.column_config.TextColumn("고치기 전 값 입력"),
            "고친 뒤": st.column_config.TextColumn("고친 뒤 값 입력")
        },
        hide_index=True,
        use_container_width=True
    )
    st.session_state["user_table"] = edited_table

with tab2:
    st.subheader("📄 모델 소개 및 성능 보고서 (통합 요약)")
    st.markdown("작성하신 내용과 평가지표 비교 표가 아래에 한눈에 모아 보여집니다.")

    st.markdown("---")
    st.markdown("### 📌 1. 모델 핵심 질문 답변 요약")
    
    def check_content(text, label):
        if text and text.strip():
            return f"**{label}:**\n{text}"
        else:
            return f"**{label}:** ⚠️ 아직 적지 않았습니다."

    st.markdown(check_content(q1 if 'q1' in locals() else "", "무슨 데이터입니까"))
    st.markdown(check_content(q2 if 'q2' in locals() else "", "무엇을 보고 맞힙니까"))
    st.markdown(check_content(q3 if 'q3' in locals() else "", "무엇을 고쳤습니까"))
    st.markdown(check_content(q4 if 'q4' in locals() else "", "이 모델을 검진센터가 사용해도 됩니까"))
    st.markdown(check_content(q5 if 'q5' in locals() else "", "이 모델이 못 하는 것 한 가지"))

    st.markdown("---")
    st.markdown("### 📊 2. 전·후 성능 지표 비교 표 요약")
    if "user_table" in st.session_state:
        st.dataframe(st.session_state["user_table"], use_container_width=True)
    else:
        st.dataframe(empty_df, use_container_width=True)
