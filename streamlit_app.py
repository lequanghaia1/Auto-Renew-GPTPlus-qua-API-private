import streamlit as st
import requests
import json
import uuid
import time
import html as html_lib
import threading
from datetime import datetime, timedelta
from urllib.parse import urlparse

try:
    import importlib
    _ws_mod = importlib.import_module("streamlit.web.server.websocket_headers")
    _ws_headers = getattr(_ws_mod, "_get_websocket_headers", None)
except Exception:
    _ws_headers = None

_global_rate_lock = threading.Lock()
_global_rate_store = {}

def get_client_ip():
    try:
        if _ws_headers is not None:
            headers = _ws_headers()
            if headers:
                forwarded = headers.get("X-Forwarded-For", "")
                if forwarded:
                    return forwarded.split(",")[0].strip()
                return headers.get("X-Real-Ip", "unknown")
    except Exception:
        pass
    return "unknown"

def check_global_rate_limit(action_key, max_requests=5, window_seconds=60):
    client_ip = get_client_ip()
    rate_key = f"{action_key}:{client_ip}"
    now = time.time()
    with _global_rate_lock:
        expired_keys = [k for k, v in _global_rate_store.items() if v and now - v[-1] > 300]
        for ek in expired_keys:
            _global_rate_store.pop(ek, None)
        if rate_key not in _global_rate_store:
            _global_rate_store[rate_key] = []
        _global_rate_store[rate_key] = [t_h for t_h in _global_rate_store[rate_key] if now - t_h < window_seconds]
        if len(_global_rate_store[rate_key]) >= max_requests:
            return False
        _global_rate_store[rate_key].append(now)
        return True

st.set_page_config(page_title="Nâng cấp ChatGPT Plus / Upgrade ChatGPT Plus", page_icon="⚡", layout="centered")

API_CHECK_KEY = st.secrets["API_CHECK_KEY"]
API_CHECKER = st.secrets["API_CHECKER"]
API_CHECK_USER = st.secrets["API_CHECK_USER"]
API_UPGRADE = st.secrets["API_UPGRADE"]
URL_GPT = st.secrets.get("URL_GPT", "https://chatgpt.com/")
URL_AUTH = st.secrets.get("URL_AUTH", "https://chatgpt.com/api/auth/session")
FIXED_CHECK_KEY = st.secrets["FIXED_CHECK_KEY"]

HEADERS_NEW = {
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Origin": f"{urlparse(API_CHECK_KEY).scheme}://{urlparse(API_CHECK_KEY).netloc}",
    "Referer": f"{urlparse(API_CHECK_KEY).scheme}://{urlparse(API_CHECK_KEY).netloc}/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

HEADERS_OLD = {
    "Content-Type": "text/plain;charset=UTF-8",
    "Accept": "*/*",
    "Origin": f"{urlparse(API_CHECK_USER).scheme}://{urlparse(API_CHECK_USER).netloc}",
    "Referer": f"{urlparse(API_CHECK_USER).scheme}://{urlparse(API_CHECK_USER).netloc}/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "x-product-id": "chatgpt",
    "x-device-id": "web"
}

if 'req_session' not in st.session_state: st.session_state.req_session = requests.Session()
if 's1_ok' not in st.session_state: st.session_state.s1_ok = False
if 's1_val' not in st.session_state: st.session_state.s1_val = ""
if 's1_pkg' not in st.session_state: st.session_state.s1_pkg = ""
if 's2_ok' not in st.session_state: st.session_state.s2_ok = False
if 's2_json' not in st.session_state: st.session_state.s2_json = ""
if 'lang' not in st.session_state: st.session_state.lang = "vi"

translations = {
    "vi": {
        "title": "Nâng cấp ChatGPT Plus",
        "refresh": "↻ Làm mới",
        "guide_title": "📝 Hướng dẫn sử dụng (Bấm để xem)",
        "guide_content": "**Bước 1: Nhập mã kích hoạt**\n* Nhập mã kích hoạt đã mua vào ô bên dưới và bấm Kiểm tra.\n\n**Bước 2: Lấy AuthSession**\n* Ấn nút Mở ChatGPT để đăng nhập, sau đó ấn Lấy AuthSession, copy toàn bộ nội dung (Ctrl A để bôi đen toàn bộ rồi Ctrl C để sao chép), quay lại ấn Ctrl V dán toàn bộ nội dung và ấn Check Auth.\n\n**Bước 3: Xác nhận nâng cấp**\n* Nếu tài khoản đủ điều kiện, nút Bắt Đầu Nâng Cấp sẽ hiện ra. Bạn ấn vào và đợi khoảng 15s là sẽ nâng cấp thành công. Nếu báo lỗi vui lòng tự kiểm tra lại.",
        "open_gpt": "↗ Mở ChatGPT",
        "get_auth": "↗ Lấy AuthSession",
        "step1": "Nhập mã kích hoạt",
        "placeholder_code": "Nhập mã kích hoạt của bạn...",
        "check_key": "Kiểm tra Key",
        "err_empty_code": "Vui lòng nhập mã",
        "err_used": "❌ Key đã sử dụng",
        "err_not_exist": "❌ Key không tồn tại",
        "err_network": "❌ Lỗi mạng: Không thể kết nối tới Server.",
        "valid_key": "✅ Key hợp lệ",
        "pkg": "💎 Gói",
        "step2": "Nhập AuthSession",
        "placeholder_json": "Dán toàn bộ nội dung AuthSession vào đây...",
        "check_auth": "Check Auth",
        "err_json": "❌ Lỗi định dạng JSON",
        "err_empty_data": "Vui lòng dán dữ liệu",
        "acc_email": "Email tài khoản",
        "status": "Trạng thái",
        "st_free": "Tài khoản Free. Sẵn sàng nâng cấp",
        "st_paid": "Tài khoản ĐÃ CÓ GÓI. Nâng sẽ bị lỗi!",
        "btn_upgrade": "BẮT ĐẦU NÂNG CẤP",
        "upgrading": "⚡ Đang thực hiện nâng cấp, vui lòng không đóng trình duyệt...",
        "success": "🎉 Đã nâng thành công. Vui lòng reload lại trang web ChatGPT.",
        "err_upgrade": "❌ Nâng cấp thất bại",
        "err_log": "Bấm vào đây để xem Log lỗi từ Server",
        "checker_title": "🔍 Kiểm tra trạng thái mã (Bấm để kiểm tra)",
        "checker_input": "Nhập mã kích hoạt (mỗi mã 1 dòng)",
        "checker_placeholder": "Dán danh sách mã vào đây, mỗi mã 1 dòng...",
        "checker_btn": "Kiểm tra",
        "checker_clear": "Xóa kết quả",
        "checker_valid": "✅ Chưa dùng",
        "checker_used": "❌ Đã dùng",
        "checker_invalid": "⚠️ Không tồn tại",
        "checker_no_input": "Vui lòng nhập ít nhất 1 mã.",
        "checker_error": "Lỗi kết nối tới server.",
        "checker_account": "Tài khoản",
        "checker_time": "Thời gian",
        "checker_total": "Tổng"
    },
    "en": {
        "title": "Upgrade ChatGPT Plus",
        "refresh": "↻ Refresh",
        "guide_title": "📝 User Guide (Click to view)",
        "guide_content": "**Step 1: Enter activation code**\n* Enter your purchased activation code in the box below and click Check.\n\n**Step 2: Get AuthSession**\n* Click Open ChatGPT to log in, then click Get AuthSession, copy all content (Ctrl A to select all, then Ctrl C to copy), return here, press Ctrl V to paste everything, and click Check Auth.\n\n**Step 3: Confirm upgrade**\n* If the account is eligible, the Start Upgrade button will appear. Click it and wait about 15s for the upgrade to succeed.",
        "open_gpt": "↗ Open ChatGPT",
        "get_auth": "↗ Get AuthSession",
        "step1": "Enter Activation Code",
        "placeholder_code": "Enter your activation code...",
        "check_key": "Check Key",
        "err_empty_code": "Please enter code",
        "err_used": "❌ Key already used",
        "err_not_exist": "❌ Key does not exist",
        "err_network": "❌ Network Error: Could not connect to Server.",
        "valid_key": "✅ Valid Key",
        "pkg": "💎 Package",
        "step2": "Enter AuthSession",
        "placeholder_json": "Paste the entire AuthSession content here...",
        "check_auth": "Check Auth",
        "err_json": "❌ JSON format error",
        "err_empty_data": "Please paste data",
        "acc_email": "Account Email",
        "status": "Status",
        "st_free": "Free account. Ready to upgrade",
        "st_paid": "Account ALREADY HAS A PLAN. Upgrade will fail!",
        "btn_upgrade": "START UPGRADE",
        "upgrading": "⚡ Upgrading, please do not close the browser...",
        "success": "🎉 Upgraded successfully. Please reload the ChatGPT website.",
        "err_upgrade": "❌ Upgrade failed",
        "err_log": "Click here to see Server Error Log",
        "checker_title": "🔍 Check Key Status (Click to check)",
        "checker_input": "Enter activation codes (one per line)",
        "checker_placeholder": "Paste your codes here, one per line...",
        "checker_btn": "Check",
        "checker_clear": "Clear Results",
        "checker_valid": "✅ Unused",
        "checker_used": "❌ Used",
        "checker_invalid": "⚠️ Not Found",
        "checker_no_input": "Please enter at least 1 code.",
        "checker_error": "Connection error to server.",
        "checker_account": "Account",
        "checker_time": "Time",
        "checker_total": "Total"
    }
}

t = translations[st.session_state.lang]

st.markdown("""
    <style>
    .step-container { display: flex; align-items: center; margin-bottom: 10px; margin-top: 25px; }
    .step-circle {
        background-color: #3B82F6; color: white; border-radius: 50%;
        width: 32px; height: 32px; display: flex;
        align-items: center; justify-content: center; font-weight: bold; margin-right: 12px;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
    }
    .guide-link {
        text-decoration: none; padding: 10px 20px; border-radius: 8px; font-weight: 600;
        display: inline-block; transition: all 0.3s;
    }
    .guide-link:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

lang_cycle = {"vi": "en", "en": "vi"}
lang_labels = {"vi": "VI", "en": "EN"}

c1, c2, c3 = st.columns([7.5, 1, 1.5])
with c1: 
    st.title(t["title"])
with c2: 
    if st.button(lang_labels[st.session_state.lang], use_container_width=True):
        st.session_state.lang = lang_cycle[st.session_state.lang]
        st.rerun()
with c3: 
    if st.button(t["refresh"], use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

with st.expander(t["guide_title"]):
    st.markdown(t["guide_content"], unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin: 15px 0;">
        <a href="{URL_GPT}" target="_blank" class="guide-link" style="background-color: #EFF6FF; color: #3B82F6; border: 1px solid #BFDBFE;">{t["open_gpt"]}</a>
        <a href="{URL_AUTH}" target="_blank" class="guide-link" style="background-color: #FDF2F8; color: #DB2777; border: 1px solid #FBCFE8;">{t["get_auth"]}</a>
    </div>
    """, unsafe_allow_html=True)

if "checker_results" not in st.session_state:
    st.session_state.checker_results = []

def offset_used_at(time_str):
    if time_str and time_str != "Unknown":
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            return (dt - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass
    return time_str

with st.expander(t["checker_title"]):
    checker_input = st.text_area(t["checker_input"], height=150, placeholder=t["checker_placeholder"], label_visibility="collapsed", key="checker_textarea")
    
    col_chk1, col_chk2 = st.columns(2)
    with col_chk1:
        checker_clicked = st.button(t["checker_btn"], use_container_width=True, type="primary", key="checker_btn")
    with col_chk2:
        checker_clear = st.button(t["checker_clear"], use_container_width=True, key="checker_clear")
    
    if checker_clear:
        st.session_state.checker_results = []
        st.rerun()
    
    if checker_clicked:
        if not check_global_rate_limit("checker", max_requests=5, window_seconds=60):
            st.error(t.get("lookup_rate_limit", "⚠️ Vui lòng thử lại sau 1 phút."))
        elif not checker_input.strip():
            st.warning(t["checker_no_input"])
        else:
            input_keys = [k.strip() for k in checker_input.split('\n') if k.strip()]
            if len(input_keys) > 50:
                st.warning(f"⚠️ Vui lòng chỉ kiểm tra tối đa 50 mã mỗi lần để tránh nghẽn máy chủ.")
            else:
                checker_url = API_CHECKER
                checker_headers = {
                    "Accept": "*/*",
                    "Content-Type": "application/json",
                    "Origin": f"{urlparse(API_CHECK_KEY).scheme}://{urlparse(API_CHECK_KEY).netloc}",
                    "Referer": f"{urlparse(API_CHECK_KEY).scheme}://{urlparse(API_CHECK_KEY).netloc}/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                try:
                    resp = requests.post(checker_url, json=input_keys, headers=checker_headers, timeout=20)
                    parsed = resp.json()
                    api_data = parsed.get("data", []) if isinstance(parsed, dict) else []
                    
                    used_map = {}
                    if isinstance(api_data, list):
                        for item in api_data:
                            code = str(item.get("cdk", "")).strip().upper()
                            used_map[code] = item
                    
                    res_list = []
                    for k in input_keys:
                        code_upper = k.upper()
                        if code_upper in used_map:
                            data = used_map[code_upper]
                            status = data.get("useStatus", "")
                            if status == "not_used":
                                res_list.append({"key": k, "status": "unused", "info": ""})
                            else:
                                account = data.get("account", "Unknown")
                                used_at = offset_used_at(data.get("usedAt", "Unknown"))
                                res_list.append({"key": k, "status": "used", "account": account, "time": used_at})
                        else:
                            res_list.append({"key": k, "status": "invalid", "info": ""})
                    
                    st.session_state.checker_results = res_list
                    st.rerun()
                except Exception:
                    st.error(t["checker_error"])
    
    results = st.session_state.checker_results
    if results:
        total = len(results)
        unused = len([r for r in results if r["status"] == "unused"])
        used = len([r for r in results if r["status"] == "used"])
        invalid = len([r for r in results if r["status"] == "invalid"])
        
        c_t, c_u, c_d, c_i = st.columns(4)
        c_t.metric(t["checker_total"], total)
        c_u.metric(t["checker_valid"], unused)
        c_d.metric(t["checker_used"], used)
        c_i.metric(t["checker_invalid"], invalid)
        
        st.markdown("---")
        
        for r in results:
            safe_key = html_lib.escape(str(r["key"]))
            if r["status"] == "unused":
                st.markdown(f"{safe_key} — {t['checker_valid']}")
            elif r["status"] == "used":
                safe_account = html_lib.escape(str(r.get("account","")))
                safe_time = html_lib.escape(str(r.get("time","")))
                st.markdown(f"{safe_key} — {t['checker_used']} — {t['checker_account']}: {safe_account} | {t['checker_time']}: {safe_time}")
            else:
                st.markdown(f"{safe_key} — {t['checker_invalid']}")

st.markdown("<br>", unsafe_allow_html=True) 

st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 25px;">
        <div style="background-color: #3b82f6; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-right: 12px; font-weight: bold; font-size: 16px;">1</div>
        <div style="font-weight: bold; font-size: 20px; color: var(--text-color);">{t["step1"]}</div>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([8, 2])

with col1:
    code_input = st.text_input("code", label_visibility="collapsed", placeholder=t["placeholder_code"], disabled=st.session_state.s1_ok)

with col2:
    if not st.session_state.s1_ok:
        if st.button(t["check_key"], use_container_width=True):
            if not code_input:
                st.warning(t["err_empty_code"])
            else:
                url_c = API_CHECK_KEY
                payload_c = {
                    "cdk": code_input,
                    "sign": str(uuid.uuid4()),
                    "timestamp": int(time.time() * 1000)
                }
                try:
                    res = st.session_state.req_session.post(url_c, json=payload_c, headers=HEADERS_NEW, timeout=10)
                    if res.status_code == 200:
                        data = res.json()
                        code_api = data.get("code")
                        msg = data.get("message", "")
                        
                        if code_api == 1:
                            st.session_state.s1_ok = True
                            st.session_state.s1_val = code_input
                            st.session_state.s1_pkg = "Plus 1M"
                            st.rerun() 
                        else:
                            if "已经被使用" in msg:
                                st.error(t["err_used"])
                            elif "不存在" in msg:
                                st.error(t["err_not_exist"])
                            elif "错误" in msg:
                                st.error(t["err_not_exist"])
                            else:
                                st.error(f"❌ {msg}")
                    else:
                        st.error(f"❌ {res.status_code}")
                except requests.exceptions.RequestException:
                    st.error(t["err_network"])
    else:
        st.markdown(f"""
            <div style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; border-radius: 8px; padding: 8px 12px; line-height: 1.4;">
                <span style="color: #10B981; font-weight: bold; font-size: 15px; display: block;">{t["valid_key"]}</span>
                <span style="color: #10B981; font-size: 14px; display: block;">{t["pkg"]}: {st.session_state.s1_pkg}</span>
            </div>
            """, unsafe_allow_html=True)

if st.session_state.s1_ok:
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; margin-top: 25px;">
        <div style="display: flex; align-items: center;">
            <div class="step-circle">2</div><div style="font-size: 1.15rem; font-weight: 700; color: var(--text-color);">{t["step2"]}</div>
        </div>
        <div>
            <a href="{URL_AUTH}" target="_blank" class="guide-link" style="background-color: #FDF2F8; color: #DB2777; border: 1px solid #FBCFE8; padding: 4px 12px; font-size: 13px;">{t["get_auth"]}</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col3, col4 = st.columns([8, 2])
    with col3:
        json_input = st.text_area("json", label_visibility="collapsed", height=120, placeholder=t["placeholder_json"])
    with col4:
        if st.button(t["check_auth"], use_container_width=True):
            if json_input:
                try:
                    auth_obj = json.loads(json_input)
                    raw_email = auth_obj.get("user", {}).get("email", "N/A")
                    email = html_lib.escape(str(raw_email))
                    auth_oneline = json_input.replace("\n", "").replace("\r", "").strip()
                    
                    url_check_user = API_CHECK_USER
                    fixed_check_key = FIXED_CHECK_KEY
                    
                    payload = {"cdk": fixed_check_key, "user": auth_oneline}
                    data_raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
                    
                    res = st.session_state.req_session.post(url_check_user, data=data_raw, headers=HEADERS_OLD, timeout=15)
                    data_api = res.json()
                    
                    if res.status_code == 200:
                        has_sub = data_api.get("has_sub", False)
                        st.session_state.check_result = {"email": email, "is_free": not has_sub}
                        st.session_state.s2_ok = not has_sub
                        st.session_state.s2_json = auth_oneline
                    else:
                        st.error(f"❌ Auth Error (HTTP {res.status_code})")
                except Exception:
                    st.error(t["err_json"])
            else:
                st.warning(t["err_empty_data"])

    if "check_result" in st.session_state:
        res = st.session_state.check_result
        color = "#10B981" if res["is_free"] else "#EF4444"
        status_txt = t["st_free"] if res["is_free"] else t["st_paid"]
        st.markdown(f"""
            <div style="background-color: var(--secondary-background-color, #f8f9fa); border: 1px solid rgba(128,128,128,0.2); border-radius: 12px; padding: 20px; margin-top: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border-left: 5px solid {color}; color: var(--text-color);">
                <span style="color: var(--text-color); opacity: 0.7; font-size: 0.85rem; text-transform: uppercase;">{t["acc_email"]}</span>
                <span style="color: var(--text-color); font-weight: 600; font-size: 1.05rem; display: block; margin-top: 2px;">{res['email']}</span>
                <div style="margin-top:10px;"></div>
                <span style="color: var(--text-color); opacity: 0.7; font-size: 0.85rem; text-transform: uppercase;">{t["status"]}</span>
                <span style="color:{color}; font-weight: 600; font-size: 1.05rem; display: block; margin-top: 2px;">{status_txt}</span>
            </div>
        """, unsafe_allow_html=True)

    if st.session_state.s2_ok:
        st.write("")
        if st.button(t["btn_upgrade"], type="primary", use_container_width=True):
            msg_area = st.empty() 
            msg_area.markdown(f'<div style="font-weight: 600; color: var(--text-color); background-color: var(--secondary-background-color, #F8FAFC); padding: 15px; border-radius: 8px; border-left: 5px solid #F59E0B; margin: 15px 0; border: 1px solid rgba(128,128,128,0.2); border-left-width: 5px;">{t["upgrading"]}</div>', unsafe_allow_html=True)
            
            url_r = API_UPGRADE
            payload_r = {
                "cdk": st.session_state.s1_val,
                "account": st.session_state.s2_json,
                "type": "gpt",
                "sign": str(uuid.uuid4()),
                "timestamp": int(time.time() * 1000)
            }
            
            try:
                res_charge = st.session_state.req_session.post(url_r, json=payload_r, headers=HEADERS_NEW, timeout=30)
                msg_area.empty() 
                
                if res_charge.status_code == 200:
                    data_charge = res_charge.json()
                    if data_charge.get("code") == 1:
                        st.success(t["success"])
                    else:
                        err_msg = html_lib.escape(str(data_charge.get("message", "Unknown error")))
                        st.error(f'{t["err_upgrade"]}')
                        with st.expander(t["err_log"]):
                            st.write(f"Error Code: {html_lib.escape(str(data_charge.get('code', 'Unknown')))}")
                            st.write(f"Message: {err_msg}")
                else:
                    st.error(f'{t["err_upgrade"]} ({res_charge.status_code})')
                    with st.expander(t["err_log"]):
                        st.write(f"HTTP Status: {res_charge.status_code}")
                        
            except requests.exceptions.RequestException:
                if 'msg_area' in locals(): msg_area.empty()
                st.error(t["err_network"])
