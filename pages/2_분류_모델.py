import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import export_text

st.set_page_config(
    page_title="분류 모델 실습",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 뇌졸중 예측 분류 모델 실습실")
st.markdown("머신러닝(확률 모델 및 질문 트리 모델)을 활용하여 뇌졸중 여부를 예측하고 시각화하는 페이지입니다.")

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

# 1. Feature selection
st.subheader("⚙️ 1. 모델 입력 속성(Feature) 선택")
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
    format_func=lambda x: feature_labels.get(x, x)
)

if len(selected_features) < 2:
    st.warning("⚠️ 입력 속성을 2개 이상 선택해 주세요!")
    st.stop()

# 2. Preprocessing & Data Split
work_df = df.copy()

# Handle BMI missing values if selected
if "bmi" in selected_features:
    bmi_median = work_df["bmi"].median()
    work_df["bmi"] = work_df["bmi"].fillna(bmi_median)
else:
    work_df = work_df.dropna(subset=selected_features + ["stroke"])

# Sort by index/id to make deterministic, take first 3 for grading/testing, rest for training
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

# 3. Models Training
# A. Probability-based model (Logistic Regression)
lr_model = LogisticRegression(random_state=42)
lr_model.fit(X_train, y_train)
lr_pred = lr_model.predict(X_test)
lr_acc = (lr_pred == y_test).mean() * 100

# B. Question-based model (Decision Tree with max_depth=3, min_samples_leaf check for <5 people, random_state fixed)
dt_model = DecisionTreeClassifier(max_depth=3, min_samples_leaf=5, random_state=42)
dt_model.fit(X_train, y_train)
dt_pred = dt_model.predict(X_test)
dt_acc = (dt_pred == y_test).mean() * 100

# C. Baseline model: Majority class predictor from training set
majority_class = y_train.mode()[0]
baseline_pred = np.full(shape=y_test.shape, fill_value=majority_class)
baseline_acc = (baseline_pred == y_test).mean() * 100

st.markdown("---")
st.subheader("🏆 2. 모델 정확도 비교 (채점용 3명 기준)")
col1, col2, col3 = st.columns(3)
col1.metric("확률 모델 (Logistic Regression)", f"{lr_acc:.1f}%")
col2.metric("질문 트리 모델 (Decision Tree)", f"{dt_acc:.1f}%")
col3.metric("다수 클래스 기준 모델 (Baseline)", f"{baseline_acc:.1f}%", help="입력을 보지 않고 훈련용에서 많은 쪽으로만 답하는 모델")

st.markdown("---")

# 4. Visualization with 2 selected axes
st.subheader("📊 3. 2차원 공간 시각화 및 결정 경계")

if len(selected_features) >= 2:
    axis_x = st.selectbox("가로축 속성 선택", options=selected_features, index=0, format_func=lambda x: feature_labels.get(x, x), key="ax_x")
    remaining_axes = [f for f in selected_features if f != axis_x]
    axis_y = st.selectbox("세로축 속성 선택", options=remaining_axes, index=0, format_func=lambda x: feature_labels.get(x, x), key="ax_y")

    # Train 2D models for boundary visualization
    X_train_2d = train_df[[axis_x, axis_y]]
    y_train_2d = train_df["stroke"]

    lr_2d = LogisticRegression(random_state=42)
    lr_2d.fit(X_train_2d, y_train_2d)

    dt_2d = DecisionTreeClassifier(max_depth=3, min_samples_leaf=5, random_state=42)
    dt_2d.fit(X_train_2d, y_train_2d)

    # Plot scatter of test data (grading set) and train data
    plot_df = train_df.copy()
    plot_df["구분"] = "훈련용"
    test_plot_df = test_df.copy()
    test_plot_df["구분"] = "채점용 (3명)"
    combined_plot_df = pd.concat([plot_df, test_plot_df])
    combined_plot_df["뇌졸중_str"] = combined_plot_df["stroke"].astype(str).replace({"0": "정상 (0)", "1": "뇌졸중 (1)"})

    fig = px.scatter(
        combined_plot_df,
        x=axis_x,
        y=axis_y,
        color="뇌졸중_str",
        symbol="구분",
        title=f"{feature_labels.get(axis_x, axis_x)} vs {feature_labels.get(axis_y, axis_y)} 산점도",
        labels={axis_x: feature_labels.get(axis_x, axis_x), axis_y: feature_labels.get(axis_y, axis_y)}
    )

    # Decision boundary for Logistic Regression (0.5 threshold line)
    x_min, x_max = combined_plot_df[axis_x].min(), combined_plot_df[axis_x].max()
    y_min, y_max = combined_plot_df[axis_y].min(), combined_plot_df[axis_y].max()

    coef = lr_2d.coef_[0]
    intercept = lr_2d.intercept_[0]

    line_out_of_bounds = False
    if abs(coef[1]) > 1e-5:
        xx = np.linspace(x_min, x_max, 100)
        yy = -(coef[0] * xx + intercept) / coef[1]
        
        if yy.max() < y_min or yy.min() > y_max or xx.max() < x_min or xx.min() > x_max:
            line_out_of_bounds = True

        fig.add_trace(go.Scatter(x=xx, y=yy, mode="lines", name="확률 모델 0.5 경계선", line=dict(color="red", dash="dash")))

    st.plotly_chart(fig, use_container_width=True)

    if line_out_of_bounds:
        st.info("ℹ️ 확률 모델이 나누는 0.5 기준선이 현재 데이터 산점도 화면(그림) 밖으로 벗어나 있습니다.")

    # Decision tree rules / questions explanation
    st.markdown("---")
    st.subheader("❓ 4. 질문 트리 모델(Decision Tree)의 질문 순서 및 규칙")
    st.markdown("질문으로 답하는 모델이 데이터를 분류하기 위해 던진 핵심 질문 순서입니다:")

    tree_rules = export_text(dt_2d, feature_names=[feature_labels.get(axis_x, axis_x), feature_labels.get(axis_y, axis_y)])
    st.code(tree_rules, language="text")

else:
    st.warning("시각화를 위해 2개 이상의 속성을 선택해 주세요.")
