# Taipei Safe Route

用 Google Routes API 取得台北車站到西門町的步行候選路線，再用臺北市政府公開 CCTV 位置估算每條路線的轉角覆蓋比例，推薦覆蓋較完整的路線。覆蓋率只以 polyline 明顯轉彎處作為 checkpoint，並以轉角周邊 100m 作為估計範圍，不再以整條道路每隔數公尺計算。

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

在 `.env` 設定 `GOOGLE_MAPS_API_KEY`，再啟動：

```bash
streamlit run app.py
```

核心演算法可離線測試：

```bash
pytest
```

覆蓋結果是依公開設備位置與距離的估算，不代表實際攝影機視角、設備狀態或即時安全狀況。
