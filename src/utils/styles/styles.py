CSS = """
<style>
    section.main > div {max-width:75rem}
    .stProgress > div > div > div > div {
    background-color: red;
    }

    [data-testid="stToolbar"] {visibility: hidden !important;}
    footer {visibility: hidden !important;}

    button[data-baseweb="tab"] {
        font-size: 24px;
        margin: 0;
        width: 100%;
        }

    button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
        font-size: 24px;
        }


    .dataframe {
        border: 1px solid #ccc;
        border-collapse: collapse;
        width: 100%;
        }

        .dataframe th, .dataframe td {
        padding: 0.5em;
        }

        .dataframe th {
        background-color: #eee;
        font-weight: bold;
        }

        .dataframe td {
        text-align: left;
        }

</style>
"""
