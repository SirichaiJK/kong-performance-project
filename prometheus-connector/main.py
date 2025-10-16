from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import os, requests

app = FastAPI(title="Kong Metrics API (Full)")

# ✅ URL ของ Prometheus ตาม docker-compose
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "10"))

# ✅ CORS สำหรับ localhost
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# ---------- UTIL ----------
def _http_get_json(path: str, params: Dict[str, Any] | None = None) -> Any:
    try:
        resp = requests.get(f"{PROMETHEUS_URL}{path}", params=params, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        j = resp.json()
        if isinstance(j, dict) and "data" in j:
            return j["data"]
        return j
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")

# ---------- ROOT ----------
@app.get("/")
def root():
    return {"message": "✅ Kong Prometheus API is running", "prometheus": PROMETHEUS_URL}

# ---------- METRICS ----------
@app.get("/kong/metrics")
def kong_metrics_list():
    """
    ✅ ดึงรายการ metric ทั้งหมดที่ขึ้นต้นด้วย kong_
    """
    data = _http_get_json("/api/v1/label/__name__/values")
    if not isinstance(data, list):
        raise HTTPException(status_code=502, detail="Invalid response from Prometheus")
    kong_metrics = sorted([m for m in data if m.startswith("kong_")])
    return {"total": len(kong_metrics), "metrics": kong_metrics}

# ---------- LATENCY ----------
@app.get("/kong/latency")
def kong_latency(
    service: Optional[str] = Query(None, description="(optional) Service name เช่น new-service-mockkkk"),
    route: Optional[str] = Query(None, description="(optional) Route name เช่น mock-api-route"),
    quantile: float = Query(0.95, description="Quantile เช่น 0.95 สำหรับ p95 latency"),
    window: str = Query("10m", description="ช่วงเวลาที่ดู เช่น 10m, 30m, 1h")
):
    """
    ✅ ดึง p95 latency จาก metric kong_request_latency_ms_bucket
    รองรับ filter ตาม service/route ได้
    """

    # ✅ สร้าง filter เฉพาะถ้ามีระบุ service/route
    label_filters = []
    if service:
        label_filters.append(f'service="{service}"')
    if route:
        label_filters.append(f'route="{route}"')

    label_str = "{" + ",".join(label_filters) + "}" if label_filters else ""

    # ✅ promQL ที่ถูกต้อง
    promql = f'''
    histogram_quantile(
      {quantile},
      sum(rate(kong_request_latency_ms_bucket{label_str}[{window}])) 
      by (le, route, service, workspace)
    )
    '''

    try:
        resp = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        result = data.get("data", {}).get("result", [])

        if not result:
            return {"message": "No latency data available", "query": promql}

        # ✅ ถ้ามีหลาย service/route → คืนเป็น list
        if len(result) > 1:
            values = []
            for r in result:
                labels = r.get("metric", {})
                val = float(r["value"][1])
                values.append({
                    "service": labels.get("service"),
                    "route": labels.get("route"),
                    "workspace": labels.get("workspace"),
                    "p": quantile,
                    "window": window,
                    "latency_ms": round(val, 2)
                })
            return {"query": promql, "results": values}

        # ✅ ถ้ามีค่าเดียว → คืนเป็น object เดียว
        val = float(result[0]["value"][1])
        labels = result[0].get("metric", {})
        return {
            "service": labels.get("service"),
            "route": labels.get("route"),
            "workspace": labels.get("workspace"),
            "p": quantile,
            "window": window,
            "latency_ms": round(val, 2),
            "query": promql
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=str(e))
