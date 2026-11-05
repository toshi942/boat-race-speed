
import streamlit as st
import requests
import json
import time
import pandas as pd
from datetime import date

st.set_page_config(page_title="ボートレース展示速報", layout="wide")

st.title("🚤 ボートレース展示・周回最速データ")
st.caption("展示・周回・周り足・直線の最速艇を確認できます")

venues = {
    1:"桐生", 2:"戸田", 3:"江戸川", 4:"平和島",
    5:"多摩川", 6:"浜名湖", 7:"蒲郡", 8:"常滑",
    9:"津", 10:"三国", 11:"びわこ", 12:"住之江",
    13:"尼崎", 14:"鳴門", 15:"丸亀", 16:"児島",
    17:"宮島", 18:"徳山", 19:"下関", 20:"若松",
    21:"芦屋", 22:"福岡", 23:"唐津", 24:"大村"
}

selected_date = st.date_input("開催日", value=date.today())
venue_name = st.selectbox("競艇場", list(venues.values()))

venue_no = next(k for k, v in venues.items() if v == venue_name)

if st.button("データ取得", type="primary"):
    results = []

    headers = {
        "Referer": "https://kyoteibiyori.com/",
        "User-Agent": "Mozilla/5.0"
    }

    url = "https://kyoteibiyori.com/request_chokuzen_info_v2.php"

    with st.spinner("データを取得しています..."):
        for race in range(1, 13):
            payload = {
                "place_no": str(venue_no),
                "race_no": str(race),
                "hiduke": selected_date.strftime("%Y%m%d")
            }

            try:
                response = requests.post(
                    url,
                    data={"data": json.dumps(payload)},
                    headers=headers,
                    timeout=20
                )

                if response.status_code == 429:
                    time.sleep(5)
                    response = requests.post(
                        url,
                        data={"data": json.dumps(payload)},
                        headers=headers,
                        timeout=20
                    )

                if response.status_code != 200:
                    continue

                data = response.json()

                if not data:
                    continue

                if isinstance(data, dict):
                    boats = data.get("data", data.get("result", []))
                else:
                    boats = data

                if not isinstance(boats, list):
                    continue

                row = {
                    "レース": f"{race}R",
                    "展示最速艇": "-", "展示最速タイム": "-",
                    "周回最速艇": "-", "周回最速タイム": "-",
                    "周り足最速艇": "-", "周り足最速タイム": "-",
                    "直線最速艇": "-", "直線最速タイム": "-"
                }

                metrics = [
                    ("tenji", "展示最速艇", "展示最速タイム"),
                    ("shukai", "周回最速艇", "周回最速タイム"),
                    ("mawariashi", "周り足最速艇", "周り足最速タイム"),
                    ("chokusen", "直線最速艇", "直線最速タイム")
                ]

                for key, lane_col, time_col in metrics:
                    values = []

                    for boat in boats:
                        try:
                            value = float(boat.get(key, 0))
                            if value > 0:
                                values.append((value, boat.get("course", "?")))
                        except:
                            pass

                    if values:
                        best = min(values, key=lambda x: x[0])
                        row[lane_col] = f"{best[1]}号艇"
                        row[time_col] = f"{best[0] / 100:.2f}"

                results.append(row)

            except Exception:
                pass

            time.sleep(1.5)

    if results:
        st.success(f"{venue_name}・{selected_date} のデータ取得完了")
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("データがありません。開催日・競艇場をご確認ください。")
