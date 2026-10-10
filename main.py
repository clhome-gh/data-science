import re
from itertools import combinations
import pandas as pd
import plotly.express as px
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="급식 규칙 찾기", page_icon="🍱", layout="wide"
)

st.title("🍱 우리 학교 급식 규칙 찾기")
st.markdown(
    "중식 식단 데이터를 바탕으로 함께 자주 나오는 메뉴 연관 규칙을 찾아봅니다."
)


@st.cache_data
def load_data():
  url = "https://raw.githubusercontent.com/teacher188-netizen/2026-datascience/refs/heads/main/sangok_meals.csv"
  df = pd.read_csv(url, encoding="utf-8")
  return df


try:
  df = load_data()
except Exception as e:
  st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
  st.stop()


# 메뉴 정제 함수 (괄호 및 내용 제거)
def clean_menu(menu_str):
  if pd.isna(menu_str):
    return []
  items = str(menu_str).split("|")
  cleaned = []
  for item in items:
    # 괄호와 그 안의 내용 제거 (반각 및 전각 괄호 대응)
    item_clean = re.sub(r"\(.*?\)", "", item)
    item_clean = re.sub(r"（.*?）", "", item_clean).strip()
    if item_clean:
      cleaned.append(item_clean)
  return cleaned


df["cleaned_menus"] = df["메뉴"].apply(clean_menu)

total_days = len(df)
all_menus = sorted(
    list(set(item for sublist in df["cleaned_menus"] for item in sublist))
)
total_menu_types = len(all_menus)

# 연관 규칙 분석 (2개 메뉴 쌍)
transactions = df["cleaned_menus"].tolist()
total_trans = len(transactions)

item_counts = {}
for t in transactions:
  for item in set(t):
    item_counts[item] = item_counts.get(item, 0) + 1

pair_counts = {}
for t in transactions:
  unique_items = sorted(list(set(t)))
  for a, b in combinations(unique_items, 2):
    pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1
    pair_counts[(b, a)] = pair_counts.get((b, a), 0) + 1

rules_data = []
for (a, b), co_count in pair_counts.items():
  supp_a_b = co_count / total_trans
  supp_a = item_counts[a] / total_trans
  supp_b = item_counts[b] / total_trans

  confidence = co_count / item_counts[a] if item_counts[a] > 0 else 0
  lift = confidence / supp_b if supp_b > 0 else 0

  rules_data.append({
      "조건": a,
      "결과": b,
      "동시": co_count,
      "지지도": round(supp_a_b, 4),
      "신뢰도": round(confidence, 4),
      "향상도": round(lift, 4),
  })

rules_df = pd.DataFrame(rules_data)
total_pairs = len(pair_counts)

# 상단 요약 정보 한 줄 표시
st.info(
    f"📊 **급식 일수:** {total_days}일 &nbsp;|&nbsp; **메뉴 종류 수:**"
    f" {total_menu_types}개 &nbsp;|&nbsp; **함께 나온 메뉴 쌍의 수:** {total_pairs}개"
)

# 사이드바 설정 (필터 및 정렬)
st.sidebar.header("🔍 검색 및 정렬 설정")

selected_menus = st.sidebar.multiselect(
    "특정 메뉴 선택 (조건 또는 결과에 포함)",
    options=all_menus,
    placeholder="메뉴를 선택하세요 (복수 선택 가능)",
)

sort_by = st.sidebar.selectbox(
    "정렬 기준", ["향상도 순", "신뢰도 순", "동시 순"]
)

# 필터링 적용
filtered_df = rules_df.copy()
if selected_menus:
  filtered_df = filtered_df[
      filtered_df["조건"].isin(selected_menus)
      | filtered_df["결과"].isin(selected_menus)
  ]

# 정렬 적용
if sort_by == "향상도 순":
  filtered_df = filtered_df.sort_values(
      by=["향상도", "신뢰도", "동시"], ascending=False
  )
elif sort_by == "신뢰도 순":
  filtered_df = filtered_df.sort_values(
      by=["신뢰도", "향상도", "동시"], ascending=False
  )
else:
  filtered_df = filtered_df.sort_values(
      by=["동시", "향상도", "신뢰도"], ascending=False
  )

st.subheader("📋 연관 규칙 표")
st.write(f"검색 결과: 총 {len(filtered_df)}건의 규칙이 있습니다.")
st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# 향상도 상위 10개 가로 막대그래프
st.subheader("📈 향상도 상위 규칙 그래프 (Top 10)")

if len(filtered_df) > 0:
  top_10 = filtered_df.head(10).copy()
  # 보기 쉽게 조건 -> 결과 라벨 생성
  top_10["규칙"] = top_10["조건"] + " ➔ " + top_10["결과"]
  # 그래프가 상위 10개가 위에서부터 보이도록 역순 정렬
  top_10 = top_10.sort_values(by="향상도", ascending=True)

  fig = px.bar(
      top_10,
      x="향상도",
      y="규칙",
      orientation="h",
      title="향상도(Lift) 기준 상위 규칙",
      labels={"향상도": "향상도 (Lift)", "규칙": "메뉴 규칙 (조건 ➔ 결과)"},
      text="향상도",
  )
  fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
  fig.update_layout(height=450, margin=dict(l=20, r=20, t=40, b=20))
  st.plotly_chart(fig, use_container_width=True)
else:
  st.warning("조건에 해당하는 규칙이 없어 그래프를 표시할 수 없습니다.")
