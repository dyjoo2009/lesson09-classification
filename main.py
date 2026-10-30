import json
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------
# 기본 설정 (브라우저 탭 제목과 아이콘)
# ---------------------------------------------------------------
APP_TITLE = "뇌졸중 예측 실습실"
APP_ICON = "🧠"

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")

DATA_URL = "https://raw.githubusercontent.com/dyjoo2009/data/refs/heads/main/stroke.csv"
RECORD_DIR = Path(__file__).parent / "내_기록"
RECORD_FILE = RECORD_DIR / "기록.json"

# 큰 숫자 카드 글자 크기
st.markdown(
    """
    <style>
    [data-testid="stMetricValue"] { font-size: 2.8rem; font-weight: 700; }
    [data-testid="stMetricLabel"] { font-size: 1.05rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------------------
@st.cache_data(show_spinner="데이터를 불러오는 중입니다...")
def load_data(url: str) -> pd.DataFrame:
    return pd.read_csv(url, encoding="utf-8")


# ---------------------------------------------------------------
# 내 기록 불러오기 / 저장하기 (내_기록/기록.json)
# ---------------------------------------------------------------
def load_records() -> dict:
    empty = {"meanings": {}, "source": ""}
    if not RECORD_FILE.exists():
        return empty
    try:
        data = json.loads(RECORD_FILE.read_text(encoding="utf-8"))
        return {
            "meanings": dict(data.get("meanings", {})),
            "source": str(data.get("source", "")),
        }
    except (json.JSONDecodeError, OSError, AttributeError, TypeError, ValueError):
        return empty


def save_records(meanings: dict, source: str) -> None:
    RECORD_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"meanings": meanings, "source": source}
    RECORD_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------
# 열별 '값의 종류' 설명 만들기
# ---------------------------------------------------------------
def describe_values(series: pd.Series) -> str:
    values = series.dropna().unique()
    if len(values) <= 10:
        return ", ".join(str(v) for v in sorted(values))
    if pd.api.types.is_numeric_dtype(series):
        return f"숫자 ({series.min():g} ~ {series.max():g})"
    return f"문자 {len(values)}가지"


# ---------------------------------------------------------------
# 화면 시작
# ---------------------------------------------------------------
st.title(f"{APP_ICON} {APP_TITLE}")
st.caption("뇌졸중 환자 데이터가 어떤 데이터인지 먼저 살펴봅니다.")

try:
    df = load_data(DATA_URL)
except Exception as e:  # 네트워크 오류 등
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()

# 처음 접속(또는 새로고침)했을 때 한 번만 파일에서 기록을 읽어 온다
if "records" not in st.session_state:
    st.session_state["records"] = load_records()
records = st.session_state["records"]

# ---------------------------------------------------------------
# 1. 큰 숫자 카드 네 개
# ---------------------------------------------------------------
total = len(df)
n_cols = df.shape[1]
n_stroke = int((df["stroke"] == 1).sum())
ratio = n_stroke / total * 100 if total else 0

st.subheader("한눈에 보기")
c1, c2, c3, c4 = st.columns(4)
with c1:
    with st.container(border=True):
        st.metric("전체 사람 수", f"{total:,}명")
with c2:
    with st.container(border=True):
        st.metric("열 개수", f"{n_cols}개")
with c3:
    with st.container(border=True):
        st.metric("stroke가 1인 사람 수", f"{n_stroke:,}명")
with c4:
    with st.container(border=True):
        st.metric("stroke가 1인 비율", f"{ratio:.2f}%")

# ---------------------------------------------------------------
# 2. 열 설명 표 (우리말 뜻 칸은 직접 입력)
# ---------------------------------------------------------------
st.subheader("열 설명 표")
st.write("**우리말 뜻** 칸을 더블클릭해서 교재를 보고 직접 적어 보세요.")

base_table = pd.DataFrame(
    {
        "열 이름": df.columns,
        "우리말 뜻": [records["meanings"].get(c, "") for c in df.columns],
        "값의 종류": [describe_values(df[c]) for c in df.columns],
        "빈 값 개수": [int(df[c].isna().sum()) for c in df.columns],
    }
)

edited_table = st.data_editor(
    base_table,
    key="meaning_editor",
    hide_index=True,
    use_container_width=True,
    num_rows="fixed",
    disabled=["열 이름", "값의 종류", "빈 값 개수"],
    column_config={
        "우리말 뜻": st.column_config.TextColumn(
            "우리말 뜻", help="교재를 보고 직접 적어 넣으세요."
        ),
    },
)

if st.button("우리말 뜻 저장", key="save_meanings"):
    meanings = {
        row["열 이름"]: (row["우리말 뜻"] or "").strip()
        for _, row in edited_table.iterrows()
    }
    save_records(meanings, st.session_state.get("source_text", records["source"]))
    st.success("우리말 뜻을 내_기록 폴더에 저장했어요.")

# ---------------------------------------------------------------
# 3. 데이터 처음 다섯 줄
# ---------------------------------------------------------------
st.subheader("데이터 처음 다섯 줄")
st.dataframe(df.head(5), use_container_width=True)

# ---------------------------------------------------------------
# 4. 데이터 출처
# ---------------------------------------------------------------
st.subheader("데이터 출처")
source_text = st.text_area(
    "교재에 나온 출처를 여기에 적어 주세요.",
    value=records["source"],
    height=120,
    key="source_text",
)

if st.button("출처 저장", key="save_source"):
    meanings = {
        row["열 이름"]: (row["우리말 뜻"] or "").strip()
        for _, row in edited_table.iterrows()
    }
    save_records(meanings, source_text)
    st.success("출처를 내_기록 폴더에 저장했어요.")
