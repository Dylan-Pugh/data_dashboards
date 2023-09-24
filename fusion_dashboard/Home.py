import streamlit as st


st.set_page_config(layout='wide', page_title='Fusion Dashboard', page_icon=':toolbox:')

""" Home page for fusion dashboard web app.
Displays title, logo, intro text and sidebar."""


# Web App Title & Header
col1, col2 = st.columns([1, 6])

with col1:
    st.image(
        'assets/fusion-logo.png',
        use_column_width='auto',
    )

with col2:
    st.markdown(
        """
    #
    Welcome to Dylan's data dashboards.

    **Credit:** App built in `Python` + `Streamlit` by [Dylan Pugh](https://github.com/Dylan-Pugh).

    ---
    """,
    )

st.sidebar.success('Select tool above.')
