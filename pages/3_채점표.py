import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression

st.set_page_config(
    page_title="채점표 및 성능 평가",
    page_icon="📋",
    layout="wide"
)

st.title("📋 모델 성능 채점표 및 오류 분석실")
st.markdown("분류 모델의 혼동행렬(Confusion Matrix), 평가지표(정확도, 정밀도, 재현율, F1), 그리고 오분류 사례를 분석하는 페이지입니다.")

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

# 1. Feature selection (same as classification page)
st.subheader("⚙️ 모델 입력 속성(Feature) 설정")
all_features = ["age", "avg_glucose_level", "bmi", "hypertension", "heart_disease"]
feature_labels = {
    "age": "나이 (age)",
    "avg_glucose_level": "평균 혈당 (avg_glucose_level)",
    "bmi": "체질량지수 (bmi)",
    "hypertension": "고혈압 (hypertension)",
    "heart_disease": "심장병 (heart_disease)"
}

default_selection = ["age", "avg_glucose_level", "hypertension", "heart_disease"]

selected_features = st.multiselect(
    "사용할 입력 속성을 골라주세요 (최소 2개 이상):",
    options=all_features,
    default=default_selection,
    format_func=lambda x: feature_labels.get(x, x),
    key="scoring_features"
)

if len(selected_features) < 2:
    st.warning("⚠️ 입력 속성을 2개 이상 선택해 주세요!")
    st.stop()

# 2. Preprocessing & Data Split
work_df = df.copy()

if "bmi" in selected_features:
    bmi_median = work_df["bmi"].median()
    work_df["bmi"] = work_df["bmi"].fillna(bmi_median)
else:
    work_df = work_df.dropna(subset=selected_features + ["stroke"])

work_df = work_df.sort_index().reset_index(drop=True)

if len(work_df) < 10:
    st.error("데이터가 너무 적습니다.")
    st.stop()

test_df = work_df.iloc[:3]   # 앞 세 명 채점용 고정
train_df = work_df.iloc[3:]  # 나머지 학습용

X_train = train_df[selected_features]
y_train = train_df["stroke"]
X_test = test_df[selected_features]
y_test = test_df["stroke"]

# Train Models
lr_model = LogisticRegression(random_state=42)
lr_model.fit(X_train, y_train)
lr_pred = lr_model.predict(X_test)

dt_model = DecisionTreeClassifier(max_depth=3, min_samples_leaf=5, random_state=42)
dt_model.fit(X_train, y_train)
dt_pred = dt_model.predict(X_test)

majority_class = y_train.mode()[0]
baseline_pred = np.full(shape=y_test.shape, fill_value=majority_class)

# Helper function to compute confusion matrix values and metrics
def get_metrics_and_cm(y_true, y_pred):
    y_t = np.array(y_true)
    y_p = np.array(y_pred)
    
    tn = int(np.sum((y_t == 0) & (y_p == 0)))
    fp = int(np.sum((y_t == 0) & (y_p == 1)))
    fn = int(np.sum((y_t == 1) & (y_p == 0)))
    tp = int(np.sum((y_t == 1) & (y_p == 1)))
    
    total = tn + fp + fn + tp
    accuracy = (tp + tn) / total if total > 0 else 0
    
    pred_pos = tp + fp
    if pred_pos == 0:
        precision = "계산할 수 없음"
    else:
        precision = tp / pred_pos
        
    actual_pos = tp + fn
    recall = tp / actual_pos if actual_pos > 0 else 0
    
    f1_denom = 2 * tp + fp + fn
    f1 = (2 * tp / f1_denom) if f1_denom > 0 else 0
    
    return {
        "TN": tn, "FP": fp, "FN": fn, "TP": tp,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1
    }

lr_metrics = get_metrics_and_cm(y_test, lr_pred)
dt_metrics = get_metrics_and_cm(y_test, dt_pred)
base_metrics = get_metrics_and_cm(y_test, baseline_pred)

st.markdown("---")
num_test = len(test_df)
num_test_stroke = int(test_df["stroke"].sum())
st.markdown(f"**📌 채점용 사람 수:** {num_test}명 | **그중 뇌졸중(1)인 사람 수:** {num_test_stroke}명")

# 3. Confusion Matrices (2x2 tables)
st.subheader("📊 1. 혼동행렬 (Confusion Matrix)")
st.markdown("행(Row)은 **실제 값**, 열(Column)은 **예측 값**입니다.")

col1, col2 = st.columns(2)

def render_cm_table(metrics, title):
    cm_df = pd.DataFrame(
        [
            [f"{metrics['TN']} (TN)", f"{metrics['FP']} (FP)", metrics['TN'] + metrics['FP']],
            [f"{metrics['FN']} (FN)", f"{metrics['TP']} (TP)", metrics['FN'] + metrics['TP']],
            [metrics['TN'] + metrics['FN'], metrics['FP'] + metrics['TP'], metrics['TN'] + metrics['FP'] + metrics['FN'] + metrics['TP']]
        ],
        index=["실제 정상 (0)", "실제 뇌졸중 (1)", "합계"],
        columns=["예측 정상 (0)", "예측 뇌졸중 (1)", "합계"]
    )
    st.markdown(f"**[{title}]**")
    st.dataframe(cm_df, use_container_width=True)

with col1:
    render_cm_table(lr_metrics, "확률 모델 (Logistic Regression)")

with col2:
    render_cm_table(dt_metrics, "질문 트리 모델 (Decision Tree)")

st.markdown("---")

# 4. Performance Metrics Comparison Table
st.subheader("🏆 2. 모델 평가지표 비교 표")

metrics_summary_df = pd.DataFrame([
    {
        "모델명": "확률 모델 (Logistic Regression)",
        "정확도 (Accuracy)": f"{lr_metrics['Accuracy']*100:.1f}%",
        "정밀도 (Precision)": f"{lr_metrics['Precision']*100:.1f}%" if isinstance(lr_metrics['Precision'], float) else lr_metrics['Precision'],
        "재현율 (Recall)": f"{lr_metrics['Recall']*100:.1f}%",
        "F1 점수": f"{lr_metrics['F1']:.3f}"
    },
    {
        "모델명": "질문 트리 모델 (Decision Tree)",
        "정확도 (Accuracy)": f"{dt_metrics['Accuracy']*100:.1f}%",
        "정밀도 (Precision)": f"{dt_metrics['Precision']*100:.1f}%" if isinstance(dt_metrics['Precision'], float) else dt_metrics['Precision'],
        "재현율 (Recall)": f"{dt_metrics['Recall']*100:.1f}%",
        "F1 점수": f"{dt_metrics['F1']:.3f}"
    },
    {
        "모델명": "다수 클래스 기준 모델 (Baseline)",
        "정확도 (Accuracy)": f"{base_metrics['Accuracy']*100:.1f}%",
        "정밀도 (Precision)": f"{base_metrics['Precision']*100:.1f}%" if isinstance(base_metrics['Precision'], float) else base_metrics['Precision'],
        "재현율 (Recall)": f"{base_metrics['Recall']*100:.1f}%",
        "F1 점수": f"{base_metrics['F1']:.3f}"
    }
])

st.dataframe(metrics_summary_df, use_container_width=True)

st.markdown("---")

# 5. Error Analysis Lists (FN: Missed patients vs FP: False alarms)
st.subheader("🔍 3. 오분류 환자/고객 분석 목록")

model_choice = st.selectbox("오분류 목록을 확인할 모델을 선택하세요:", options=["확률 모델 (Logistic Regression)", "질문 트리 모델 (Decision Tree)"])
chosen_preds = lr_pred if "Logistic" in model_choice else dt_pred

eval_df = test_df.copy()
eval_df["pred"] = chosen_preds

fn_df = eval_df[(eval_df["stroke"] == 1) & (eval_df["pred"] == 0)].copy()
fp_df = eval_df[(eval_df["stroke"] == 0) & (eval_df["pred"] == 1)].copy()

if len(fn_df) > 0:
    fn_df = fn_df.sort_values(by="age", ascending=False)
if len(fp_df) > 0:
    fp_df = fp_df.sort_values(by="age", ascending=False)

col1, col2 = st.columns(2)

def format_error_df(sub_df):
    if len(sub_df) == 0:
        return pd.DataFrame(columns=["번호", "나이", "평균 혈당", "고혈압", "심장병"])
    
    display_df = pd.DataFrame({
        "번호": sub_df.index,
        "나이": sub_df["age"],
        "평균 혈당": sub_df["avg_glucose_level"],
        "고혈압": sub_df["hypertension"],
        "심장병": sub_df["heart_disease"]
    })
    return display_df.reset_index(drop=True)

fn_display = format_error_df(fn_df)
fp_display = format_error_df(fp_df)

fn_count_total = len(fn_df)
fp_count_total = len(fp_df)

fn_title = f"실제 뇌졸중인데 아니라고 예측한 사람 (놓친 환자) - 총 {fn_count_total}명" if fn_count_total <= 20 else f"실제 뇌졸중인데 아니라고 예측한 사람 (놓친 환자) - 총 {fn_count_total}명 중 상위 20명"
fp_title = f"아닌데 뇌졸중이라고 예측한 사람 (헛짚은 사람) - 총 {fp_count_total}명" if fp_count_total <= 20 else f"아닌데 뇌졸중이라고 예측한 사람 (헛짚은 사람) - 총 {fp_count_total}명 중 상위 20명"

with col1:
    st.markdown(f"**[{fn_title}]**")
    st.dataframe(fn_display.head(20), use_container_width=True)

with col2:
    st.markdown(f"**[{fp_title}]**")
    st.dataframe(fp_display.head(20), use_container_width=True)

chosen_metrics = lr_metrics if "Logistic" in model_choice else dt_metrics
st.markdown(f"👉 **확인:** 위 두 목록의 사람 수({fn_count_total}명, {fp_count_total}명)는 선택한 모델 혼동행렬의 **FN({chosen_metrics['FN']})** 및 **FP({chosen_metrics['FP']})** 칸의 수와 정확히 일치합니다.")
