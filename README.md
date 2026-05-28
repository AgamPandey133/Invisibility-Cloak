# 🪄 Adaptive Invisibility Cloak

> A real-time invisibility effect built with **Python + OpenCV**.

Hold a colored cloth in front of the camera, calibrate it, and watch it disappear in real time.

The project uses **adaptive HSV color detection** to identify the cloak and replaces it with a previously captured background.

No ML. No heavy frameworks. Just computer vision.

---

## ✨ How It Works

```text
Webcam
   ↓
HSV Color Detection
   ↓
Adaptive Cloak Mask
   ↓
Mask Cleanup
   ↓
Replace Cloak with Background
   ↓
🪄 Invisible
```

The process is simple:

1. Capture a clean background.
2. Hold the cloak inside the calibration area.
3. The system learns its color automatically.
4. The cloak is detected in every frame.
5. Detected pixels are replaced with the matching background pixels.

---

## 🎯 The Interesting Part

Unlike a basic green-screen implementation, the cloak color **isn't hardcoded**.

Press `C`, show the system your cloth, and it calculates an HSV range automatically.

So you're not limited to green:

**🟢 Green · 🔵 Blue · 🟣 Purple · 🔴 Red · 🟡 Yellow**

As long as the color is sufficiently distinct from the environment, it can be used as the cloak.

---

## 🧠 Why HSV?

HSV separates **color (Hue)** from **saturation** and **brightness**, making it much more suitable for real-time color segmentation than directly thresholding RGB values.

The calibration system also handles HSV's circular hue range, including colors such as red that sit around the `0/179` boundary.

---

## 🛠️ Built With

* Python
* OpenCV
* NumPy

That's it.

---

## 📁 Project Structure

```text
Invisibility-Cloak/
│
├── main.py
├── calibration.py
├── cloak.py
├── effects.py
├── requirements.txt
├── README.md
└── .gitignore
```

| File             | Purpose                                    |
| ---------------- | ------------------------------------------ |
| `main.py`        | Camera loop, state management and controls |
| `calibration.py` | Adaptive color calibration                 |
| `cloak.py`       | Mask generation and invisibility effect    |
| `effects.py`     | HUD and visual interface                   |

---

## 🚀 Setup

### Requirements

* Python 3.10+
* Webcam
* Solid-colored cloth

### Install

```bash
git clone https://github.com/AgamPandey133/Invisibility-Cloak.git
cd Invisibility-Cloak

python -m venv .venv
```

**Windows:**

```bash
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
python main.py
```

---

## 🎮 Controls

| Key         | Action                         |
| ----------- | ------------------------------ |
| `B`         | Capture / recapture background |
| `C`         | Calibrate cloak color          |
| `R`         | Reset calibration              |
| `Q` / `ESC` | Quit                           |

---

## 📸 Getting the Best Result

* Keep the camera completely stationary.
* Use a **bright, solid-colored cloth**.
* Avoid having the same color elsewhere in the background.
* Keep lighting reasonably consistent.
* Capture the background before entering the scene.

**Bright green** is the easiest color to start with.

---

## ⚠️ Limitations

This is a camera illusion, not actual invisibility.

* The camera needs to stay still.
* The background reference is static.
* Objects sharing the cloak's color may also disappear.
* Major lighting changes can affect detection.
* Shadows and reflections can create small mask artifacts.

---

## 🔮 Possible Improvements

* Better edge smoothing
* Temporal mask stabilization
* Improved color modelling
* Automatic background capture
* Background stabilization

---

## 📜 License

MIT — free for personal and educational use.

---

<div align="center">

**Built with 🐍 Python + 👁️ OpenCV**

[GitHub](https://github.com/AgamPandey133)

</div>
