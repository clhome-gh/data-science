import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression

st.set_page_config(
    page_title="데이터 전처리 및 모델 비교",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ 데이터 전처리 및 클래스 불균형 조정 실습실")
st.markdown("클래스 가중치(Balanced Weight) 조정 및 결측치 처리 방식에 따른 모델 성능 변화를 비교하는 페이지입니다.")

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

# 1. Controls at the top
st.subheader("⚙️ 1. 전처리 및 모델 설정 옵션")

# Switch 1: Class weights balanced
use_balanced = st.checkbox("⚖️ 뇌졸중 클래스 가중치 균형 맞추기 (class_weight='balanced')", value=False)

# Switch 2: BMI missing values handling
bmi_action = st.radio("📉 BMI 결측치 처리 방법", options=["그대로 두기 (중앙값 채우기)", "지우기 (결측치 행 제거)"], horizontal=True)

# Switch 3: Feature selection (default: age, avg_glucose_level, hypertension, heart_disease)
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
    key="preprocessing_features"
)

if len(selected_features) < 2:
    st.warning("⚠️ 입력 속성을 2개 이상 선택해 주세요!")
    st.stop()

# 2. Preprocessing & Data Split
work_df = df.copy()

original_len = len(work_df)
if "지우기" in bmi_action:
    null_bmi_df = work_df[work_df["bmi"].isnull()]
    dropped_count = len(null_bmi_df)
    dropped_stroke_count = int(null_bmi_df["stroke"].sum()) if dropped_count > 0 else 0
    
    work_df = work_df.dropna(subset=["bmi"])
    st.info(f"ℹ️ BMI 결측치 제거 결과: 총 **{dropped_count}명**이 지워졌으며, 그 중 뇌졸중 환자는 **{dropped_stroke_count}명**이었습니다.")
else:
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

# 3. Train models BEFORE and AFTER balanced weight
lr_before = LogisticRegression(random_state=42)
lr_before.fit(X_train, y_train)
lr_pred_before = lr_before.predict(X_test)

dt_before = DecisionTreeClassifier(max_depth=3, min_samples_leaf=5, random_state=42)
dt_before.fit(X_train, y_train)
dt_pred_before = dt_before.predict(X_test)

lr_after = LogisticRegression(class_weight="balanced" if use_balanced else None, random_state=42)
lr_after.fit(X_train, y_train)
lr_pred_after = lr_after.predict(X_test)

dt_after = DecisionTreeClassifier(class_weight="balanced" if use_balanced else None, max_depth=3, min_samples_leaf=5, random_state=42)
dt_after.fit(X_train, y_train)
dt_pred_after = dt_after.predict(X_test)

def get_metrics(y_true, y_pred):
    y_t = np.array(y_true)
    y_p = np.array(y_pred)
    tn = int(np.sum((y_t == 0) & (y_p == 0)))
    fp = int(np.sum((y_t == 0) & (y_p == 1)))
    fn = int(np.sum((y_t == 1) & (y_p == 0)))
    tp = int(np.sum((y_t == 1) & (y_p == 1)))
    total = tn + fp + fn + tp
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_denom = 2 * tp + fp + fn
    f1 = (2 * tp / f1_denom) if f1_denom > 0 else 0
    return {"TN": tn, "FP": fp, "FN": fn, "TP": tp, "Accuracy": accuracy, "Precision": precision, "Recall": recall, "F1": f1}

m_lr_b = get_metrics(y_test, lr_pred_before)
m_lr_a = get_metrics(y_test, lr_pred_after)
m_dt_b = get_metrics(y_test, dt_pred_before)
m_dt_a = get_metrics(y_test, dt_pred_after)

st.markdown("---")
st.subheader("📊 2. 가중치 조정 전·후 모델 성능 비교 표 (전 vs 후)")

def build_comparison_table(mb, ma, model_name):
    comp_df = pd.DataFrame([
        {
            "구분": "무게 맞추기 전 (Before)",
            "정확도": f"{mb['Accuracy']*100:.1f}%",
            "정밀도": f"{mb['Precision']*100:.1f}%",
            "재현율": f"{mb['Recall']*100:.1f}%",
            "F1 점수": f"{mb['F1']:.3f}",
            "혼동행렬 (TN, FP, FN, TP)": f"TN:{mb['TN']}, FP:{mb['FP']}, FN:{mb['FN']}, TP:{mb['TP']}"
        },
        {
            "구분": "무게 맞춘 뒤 (After)",
            "정확도": f"{ma['Accuracy']*100:.1f}%",
            "정밀도": f"{ma['Precision']*100:.1f}%",
            "재현율": f"{ma['Recall']*100:.1f}%",
            "F1 점수": f"{ma['F1']:.3f}",
            "혼동행렬 (TN, FP, FN, TP)": f"TN:{ma['TN']}, FP:{ma['FP']}, FN:{ma['FN']}, TP:{ma['TP']}"
        }
    ])
    st.markdown(f"**[{model_name}]**")
    st.dataframe(comp_df, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    build_comparison_table(m_lr_b, m_lr_a, "확률 모델 (Logistic Regression)")
    st.caption(f"👉 환자 수 변화: 찾아낸 환자(TP) {m_lr_b['TP']}명 ➔ {m_lr_a['TP']}명 | 놓친 환자(FN) {m_lr_b['FN']}명 ➔ {m_lr_a['FN']}명 | 헛짚은 사람(FP) {m_lr_b['FP']}명 ➔ {m_lr_a['FP']}명")

with col2:
    build_comparison_table(m_dt_b, m_dt_a, "질문 트리 모델 (Decision Tree)")
    st.caption(f"👉 환자 수 변화: 찾아낸 환자(TP) {m_dt_b['TP']}명 ➔ {m_dt_a['TP']}명 | 놓친 환자(FN) {m_dt_b['FN']}명 ➔ {m_dt_a['FN']}명 | 헛짚은 사람(FP) {m_dt_b['FP']}명 ➔ {m_dt_a['FP']}명")

st.markdown("---")

# 4. Visualization: 2D or 3D scatter with boundaries before & after
st.subheader("📈 3. 결정 경계(Boundary) 시각화 (전·후 비교)")

if len(selected_features) >= 2:
    axis_x = st.selectbox("가로축 속성 선택", options=selected_features, index=0, format_func=lambda x: feature_labels.get(x, x), key="pre_x")
    remaining_axes = [f for f in selected_features if f != axis_x]
    axis_y = st.selectbox("세로축 속성 선택", options=remaining_axes, index=0, format_func=lambda x: feature_labels.get(x, x), key="pre_y")

    if len(selected_features) >= 3:
        use_3d = st.checkbox("🧊 3차원 산점도 및 결정 평면 보기 (3개 항목 선택 시)", value=False)
    else:
        use_3d = False

    if use_3d and len(selected_features) >= 3:
        rem_axes_3d = [f for f in remaining_axes if f != axis_y]
        axis_z = st.selectbox("세 번째 축(Z축) 속성 선택", options=rem_axes_3d, index=0, format_func=lambda x: feature_labels.get(x, x), key="pre_z")
        
        plot_3d_df = test_df.copy()
        plot_3d_df["뇌졸중_str"] = plot_3d_df["stroke"].astype(str).replace({"0": "정상 (0)", "1": "뇌졸중 (1)"})
        
        fig3d = px.scatter_3d(
            plot_3d_df,
            x=axis_x, y=axis_y, z=axis_z,
            color="뇌졸중_str",
            title=f"3차원 산점도 ({feature_labels.get(axis_x)}, {feature_labels.get(axis_y)}, {feature_labels.get(axis_z)})"
        )
        st.plotly_chart(fig3d, use_container_width=True)
        st.info("ℹ️ 3차원 공간 내 전후 모델 결정 평면 비교 시각화 영역입니다.")
    else:
        X_train_2d = train_df[[axis_x, axis_y]]
        y_train_2d = train_df["stroke"]

        lr_2d_b = LogisticRegression(random_state=42)
        lr_2d_b.fit(X_train_2d, y_train_2d)

        lr_2d_a = LogisticRegression(class_weight="balanced" if use_balanced else None, random_state=42)
        lr_2d_a.fit(X_train_2d, y_train_2d)

        plot_df = train_df.copy()
        plot_df["구분"] = "훈련용"
        test_plot_df = test_df.copy()
        test_plot_df["구분"] = "채점용 (3명)"
        combined_plot_df = pd.concat([plot_df, test_plot_df])
        combined_plot_df["뇌졸중_str"] = combined_plot_df["stroke"].astype(str).replace({"0": "정상 (0)", "1": "뇌졸중 (1)"})

        fig = px.scatter(
            combined_plot_df,
            x=axis_x, y=axis_y,
            color="뇌졸중_str",
            symbol="구분",
            title=f"확률 모델 0.5 경계선 비교: 전(파란색) vs 후(붉은색)",
            labels={axis_x: feature_labels.get(axis_x), axis_y: feature_labels.get(axis_y)}
        )

        x_min, x_max = combined_plot_df[axis_x].min(), combined_plot_df[axis_x].max()
        y_min, y_max = combined_plot_df[axis_y].min(), combined_plot_df[axis_y].max()
        xx = np.linspace(x_min, x_max, 100)

        cb = lr_2d_b.coef_[0]
        ib = lr_2d_b.intercept_[0]
        out_b = False
        if abs(cb[1]) > 1e-5:
            yy_b = -(cb[0] * xx + ib) / cb[1]
            if yy_b.max() < y_min or yy_b.min() > y_max:
                out_b = True
            fig.add_trace(go.Scatter(x=xx, y=yy_b, mode="lines", name="무게 맞추기 전 경계선", line=dict(color="blue", dash="dash")))

        ca = lr_2d_a.coef_[0]
        ia = lr_2d_a.intercept_[0]
        out_a = False
        if abs(ca[1]) > 1e-5:
            yy_a = -(ca[0] * xx + ia) / ca[1]
            if yy_a.max() < y_min or yy_a.min() > y_max:
                out_a = True
            fig.add_trace(go.Scatter(x=xx, y=yy_a, mode="lines", name="무게 맞춘 뒤 경계선", line=dict(color="red")))

        st.plotly_chart(fig, use_container_width=True)

        if out_b:
            st.warning("⚠️ 무게 맞추기 전 0.5 경계선이 현재 그림(산점도 범위) 밖으로 벗어나 있습니다.")
        if out_a:
            st.warning("⚠️ 무게 맞춘 뒤 0.5 경계선이 현재 그림(산점도 범위) 밖으로 벗어나 있습니다.")

st.markdown("---")

# 5. Missed patients list for Logistic Regression (based on switch)
st.subheader("🔍 4. 확률 모델이 놓친 환자(False Negative) 목록")
st.markdown("스위치 설정에 따른 현재 모델 기준, 실제 뇌졸중 환자 중 정상으로 잘못 예측한 목록입니다.")

chosen_lr_pred = lr_pred_after if use_balanced else lr_pred_before
eval_lr_df = test_df.copy()
eval_lr_df["pred"] = chosen_lr_pred

missed_df = eval_lr_df[(eval_lr_df["stroke"] == 1) & (eval_lr_df["pred"] == 0)].copy()

if len(missed_df) > 0:
    missed_df = missed_df.sort_values(by="age", ascending=True)
    display_missed = pd.DataFrame({
        "번호": missed_df.index,
        "나이": missed_df["age"],
        "고혈압 여부": missed_df["hypertension"],
        "심장병 여부": missed_df["heart_disease"]
    }).reset_index(drop=True)
    st.dataframe(display_missed, use_container_width=True)
else:
    st.success("🎉 현재 선택된 설정에서 확률 모델이 놓친 환자가 없습니다 (모두 맞춤)!")
