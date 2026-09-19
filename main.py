import streamlit as st
import pandas as pd
import math
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

st.set_page_config(
page_title="영화 유형 나누기",
page_icon="🎬",
layout="wide"
)

st.title("🎬 영화 유형 나누기")
st.markdown("KOBIS 데이터를 바탕으로 영화를 여러 유형으로 군집화하고 시각화하는 앱입니다.")

@st.cache_data
def load_data():
url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
df = pd.read_csv(url, encoding='utf-8')
return df

try:
df_raw = load_data()
except Exception as e:
st.error(f"데이터를 불러오는 데 실패했습니다: {e}")
st.stop()

total_rows = len(df_raw)
df = df_raw.copy()

df = df[df['first_week_audi'].notnull() & (df['first_week_audi'] > 0)]
required_cols = ['first_scrn', 'total_audi', 'days_in_top10', 'first_week_audi']
df = df.dropna(subset=required_cols)

valid_rows = len(df)

df['log_scrn'] = df['first_scrn'].apply(lambda x: math.log10(x) if x > 0 else 0)
df['log_audi'] = df['total_audi'].apply(lambda x: math.log10(x) if x > 0 else 0)
df['raw_days'] = df['days_in_top10']
df['long_run'] = df.apply(lambda row: min(row['total_audi'] / row['first_week_audi'], 20), axis=1)

feature_map = {
"스크린 수 (로그)": "log_scrn",
"누적 관객 (로그)": "log_audi",
"10위권 일수": "raw_days",
"롱런 지수": "long_run"
}

st.markdown(f"전체 편수: {total_rows}개 | 분석에 사용된 편수: {valid_rows}개 (결측치 및 첫 주 관객 0인 영화 제외)")

st.sidebar.header("설정")
selected_feature_labels = st.sidebar.multiselect(
"군집화에 사용할 속성 선택 (2개 이상)",
options=list(feature_map.keys()),
default=list(feature_map.keys())
)

n_clusters = st.sidebar.slider(
"묶음 수 선택",
min_value=2,
max_value=7,
value=3,
step=1
)

if len(selected_feature_labels) < 2:
st.warning("속성을 2개 이상 선택해 주세요.")
st.stop()

selected_feature_cols = [feature_map[label] for label in selected_feature_labels]

X = df[selected_feature_cols]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
df['cluster_raw'] = kmeans.fit_predict(X_scaled)

cluster_means_audi = df.groupby('cluster_raw')['total_audi'].mean().sort_values(ascending=False)
cluster_order = cluster_means_audi.index.tolist()

symbols = ["㉮", "㉯", "㉰", "㉱", "㉲", "㉳", "㉴"]
label_mapping = {cluster_order[i]: symbols[i] for i in range(n_clusters)}
cluster_groups = [symbols[i] for i in range(n_clusters)]

df['cluster'] = df['cluster_raw'].map(label_mapping)

sil_score = silhouette_score(X_scaled, df['cluster_raw'])
st.markdown(f"실루엣 점수: {sil_score:.4f} (점수는 -1에서 1 사이이며, 1에 가까울수록 묶음이 뚜렷함을 뜻합니다.)")

st.subheader("📊 2차원 산점도")
col1, col2 = st.columns(2)
with col1:
x_axis_2d = st.selectbox("2D 가로축 속성", options=selected_feature_labels, index=0)
with col2:
y_axis_2d = st.selectbox("2D 세로축 속성", options=selected_feature_labels, index=min(1, len(selected_feature_labels)-1))

fig_2d = px.scatter(
df,
x=feature_map[x_axis_2d],
y=feature_map[y_axis_2d],
color='cluster',
hover_name='movieNm',
category_orders={'cluster': cluster_groups},
title=f"2D 산점도: {x_axis_2d} vs {y_axis_2d}",
labels={feature_map[x_axis_2d]: x_axis_2d, feature_map[y_axis_2d]: y_axis_2d}
)
st.plotly_chart(fig_2d, use_container_width=True)

st.subheader("🧊 3차원 산점도")
if len(selected_feature_labels) >= 3:
c1, c2, c3 = st.columns(3)
with c1:
x_axis_3d = st.selectbox("3D X축 속성", options=selected_feature_labels, index=0)
with c2:
y_axis_3d = st.selectbox("3D Y축 속성", options=selected_feature_labels, index=1)
with c3:
z_axis_3d = st.selectbox("3D Z축 속성", options=selected_feature_labels, index=2)

fig_3d = px.scatter_3d(
    df,
    x=feature_map[x_axis_3d],
    y=feature_map[y_axis_3d],
    z=feature_map[z_axis_3d],
    color='cluster',
    hover_name='movieNm',
    category_orders={'cluster': cluster_groups},
    title=f"3D 산점도: {x_axis_3d}, {y_axis_3d}, {z_axis_3d}"
)
fig_3d.update_traces(marker=dict(size=3))
st.plotly_chart(fig_3d, use_container_width=True)


else:
st.info("3차원 산점도를 그리려면 속성을 3개 이상 선택해 주세요.")

st.subheader("📈 묶음 수별 이너시아(Inertia) 변화 및 최적 묶음 수 분석")
inertias = []
k_range = list(range(1, 8))
for k in k_range:
km = KMeans(n_clusters=k, random_state=42, n_init=10)
km.fit(X_scaled)
inertias.append(km.inertia_)

fig_elbow = go.Figure()
fig_elbow.add_trace(go.Scatter(x=k_range, y=inertias, mode='lines+markers', name='Inertia'))
fig_elbow.add_vline(x=n_clusters, line_dash="dash", line_color="red", annotation_text=f"현재 묶음 수 ({n_clusters})")
fig_elbow.update_layout(
title="묶음 수에 따른 이너시아(거리 제곱의 합) 꺾은선 그래프",
xaxis_title="묶음 수 (k)",
yaxis_title="이너시아 (Inertia)"
)
st.plotly_chart(fig_elbow, use_container_width=True)

elbow_data = []
prev_val = None
for i, k in enumerate(k_range):
val = inertias[i]
if prev_val is None:
diff = ""
else:
diff = f"{prev_val - val:,.2f}"

elbow_data.append({
    "묶음 수": k,
    "이너시아(거리 제곱의 합)": f"{val:,.2f}",
    "이전 값과의 차이(감소량)": diff
})
prev_val = val


elbow_df = pd.DataFrame(elbow_data)
st.table(elbow_df)

st.subheader("📋 유형별 요약 및 대표 영화")

summary_data = []
for clu in cluster_groups:
subset = df[df['cluster'] == clu]
count = len(subset)
mean_scrn = subset['first_scrn'].mean()
mean_audi = subset['total_audi'].mean()
mean_days = subset['days_in_top10'].mean()
mean_long = subset['long_run'].mean()

summary_data.append({
    "묶음": clu,
    "편수": count,
    "스크린 수 평균": f"{mean_scrn:,.1f}",
    "누적 관객 평균": f"{mean_audi:,.1f}",
    "10위권 일수 평균": f"{mean_days:,.1f}",
    "롱런 지수 평균": f"{mean_long:,.2f}"
})


summary_df = pd.DataFrame(summary_data)
st.table(summary_df)

st.markdown("### 🎬 유형별 누적 관객 상위 영화 (Top 5)")
for clu in cluster_groups:
subset = df[df['cluster'] == clu]
top5 = subset.sort_values(by='total_audi', ascending=False).head(5)
movie_titles = ", ".join(top5['movieNm'].tolist())
st.markdown(f"- 묶음 {clu}: {movie_titles}")
