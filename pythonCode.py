#pip install flask
#pip install datafeel.device
from flask import Flask, request
from datafeel.device import discover_devices

app = Flask(__name__)

# Color mappings to LED and vibration settings
HAPTIC_MAPPINGS = {
    "yellow": {"led": (255, 255, 0), "vibration": 150},
    "red": {"led": (255, 0, 0), "vibration": 200},
    "blue": {"led": (0, 0, 255), "vibration": 250},
    "green": {"led": (0, 255, 0), "vibration": 100},
}

@app.route("/haptic-feedback")
def haptic_feedback():
    color = request.args.get("color")
    if color not in HAPTIC_MAPPINGS:
        return "Invalid color", 400

    # Discover Datafeel Dots
    devices = discover_devices(1)
    if not devices:
        return "No dots found", 500

    dot = devices[0]
    settings = HAPTIC_MAPPINGS[color]

    # Set LED color
    dot.set_led(*settings["led"])

    # Set vibration
    dot.registers.set_vibration_mode(1)  # Manual mode
    dot.registers.set_vibration_frequency(settings["vibration"])
    dot.registers.set_vibration_intensity(1.0)

    return f"Haptic feedback triggered for {color}!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
