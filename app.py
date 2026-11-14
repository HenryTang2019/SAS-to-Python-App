import os
import io
import json
import pandas as pd
import streamlit as st

# ==========================================
# 0. 頁面初始化與基本設定
# ==========================================
st.set_page_config(
page_title="SAS → Python 學習與轉換助手",
page_icon="🔄",
layout="wide"
)

# 初始化 Session State
if "df_data" not in st.session_state:
    st.session_state.df_data = pd.DataFrame({
        "EmpID": [101, 102, 103, 104, 105],
        "Dept": ["HR", "IT", "IT", "HR", "FIN"],
        "Salary": [50000, 75000, 82000, 52000, 90000],
        "Bonus": [5000, None, 8000, None, 10000],
        "HireDate": pd.to_datetime(["2020-01-15", "2019-03-20", "2021-06-01", "2018-11-10", "2017-05-04"]),
        "Name": ["Alice", "Bob", "Charlie", "David", "Eva"]
    })

if "ocr_text" not in st.session_state:
    st.session_state.ocr_text = ""
if "conversion_result" not in st.session_state:
    st.session_state.conversion_result = None
  
# API Key 環境變數檢查
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 內置知識庫 (用於疑問解答優先檢索)
KNOWLEDGE_BASE = {
"data step": "SAS DATA Step 是隱含的逐行迴圈 (Implicit Loop)；pandas 則是向量化運算 (Vectorized Operations)，應儘量避免在 DataFrame 上使用 for 迴圈。",
"first.": "SAS 中的 FIRST.var 需要先 SORT，再用 DATA Step 判斷。pandas 替代方案為 `df.groupby('var').first()` 或 `df.groupby('var').head(1)` 或 `df.groupby('var')['target'].transform('first')`。",
"last.": "SAS 中的 LAST.var 替代方案為 `df.groupby('var').last()` 或 `df.groupby('var').tail(1)`。",
"substr": "SAS substr(s, 1, 2) 從位置 1 開始切取長度 2。Python 索引從 0 開始且左閉右開，字串切片為 `s[0:2]`；在 DataFrame 列上需使用 `.str[0:2]`。",
"proc sql": "SAS PROC SQL 中的 LEFT JOIN / INNER JOIN 對應 pandas 的 `pd.merge(df1, df2, on='key', how='left')` 或 `how='inner'`。",
"coalesce": "SAS COALESCE 函數可用於補空值。pandas 中可使用 `df['A'].fillna(df['B'])` 或 `df['A'].combine_first(df['B'])`。",
"proc transpose": "SAS PROC TRANSPOSE 長轉寬/寬轉長。pandas 寬轉長用 `pd.melt()`，長轉寬用 `df.pivot()` 或 `pd.pivot_table()`，簡單矩陣轉置用 `.T`。",
"proc freq": "SAS PROC FREQ 對應 pandas 的 `df['col'].value_counts(dropna=False)` 或雙變數交叉表 `pd.crosstab(df['col1'], df['col2'])`。",
"proc means": "SAS PROC MEANS 對應 pandas 的 `df.describe()` 或自訂聚合 `df.groupby('group').agg({'col': ['mean', 'std', 'min', 'max']})`。",
"macro": "SAS Macro (%macro / %end) 用於文字替換與動態生成代碼。Python 中直接採用標準函數 `def func(...)` 與模組化傳參即可。",
"missing": "SAS 數值型態缺失值標記為英文句點 `.`。pandas 讀入後會統一轉換為 `NaN` (或 `None` / `pd.NA`)。"
}

# Mock LLM API 呼叫 (若未配置真實 API 密鑰時的回退安全機制)
def call_llm_api(prompt, system_instruction=""):
if not OPENAI_API_KEY:
# 當沒有配置 OpenAI 密鑰時提供結構化模擬回應
return None
try:
import openai
client = openai.OpenAI(api_key=OPENAI_API_KEY)
response = client.chat.completions.create(
model="gpt-4o",
messages=[
{"role": "system", "content": system_instruction},
{"role": "user", "content": prompt}
],
temperature=0.2
)
return response.choices[0].message.content
except Exception as e:
return f"LLM API 呼叫失敗：{str(e)}"

# Mock / Engine OCR 處理
def process_ocr(image_file, engine="OCY"):
# 模擬 OCR 識別結果
mock_text = """DATA work.output;
SET work.sample_data;
IF Salary > 60000 THEN Salary_Class = 'High';
ELSE Salary_Class = 'Low';
Sub_Name = SUBSTR(Name, 1, 3);
RUN;"""
confidence = 0.96 if engine == "OCY" else (0.91 if engine == "Xberg" else 0.85)
return mock_text, confidence


# ==========================================
# UI 介面設計：標題與頁籤
# ==========================================
st.title("🔄 SAS → Python (pandas) 學習與代碼轉換助手")
st.markdown("專為 SAS 背景資料分析師打造的範式轉換與自動化翻譯工具")

tabs = st.tabs(["📘 教學與練習區", "🔄 代碼轉換器", "❓ 疑問與解答", "📂 資料 IO 區", "🎯 學習通關清單"])

# ------------------------------------------
# Tab 1: 教學與練習區
# ------------------------------------------
with tabs[0]:
st.header("📘 SAS 轉 Python 階梯式教學")
st.markdown("以下範例皆圍繞 `sample_data` 資料集展示 SAS 與 Python (pandas) 的語法與範式差異。")

stage = st.selectbox("選擇學習階段", [
"階段 1：環境與思維轉換 (Environment & Mindset)",
"階段 2：DATA Step 核心語法 (DATA Step Essentials)",
"階段 3：PROC SQL 與統計過程 (SQL & Summary Procedures)",
"階段 4：Macro 與函數化 (Macro System to Python Functions)"
])

if "階段 1" in stage:
st.subheader("階段 1：環境與思維轉換")

st.markdown("### 1.1 DataFrame vs DATA Step 隱含迴圈")
col1, col2 = st.columns(2)
with col1:
st.code("""/* SAS: 逐行隱含迴圈 */
DATA work.emp_bonus;
SET work.sample_data;
IF Bonus IS MISSING THEN Total = Salary;
ELSE Total = Salary + Bonus;
RUN;""", language="sas")
with col2:
st.code("""# Python: 向量化直接計算 (非 for 迴圈)
df['Total'] = df['Salary'] + df['Bonus'].fillna(0)""", language="python")
st.info("💡 **轉換要點**：SAS DATA Step 底層是 implicit loop（逐行讀取與處理）；pandas 優先採用向量化 (Vectorized) 運算，底層由 C 語言執行，速度遠快於 Python 原生 for 迴圈。")

with st.expander("✏️ 小練習 1.1"):
st.markdown("**題目**：寫出將 `Salary` 加薪 10% 產生新欄位 `New_Salary` 的 pandas 程式碼。")
st.code("df['New_Salary'] = df['Salary'] * 1.1", language="python")

st.markdown("---")
st.markdown("### 1.2 索引與字串切片差異")
col1, col2 = st.columns(2)
with col1:
st.code("""/* SAS: 位置從 1 開始，substr(s, start, length) */
DATA work.emp_sub;
SET work.sample_data;
Short_Name = SUBSTR(Name, 1, 2);
RUN;""", language="sas")
with col2:
st.code("""# Python: 索引從 0 開始，左閉右開 [start:stop]
df['Short_Name'] = df['Name'].str[0:2]""", language="python")
st.info("💡 **轉換要點**：SAS 的字串切片從位置 1 開始，第三個參數為「長度」；Python 索引從 0 開始，切片 `[0:2]` 代表索引 0 與 1（長度為 2）。在 pandas 欄位上需加上 `.str` 向量化屬性。")

elif "階段 2" in stage:
st.subheader("階段 2：DATA Step 核心語法")

st.markdown("### 2.1 FIRST. / LAST. 的復現")
col1, col2 = st.columns(2)
with col1:
st.code("""/* SAS: FIRST. / LAST. */
PROC SORT DATA=work.sample_data OUT=sorted_emp;
BY Dept Salary;
RUN;

DATA work.highest_paid;
SET sorted_emp;
BY Dept;
IF LAST.Dept;
RUN;""", language="sas")
with col2:
st.code("""# Python: groupby + tail / last / transform
df_sorted = df.sort_values(by=['Dept', 'Salary'])
highest_paid = df_sorted.groupby('Dept').tail(1)
# 或直接取得每個 Dept 最高的 Salary
# df_sorted.groupby('Dept').last().reset_index()""", language="python")
st.info("💡 **轉換要點**：SAS 依賴 `BY` 語句配合 `FIRST.` / `LAST.` 標記標籤；pandas 使用 `groupby()` 搭配 `head(1)` / `tail(1)` 或 `last()` 即可達到相同效果。")

with st.expander("✏️ 小練習 2.1"):
st.markdown("**題目**：如何取得每個部門 (Dept) 入職時間最早 (HireDate) 的員工？")
st.code("df.sort_values('HireDate').groupby('Dept').first().reset_index()", language="python")

elif "階段 3" in stage:
st.subheader("階段 3：PROC SQL 與統計過程")

st.markdown("### 3.1 PROC SQL JOIN & COALESCE")
col1, col2 = st.columns(2)
with col1:
st.code("""/* SAS: PROC SQL LEFT JOIN */
PROC SQL;
CREATE TABLE work.merged AS
SELECT a.*, COALESCE(a.Bonus, 0) AS Fixed_Bonus
FROM work.sample_data AS a;
QUIT;""", language="sas")
with col2:
st.code("""# Python: merge 與 fillna / combine_first
df['Fixed_Bonus'] = df['Bonus'].fillna(0)""", language="python")
st.info("💡 **轉換要點**：SAS PROC SQL 的 `COALESCE(val1, val2)` 在 pandas 中常用 `.fillna()` 或 `.combine_first()` 實現。多表 JOIN 使用 `pd.merge(df1, df2, on='key', how='left')`。")

st.markdown("---")
st.markdown("### 3.2 PROC FREQ 與 PROC MEANS")
col1, col2 = st.columns(2)
with col1:
st.code("""/* SAS: PROC FREQ & MEANS */
PROC FREQ DATA=work.sample_data;
TABLES Dept / MISSING;
RUN;

PROC MEANS DATA=work.sample_data MEAN STD;
VAR Salary;
CLASS Dept;
RUN;""", language="sas")
with col2:
st.code("""# Python: value_counts 與 groupby + agg
# PROC FREQ
freq = df['Dept'].value_counts(dropna=False)

# PROC MEANS
means = df.groupby('Dept')['Salary'].agg(['mean', 'std'])""", language="python")
st.info("💡 **轉換要點**：SAS 的 `PROC FREQ` 預設不統計缺失值 (需加 `/ MISSING`)，而 pandas `value_counts()` 預設亦會忽略 `NaN`，需帶入 `dropna=False`。`PROC MEANS` 可用 `describe()` 或 `groupby().agg()` 完整對照。")

elif "階段 4" in stage:
st.subheader("階段 4：Macro 與函數化")
st.markdown("### 4.1 SAS Macro (%IF/%DO) → Python Function")
col1, col2 = st.columns(2)
with col1:
st.code("""/* SAS: Macro 代碼 */
%MACRO filter_dept(data_in=, dept_name=, min_sal=0);
DATA work.filtered_out;
SET &data_in;
WHERE Dept = "&dept_name" AND Salary >= &min_sal;
RUN;
%MEND filter_dept;

%filter_dept(data_in=work.sample_data, dept_name=IT, min_sal=80000);""", language="sas")
with col2:
st.code("""# Python: 標準函數與參數傳遞
def filter_dept(data: pd.DataFrame, dept_name: str, min_sal: float = 0) -> pd.DataFrame:
filtered_df = data[(data['Dept'] == dept_name) & (data['Salary'] >= min_sal)].copy()
return filtered_df

# 呼叫函數
result_df = filter_dept(df, dept_name="IT", min_sal=80000)""", language="python")
st.info("💡 **轉換要點**：SAS Macro 是預處理器的文字替換機制；Python 無需 Macro 語法，直接使用包含明確參數型態與回傳值的標準 `def` 函數即可。")


# ------------------------------------------
# Tab 2: 代碼轉換器
# ------------------------------------------
with tabs[1]:
st.header("🔄 SAS → Python 代碼轉換器")

convert_mode = st.radio("轉換模式", ["手動輸入 SAS 代碼", "上傳圖片 (OCR 識別)"], horizontal=True)

input_sas_code = ""

if convert_mode == "手動輸入 SAS 代碼":
input_sas_code = st.text_area("請輸入 SAS 代碼", value="""DATA work.target_emp;
SET work.sample_data;
IF Dept = 'IT' THEN Bonus_Rate = 0.15;
ELSE Bonus_Rate = 0.05;
Total_Comp = Salary * (1 + Bonus_Rate);
Sub_Name = SUBSTR(Name, 1, 3);
RUN;""", height=180)
else:
st.subheader("圖片上傳與 OCR 識別")
uploaded_image = st.file_uploader("上傳 SAS 代碼截圖", type=["png", "jpg", "jpeg"])
ocr_engine = st.selectbox("選擇 OCR 後端引擎", ["OCY (程式碼推薦)", "Xberg", "Tesseract"])

if uploaded_image:
if st.button("進行 OCR 文字識別"):
raw_text, conf = process_ocr(uploaded_image, engine=ocr_engine)
st.session_state.ocr_text = raw_text
st.success(f"OCR 識別完成 (選用引擎: {ocr_engine}, 識別置信度: {conf*100:.1f}%)")

st.markdown("**OCR 識別結果 (可手動校正)：**")
input_sas_code = st.text_area("請校正 OCR 辨識結果", value=st.session_state.ocr_text, height=180)

if st.button("🚀 開始轉換為 Python (pandas)"):
if not input_sas_code.strip():
st.warning("請先輸入或 OCR 識別 SAS 代碼。")
else:
# 優先使用 LLM 轉換，若無 Key 則切換至內置規則翻譯引擎
system_prompt = "你是一位精通 SAS 與 Python pandas 的資料工程大師。請將 SAS 代碼轉換為 Python 代碼，並輸出逐行對照表與轉換難度評分。請以 JSON 格式回應。"
user_prompt = f"""請將以下 SAS 代碼轉換為 Python (pandas) 代碼：

```sas
{input_sas_code}

