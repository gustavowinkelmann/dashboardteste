 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/app.py b/app.py
new file mode 100644
index 0000000000000000000000000000000000000000..4bdcca8da44e6c8bdc6394a799f8592eeb97a932
--- /dev/null
+++ b/app.py
@@ -0,0 +1,128 @@
+import pandas as pd
+import plotly.express as px
+import streamlit as st
+
+st.set_page_config(
+    page_title="Painel Comercial 2025",
+    layout="wide",
+    initial_sidebar_state="expanded",
+)
+
+@st.cache_data
+def load_data(path: str) -> pd.DataFrame:
+    df = pd.read_csv(path)
+    month_order = [
+        "Enero",
+        "Febrero",
+        "Marzo",
+        "Abril",
+        "Mayo",
+        "Junio",
+        "Julio",
+        "Agosto",
+        "Septiembre",
+        "Octubre",
+        "Noviembre",
+        "Diciembre",
+    ]
+    df["Mes"] = pd.Categorical(df["Mes"], categories=month_order, ordered=True)
+    df = df.sort_values("Mes").reset_index(drop=True)
+    return df
+
+def format_currency(value: float) -> str:
+    return f"R$ {value:,.0f}".replace(",", "_").replace(".", ",").replace("_", ".")
+
+def main() -> None:
+    df = load_data("data/ventas_2025.csv")
+    seller_columns = [col for col in df.columns if col not in {"Mes", "Total"}]
+
+    st.title("Painel Comercial 2025")
+    st.caption(
+        "Resumo executivo do potencial mensal por vendedor baseado na consolidação fornecida pela área comercial."
+    )
+
+    month_options = df["Mes"].tolist()
+    start_month, end_month = st.select_slider(
+        "Selecione o intervalo de meses a analisar",
+        options=month_options,
+        value=(month_options[0], month_options[-1]),
+    )
+    start_index = month_options.index(start_month)
+    end_index = month_options.index(end_month)
+    selected_months = month_options[start_index : end_index + 1]
+    filtered_df = df[df["Mes"].isin(selected_months)].copy()
+
+    total_period = float(filtered_df["Total"].sum())
+    best_month_row = filtered_df.loc[filtered_df["Total"].idxmax()]
+    best_month_name = str(best_month_row["Mes"])
+    best_month_total = float(best_month_row["Total"])
+
+    sellers_totals = filtered_df[seller_columns].sum().sort_values(ascending=False)
+    top_seller = sellers_totals.index[0]
+    top_seller_total = float(sellers_totals.iloc[0])
+    last_month_total = float(filtered_df["Total"].iloc[-1])
+    previous_month_total = float(filtered_df["Total"].iloc[-2]) if len(filtered_df) > 1 else None
+
+    delta_text = "N/A"
+    if previous_month_total not in (None, 0):
+        delta_last_month = (last_month_total - previous_month_total) / previous_month_total * 100
+        delta_text = f"{delta_last_month:.1f}%"
+
+    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
+    metric_col1.metric("Potencial acumulado no período", format_currency(total_period))
+    metric_col2.metric("Melhor mês", best_month_name, format_currency(best_month_total))
+    metric_col3.metric("Top vendedor", top_seller, format_currency(top_seller_total))
+    metric_col4.metric("Último mês vs. anterior", format_currency(last_month_total), delta_text)
+
+    st.divider()
+
+    selected_sellers = st.multiselect(
+        "Escolha os vendedores para analisar",
+        seller_columns,
+        default=seller_columns,
+    )
+
+    if not selected_sellers:
+        st.warning("Selecione ao menos um vendedor para visualizar os gráficos.")
+        return
+
+    fig_total = px.line(
+        filtered_df,
+        x="Mes",
+        y="Total",
+        markers=True,
+        title="Evolução do potencial total",
+        labels={"Mes": "Mês", "Total": "Potencial (R$)"},
+    )
+    fig_total.update_layout(yaxis_tickprefix="R$ ", hovermode="x unified")
+
+    melted = filtered_df.melt(
+        id_vars="Mes", value_vars=selected_sellers, var_name="Vendedor", value_name="Potencial"
+    )
+    fig_sellers = px.bar(
+        melted,
+        x="Mes",
+        y="Potencial",
+        color="Vendedor",
+        title="Participação mensal por vendedor",
+        labels={"Mes": "Mês", "Potencial": "Potencial (R$)"},
+    )
+    fig_sellers.update_layout(yaxis_tickprefix="R$ ", legend_title="Vendedores")
+
+    chart_col1, chart_col2 = st.columns(2)
+    chart_col1.plotly_chart(fig_total, use_container_width=True)
+    chart_col2.plotly_chart(fig_sellers, use_container_width=True)
+
+    st.subheader("Visão detalhada")
+    styled_df = filtered_df.set_index("Mes")
+    styled_df[selected_sellers + ["Total"]] = styled_df[selected_sellers + ["Total"]].applymap(
+        lambda x: format_currency(float(x))
+    )
+    st.dataframe(styled_df, use_container_width=True)
+
+    st.caption(
+        "Notas: valores em reais e correspondem às projeções comerciais fornecidas. Os meses sem informação aparecem com zero para garantir a visão anual."
+    )
+
+if __name__ == "__main__":
+    main()
 
EOF
)
