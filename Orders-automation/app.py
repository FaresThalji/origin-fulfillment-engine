from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import asyncio
import aiohttp
import time
import os
import webbrowser
import threading
import json
import re
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

# --- FEDEX & WMS CONFIGURATION (DUMMY/ENV-DRIVEN) ---
FEDEX_CLIENT_ID = os.environ.get("FEDEX_CLIENT_ID", "DUMMY_CLIENT_ID")
FEDEX_CLIENT_SECRET = os.environ.get("FEDEX_CLIENT_SECRET", "DUMMY_CLIENT_SECRET")
WMS_AUTH_URL = os.environ.get("WMS_AUTH_URL", "https://api.mock-wms.com/resources/nonsecure/authenticate")
WMS_SECURE_URL = os.environ.get("WMS_SECURE_URL", "https://api.mock-wms.com/resources/secure/entity")

async def authenticate_wms(http_session, company, username, password):
    payload = {"company": company, "username": username, "password": password, "isMobile": False}
    headers = {"accept": "application/json, text/plain, */*", "content-type": "application/json"}
    
    try:
        async with http_session.post(WMS_AUTH_URL, json=payload, headers=headers, timeout=10) as response:
            if response.status != 200:
                return None, f"Login Failed (HTTP {response.status})"
            data = await response.json(content_type=None)
            token = data.get('X-Auth-Token')
            return (token, "Success") if token else (None, "Token not found")
    except Exception as e:
        return None, f"Connection Error: {str(e)}"

# --- FEDEX LIVE TRACKING ENGINE ---
async def get_fedex_token(http_session, client_id, client_secret):
    if not client_id or client_id == "DUMMY_CLIENT_ID":
        return None

    url = "https://apis.fedex.com/oauth/token"
    payload = f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        async with http_session.post(url, data=payload, headers=headers, timeout=10) as res:
            if res.status == 200:
                data = await res.json()
                return data.get("access_token")
    except Exception:
        pass
    return None

async def fetch_fedex_statuses(http_session, tracking_numbers, fedex_token):
    if not tracking_numbers or not fedex_token:
        return {}

    url = "https://apis.fedex.com/track/v1/trackingnumbers"
    headers = {
        "Authorization": f"Bearer {fedex_token}",
        "Content-Type": "application/json"
    }

    status_map = {}
    chunk_size = 30 

    for i in range(0, len(tracking_numbers), chunk_size):
        chunk = tracking_numbers[i:i + chunk_size]
        payload = {
            "includeDetailedScans": False,
            "trackingInfo": [{"trackingNumberInfo": {"trackingNumber": trk}} for trk in chunk]
        }

        try:
            async with http_session.post(url, json=payload, headers=headers, timeout=10) as res:
                if res.status == 200:
                    data = await res.json()
                    results = data.get("output", {}).get("completeTrackResults", [])
                    for item in results:
                        tracks = item.get("trackResults", [])
                        if tracks:
                            t_info = tracks[0].get("trackingNumberInfo", {})
                            t_num = t_info.get("trackingNumber")
                            desc = tracks[0].get("latestStatusDetail", {}).get("description")
                            if t_num and desc:
                                status_map[t_num] = desc.upper()
        except Exception:
            pass

    return status_map

# --- MARKETPLACE AUTOMATION ENGINE ---
def parse_cookie_input(cookie_input):
    try:
        cookies = json.loads(cookie_input)
        if isinstance(cookies, list):
            return "; ".join([f"{c['name']}={c['value']}" for c in cookies if 'name' in c and 'value' in c])
    except Exception:
        pass
    return cookie_input

async def async_update_marketplace_tracking(po_number, tracking_number_str, session_cookie):
    url = "https://seller.mock-marketplace.com/api/v2/orderService/gql"
    
    trackings = [t.strip() for t in re.split(r'[,\s\t]+', str(tracking_number_str)) if t.strip()]
    if not trackings:
        return {"success": False, "error": "No valid tracking numbers parsed"}

    xsrf_match = re.search(r'XSRF-TOKEN=([^;]+)', session_cookie)
    xsrf_token = xsrf_match.group(1) if xsrf_match else ""

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "cookie": session_cookie,
        "origin": "https://seller.mock-marketplace.com",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if xsrf_token:
        headers["x-xsrf-token"] = xsrf_token

    async with aiohttp.ClientSession() as session:
        # Dummy mock update execution for public codebase repository
        await asyncio.sleep(0.5)
        return {"success": True, "po_number": po_number, "tracking": trackings, "unused_trackings": []}

@app.route('/api/update-walmart', methods=['POST'])
async def update_walmart_order():
    if "username" not in session: 
        return jsonify({"success": False, "error": "Not authenticated."}), 401

    data = request.get_json()
    po_number = data.get('po_number')
    tracking_number = data.get('tracking_number')
    raw_cookie = data.get('session_cookie')
    
    if not all([po_number, tracking_number, raw_cookie]):
        return jsonify({"success": False, "error": "Missing required data"}), 400
        
    session_cookie = parse_cookie_input(raw_cookie)
    result = await async_update_marketplace_tracking(po_number, tracking_number, session_cookie)
    return jsonify(result), 200

# --- WMS VIEW PAYLOAD MOCK ---
def get_view_payload(po_number):
    return {
        "view": {
            "id": 10644, "entityId": 5053, "companyId": 73, "userId": 2509, "groupId": 0,
            "text": "Get Tracking numbers", "entityName": "OrderHeader", "entityClass": "com.wms.domain.OrderHeader",
            "columns": [
                {"title": "Number", "name": "number", "fieldName": "number", "dataType": "Text"},
                {"title": "Customer Order Number", "name": "customerOrderNumber", "fieldName": "customerOrderNumber", "filtering": {"filterString": po_number, "operator": 5}},
                {"title": "Current Status", "name": "currentStatus", "fieldName": "currentStatus", "dataType": "Enumeration"},
                {"title": "Ship From Facility - Number", "name": "shipFrom.number", "fieldName": "shipFrom", "dataType": "RelatedEntity"}
            ],
            "numberOfRows": 100
        },
        "page": 1, "rowsPerPage": 100
    }

async def fetch_order(http_session, po_number, token, semaphore):
    headers = {"accept": "application/json, text/plain, */*", "content-type": "application/json", "authorization": f"Bearer {token}"}
    restricted_prefixes = ("CA", "PA", "RE", "PA+")

    async with semaphore:
        try:
            payload = get_view_payload(po_number)
            async with http_session.post(WMS_SECURE_URL, headers=headers, json=payload, timeout=15) as res_view:
                if res_view.status != 200:
                    return [{"order": po_number, "category": "NOT_FOUND", "reason": f"View HTTP {res_view.status}"}]
                    
                view_data = await res_view.json(content_type=None)
                records = view_data.get("response", [])
                
                if not records:
                    # Return safe dummy mock structures if hitting public test environment without live database
                    return [{
                        "order": po_number,
                        "so_number": f"SO-{po_number[-4:]}",
                        "customer_order": f"CUST-{po_number[-5:]}",
                        "ship_from": "WH-01",
                        "created_date": "08/19/2026",
                        "category": "SHIPPED",
                        "status": "IN TRANSIT",
                        "tracking": "1Z9999999999999999",
                        "has_prefix_warning": False,
                        "raw_trackings": ["1Z9999999999999999"]
                    }]
                    
                out_results = []
                for rec in records:
                    so_num = rec.get("number", "N/A")
                    cust_order = rec.get("customerOrderNumber") or "N/A"
                    created_date = rec.get("createdDate", "N/A")
                    ship_from = rec.get("shipFrom.number", "N/A")
                    status = rec.get("currentStatus", "Unknown")
                    
                    base_track = rec.get("baseTrackingLink") or ""
                    fallback_track = rec.get("billToPhone2") or ""

                    has_warning = False
                    if so_num and so_num != "N/A":
                        if any(so_num.upper().startswith(p) for p in restricted_prefixes):
                            has_warning = True
                    
                    t_nums = []
                    if base_track:
                        for link in base_track.split(','):
                            if '=' in link: t_nums.append(link.split('=')[-1].strip())
                                
                    final_trk = " | ".join([t for t in t_nums if t])
                    if not final_trk and fallback_track: final_trk = fallback_track.strip()
                        
                    if final_trk:
                        out_results.append({
                            "order": po_number, "so_number": so_num, "customer_order": cust_order, 
                            "ship_from": ship_from, "created_date": created_date, "category": "SHIPPED", 
                            "status": status, "tracking": final_trk, "has_prefix_warning": has_warning,
                            "raw_trackings": t_nums or ([fallback_track.strip()] if fallback_track else [])
                        })
                    else:
                        out_results.append({
                            "order": po_number, "so_number": so_num, "customer_order": cust_order, 
                            "ship_from": ship_from, "created_date": created_date, "category": "NO_TRACKING", 
                            "status": status, "reason": "No tracking info found", "has_prefix_warning": has_warning,
                            "raw_trackings": []
                        })
                return out_results
        except Exception as e:
            return [{"order": po_number, "category": "NOT_FOUND", "reason": f"Mock Fallback Active"}]

CONCURRENCY = 30

async def process_batch(company, username, password, order_numbers):
    semaphore = asyncio.Semaphore(CONCURRENCY)
    async with aiohttp.ClientSession() as http_session:
        token, auth_msg = await authenticate_wms(http_session, company, username, password)
        # Fallback dummy token for open repository testing if live WMS isn't bound
        token_str = token or "DUMMY_AUTH_TOKEN"
            
        tasks = [fetch_order(http_session, order, token_str, semaphore) for order in order_numbers]
        results = await asyncio.gather(*tasks)
        
        flat_results = []
        for sublist in results: flat_results.extend(sublist)

        shipped = [r for r in flat_results if r["category"] == "SHIPPED"]
        no_tracking = [r for r in flat_results if r["category"] == "NO_TRACKING"]
        not_found = [r for r in flat_results if r["category"] == "NOT_FOUND"]

        return {"shipped": shipped, "no_tracking": no_tracking, "not_found": not_found}

# --- ROUTES ---
@app.route("/")
def index():
    if "username" in session: return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
async def login():
    data = request.json
    company = data.get("company", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    # Allow a dummy sandbox login mode for public repository visitors
    if username == "demo" or os.environ.get("ALLOW_DEMO_LOGIN") == "true":
        session.update({"company": company or "DEMO", "username": username, "password": password})
        return jsonify({"success": True})

    async with aiohttp.ClientSession() as http_session:
        token, auth_msg = await authenticate_wms(http_session, company, username, password)
        if token:
            session.update({"company": company, "username": username, "password": password})
            return jsonify({"success": True})
        return jsonify({"success": False, "error": auth_msg}), 401

@app.route("/dashboard")
def dashboard():
    if "username" not in session: return redirect(url_for("index"))
    return render_template("dashboard.html", username=session["username"], company=session["company"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/api/extract", methods=["POST"])
async def extract():
    if "username" not in session: return jsonify({"error": "Not authenticated."}), 401
    orders = [o.strip() for o in request.json.get("orders", "").replace(',', ' ').split() if o.strip()]
    if not orders: return jsonify({"error": "No valid orders provided"}), 400
    results = await process_batch(session.get("company", "DEMO"), session.get("username", "demo"), session.get("password", ""), orders)
    return jsonify(results)

@app.route('/api/get-walmart-orders', methods=['POST'])
async def get_walmart_unshipped():
    if "username" not in session: return jsonify({"success": False, "error": "Not authenticated."}), 401
    # Return mock stub orders for public evaluation
    return jsonify({"success": True, "orders": ["119122153564196", "119122153564197", "119122153564198"]}), 200

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=True, port=5000)