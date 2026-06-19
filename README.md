# HTTP Flood Simulation & Monitoring Platform

## 快速啟動

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 啟動伺服器
python app.py

# 3. 瀏覽器開啟
http://127.0.0.1:5000
```

## 操作說明

| 按鈕 | 功能 |
|------|------|
| ▶ Start Flood | 啟動 40 個執行緒，持續對 /demo 發送請求 |
| ■ Stop Flood  | 停止所有模擬執行緒 |
| ↺ Reset       | 清除所有統計數據 |

## Dashboard 指標說明

| 指標 | 說明 |
|------|------|
| Requests/sec (RPS) | 每秒收到的請求數，即時計算 |
| Active Connections | 目前追蹤到的活躍 IP 連線數 |
| Total Requests | 自啟動後累計請求總數 |
| Flood Threads | 目前模擬中的執行緒數 |
| CPU Usage | psutil 量測的 CPU 使用率（%) |
| RAM Usage | psutil 量測的記憶體使用率（%) |
| Network I/O | 累計送出 / 接收流量 (MB) |
| RPS Trend Chart | 過去 60 秒的 RPS 曲線圖 |

## 注意事項

- 僅限在 localhost / 實驗室內網環境使用
- 不得對外部主機進行模擬測試
- 模擬期間 CPU 會明顯上升，這是正常現象
