from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Tank State Store
tank_state = {
    "total_capacity": 800.0,
    "current_level": 350.0,     # Initial water level in Liters
    "alert_limit": 400.0,       # Default alert threshold in Liters
    "divisions": [200, 400, 600, 800],
    "inflow_active": False,
    "outflow_active": False,
    "pump_speed": 15.0          # Liters per update tick
}

def calculate_status():
    current = tank_state["current_level"]
    limit = tank_state["alert_limit"]
    total = tank_state["total_capacity"]
    
    is_alert = current >= limit
    percentage = round((current / total) * 100.0, 1)
    
    # Determine level state text and color theme
    if is_alert:
        status_code = "ALERT"
        status_message = f"⚠️ ALERT: Water level ({current:.0f}L) reached or exceeded limit ({limit:.0f}L)!"
    elif current >= (limit * 0.85):
        status_code = "WARNING"
        status_message = f"⚡ WARNING: Approaching alert threshold ({limit:.0f}L)..."
    else:
        status_code = "SAFE"
        status_message = f"✅ Normal Operation: Water level is safe ({current:.0f}L / {total:.0f}L)."
        
    return {
        "current_level": round(current, 1),
        "alert_limit": round(limit, 1),
        "total_capacity": total,
        "divisions": tank_state["divisions"],
        "is_alert": is_alert,
        "percentage": percentage,
        "status_code": status_code,
        "status_message": status_message,
        "inflow_active": tank_state["inflow_active"],
        "outflow_active": tank_state["outflow_active"]
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status", methods=["GET"])
def get_status():
    # If inflow or outflow is active, update the level
    if tank_state["inflow_active"]:
        tank_state["current_level"] = min(
            tank_state["total_capacity"], 
            tank_state["current_level"] + tank_state["pump_speed"]
        )
    elif tank_state["outflow_active"]:
        tank_state["current_level"] = max(
            0.0, 
            tank_state["current_level"] - tank_state["pump_speed"]
        )
        
    return jsonify(calculate_status())

@app.route("/api/set_level", methods=["POST"])
def set_level():
    data = request.get_json() or {}
    if "level" in data:
        try:
            val = float(data["level"])
            val = max(0.0, min(tank_state["total_capacity"], val))
            tank_state["current_level"] = val
            return jsonify({"success": True, "status": calculate_status()})
        except ValueError:
            return jsonify({"success": False, "error": "Invalid level value"}), 400
    return jsonify({"success": False, "error": "Missing level field"}), 400

@app.route("/api/set_limit", methods=["POST"])
def set_limit():
    data = request.get_json() or {}
    if "limit" in data:
        try:
            val = float(data["limit"])
            val = max(0.0, min(tank_state["total_capacity"], val))
            tank_state["alert_limit"] = val
            return jsonify({"success": True, "status": calculate_status()})
        except ValueError:
            return jsonify({"success": False, "error": "Invalid limit value"}), 400
    return jsonify({"success": False, "error": "Missing limit field"}), 400

@app.route("/api/toggle_flow", methods=["POST"])
def toggle_flow():
    data = request.get_json() or {}
    action = data.get("action")
    
    if action == "inflow_on":
        tank_state["inflow_active"] = True
        tank_state["outflow_active"] = False
    elif action == "inflow_off":
        tank_state["inflow_active"] = False
    elif action == "outflow_on":
        tank_state["outflow_active"] = True
        tank_state["inflow_active"] = False
    elif action == "outflow_off":
        tank_state["outflow_active"] = False
    elif action == "stop_all":
        tank_state["inflow_active"] = False
        tank_state["outflow_active"] = False
    else:
        return jsonify({"success": False, "error": "Unknown action"}), 400
        
    return jsonify({"success": True, "status": calculate_status()})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
