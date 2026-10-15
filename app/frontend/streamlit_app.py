import streamlit as st
import pandas as pd
import plotly.express as px

from app.analysis.io import load_dataframe
from app.analysis.profiling import profile_dataframe, quality_report
from app.analysis.engine import execute, validate
from app.analysis.charts import chart_for
from app.ai.parser import parse
from app.ai.insights import verified_insight
from app.ai.smart_parser import smart_parse
from app.ai.ollama_client import ask_ai
from app.database.loader import load_dataframe_to_sql
from app.database.sql_engine import analyze_question_with_sql
from app.config import settings
from app.cloud.blob import BlobStore


st.set_page_config(
    page_title="AI Data Analyst",
    layout="wide"
)

st.title("📊 Cloud-Based AI-Powered Data Analyst Platform")
st.caption(
    "Local-first production architecture — Phase 1 + extensible Azure foundation"
)

st.info("Upload a dataset to begin.")

uploaded_file = st.file_uploader(
    "Upload CSV, XLSX or XLS",
    type=["csv", "xlsx", "xls"]
)


if uploaded_file is not None:
    try:
        blob_store = BlobStore(
            settings.azure_storage_connection_string,
            settings.azure_storage_container
        )

        blob_result = blob_store.upload(
            uploaded_file.getvalue(),
            uploaded_file.name
        )

        st.session_state["blob_result"] = blob_result
        st.success(f"Storage status: {blob_result['stored']} | File: {blob_result['name']}")

    except Exception as blob_error:
        st.warning(
            f"Dataset will still load locally. "
            f"Blob Storage upload failed: {blob_error}"
        )

    try:
        df = load_dataframe(uploaded_file)
        st.session_state["df"] = df
        st.session_state["filename"] = uploaded_file.name

        # SQL storage is optional for this local-first phase.
        try:
            table_name = load_dataframe_to_sql(df, uploaded_file.name)
            st.session_state["table_name"] = table_name
        except Exception as sql_load_error:
            st.session_state.pop("table_name", None)
            st.warning(
                "Dataset loaded, but saving it to SQL was unavailable. "
                f"Ask Data will still try local analysis. Details: {sql_load_error}"
            )

    except Exception as e:
        st.error(f"Could not load dataset: {e}")

        st.session_state["df"] = df
        st.session_state["filename"] = uploaded_file.name

        # SQL storage is optional for this local-first phase. The uploaded
        # DataFrame remains usable even if SQL persistence is unavailable.
        try:
            table_name = load_dataframe_to_sql(df, uploaded_file.name)
            st.session_state["table_name"] = table_name
        except Exception as sql_load_error:
            st.session_state.pop("table_name", None)
            st.warning(
                "Dataset loaded, but saving it to SQL was unavailable. "
                f"Ask Data will still try local analysis. Details: {sql_load_error}"
            )

    except Exception as e:
        st.error(f"Could not load dataset: {e}")


df = st.session_state.get("df")

if df is not None:

    st.success(
        f"Dataset loaded successfully: {st.session_state['filename']}"
    )

    tabs = st.tabs([
        "Preview",
        "Profile",
        "Ask Data",
        "Dashboard"
    ])

    # -------------------------
    # Preview
    # -------------------------
    with tabs[0]:
        st.subheader("Dataset Preview")
        st.dataframe(
            df.head(100),
            width="stretch"
        )

    # -------------------------
    # Profile
    # -------------------------
    with tabs[1]:
        st.subheader("Data Profile")

        profile = profile_dataframe(df)

        col1, col2, col3 = st.columns(3)

        col1.metric("Rows", profile["rows"])
        col2.metric("Columns", profile["columns"])
        col3.metric("Duplicates", profile["duplicates"])

        st.subheader("Column Details")

        st.dataframe(
            pd.DataFrame(profile["columns_detail"]),
            width="stretch"
        )


        st.subheader("Data Quality Report")

        issues = quality_report(df)

        if len(df) == 0:
            st.warning("The dataset is empty.")

        if len(df.columns) == 0:
            st.warning("The dataset has no columns.")

        if issues and issues != ["No basic data quality issues detected."]:
            st.warning(f"Found {len(issues)} data quality issue(s).")

            for issue in issues:
                st.write(f"⚠️ {issue}")
        else:
            st.success("No basic data quality issues detected.")

        if len(df) > 0:
            missing_count = int(df.isna().sum().sum())
            duplicate_count = int(df.duplicated().sum())
            complete_cells = int(df.notna().sum().sum())
            total_cells = int(df.shape[0] * df.shape[1])

            quality_col1, quality_col2, quality_col3 = st.columns(3)

            quality_col1.metric("Missing Values", missing_count)
            quality_col2.metric("Duplicate Rows", duplicate_count)

            completeness = (
                (complete_cells / total_cells) * 100
                if total_cells > 0 else 0
            )

            quality_col3.metric(
                "Data Completeness",
                f"{completeness:.1f}%"
            )


    # -------------------------
    # Ask Data
    # -------------------------

    with tabs[2]:
        st.subheader("Ask Questions About Your Data")

        question = st.text_input(
            "Ask your data",
            placeholder="Which products have the highest sales?"
        )

        analyze_clicked = st.button("Analyze", type="primary")

        if analyze_clicked:
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                try:
                    with st.spinner("AI is understanding your question..."):
                        plan = smart_parse(question, df)

                    st.subheader("Smart AI Analysis Plan")
                    st.json(plan)

                    with st.spinner("Calculating from your dataset..."):
                        result = execute(df, plan)

                    validation = validate(result)

                    st.subheader("Verified Result")
                    st.dataframe(result, width="stretch")
                    st.caption(f"Validation: {validation}")

                    chart = chart_for(result, plan)
                    if chart is not None:
                        st.subheader("Visualization")
                        st.plotly_chart(
                            chart,
                            width="stretch"
                        )

                    st.subheader("AI Business Explanation")
                    result_text = result.to_string(index=False)

                    ai_prompt = f"""
 Do not add currency symbols such as $, ₹, or units unless
 they are explicitly confirmed by the dataset or metadata.
 Preserve the numeric values exactly as shown in the verified result.
You are explaining the output of a data analysis tool.

User question:
{question}

Analysis plan:
{plan}

Verified calculation result:
{result_text}

Rules:
1. Treat the verified result as the only source of numerical facts.
2. Do not calculate, estimate, or invent additional numbers.
3. Do not invent causes, trends, or business reasons not shown by the result.
4. Explain only what the displayed result supports.
5. If the result is insufficient, clearly state that limitation.
6. Never claim that you performed calculations yourself.
7. Use simple, concise language.
"""

                    with st.spinner("AI is explaining the result..."):
                        try:
                            explanation = ask_ai(ai_prompt)
                            if explanation and explanation.strip():
                                st.info(
                                    "AI explanation — the verified table "
                                    "above remains the source of truth."
                                )
                                st.write(explanation)
                            else:
                                st.warning(
                                    "AI returned an empty explanation. "
                                    "Use the verified result above."
                                )
                        except Exception as ai_error:
                            st.warning(
                                "AI explanation unavailable. "
                                "The verified calculation above remains "
                                f"available. Details: {ai_error}"
                            )

                except Exception as smart_error:
                    st.warning(
                        f"Smart AI analysis unavailable: {smart_error}"
                    )

                    try:
                        table_name = st.session_state.get("table_name")
                        if not table_name:
                            raise ValueError(
                                "Please upload the dataset again."
                            )

                        st.info("Trying the existing SQL analysis...")
                        sql_result = analyze_question_with_sql(
                            question, table_name
                        )

                        st.subheader("SQL Analysis Result")
                        st.dataframe(
                            sql_result,
                            width="stretch"
                        )

                    except Exception as sql_error:
                        st.warning(
                            f"SQL fallback unavailable: {sql_error}"
                        )

                        try:
                            st.info("Trying the basic analysis parser...")
                            plan = parse(question, df)
                            result = execute(df, plan)

                            st.subheader("Basic Analysis Plan")
                            st.json(plan)

                            st.subheader("Verified Result")
                            st.dataframe(
                                result,
                                width="stretch"
                            )
                            st.caption(
                                f"Validation: {validate(result)}"
                            )

                            chart = chart_for(result, plan)
                            if chart is not None:
                                st.subheader("Visualization")
                                st.plotly_chart(
                                    chart,
                                    width="stretch"
                                )

                            st.subheader("Verified Business Insight")
                            st.write(verified_insight(plan, result))

                        except Exception as fallback_error:
                            st.error(
                                "All analysis methods failed. "
                                f"Smart AI: {smart_error}; "
                                f"SQL: {sql_error}; "
                                f"Basic parser: {fallback_error}"
                            )


    # Dashboard
    with tabs[3]:
        st.subheader("Advanced Analytics Dashboard")
        st.caption("Explore your dataset using filters, KPI cards, and charts.")

        numeric_columns = df.select_dtypes(
            include="number"
        ).columns.tolist()

        categorical_columns = [
            column for column in df.columns
            if (
                pd.api.types.is_object_dtype(df[column])
                or isinstance(df[column].dtype, pd.CategoricalDtype)
            )
            and df[column].nunique(dropna=True) > 1
        ]

        # Dashboard filters
        st.subheader("Dashboard Filters")

        filtered_df = df.copy()

        if categorical_columns:
            filter_column = st.selectbox(
                "Filter dataset by",
                options=["All data"] + categorical_columns,
                key="dashboard_filter_column"
            )

            if filter_column != "All data":
                filter_values = sorted(
                    filtered_df[filter_column]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                selected_values = st.multiselect(
                    f"Select {filter_column}",
                    options=filter_values,
                    default=filter_values,
                    key="dashboard_filter_values"
                )

                filtered_df = filtered_df[
                    filtered_df[filter_column]
                    .astype(str)
                    .isin(selected_values)
                ]

        if filtered_df.empty:
            st.warning("No rows match the selected filters.")

        else:
            # KPI cards
            st.subheader("Key Performance Indicators")

            kpi1, kpi2, kpi3 = st.columns(3)

            kpi1.metric("Total Rows", f"{len(filtered_df):,}")
            kpi2.metric("Total Columns", f"{len(filtered_df.columns):,}")

            duplicate_count = int(
                filtered_df.duplicated().sum()
            )
            kpi3.metric("Duplicate Rows", f"{duplicate_count:,}")

            if numeric_columns:
                metric_column = st.selectbox(
                    "Choose a numeric metric",
                    options=numeric_columns,
                    key="dashboard_metric"
                )

                total_value = filtered_df[metric_column].sum()
                average_value = filtered_df[metric_column].mean()

                metric1, metric2 = st.columns(2)

                metric1.metric(
                    f"Total {metric_column}",
                    f"{total_value:,.2f}"
                )

                metric2.metric(
                    f"Average {metric_column}",
                    (
                        f"{average_value:,.2f}"
                        if pd.notna(average_value)
                        else "N/A"
                    )
                )

                # Chart controls
                st.subheader("Interactive Visualization")

                if categorical_columns:
                    chart_col1, chart_col2 = st.columns(2)

                    with chart_col1:
                        group_column = st.selectbox(
                            "Group results by",
                            options=categorical_columns,
                            key="dashboard_group"
                        )

                    with chart_col2:
                        aggregation = st.selectbox(
                            "Aggregation",
                            options=["sum", "mean", "count"],
                            key="dashboard_aggregation"
                        )

                    if aggregation == "count":
                        chart_data = (
                            filtered_df
                            .groupby(group_column, dropna=False)[metric_column]
                            .count()
                            .reset_index(name="Value")
                        )
                    else:
                        chart_data = (
                            filtered_df
                            .groupby(group_column, dropna=False)[metric_column]
                            .agg(aggregation)
                            .reset_index(name="Value")
                        )

                    chart_data[group_column] = (
                        chart_data[group_column]
                        .fillna("Missing")
                        .astype(str)
                    )

                    chart_data = chart_data.sort_values(
                        "Value",
                        ascending=False
                    )

                    fig = px.bar(
                        chart_data,
                        x=group_column,
                        y="Value",
                        title=f"{aggregation.title()} of {metric_column} by {group_column}",
                        labels={
                            group_column: group_column,
                            "Value": f"{aggregation.title()} {metric_column}"
                        },
                        hover_data={"Value": ":,.2f"}
                    )

                    fig.update_layout(
                        xaxis_title=group_column,
                        yaxis_title=f"{aggregation.title()} {metric_column}",
                        xaxis_tickangle=-30
                    )

                    st.plotly_chart(
                        fig,
                        width="stretch"
                    )

                else:
                    st.info(
                        "No suitable categorical columns found for a grouped chart."
                    )

            else:
                st.info(
                    "No numeric columns available for KPI metrics or numeric charts."
                )

            # Top Categories Analysis
            if categorical_columns and numeric_columns:
                st.subheader("🏆 Top Categories Analysis")

                top_category_column = st.selectbox(
                    "Choose a category for ranking",
                    options=categorical_columns,
                    key="top_category_column"
                )

                top_metric_column = st.selectbox(
                    "Choose a metric for ranking",
                    options=numeric_columns,
                    key="top_metric_column"
                )

                top_n = st.slider(
                    "Number of top categories",
                    min_value=1,
                    max_value=10,
                    value=5,
                    key="top_n_categories"
                )

                top_data = (
                    filtered_df
                    .groupby(top_category_column, dropna=False)[top_metric_column]
                    .sum()
                    .reset_index(name="Total")
                    .sort_values("Total", ascending=False)
                    .head(top_n)
                )

                top_data[top_category_column] = (
                    top_data[top_category_column]
                    .fillna("Missing")
                    .astype(str)
                )

                st.plotly_chart(
                    px.bar(
                        top_data,
                        x=top_category_column,
                        y="Total",
                        title=f"Top {top_n} by {top_metric_column}",
                        labels={
                            top_category_column: top_category_column,
                            "Total": f"Total {top_metric_column}"
                        }
                    ),
                    width="stretch"
                )

            # Sales and Profit Trend Analysis
            st.subheader("📈 Trend Analysis")

            date_columns = [
                column for column in filtered_df.columns
                if (
                    pd.api.types.is_datetime64_any_dtype(filtered_df[column])
                    or "date" in column.lower()
                )
            ]

            if date_columns and numeric_columns:
                trend_col1, trend_col2 = st.columns(2)

                with trend_col1:
                    date_column = st.selectbox(
                        "Choose date column",
                        options=date_columns,
                        key="trend_date_column"
                    )

                with trend_col2:
                    trend_metric = st.selectbox(
                        "Choose metric for trend",
                        options=numeric_columns,
                        key="trend_metric"
                    )

                trend_df = filtered_df.copy()
                trend_df[date_column] = pd.to_datetime(
                    trend_df[date_column],
                    errors="coerce"
                )
                trend_df[trend_metric] = pd.to_numeric(
                    trend_df[trend_metric],
                    errors="coerce"
                )

                trend_df = trend_df.dropna(
                    subset=[date_column, trend_metric]
                )

                if not trend_df.empty:
                    trend_df["Month"] = (
                        trend_df[date_column]
                        .dt.to_period("M")
                        .astype(str)
                    )

                    monthly_trend = (
                        trend_df.groupby("Month")[trend_metric]
                        .sum()
                        .reset_index()
                        .sort_values("Month")
                    )

                    st.plotly_chart(
                        px.line(
                            monthly_trend,
                            x="Month",
                            y=trend_metric,
                            markers=True,
                            title=f"Monthly {trend_metric} Trend"
                        ),
                        width="stretch"
                    )
                else:
                    st.info(
                        "No valid dates or numeric values available for trend analysis."
                    )
            else:
                st.info(
                    "Trend analysis requires a date column and a numeric column."
                )


            # Download Analysis Report
            st.subheader("📥 Download Analysis Report")

            report_df = filtered_df.copy()

            download_col1, download_col2 = st.columns(2)

            with download_col1:
                csv_data = report_df.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="analysis_report.csv",
                    mime="text/csv",
                    key="download_analysis_csv"
                )

            with download_col2:
                import io

                excel_buffer = io.BytesIO()

                with pd.ExcelWriter(
                    excel_buffer,
                    engine="openpyxl"
                ) as writer:
                    report_df.to_excel(
                        writer,
                        index=False,
                        sheet_name="Analysis Report"
                    )

                st.download_button(
                    label="Download Excel",
                    data=excel_buffer.getvalue(),
                    file_name="analysis_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_analysis_excel"
                )

            # Show filtered records
            with st.expander("View filtered dataset"):
                st.dataframe(
                    filtered_df,
                    width="stretch"
                )

else:
    st.info("Upload a dataset above to begin.")
