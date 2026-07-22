import json
import time
import os
from datetime import datetime
import pytz
from flask import Flask, render_template_string, Response, request, jsonify, session, redirect, url_for

app = Flask(__name__)

ADMIN_PASSWORD = "SECRET"
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key-12345")

queue_state = {
    "current_called": 0,
    "last_reset_date": ""
}

def check_and_reset_queue():
    tz_ph = pytz.timezone('Asia/Manila')
    current_date_ph = datetime.now(tz_ph).date().isoformat()
    if not queue_state["last_reset_date"]:
        queue_state["last_reset_date"] = current_date_ph
        return
    if current_date_ph != queue_state["last_reset_date"]:
        queue_state["current_called"] = 0
        queue_state["last_reset_date"] = current_date_ph

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Counter Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; background: #1a1a24; color: #fff; }
        .box { border: 2px solid #3a3a4a; padding: 30px; display: inline-block; border-radius: 12px; background: #222230; width: 85%; max-width: 400px; }
        .btn-main { font-size: 22px; padding: 15px; background: #00ca72; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; margin-bottom: 15px; }
        .btn-back { font-size: 18px; padding: 12px; background: #f39c12; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; }
        .reset { background: #ff4a4a; margin-top: 30px; font-size: 14px; padding: 8px; border: none; border-radius: 5px; color: white; cursor: pointer; }
        .logout { display: block; margin-top: 15px; color: #bbb; text-decoration: none; font-size: 14px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>ADMIN PANEL</h1>
        <h2>Now Serving: <span id="current">{{ current_called }}</span></h2>
        <button class="btn-main" onclick="nextQueue()">NEXT CUSTOMER</button>
        <button class="btn-back" onclick="backQueue()">BACK</button>
        <br>
        <button class="reset" onclick="manualReset()">Manual Reset to 0</button>
        <a class="logout" href="/admin/logout">Logout</a>
    </div>
    <script>
        function nextQueue() { fetch('/next-turn', { method: 'POST' }).then(res => res.json()).then(data => { document.getElementById("current").innerText = data.current_called; }); }
        function backQueue() { fetch('/back-turn', { method: 'POST' }).then(res => res.json()).then(data => { document.getElementById("current").innerText = data.current_called; }); }
        function manualReset() { if(confirm("Ibalik sa 0 ang pila?")) { fetch('/manual-reset', { method: 'POST' }).then(res => res.json()).then(data => { document.getElementById("current").innerText = data.current_called; }); } }
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 100px; background: #1a1a24; color: #fff; }
        .box { border: 2px solid #3a3a4a; padding: 30px; display: inline-block; border-radius: 12px; background: #222230; width: 85%; max-width: 350px; }
        input[type="password"] { font-size: 18px; padding: 10px; width: 90%; border-radius: 5px; border: 1px solid #444; background: #111; color: white; margin-bottom: 15px; text-align: center; }
        button { font-size: 18px; padding: 10px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; width: 96%; font-weight: bold; }
        .error { color: #ff4a4a; font-size: 14px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>ADMIN LOGIN</h2>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        <form method="POST" action="/admin/login">
            <input type="password" name="password" placeholder="Password" required autofocus><br>
            <button type="submit">LOGIN</button>
        </form>
    </div>
</body>
</html>
"""

CUSTOMER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Status ng Pila</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; background: #11111a; color: #fff; }
        .box { border: 2px solid #2980b9; padding: 40px; display: inline-block; border-radius: 12px; background: #1c1c28; width: 85%; max-width: 400px; }
        .num { font-size: 90px; color: #3498db; font-weight: bold; margin: 20px 0; }
        input { font-size: 24px; padding: 10px; width: 120px; text-align: center; background: #2c2c3e; border: 2px solid #444; color: white; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>NOW SERVING</h1>
        <div class="num" id="current_display">0</div>
        <hr style="border:1px solid #333">
        <p>Ipasok ang iyong Ticket Number:</p>
        <input type="number" id="user_ticket" placeholder="0" min="1">
        <p style="font-size:12px; color:#888;">Mag-o-automatic beep at alert kapag turn mo na.</p>
    </div>
    <script>
        const eventSource = new EventSource("/stream-pila");
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            const currentCalled = data.current_called;
            document.getElementById("current_display").innerText = currentCalled;
            const userTicket = parseInt(document.getElementById("user_ticket").value);
            if (userTicket === currentCalled && currentCalled !== 0) {
                let context = new (window.AudioContext || window.webkitAudioContext)();
                let osc = context.createOscillator();
                osc.type = "sine"; osc.connect(context.destination); osc.start();
                setTimeout(() => osc.stop(), 600);
                alert("IKAW NA ANG SUSUNOD! Ticket #" + userTicket);
            }
        };
    </script>
</body>
</html>
"""

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_page'))
        return render_template_string(LOGIN_TEMPLATE, error="Maling Password!")
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_page():
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    check_and_reset_queue()
    return render_template_string(ADMIN_TEMPLATE, current_called=queue_state["current_called"])

@app.route('/pila')
def customer_page():
    return render_template_string(CUSTOMER_TEMPLATE)

@app.route('/next-turn', methods=['POST'])
def next_turn():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    check_and_reset_queue()
    queue_state["current_called"] += 1
    return jsonify(queue_state)

@app.route('/back-turn', methods=['POST'])
def back_turn():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    check_and_reset_queue()
    if queue_state["current_called"] > 0: queue_state["current_called"] -= 1
    return jsonify(queue_state)

@app.route('/manual-reset', methods=['POST'])
def manual_reset():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    queue_state["current_called"] = 0
    return jsonify(queue_state)

@app.route('/stream-pila')
def stream_pila():
    def event_stream():
        last_sent = -1
        while True:
            check_and_reset_queue()
            if queue_state["current_called"] != last_sent:
                yield f"data: {json.dumps(queue_state)}\n\n"
                last_sent = queue_state["current_called"]
            time.sleep(1)
    return Response(event_stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
