import streamlit as st
import pandas as pd
from scipy import stats

# --- 页面设置 ---
st.set_page_config(page_title="统计差异分析助手", page_icon="🧮", layout="wide")

st.title("🧮 统计学差异分析智能推荐器")
st.markdown("### 上传数据 -> 自动检验 -> 推荐方法")

# --- 侧边栏：使用说明 ---
with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    1. **准备数据**：请使用 Excel 或 CSV。
    2. **格式要求**：需要两列：
       - **分组列** (如：A组, B组)
       - **数值列** (如：体重, 血压)
    3. **上传**：在右侧上传文件。
    """)
    st.info("数据将由 Python Scipy 库进行运算")

# --- 主体逻辑 ---
uploaded_file = st.file_uploader("📂 请上传您的 Excel 或 CSV 文件", type=["csv", "xlsx"])

if uploaded_file:
    try:
        # 读取数据
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success("数据上传成功！请选择变量进行分析：")
        
        # 布局：变量选择
        c1, c2 = st.columns(2)
        cols = df.columns.tolist()
        
        with c1:
            group_col = st.selectbox("选择分组变量 (例如: 组别)", cols)
        with c2:
            value_col = st.selectbox("选择数值变量 (例如: 测量值)", [c for c in cols if c != group_col])

        if st.button("🚀 开始分析"):
            # 数据清洗
            data_clean = df[[group_col, value_col]].dropna()
            groups = data_clean[group_col].unique()
            group_data = [data_clean[data_clean[group_col] == g][value_col].values for g in groups]
            n_groups = len(groups)

            if n_groups < 2:
                st.error("错误：至少需要2个组别才能比较。")
            else:
                st.write("---")
                
                # 1. 正态性检验
                st.subheader("1️⃣ 正态性检验 (Shapiro-Wilk)")
                is_normal = True
                norm_results = []
                for i, g in enumerate(groups):
                    if len(group_data[i]) < 3:
                        p_val = 0 # 样本太少视为非正态
                        note = "样本量不足"
                    else:
                        stat, p_val = stats.shapiro(group_data[i])
                        note = ""
                    
                    is_pass = p_val > 0.05
                    if not is_pass: is_normal = False
                    norm_results.append(f"**{g}**: p={p_val:.4f} {'✅' if is_pass else '❌'} {note}")
                
                for res in norm_results: st.write(res)
                st.caption("p > 0.05 表示服从正态分布")

                # 2. 方差齐性检验
                st.subheader("2️⃣ 方差齐性检验 (Levene)")
                is_equal_var = True
                if n_groups >= 2:
                    stat, p_levene = stats.levene(*group_data)
                    is_equal_var = p_levene > 0.05
                    st.write(f"**Levene Test**: p={p_levene:.4f} {'✅ 方差齐' if is_equal_var else '❌ 方差不齐'}")
                st.caption("p > 0.05 表示方差齐")

                # 3. 智能推荐
                st.write("---")
                st.header("🧠 推荐统计方法")
                
                method = "未知"
                reason = "未知"
                code_snippet = ""

                # 决策树逻辑
                if n_groups == 2:
                    if not is_normal:
                        method = "Mann-Whitney U 检验"
                        reason = "数据不满足正态分布，应使用非参数检验。"
                        res_calc = stats.mannwhitneyu(group_data[0], group_data[1])
                    elif is_normal and is_equal_var:
                        method = "独立样本 t 检验 (Student's t-test)"
                        reason = "数据满足正态性和方差齐性，这是标准方法。"
                        res_calc = stats.ttest_ind(group_data[0], group_data[1], equal_var=True)
                    else: # 正态但不齐
                        method = "Welch's t 检验"
                        reason = "数据正态但方差不齐，需使用修正的 t 检验。"
                        res_calc = stats.ttest_ind(group_data[0], group_data[1], equal_var=False)
                
                else: (n_groups >= 3)
                    if not is_normal:
                        method = "Kruskal-Wallis H 检验"
                        reason = "多组数据且非正态，使用非参数 ANOVA。"
                        res_calc = stats.kruskal(*group_data)
                    elif is_normal and is_equal_var:
                        method = "单因素方差分析 (One-Way ANOVA)"
                        reason = "多组数据，满足正态和方差齐。"
                        res_calc = stats.f_oneway(*group_data)
                    else:
                        method = "Welch's ANOVA"
                        reason = "多组数据，正态但方差不齐。"
                        res_calc = None # Scipy无直接函数，需额外库，此处略过计算

                st.success(f"👉 建议使用：**{method}**")
                st.info(f"理由：{reason}")
                
                # 显示计算结果
                if res_calc:
                    with st.expander("查看计算结果 (P值)"):
                        st.write(f"Statistic: {res_calc.statistic:.3f}")
                        st.write(f"P-value: {res_calc.pvalue:.4f}")
                        if res_calc.pvalue < 0.05:
                            st.write("🔴 **结论：组间存在显著差异**")
                        else:
                            st.write("🔵 **结论：组间无显著差异**")

    except Exception as e:
        st.error(f"读取文件出错，请确保没有上传空文件或格式错误。\n错误信息: {e}")