# Copyright (c) 2026 Pietro Chierico
# SPDX-License-Identifier: MIT

import os
import sys
import subprocess
import webbrowser
from pathlib import Path
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

BASE_DIR = Path(__file__).parent.resolve()

SCRIPT_MAIN = BASE_DIR / "visualize_filters.py"

SCRIPT_1 = BASE_DIR / "script1_stress_dataset_collection.py"
SCRIPT_2 = BASE_DIR / "script2_stress_analysis_training_export.py"
SCRIPT_3 = BASE_DIR / "script3_stress_live_detection_challenge.py"


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>PulseCraft PPG</title>

    <style>
        :root {
            --bg: #f5f7fb;
            --text: #111114;
            --muted: #5f6368;
            --blue: #0071e3;
            --green: #36d399;
            --purple: #8b5cf6;
            --dark: #0b0f19;
            --card: rgba(255, 255, 255, 0.78);
            --glass: rgba(255, 255, 255, 0.58);
            --border: rgba(255, 255, 255, 0.45);
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background:
                radial-gradient(circle at top left, #d9e8ff 0%, transparent 32%),
                radial-gradient(circle at top right, #e8ddff 0%, transparent 30%),
                linear-gradient(180deg, #f8fbff 0%, #eef2f8 100%);
            color: var(--text);
        }

        header {
            min-height: 92vh;
            padding: 40px 10% 80px;
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: center;
            overflow: hidden;
        }

        header::after {
            content: "";
            position: absolute;
            width: 520px;
            height: 520px;
            right: -120px;
            top: 130px;
            background: radial-gradient(circle, rgba(0,113,227,0.22), transparent 68%);
            filter: blur(8px);
            z-index: 0;
        }

        .top-bar {
            position: absolute;
            top: 34px;
            left: 10%;
            right: 10%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 2;
        }

        .logo {
            height: 86px;
            border-radius: 18px;
            box-shadow: 0 18px 45px rgba(0,0,0,0.12);
        }

        .nav-pill {
            padding: 12px 20px;
            border-radius: 999px;
            background: var(--glass);
            backdrop-filter: blur(18px);
            font-weight: 700;
            color: #1d1d1f;
            border: 1px solid var(--border);
        }

        .hero {
            max-width: 950px;
            z-index: 2;
        }

        .tag {
            display: inline-block;
            background: rgba(0,113,227,0.10);
            color: var(--blue);
            padding: 9px 18px;
            border-radius: 999px;
            font-weight: 700;
            margin-bottom: 24px;
        }

        .dark-card .tag {
            background: rgba(54,211,153,0.12);
            color: #8ff0c3;
        }

        h1 {
            font-size: clamp(54px, 8vw, 112px);
            line-height: 0.95;
            margin: 0 0 28px;
            letter-spacing: -5px;
        }

        h2 {
            font-size: clamp(34px, 4vw, 56px);
            letter-spacing: -2px;
            margin: 0 0 18px;
        }

        h3 {
            font-size: 24px;
            margin-bottom: 10px;
        }

        p {
            font-size: 20px;
            line-height: 1.65;
            color: var(--muted);
        }

        .hero p {
            max-width: 760px;
            font-size: 24px;
        }

        section {
            padding: 70px 10%;
        }

        .card {
            background: var(--card);
            backdrop-filter: blur(24px);
            border: 1px solid var(--border);
            border-radius: 34px;
            padding: 46px;
            box-shadow: 0 28px 70px rgba(25, 35, 60, 0.12);
            margin-bottom: 46px;
        }

        .dark-card {
            background:
                radial-gradient(circle at top left, rgba(54,211,153,0.26), transparent 30%),
                radial-gradient(circle at top right, rgba(139,92,246,0.30), transparent 32%),
                linear-gradient(135deg, #07111f, #141827 54%, #1a102a);
            color: white;
        }

        .dark-card p {
            color: #c9d2e3;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 18px;
            margin-top: 32px;
        }

        .mini-card {
            padding: 26px;
            border-radius: 26px;
            background: rgba(255,255,255,0.70);
            border: 1px solid rgba(255,255,255,0.55);
        }

        .dark-card .mini-card {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
        }

        .mini-card span {
            display: block;
            color: var(--blue);
            font-weight: 800;
            margin-bottom: 12px;
        }

        .dark-card .mini-card span {
            color: #8ff0c3;
        }

        button {
            border: none;
            border-radius: 999px;
            padding: 17px 30px;
            font-size: 17px;
            font-weight: 700;
            background: var(--blue);
            color: white;
            cursor: pointer;
            margin: 12px 12px 0 0;
            transition: 0.22s ease;
            box-shadow: 0 14px 28px rgba(0,113,227,0.26);
        }

        button:hover {
            background: #005bb5;
            transform: translateY(-3px);
        }

        .outline {
            background: rgba(255,255,255,0.14);
            border: 1px solid rgba(255,255,255,0.22);
            box-shadow: none;
        }

        .outline:hover {
            background: rgba(255,255,255,0.23);
        }

        .workflow {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 18px;
            margin-top: 34px;
        }

        .workflow-step {
            position: relative;
            padding: 30px;
            border-radius: 28px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.13);
            min-height: 210px;
        }

        .number {
            width: 42px;
            height: 42px;
            display: grid;
            place-items: center;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--green), var(--purple));
            color: white;
            font-weight: 800;
            margin-bottom: 18px;
        }

        .question {
            margin-top: 26px;
            padding: 26px;
            border-radius: 26px;
            background: rgba(54,211,153,0.10);
            border: 1px solid rgba(54,211,153,0.18);
        }

        .feature-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 24px;
        }

        .feature-pill {
            padding: 11px 16px;
            border-radius: 999px;
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.14);
            color: #dce8ff;
            font-weight: 700;
        }

        footer {
            padding: 48px 10%;
            color: #6e6e73;
            font-weight: 600;
        }
    </style>
</head>

<body>

<header>
    <div class="top-bar">
        <div class="nav-pill">Biomedical Signal Processing Demo</div>
        <img class="logo" src="https://upload.wikimedia.org/wikipedia/en/6/6a/KUSTAR_Logo.jpg">
    </div>

    <div class="hero">
        <span class="tag">PulseCraft PPG</span>
        <h1>PulseCraft PPG</h1>
        <p>
            A futuristic interactive platform for exploring Arduino USB serial PPG acquisition,
            signal quality, filtering, motion artifacts, feature extraction,
            machine learning, and real-time biomedical classification.
        </p>
    </div>
</header>

<section>
    <div class="card">
        <span class="tag">Background</span>
        <h2>What is PPG?</h2>

        <p>
            Photoplethysmography, or PPG, is a non-invasive optical technique
            used to measure blood volume changes in tissue. A light source
            illuminates the skin, while a photodetector measures variations in
            the reflected or transmitted light.
        </p>

        <p>
            These variations are related to cardiovascular activity and can be
            used to estimate heart rate, pulse waveform morphology, perfusion
            changes, and signal quality. Because PPG is very sensitive to
            motion, pressure, sensor placement, and ambient conditions, signal
            processing is essential.
        </p>

        <div class="grid">
            <div class="mini-card">
                <span>01</span>
                <h3>Optical Sensing</h3>
                <p>Light interacts with tissue and blood volume changes.</p>
            </div>

            <div class="mini-card">
                <span>02</span>
                <h3>Raw Signal</h3>
                <p>The sensor captures a noisy IR waveform affected by movement.</p>
            </div>

            <div class="mini-card">
                <span>03</span>
                <h3>Filtering</h3>
                <p>Signal processing improves readability and pulse detection.</p>
            </div>

            <div class="mini-card">
                <span>04</span>
                <h3>Signal Quality</h3>
                <p>Students can test how motion changes raw and filtered PPG.</p>
            </div>
        </div>

        <button onclick="launchMain()">Launch Real-Time Serial Raw vs Filtered Demo</button>
    </div>
</section>

<section>
    <div class="card dark-card">
        <span class="tag">Project 5: Mental Stress Detection</span>
        <h2>Mental Stress Detection from PPG Features</h2>

        <p>
            In this demo, students explore how mental stress influences cardiovascular
            dynamics using wearable PPG sensors connected through an Arduino USB
            serial COM port. Participants complete relaxed baseline periods, mental
            arithmetic, timed reaction tasks, and cognitive interference challenges
            while physiological signals are recorded.
        </p>

        <p>
            The goal is to compare relaxed and stressed physiological states, analyze
            heart-rate variability and pulse waveform changes, investigate autonomic
            nervous system responses, and train an AI model for live stress-state
            classification.
        </p>

        <div class="question">
            <h3>Research Question</h3>
            <p>
                Which PPG-derived waveform and HRV features change during cognitive
                stress, and can those IR features classify relaxed versus stressed
                states in real time?
            </p>
        </div>

        <div class="feature-strip">
            <div class="feature-pill">Relaxed Baseline</div>
            <div class="feature-pill">Mental Arithmetic</div>
            <div class="feature-pill">Timed Reaction Test</div>
            <div class="feature-pill">Cognitive Challenge</div>
            <div class="feature-pill">HRV Features</div>
            <div class="feature-pill">Pulse Waveform</div>
            <div class="feature-pill">Autonomic Response</div>
            <div class="feature-pill">AI Stress Classifier</div>
        </div>

        <div class="workflow">
            <div class="workflow-step">
                <div class="number">1</div>
                <h3>Stress Dataset Collection</h3>
                <p>
                    Run repeated recordings with a fixed protocol: stabilization,
                    relaxed baseline, mental arithmetic, recovery, timed reaction,
                    cognitive interference, and final calm recording. Export labeled
                    Relaxed and Stressed feature rows to CSV.
                </p>
                <button class="outline" onclick="launchScript1()">Launch Stress Data Collection · Export Data</button>
            </div>

            <div class="workflow-step">
                <div class="number">2</div>
                <h3>Analysis and Training</h3>
                <p>
                    Load the exported CSV, generate one boxplot per PPG and HRV
                    feature comparing Relaxed vs Stressed, train the stress classifier,
                    and export the trained model.
                </p>
                <button class="outline" onclick="launchScript2()">Load Data and Train Stress Model</button>
            </div>

            <div class="workflow-step">
                <div class="number">3</div>
                <h3>Live Stress Detection</h3>
                <p>
                    Load the trained model, select the available Arduino COM port, stream
                    live serial PPG, extract the same features, and display a real-time
                    mental stress score during an interactive challenge.
                </p>
                <button class="outline" onclick="launchScript3()">Load Model and Detect Live Stress</button>
            </div>
        </div>
    </div>
</section>

<footer>
    PulseCraft PPG · Designed by Pietro Chierico · Visiting PhD at Khalifa University · Project 5
</footer>

<script>
    async function launchMain() {
        const res = await fetch("/launch/main");
        console.log(await res.json());
    }

    async function launchScript1() {
        const res = await fetch("/launch/script1");
        console.log(await res.json());
    }

    async function launchScript2() {
        const res = await fetch("/launch/script2");
        console.log(await res.json());
    }

    async function launchScript3() {
        const res = await fetch("/launch/script3");
        console.log(await res.json());
    }
</script>

</body>
</html>
"""


def launch_python_script(script_path: Path):
    if not script_path.exists():
        return {
            "status": "error",
            "message": f"Script not found: {script_path}",
        }

    try:
        kwargs = {}

        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE

        subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(script_path.parent),
            **kwargs,
        )

        return {
            "status": "ok",
            "message": f"Launched {script_path.name}",
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


@app.route("/")
def home():
    return render_template_string(HTML_PAGE)


@app.route("/launch/main")
def launch_main():
    return jsonify(launch_python_script(SCRIPT_MAIN))


@app.route("/launch/script1")
def launch_script1():
    return jsonify(launch_python_script(SCRIPT_1))


@app.route("/launch/script2")
def launch_script2():
    return jsonify(launch_python_script(SCRIPT_2))


@app.route("/launch/script3")
def launch_script3():
    return jsonify(launch_python_script(SCRIPT_3))


if __name__ == "__main__":
    url = "http://127.0.0.1:5000"

    print("Starting local PPG Arduino serial mental stress demo website...")
    print(f"Open: {url}")

    webbrowser.open(url)

    app.run(host="127.0.0.1", port=5000, debug=False)
