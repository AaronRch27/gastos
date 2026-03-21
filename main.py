import streamlit as st
import pandas as pd
from tablas import init_db, get_connection
from datetime import datetime
import plotly.express as px


hoy = datetime.today()

init_db()

st.write("Base de datos inicializada correctamente ✅")



# Configuración general
st.set_page_config(
    page_title="Gastos del Hogar",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Tablero de Gastos del Hogar")

conn = get_connection()

query = """
SELECT g.*, u.nombre as usuario
FROM gastos g
JOIN usuarios u
ON g.usuario_id = u.id
ORDER BY fecha DESC
"""

df1 = pd.read_sql_query(query, conn)
conn.close()

df1["monto"] = (
    df1["monto"]
    .astype(str)
    .str.replace(",", ".", regex=False)
    .astype(float)
)
df1["fecha"] = pd.to_datetime(df1["fecha"], errors="coerce")

tab1, tab2, tab3 = st.tabs(["Tabla de gastos", "➕ Nuevo / Editar gasto", "📊Gráficos"])
# ----- Layout dashboard -----

with tab1:
    filtro1 = st.selectbox(
        "Selecciona periodo",
        ["Mes actual", "Todos"]
    )

    if filtro1 == "Mes actual":
        df = df1[
            (df1["fecha"].dt.month == hoy.month) &
            (df1["fecha"].dt.year == hoy.year)
        ]
    else:
        df = df1.copy()
    col_tabla, col_info = st.columns([7, 3])

    # =============================
    # 📊 COLUMNA IZQUIERDA - TABLA
    # =============================
    with col_tabla:
        st.subheader("Movimientos")
        st.dataframe(df, use_container_width=True)
        

    # =============================
    # 📈 COLUMNA DERECHA - PANEL INFO
    # =============================
    with col_info:
        st.subheader("Resumen")

        total = df["monto"].sum()
        gastos_promedio = df["monto"].mean()
        total_movimientos = len(df)
        porcentaje = 0.30
        Aaron = 22000
        Mariana = 16000
        disp = (Aaron * porcentaje) + (Mariana * porcentaje)
        vv = disp - total

        st.metric("Dinero del mes", f"${disp:,.2f}")
        st.metric("Gasto del periodo", f"${total:,.2f}")
        st.metric("Promedio por gasto", f"${gastos_promedio:,.2f}")
        st.metric("Dinero disponible", f'${vv:,.2f}' if vv > 0 else "valores negativos")


with tab2:
    st.subheader("Agregar nuevo gasto")

    conn = get_connection()
    usuarios = pd.read_sql_query("SELECT id, nombre FROM usuarios", conn)
    conn.close()

    with st.form("form_gasto"):
        fecha = st.date_input("Fecha")
        concepto = st.text_input("Concepto")
        categoria = st.selectbox("Categoría", ["comida", "casa", "transporte", "convivencia", "medicamentos", "servicios"])
        comentario = st.text_area("Comentario")
        monto = st.number_input("Monto", min_value=0.0, format="%.2f")
        modo_pago = st.selectbox("Modo de pago", ["Efectivo", "Tarjeta", "Transferencia"])
        usuario_nombre = st.selectbox("Usuario", usuarios["nombre"])

        submitted = st.form_submit_button("Guardar")

        if submitted:
            if not concepto:
                st.error("El concepto es obligatorio")
            else:
                usuario_id = usuarios.loc[
                    usuarios["nombre"] == usuario_nombre, "id"
                ].values[0]

                try:
                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute("""
                    INSERT INTO gastos 
                    (fecha, concepto, categoria, comentario, monto, modo_pago, usuario_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        fecha.strftime("%Y-%m-%d"),  # 🔥 clave
                        concepto,
                        categoria,
                        comentario,
                        float(monto),
                        modo_pago,
                        int(usuario_id)
                    ))

                    conn.commit()
                    conn.close()

                    st.success("Gasto guardado correctamente ✅")
                    st.rerun()

                except Exception as e:
                    st.error(f"Error al guardar: {e}")


    st.subheader("Editar gasto")

    id_editar = st.number_input("ID a editar", min_value=1, step=1, key="edit_id")

    if st.button("Cargar gasto"):
        conn = get_connection()
        df_edit = pd.read_sql_query(
            f"SELECT * FROM gastos WHERE id = {id_editar}", conn
        )
        conn.close()

        if not df_edit.empty:
            st.session_state["edit_data"] = df_edit.iloc[0].to_dict()
        else:
            st.error("ID no encontrado")

    if "edit_data" in st.session_state:
        data = st.session_state["edit_data"]

        nuevo_concepto = st.text_input("Concepto", value=data["concepto"])
        nuevo_monto = st.number_input("Monto", value=float(data["monto"]))

        if st.button("Guardar cambios"):
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
            UPDATE gastos
            SET concepto = ?, monto = ?
            WHERE id = ?
            """, (nuevo_concepto, nuevo_monto, id_editar))

            conn.commit()
            conn.close()

            st.success("Gasto actualizado ✅")
            st.rerun()

    st.subheader("Eliminar gasto")

    id_eliminar = st.number_input("ID a eliminar", min_value=1, step=1)

    if st.button("Eliminar"):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM gastos WHERE id = ?", (id_eliminar,))
        conn.commit()
        conn.close()

        st.warning("Gasto eliminado ⚠️")
        st.rerun()


with tab3:
    st.subheader("📊 Análisis")

    filtro = st.selectbox(
        "Selecciona periodo",
        ["Mes actual", "Todos"], key="filtro_tab3"
    )

    if filtro == "Mes actual":
        df = df1[
            (df1["fecha"].dt.month == hoy.month) &
            (df1["fecha"].dt.year == hoy.year)
        ]
    else:
        df = df1.copy()
    df["dia_semana"] = df["fecha"].dt.day_name()
    orden_dias = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
    ]

    df["dia_semana"] = pd.Categorical(df["dia_semana"], categories=orden_dias, ordered=True)
    dias_map = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sábado",
    "Sunday": "Domingo"
    }

    df["dia_semana"] = df["fecha"].dt.day_name().map(dias_map)

    orden_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    df["dia_semana"] = pd.Categorical(df["dia_semana"], categories=orden_dias, ordered=True)
    
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        st.subheader("Distribución por categoría")

        data = df.groupby("categoria")["monto"].sum().reset_index()

        fig = px.pie(
            data,
            names="categoria",
            values="monto",
            title="Gastos por categoría"
        )

        st.plotly_chart(fig)

    with col2:
        st.subheader("Gasto por día de la semana")
        gasto_dias = df.groupby("dia_semana")["monto"].sum()
        st.bar_chart(gasto_dias)

    with col3:
        st.subheader("Gasto por día")
        diario = df.groupby("fecha")["monto"].sum().sort_index()
        st.line_chart(diario)

    with col4:
        st.subheader("📍 Gastos por fecha")

        fig = px.scatter(
            df,
            x="fecha",
            y="monto",
            color="categoria",
            hover_data={
                "concepto": True,
                "categoria": True,
                "monto": True,
                "fecha": True
            },
            title="Gastos en el tiempo"
        )

        st.plotly_chart(fig, use_container_width=True)