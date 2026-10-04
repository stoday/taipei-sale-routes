# PRD — Taipei Safe Route

## 1. 專案名稱

**Taipei Safe Route**

中文暫名：

**臺北安心監視覆蓋路線**

---

# 2. 專案目標

在兩小時 Hackathon 開發時間內，完成一個可操作 Demo。

使用者查看：

> 台北車站 → 西門町

的步行路線。

系統透過 Google Routes API 取得候選步行路線，並結合臺北市政府公開 CCTV 資料，判斷每條路線沿途是否持續位於公開攝影機的「估計監視覆蓋範圍」。

最終推薦：

> **估計監視覆蓋最完整的步行路線**

---

# 3. 核心展示概念

一般 Google Maps 主要考量：

- 距離
- 行程時間
- 道路條件

本專案示範：

> 可以在 Google 路線上加入外部城市公開資料，建立新的客製路線評分方式。

本次加入：

> 公開 CCTV 估計監視覆蓋

---

# 4. MVP 範圍

只支援：

```text
台北車站
→
西門町
```

第一版不提供任意台北市路線搜尋。

原因：

- 縮小 CCTV 資料範圍
- 避免大量 geocoding
- 提高兩小時完成機率
- 專注驗證核心概念

---

# 5. 技術架構

使用：

```text
Python 3.11
Streamlit
Folium
streamlit-folium
requests
pandas
numpy
python-dotenv
polyline
```

不使用：

```text
React
Vue
Next.js
FastAPI
Database
GeoPandas
PostGIS
```

專案維持單一 Python application。

架構：

```text
Streamlit UI
     │
     ▼
Google Routes API
     │
     ▼
候選步行路線
     │
     ├─────────────┐
     ▼             ▼
Route sampling   CCTV CSV
     │             │
     └──────┬──────┘
            ▼
     Coverage Engine
            │
            ▼
      Route Ranking
            │
            ▼
      Folium Map
```

---

# 6. Google API

## 必要 API

MVP 只需要：

```text
Google Routes API
```

Google Routes API 已完成實際測試。

目前測試：

```text
台北車站附近
25.0478, 121.5170

→

西門站附近
25.0422, 121.5081
```

可以成功取得：

```text
distanceMeters
duration
polyline.encodedPolyline
```

---

# 7. Environment

建立：

```text
.env
```

內容：

```env
GOOGLE_MAPS_API_KEY=YOUR_API_KEY
```

程式使用：

```python
from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv(
    "GOOGLE_MAPS_API_KEY"
)
```

建立：

```text
.gitignore
```

包含：

```text
.env
```

不得將 API key commit 到 Git。

---

# 8. CCTV 資料

使用臺北市政府公開 CCTV 資料。

優先資料來源：

> 臺北市政府警察局錄影監視系統設置區位

原始資料具有：

```text
編號
所屬單位
安裝地址
攝影方向
```

本 MVP 不處理全臺北市。

只整理：

> 台北車站至西門町周邊

的 CCTV。

---

# 9. MVP CCTV Dataset

事先建立：

```text
data/臺北市CCTV設備.csv
```

格式：

```csv
id,lat,lng,direction
CAM001,25.0468,121.5152,E
CAM002,25.0459,121.5138,SW
CAM003,25.0448,121.5115,W
```

direction 使用：

```text
N
NE
E
SE
S
SW
W
NW
UNKNOWN
```

如果官方方向資料不能可靠解析：

```text
UNKNOWN
```

---

# 10. CCTV Data Preparation

Hackathon 時不要做完整 geocoding pipeline。

可在開始前準備：

```text
data/臺北市CCTV設備.csv
```

若 CCTV 原始資料只有地址，可用：

```text
Google Geocoding
或
人工預處理
```

取得 lat / lng。

Hackathon 主程式只讀取已準備好的座標資料。

---

# 11. 起點終點

第一版固定：

```python
TAIPEI_MAIN_STATION = {
    "lat": 25.0478,
    "lng": 121.5170
}

XIMEN = {
    "lat": 25.0422,
    "lng": 121.5081
}
```

UI 可以顯示：

```text
台北車站
→
西門町
```

但不需要 Places Autocomplete。

---

# 12. Routes API

呼叫：

```text
POST
https://routes.googleapis.com/directions/v2:computeRoutes
```

request：

```json
{
  "origin": {
    "location": {
      "latLng": {
        "latitude": 25.0478,
        "longitude": 121.5170
      }
    }
  },
  "destination": {
    "location": {
      "latLng": {
        "latitude": 25.0422,
        "longitude": 121.5081
      }
    }
  },
  "travelMode": "WALK",
  "computeAlternativeRoutes": true
}
```

Field mask：

```text
routes.duration
routes.distanceMeters
routes.polyline.encodedPolyline
```

---

# 13. Route Model

建立：

```python
@dataclass
class RouteCandidate:
    route_id: str

    distance_m: float
    duration_sec: float

    encoded_polyline: str
    points: list[tuple[float, float]]

    coverage_ratio: float = 0.0

    longest_uncovered_gap_m: float = 0.0

    covered: bool = False
```

---

# 14. Polyline Decode

使用：

```text
polyline
```

Python package。

例如：

```python
import polyline

points = polyline.decode(
    encoded_polyline
)
```

取得：

```text
[
    (lat, lng),
    (lat, lng),
    ...
]
```

---

# 15. Route Sampling

Google polyline points 密度不固定。

因此沿路線每：

```text
10 m
```

建立 sample point。

函式：

```python
sample_route(
    points,
    interval_m=10
)
```

輸出：

```text
sample_0
sample_1
sample_2
...
```

若實作時間不足：

可以直接使用 decoded polyline points。

但優先完成 10m sampling。

---

# 16. Coverage Definition

本專案不是判斷：

> 附近有多少攝影機

而是判斷：

> 每一小段路線是否至少有一支 CCTV 可能覆蓋。

對 route sample point：

```text
P
```

搜尋所有 CCTV：

```text
C1
C2
C3
...
```

只要至少有一支符合：

```text
Covered(camera, P) == True
```

此 sample 即：

```text
covered = True
```

---

# 17. MVP Coverage Rule

第一版：

```text
camera 與 sample point 距離 <= 50m
```

即可視為：

```text
distance_covered = True
```

---

# 18. Camera Direction

如果 camera direction 可用：

進一步檢查：

```text
camera 朝向
vs
camera → sample point 的 bearing
```

direction mapping：

```text
N  = 0°
NE = 45°
E  = 90°
SE = 135°
S  = 180°
SW = 225°
W  = 270°
NW = 315°
```

假設：

```text
CAMERA_FOV_HALF_ANGLE = 45°
```

則：

```text
angle_difference <= 45°
```

視為：

```text
direction_match = True
```

完整：

```text
Covered =
distance <= 50m
AND
direction_match
```

---

# 19. UNKNOWN Direction

如果：

```text
direction == UNKNOWN
```

MVP 採寬鬆模式：

```text
Covered =
distance <= 50m
```

避免因資料品質導致 Demo 完全失敗。

UI 必須說明：

> 部分設備因公開方向資訊不足，僅依距離估算。

---

# 20. Distance

使用 Haversine distance。

建立：

```python
haversine_m(
    lat1,
    lng1,
    lat2,
    lng2
)
```

不要導入 GeoPandas。

---

# 21. Bearing

建立：

```python
bearing_degree(
    camera_lat,
    camera_lng,
    target_lat,
    target_lng
)
```

結果：

```text
0 ~ 360°
```

建立：

```python
angle_difference(
    a,
    b
)
```

結果：

```text
0 ~ 180°
```

---

# 22. Coverage Ratio

假設 route 有：

```text
100 samples
```

其中：

```text
96 samples covered
```

則：

```text
coverage_ratio = 0.96
```

UI：

```text
96%
```

---

# 23. Longest Uncovered Gap

連續 uncovered samples：

例如：

```text
✓ ✓ ✓ ✗ ✗ ✗ ✓ ✓
```

若 interval：

```text
10m
```

則：

```text
longest_uncovered_gap = 30m
```

建立：

```python
calculate_longest_gap(
    coverage_flags,
    sample_interval_m
)
```

---

# 24. Full Coverage Rule

理想：

```text
coverage_ratio == 1.0
```

但考量公開資料與 geocoding 誤差，Demo 推薦條件設定：

```text
coverage_ratio >= 0.95
AND
longest_uncovered_gap_m <= 20
```

符合：

```text
covered = True
```

UI 名稱：

> 全程估計監視覆蓋

不要寫：

> 100% 一定會被拍到

---

# 25. Route Ranking

優先排序：

## Priority 1

```text
covered == True
```

---

## Priority 2

```text
coverage_ratio 越高越好
```

---

## Priority 3

```text
longest_uncovered_gap 越短越好
```

---

## Priority 4

```text
duration 越短越好
```

---

# 26. Recommendation

若存在 covered route：

顯示：

```text
🛡 推薦：全程估計監視覆蓋路線
```

例如：

```text
步行時間：24 分鐘
距離：1.5 km
估計覆蓋：98%
最大未覆蓋區段：10 m
```

同時比較最快路線：

```text
比最快路線多 3 分鐘
```

---

# 27. No Full Coverage Case

若沒有任何路線達標：

不要假裝有安全路線。

顯示：

```text
目前沒有找到符合
「全程估計監視覆蓋」
條件的候選路線。
```

並顯示：

```text
最佳候選

估計覆蓋：91%
最大未覆蓋區段：70m
```

---

# 28. Streamlit UI

畫面：

```text
Taipei Safe Route

台北車站
    ↓
西門町

[ 分析路線 ]
```

執行後：

```text
推薦路線

🛡 全程估計監視覆蓋

24 min
1.5 km

Coverage
█████████▊ 98%

最大未覆蓋
10m
```

再顯示：

```text
最快路線

21 min
1.38 km

Coverage
████████░░ 82%

最大未覆蓋
90m
```

---

# 29. Map

使用：

```text
Folium
streamlit-folium
```

底圖：

```text
OpenStreetMap
```

Google Routes API 只負責算路。

不使用 Maps JavaScript API。

---

# 30. Map Content

地圖顯示：

```text
● 台北車站
● 西門町

━━ 推薦 route

· CCTV
```

如果時間允許：

```text
綠色 circle
```

表示 camera 的 50m estimated radius。

但不必要。

---

# 31. Coverage Visualization

Bonus：

將 route segment 分成：

```text
covered
uncovered
```

例如：

```text
━━━━━━ covered

------ uncovered
```

如果時間不足：

只畫整條 route。

---

# 32. CCTV Marker

只顯示：

```text
距離 route 100m
```

內的 CCTV。

不要把所有 CCTV marker 畫到地圖。

---

# 33. Disclaimer

頁面底部一定顯示：

> 本服務依臺北市政府公開監視設備位置與方向資料進行估算。估計覆蓋範圍不代表攝影機實際視角、設備運作狀態、影像品質或即時安全狀況，本結果僅供路線比較與技術展示使用。

---

# 34. Project Structure

保持極簡：

```text
taipei-safe-route/

├── app.py
│
├── routes.py
├── coverage.py
├── geo.py
│
├── data/
│   └── 臺北市CCTV設備.csv
│
├── tests/
│   ├── test_geo.py
│   └── test_coverage.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

# 35. app.py

負責：

```text
Streamlit UI

↓

get_routes()

↓

analyze_route()

↓

rank_routes()

↓

Folium map

↓

display result
```

---

# 36. routes.py

提供：

```python
get_routes()
```

輸入：

```text
origin
destination
```

輸出：

```text
list[RouteCandidate]
```

---

# 37. geo.py

提供：

```python
haversine_m()

bearing_degree()

angle_difference()

sample_route()
```

---

# 38. coverage.py

提供：

```python
is_camera_covering_point()

analyze_route_coverage()

calculate_longest_gap()

rank_routes()
```

---

# 39. Configuration

不要建立 YAML。

直接集中在：

```python
# config section

CAMERA_RADIUS_M = 50

CAMERA_FOV_HALF_ANGLE = 45

ROUTE_SAMPLE_INTERVAL_M = 10

MIN_COVERAGE_RATIO = 0.95

MAX_UNCOVERED_GAP_M = 20
```

放：

```text
coverage.py
```

或：

```text
config.py
```

即可。

---

# 40. Tests

因只有兩小時，不要求完整 TDD。

至少完成：

```text
test_haversine
test_bearing

test_camera_within_radius

test_camera_outside_radius

test_camera_direction_match

test_camera_direction_not_match

test_longest_uncovered_gap
```

---

# 41. Synthetic Test

在串 Google API 前，先建立簡單測試：

```text
Camera A
Camera B

Route 1
Route 2
```

確認：

```text
Route 1 coverage = 100%

Route 2 coverage < 100%
```

---

# 42. Error Handling

如果：

```text
Google Routes API error
```

顯示：

```text
無法取得路線，請確認 API key 與網路連線。
```

如果：

```text
cameras.csv 不存在
```

顯示：

```text
找不到 CCTV 資料。
```

如果：

```text
Google 沒有 alternative routes
```

仍正常分析 default route。

---

# 43. README

README 至少包含：

## Setup

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

若使用 uv：

```bash
uv sync
```

---

## Environment

```bash
cp .env.example .env
```

設定：

```text
GOOGLE_MAPS_API_KEY
```

---

## Run

```bash
streamlit run app.py
```

---

# 44. requirements.txt

至少：

```text
streamlit
streamlit-folium
folium
requests
pandas
numpy
python-dotenv
polyline
pytest
```

---

# 45. Development Priority

Codex 必須嚴格按照以下順序實作。

## P0 — 必須完成

```text
1. 建立 project structure

2. 建立 .env loader

3. 實作 Google Routes API

4. decode polyline

5. 載入 cameras.csv

6. 實作 Haversine

7. 實作 route sampling

8. 判斷 CCTV distance coverage

9. 計算 coverage ratio

10. 計算 longest uncovered gap

11. route ranking

12. Streamlit 顯示結果
```

---

## P1 — 有時間完成

```text
13. Camera direction

14. bearing

15. directional coverage

16. Folium map

17. CCTV markers
```

---

## P2 — Bonus

```text
18. covered / uncovered segment 不同樣式

19. camera coverage circle

20. alternative route comparison UI
```

---

# 46. IMPORTANT — Timebox

總開發時間：

```text
2 hours
```

因此 Codex 必須：

```text
優先完成可跑 Demo
```

不得：

```text
過度重構
過度 abstraction
建立複雜 architecture
新增 database
建立完整 GIS pipeline
建立 React frontend
加入不必要 framework
```

---

# 47. 建議時間分配

## 0–20 min

```text
Project setup

Google Routes API

確認 route 可以取得
```

---

## 20–50 min

```text
CCTV CSV

Haversine

Route sampling

Coverage calculation
```

---

## 50–80 min

```text
Route ranking

Streamlit UI

基本結果顯示
```

---

## 80–105 min

```text
Folium map

Route visualization

CCTV marker
```

---

## 105–120 min

```text
Camera direction

或

UI polish

或

Bug fixing
```

優先：

```text
Bug fixing > Camera direction
```

---

# 48. Demo Flow

Demo 時：

### Step 1

打開：

```text
Taipei Safe Route
```

---

### Step 2

畫面顯示：

```text
台北車站
→
西門町
```

---

### Step 3

點：

```text
分析路線
```

---

### Step 4

Google Routes API 取得候選 route。

---

### Step 5

系統顯示：

```text
最快路線

21 分鐘
1.38 km

估計監視覆蓋：
82%

最大未覆蓋：
90m
```

---

### Step 6

顯示：

```text
🛡 推薦路線

24 分鐘
1.50 km

估計監視覆蓋：
98%

最大未覆蓋：
10m
```

---

### Step 7

說明：

> Google Maps 幫我們找出一般步行路線，我們再加入城市公開 CCTV 資料，重新分析每一小段道路的監視設備覆蓋狀況，因此可以找到不是單純最快，而是監視覆蓋較完整的路線。

---

# 49. Demo Narrative

簡短版：

> 一般導航只告訴你怎麼走比較快，但有些使用者晚上走路更在意沿途是否有人、是否有公共安全設施。

> 我們利用 Google Routes API 加上臺北市政府公開 CCTV 資料，把每條步行路線切成小段，分析是否持續有公開監視設備可能覆蓋。

> 因此同樣從台北車站走到西門町，我們可以比較最快路線和監視覆蓋較完整的路線。

---

# 50. Product Boundary

本系統不得宣稱：

```text
此路線一定安全
```

不得宣稱：

```text
一定會被攝影機拍到
```

正確說法：

```text
公開監視設備估計覆蓋

全程估計監視覆蓋

公開 CCTV 覆蓋分析
```

---

# 51. Definition of Done

MVP 完成的最低條件：

- Streamlit 可以啟動
- Google Routes API 可以成功取得台北車站 → 西門町路線
- CCTV CSV 可以成功讀取
- Route 可以 decode
- Route 可以 sampling
- 每個 sample 可以判斷 CCTV 是否鄰近
- 可以得到 coverage ratio
- 可以得到 longest uncovered gap
- 可以比較候選 routes
- 可以推薦 coverage 較完整 route
- 畫面可直接用於 Hackathon 展示

如果以上全部成立：

> MVP Done

---

# 52. Codex Final Instruction

請先閱讀整份 PRD，再開始實作。

本專案是兩小時 Hackathon MVP。

優先原則：

```text
Working Demo
>
Correct Core Algorithm
>
Readable Code
>
UI Polish
>
Architecture Elegance
```

不要自行擴大 Scope。

若某功能會明顯拖延：

```text
Camera direction
FOV
Complex GIS
```

可以先略過，使用：

```text
50m distance-based estimated coverage
```

確保主流程可正常展示。

每完成核心功能後即執行：

```bash
pytest
```

最終必須確保：

```bash
streamlit run app.py
```

可以直接啟動 Demo。