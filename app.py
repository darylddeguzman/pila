from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import json
import time
import os

app = Flask(__name__)

ADMIN_PASSWORD = "PASSWORD"
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key-12345")

queue_state = {
    "current_called": 0,
    "last_number": 0,
    "last_reset_date": "",
    "called_time": 0,
    "custom_message": "",
    "tickets": {}
}

def check_and_reset_queue():
    current_day = time.strftime("%Y-%m-%d", time.gmtime(time.time() + 28800))
    if not queue_state["last_reset_date"]:
        queue_state["last_reset_date"] = current_day
        return
    if current_day != queue_state["last_reset_date"]:
        queue_state["current_called"] = 0
        queue_state["last_number"] = 0
        queue_state["called_time"] = 0
        queue_state["custom_message"] = ""
        queue_state["tickets"] = {}
        queue_state["last_reset_date"] = current_day

@app.route('/admin')
def admin_page():
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    check_and_reset_queue()
    with open('admin.html', 'r', encoding='utf-8') as f:
        return render_template_string(f.read())

@app.route('/pila')
def customer_page():
    with open('customer.html', 'r', encoding='utf-8') as f:
        return render_template_string(f.read())

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_page'))
        with open('login.html', 'r', encoding='utf-8') as f:
            return render_template_string(f.read(), error="Maling Password!")
    with open('login.html', 'r', encoding='utf-8') as f:
        return render_template_string(f.read(), error=None)

@app.route('/get-data', methods=['GET'])
def get_data():
    check_and_reset_queue()
    return jsonify(queue_state)

@app.route('/get-ticket', methods=['POST'])
def get_ticket():
    check_and_reset_queue()
    req_data = request.get_json() or {}
    cust_name = req_data.get("name", "Anonymous").strip() or "Anonymous"
    queue_state["last_number"] += 1
    new_ticket = queue_state["last_number"]
    queue_state["tickets"][str(new_ticket)] = cust_name
    return jsonify({"your_ticket": new_ticket})

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/next-turn', methods=['POST'])
def next_turn():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    check_and_reset_queue()
    now = int(time.time())
    if queue_state["current_called"] > 0:
        elapsed = now - queue_state["called_time"]
        if elapsed < 120: return jsonify(queue_state)
    if queue_state["current_called"] < queue_state["last_number"]:
        queue_state["current_called"] += 1
        queue_state["called_time"] = now
        queue_state["custom_message"] = ""
    return jsonify(queue_state)

@app.route('/back-turn', methods=['POST'])
def back_turn():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    check_and_reset_queue()
    if queue_state["current_called"] > 0:
        queue_state["current_called"] -= 1
        queue_state["called_time"] = int(time.time())
        queue_state["custom_message"] = ""
    return jsonify(queue_state)

@app.route('/send-message', methods=['POST'])
def send_message():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    queue_state["custom_message"] = data.get("message", "")
    return jsonify(queue_state)

@app.route('/manual-reset', methods=['POST'])
def manual_reset():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    queue_state["current_called"] = 0
    queue_state["last_number"] = 0
    queue_state["called_time"] = 0
    queue_state["custom_message"] = ""
    queue_state["tickets"] = {}
    return jsonify(queue_state)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
