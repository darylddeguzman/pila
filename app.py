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

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Counter Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 20px; background: #1a1a24; color: #fff; }
        .box { border: 2px solid #3a3a4a; padding: 25px; display: inline-block; border-radius: 12px; background: #222230; width: 85%; max-width: 420px; text-align: left; }
        h1, h2, .timer, .info { text-align: center; }
        .btn-main { font-size: 22px; padding: 15px; background: #00ca72; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; margin-bottom: 15px; }
        .btn-back { font-size: 18px; padding: 12px; background: #f39c12; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; margin-bottom: 15px; }
        .btn-msg { font-size: 16px; padding: 10px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; margin-bottom: 15px; }
        .reset-container { text-align: center; }
        .reset { background: #ff4a4a; margin-top: 15px; font-size: 14px; padding: 8px; border: none; border-radius: 5px; color: white; cursor: pointer; }
        .logout { display: block; margin-top: 15px; color: #bbb; text-decoration: none; font-size: 14px; text-align: center; }
        .info { font-size: 16px; color: #aaa; margin-bottom: 15px; }
        .timer { font-size: 18px; color: #e74c3c; font-weight: bold; margin-bottom: 15px; }
        .serving-name { font-size: 20px; color: #00ca72; font-weight: bold; text-align: center; margin-bottom: 15px; }
        .queue-list { background: #11111a; padding: 15px; border-radius: 8px; max-height: 150px; overflow-y: auto; font-size: 14px; border: 1px solid #3a3a4a; }
        .queue-item { padding: 5px 0; border-bottom: 1px solid #222; display: flex; justify-content: space-between; }
    </style>
</head>
<body>
    <div class="box">
        <h1>ADMIN PANEL</h1>
        <div class="info">Total Tickets: <span id="total_tickets">0</span></div>
        <h2>Now Serving: <span id="current">0</span></h2>
        <div class="serving-name" id="serving_name_display">Name: ---</div>
        <div class="timer" id="timer_display">Time Remaining: 02:00</div>
        <button class="btn-main" id="next_btn" onclick="nextQueue()">NEXT CUSTOMER</button>
        <button class="btn-back" onclick="backQueue()">BACK</button>
        <button class="btn-msg" onclick="sendMsg()">SEND FOLLOW-UP MESSAGE</button>
        <h3>Upcoming Queue:</h3>
        <div class="queue-list" id="queue_list_container"></div>
        <div class="reset-container">
            <button class="reset" onclick="manualReset()">Manual Reset to 0</button>
            <a class="logout" href="/admin/logout">Logout</a>
        </div>
    </div>
    <script>
        function updateAdminDisplay() {
            fetch('/get-data').then(res => res.json()).then(data => {
                document.getElementById("current").innerText = data.current_called;
                document.getElementById("total_tickets").innerText = data.last_number;
                let currentNum = data.current_called;
                if (currentNum > 0 && data.tickets[String(currentNum)]) {
                    document.getElementById("serving_name_display").innerText = "Name: " + data.tickets[String(currentNum)];
                } else {
                    document.getElementById("serving_name_display").innerText = "Name: ---";
                }
                let listHtml = "";
                let startNum = currentNum + 1;
                if (currentNum === 0) startNum = 1;
                for (let i = startNum; i <= data.last_number; i++) {
                    let name = data.tickets[String(i)] || "Anonymous";
                    listHtml += '<div class="queue-item"><span>Ticket #' + i + '</span><span>' + name + '</span></div>';
                }
                document.getElementById("queue_list_container").innerHTML = listHtml || "<div style='color:#666;'>No one in queue.</div>";
                if (currentNum === 0) {
                    document.getElementById("timer_display").innerText = "Time Remaining: 02:00";
                    document.getElementById("next_btn").disabled = false;
                    return;
                }
                let now = Math.floor(Date.now() / 1000);
                let elapsed = now - data.called_time;
                let remaining = 120 - elapsed;
                if (remaining > 0) {
                    let mins = Math.floor(remaining / 60);
                    let secs = remaining % 60;
                    document.getElementById("timer_display").innerText = "Time Remaining: " + (mins < 10 ? "0" : "") + mins + ":" + (secs < 10 ? "0" : "") + secs;
                    document.getElementById("next_btn").disabled = true;
                    document.getElementById("next_btn").style.background = "#555";
                } else {
                    document.getElementById("timer_display").innerText = "Time Expired! You can click NEXT.";
                    document.getElementById("next_btn").disabled = false;
                    document.getElementById("next_btn").style.background = "#00ca72";
                }
            });
        }
        function nextQueue() { fetch('/next-turn', { method: 'POST' }).then(res => res.json()).then(data => { updateAdminDisplay(); }); }
        function backQueue() { fetch('/back-turn', { method: 'POST' }).then(res => res.json()).then(data => { updateAdminDisplay(); }); }
        function sendMsg() { 
            let msg = prompt("Ipasok ang follow-up message:");
            if (msg) {
                fetch('/send-message', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
            }
        }
        function manualReset() { if(confirm("Ibalik sa 0 ang pila?")) { fetch('/manual-reset', { method: 'POST' }).then(res => res.json()).then(data => { updateAdminDisplay(); }); } }
        setInterval(updateAdminDisplay, 1000);
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
        body { font-family: sans-serif; text-align: center; margin-top: 30px; background: #11111a; color: #fff; }
        .box { border: 2px solid #2980b9; padding: 35px; display: inline-block; border-radius: 12px; background: #1c1c28; width: 85%; max-width: 400px; }
        .num { font-size: 80px; color: #3498db; font-weight: bold; margin: 15px 0; }
        .btn-ticket { font-size: 20px; padding: 15px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; margin-bottom: 20px; }
        .input-name { font-size: 18px; padding: 12px; width: 90%; border-radius: 8px; border: 2px solid #444; background: #2c2c3e; color: white; text-align: center; margin-bottom: 15px; }
        .ticket-box { background: #222230; padding: 15px; border-radius: 8px; border: 1px dashed #3498db; margin-bottom: 20px; }
        .my-num { font-size: 40px; color: #00ca72; font-weight: bold; }
        .msg-box { background: #e74c3c; color: white; padding: 10px; border-radius: 5px; font-weight: bold; margin-top: 10px; display: none; }
    </style>
</head>
<body>
    <div class="box">
        <div id="registration_section">
