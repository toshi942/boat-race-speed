
import streamlit as st
import requests
import json
import time
import pandas as pd
from datetime import date

st.set_page_config(
    page_title="ボートレース展示速報",
    layout="wide"
)

# スマホ表示調整
st.markdown("""
<style>
.block-container {
    padding: 1rem 0.7rem !important;
    max-width: 100% !important;
}
h1 {
    font-size: 1.5rem !important;
}
[data-testid="stDataFrame"] {
    width: 100%;
}
div.stButton > button {
    width: 100%;
    height: 3rem;
    font-size: 1.1rem;
}
</style>
""", unsafe_allow_html=True)

st.title("🚤 展示・周回最速データ")
st.caption("展示・周回・周り足・直線の最速艇を確認")

venues = {
    1:"桐生", 2:"戸田", 3:"江戸川", 4:"平和島",
    5:"多摩川", 6:"浜名湖", 7:"蒲郡", 8:"常滑",
    9:"津", 10:"三国", 11:"びわこ", 12:"住之江",
    13:"尼崎", 14:"鳴門", 15:"丸亀", 16:"児島",
    17:"宮島", 18:"徳山", 19:"下関", 20:"若松",
    21:"芦屋", 22:"福岡", 23:"唐津", 24:"大村"
}

selected_date = st.date_input(
    "開催日",
    value=date.today()
)

venue_name = st.selectbox(
    "競艇場",
    list(venues.values())
)

venue_no = next(
    k for k, v in venues.items()
    if v == venue_name
)

if st.button("📥 データ取得", type="primary"):

    url = "https://kyoteibiyori.com/request_chokuzen_info_v2.php"

    headers = {
        "Referer": "https://kyoteibiyori.com/",
        "User-Agent": "Mozilla/5.0"
    }

    results = []

    with st.spinner("データ取得中です..."):

        for race_no in range(1, 13):

            payload = {
                "place_no": str(venue_no),
                "race_no": str(race_no),
                "hiduke": selected_date.strftime("%Y%m%d")
            }

            try:
                response = None

                for attempt in range(4):
                    response = requests.post(
                        url,
                        data={"data": json.dumps(payload)},
                        headers=headers,
                        timeout=20
                    )

                    if response.status_code == 429:
                        time.sleep(3 * (attempt + 1))
                        continue

                    response.raise_for_status()
                    break

                if response is None or response.status_code == 429:
                    continue

                data = response.json()

                if isinstance(data, dict):
                    boats = data.get("data", data.get("result", []))
                else:
                    boats = data

                if isinstance(boats, dict):
                    boats = boats.get("data", [])

                if not isinstance(boats, list):
                    continue

                row = {
                    "レース": f"{race_no}R"
                }

                metrics = {
                    "tenji": ("展示最速艇", "展示最速タイム"),
                    "shukai": ("周回最速艇", "周回最速タイム"),
                    "mawariashi": ("周り足最速艇", "周り足最速タイム"),
                    "chokusen": ("直線最速艇", "直線最速タイム")
                }

                for key, names in metrics.items():

                    values = []

                    for boat in boats:
                        if not isinstance(boat, dict):
                            continue

                        lane = boat.get("course")
                        value = boat.get(key)

                        try:
                            value = float(value) / 100
                            values.append((lane, value))
                        except (ValueError, TypeError):
                            continue

                    if values:
                        fastest = min(values, key=lambda x: x[1])
                        row[names[0]] = fastest[0]
                        row[names[1]] = f"{fastest[1]:.2f}"
                    else:
                        row[names[0]] = "-"
                        row[names[1]] = "-"

                if len(row) > 1:
                    results.append(row)

            except Exception:
                continue

            time.sleep(1.5)

    if results:
        df = pd.DataFrame(results)

        st.success(f"{venue_name} のデータ取得完了")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.warning("データが取得できませんでした。")
