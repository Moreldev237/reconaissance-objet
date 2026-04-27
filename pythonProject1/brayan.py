import tkinter as tk
from tkinter import filedialog
import cv2
from ultralytics import YOLO
import threading
import pyttsx3
import time

# =========================
# 🤖 INITIALISATION IA + VOIX
# =========================
model = YOLO("yolov8n.pt")

engine = pyttsx3.init()
engine.setProperty('rate', 150)  # vitesse de la voix

camera_running = False
last_spoken = 0  # anti spam voix


# =========================
# 📸 DÉTECTION IMAGE
# =========================
def detect_image():
    path = filedialog.askopenfilename()

    if not path:
        return

    image = cv2.imread(path)

    if image is None:
        print("❌ Image invalide")
        return

    results = model(image)
    result = results[0]

    # Dessin
    result_img = result.plot()

    # Récupération objets
    names = result.names
    boxes = result.boxes

    detected_objects = []

    if boxes is not None:
        for cls in boxes.cls:
            detected_objects.append(names[int(cls)])

    detected_objects = list(set(detected_objects))

    if detected_objects:
        text = "Objets détectés : " + ", ".join(detected_objects)
        print(text)
        engine.say(text)
        engine.runAndWait()

    cv2.imshow("Détection Image", result_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# =========================
# 🎥 CAMÉRA TEMPS RÉEL
# =========================
def camera_loop():
    global camera_running, last_spoken

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Caméra introuvable")
        camera_running = False
        return

    print("🎥 Caméra démarrée (ESC pour quitter)")

    while camera_running:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        result = results[0]

        frame = result.plot()

        names = result.names
        boxes = result.boxes

        detected_objects = []

        if boxes is not None:
            for cls in boxes.cls:
                detected_objects.append(names[int(cls)])

        detected_objects = list(set(detected_objects))

        # Affichage console + voix (toutes les 3 secondes)
        if detected_objects and time.time() - last_spoken > 3:
            text = "Je vois " + ", ".join(detected_objects)
            print(text)
            engine.say(text)
            engine.runAndWait()
            last_spoken = time.time()

        cv2.imshow("YOLOv8 - Caméra", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    camera_running = False


# =========================
# 🎥 START CAMÉRA
# =========================
def start_camera():
    global camera_running

    if camera_running:
        print("⚠️ Caméra déjà active")
        return

    camera_running = True
    thread = threading.Thread(target=camera_loop)
    thread.daemon = True
    thread.start()


# =========================
# 🛑 STOP CAMÉRA
# =========================
def stop_camera():
    global camera_running
    camera_running = False
    print("🛑 Caméra arrêtée")


# =========================
# 🖥️ INTERFACE
# =========================
root = tk.Tk()
root.title("IA - Détection intelligente")
root.geometry("500x350")
root.configure(bg="#0B0F1A")

title = tk.Label(
    root,
    text="🤖 IA DE DÉTECTION EN TEMPS RÉEL",
    font=("Arial", 16, "bold"),
    fg="#00FFC8",
    bg="#0B0F1A"
)
title.pack(pady=20)

btn1 = tk.Button(
    root,
    text="📸 Analyser une image",
    command=detect_image,
    width=30,
    bg="#1F2A44",
    fg="white"
)
btn1.pack(pady=10)

btn2 = tk.Button(
    root,
    text="🎥 Lancer caméra",
    command=start_camera,
    width=30,
    bg="#1F2A44",
    fg="white"
)
btn2.pack(pady=10)

btn3 = tk.Button(
    root,
    text="🛑 Arrêter caméra",
    command=stop_camera,
    width=30,
    bg="#7C4DFF",
    fg="white"
)
btn3.pack(pady=10)

btn4 = tk.Button(
    root,
    text="❌ Quitter",
    command=root.quit,
    width=30,
    bg="red",
    fg="white"
)
btn4.pack(pady=10)


def on_close():
    stop_camera()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()