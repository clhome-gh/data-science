import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="영화 흥행 예측기", page_icon="🎬", layout="wide"
)

st.title("🎬 영화 흥행 예측기")
st.markdown(
    "KOBIS 박스오피스 데이터를 바탕으로 영화의 **총 관객 수**를 예측하는 다중"
    " 회귀 모델 앱입니다."
)

# ⚠️ 사후 집계 데이터 안내 문구 추가
st.warning(
    "⚠️ **안내사항**: 본 데이터셋(`kobis_movies.csv`)은 영화 상영 종료 후"
    " 집계된 **사후 집계값**을 포함하고 있습니다. 따라서 실제 개봉 전 시점에서"
    " 미래를 예측하는 순수 예측 성능이 아님을 참고해 주세요."
)


# 데이터 로드 함수
@st.cache_data
def load_data():
  daily_url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"
  movies_url = (
      "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
  )
  df_daily = pd.read_csv(daily_url, encoding="utf-8")
  df_movies = pd.read_csv(movies_url, encoding="utf-8")
  return df_daily, df_movies


try:
  df_daily, df_movies = load_data()
except Exception as e:
  st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
  st.stop()

# 1. 기준 기간 추출 (kobis_daily.csv)
date_col = "날짜" if "날짜" in df_daily.columns else df_daily.columns[0]
min_date_raw = str(df_daily[date_col].min())
max_date_raw = str(df_daily[date_col].max())


def format_date(d_str):
  if len(d_str) == 8:
    return f"{d_str[:4]}년 {d_str[4:6]}월 {d_str[6:]}일"
  return d_str


period_str = f"{format_date(min_date_raw)} ~ {format_date(max_date_raw)}"

# 2. 데이터 요약 및 상위 10줄 표시
st.subheader("📊 영화 정보 표 (상위 10개 행)")
st.dataframe(df_movies.head(10), use_container_width=True)

# 3. 사이드바: 회귀 모델 변수 선택 체크박스
st.sidebar.header("⚙️ 모델 설정")
st.sidebar.subheader("학습에 사용할 변수 선택")

potential_features = [
    "first_scrn",
    "first_show",
    "peak",
    "first_week_audi",
    "days_in_top10",
]
feature_labels = {
    "first_scrn": "첫 관측일 스크린수 (first_scrn)",
    "first_show": "첫 관측일 상영횟수 (first_show)",
    "peak": "성수기 개봉 여부 (peak)",
    "first_week_audi": "첫 주 관객수 (first_week_audi)",
    "days_in_top10": "TOP 10 진입 일수 (days_in_top10)",
}

selected_features = []
for feat in potential_features:
  if feat in df_movies.columns:
    # 기본값으로 first_week_audi, first_scrn은 체크
    default_val = True if feat in ["first_week_audi", "first_scrn"] else False
    if st.sidebar.checkbox(
        feature_labels.get(feat, feat), value=default_val
    ):
      selected_features.append(feat)

if not selected_features:
  st.warning(
      "⚠️ 적어도 하나의 변수를 선택해주세요. 기본값으로 'first_week_audi'를"
      " 사용합니다."
  )
  selected_features = ["first_week_audi"]

# 4. 데이터 분할 로직 (영화코드 순 정렬 -> 열 편마다 앞 3편 테스트, 나머지 학습)
df_movies_sorted = df_movies.sort_values("movieCd").reset_index(drop=True)

train_chunks = []
test_chunks = []

for i in range(0, len(df_movies_sorted), 10):
  chunk = df_movies_sorted.iloc[i : i + 10]
  if len(chunk) >= 3:
    test_chunks.append(chunk.iloc[:3])
    train_chunks.append(chunk.iloc[3:])
  else:
    train_chunks.append(chunk)

train_df = (
    pd.concat(train_chunks).reset_index(drop=True)
    if train_chunks
    else pd.DataFrame()
)
test_df = (
    pd.concat(test_chunks).reset_index(drop=True)
    if test_chunks
    else pd.DataFrame()
)

target_col = "target_audi" if "target_audi" in df_movies.columns else "total_audi"

# 4-1. [추가 요구사항] 기본 변수 3가지 모델 vs 첫 주 관객 포함 모델 비교 분석 수행
base_default_features = ["first_scrn", "first_show", "peak"]
extended_features = ["first_scrn", "first_show", "peak", "first_week_audi"]


def evaluate_model(feats):
  v_cols = feats + [target_col]
  tr_sub = train_df.dropna(subset=v_cols)
  te_sub = test_df.dropna(subset=v_cols)
  if len(tr_sub) == 0 or len(te_sub) == 0:
    return None, None, 0, 0
  m = LinearRegression()
  m.fit(tr_sub[feats], tr_sub[target_col])
  preds = m.predict(te_sub[feats])
  actuals = te_sub[target_col]
  return (
      r2_score(actuals, preds),
      mean_absolute_error(actuals, preds),
      len(tr_sub),
      len(te_sub),
  )


r2_base, mae_base, tr_cnt_b, te_cnt_b = evaluate_model(base_default_features)
r2_ext, mae_ext, tr_cnt_e, te_cnt_e = evaluate_model(extended_features)

st.markdown("---")
st.subheader("⚖️ 변수 구성별 예측 점수 비교")
col_comp1, col_comp2 = st.columns(2)
with col_comp1:
  st.markdown("### 🔹 기본 변수 3가지\n(`first_scrn`, `first_show`, `peak`)")
  if r2_base is not None:
    st.metric("결정계수 ($R^2$)", f"{r2_base:.4f}")
    st.metric("평균 절대 오차 (MAE)", f"{mae_base:,.0f} 명")
  else:
    st.warning("데이터 부족으로 계산할 수 없습니다.")

with col_comp2:
  st.markdown("### 🔸 첫 주 관객 수 추가\n(+ `first_week_audi`)")
  if r2_ext is not None:
    st.metric("결정계수 ($R^2$)", f"{r2_ext:.4f}")
    st.metric("평균 절대 오차 (MAE)", f"{mae_ext:,.0f} 명")
  else:
    st.warning("데이터 부족으로 계산할 수 없습니다.")


# 결측치 제거 (사용자가 사이드바에서 선택한 현재 설정 기준)
valid_cols = selected_features + [target_col]
current_train_df = train_df.dropna(subset=valid_cols)
current_test_df = test_df.dropna(subset=valid_cols)

train_count = len(current_train_df)
test_count = len(current_test_df)

# 5. 학습 및 평가 현황 표시
st.markdown("---")
st.subheader("📈 현재 선택 모델 학습 및 평가 현황")
col1, col2, col3 = st.columns(3)
col1.metric("학습에 쓴 영화 편수", f"{train_count}편")
col2.metric("점수를 평가한 영화 편수", f"{test_count}편")
col3.metric("기준 기간", period_str)

if test_count == 0:
  st.error(
      "평가할 테스트 데이터가 부족합니다. 데이터 전체 개수를 확인해주세요."
  )
  st.stop()

# 6. 다중 회귀 모델 학습 및 예측 (사이드바 선택 기준)
X_train = current_train_df[selected_features]
y_train = current_train_df[target_col]
X_test = current_test_df[selected_features]
y_test = current_test_df[target_col]

model = LinearRegression()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

# 성능 지표
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

st.markdown("---")
st.subheader("🎯 현재 선택 모델 성능 평가")
m1, m2 = st.columns(2)
m1.metric("결정계수 ($R^2$)", f"{r2:.4f}")
m2.metric("평균 절대 오차 (MAE)", f"{mae:,.0f} 명")

# 7. 1,000명 미만 예측 처리
under_1000_mask = y_pred < 1000
under_1000_count = under_1000_mask.sum()

st.info(
    f"ℹ️ **예측 관객 수가 1,000명 미만인 영화 수:** {under_1000_count}편 (로그"
    " 스케일 그래프의 바닥 영역에 고정되어 표시됩니다)"
)

# 평가 데이터프레임 구성
eval_df = current_test_df[["movieNm", target_col]].copy()
eval_df["actual_audi"] = y_test
eval_df["pred_audi"] = y_pred

# 로그 스케일 표현을 위해 1,000 미만 예측값은 하한선으로 클리핑하여 시각화 대응
plot_pred = np.where(y_pred < 1000, 100, y_pred)
eval_df["plot_pred"] = plot_pred

# 8. Plotly 산점도 그리기 (로그 스케일)
st.markdown("---")
st.subheader("📉 실제 관객 수 vs 예측 관객 수 산점도 (로그 스케일)")

fig = px.scatter(
    eval_df,
    x="actual_audi",
    y="plot_pred",
    hover_name="movieNm",
    labels={
        "actual_audi": "실제 총 관객 수 (명)",
        "plot_pred": "예측 총 관객 수 (명)",
    },
    title="테스트셋 실제 관객 수 vs 예측 관객 수",
    log_x=True,
    log_y=True,
    custom_data=["pred_audi"],
)

fig.update_traces(
    hovertemplate=(
        "<b>%{hovername}</b><br>실제 관객 수: %{x:,.0f}명<br>예측 관객 수:"
        " %{customdata[0]:,.0f}명<extra></extra>"
    )
)

# 대각선 (y = x) 추가
all_vals = pd.concat([eval_df["actual_audi"], eval_df["plot_pred"]])
min_val = max(1, all_vals.min() / 2)
max_val = all_vals.max() * 2

fig.add_trace(
    go.Scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode="lines",
        name="실제값 = 예측값 (기준선)",
        line=dict(dash="dash", color="red"),
    )
)

fig.update_layout(
    xaxis=dict(range=[np.log10(min_val), np.log10(max_val)]),
    yaxis=dict(range=[np.log10(min_val), np.log10(max_val)]),
    height=600,
)

st.plotly_chart(fig, use_container_width=True)
