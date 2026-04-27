from cProfile import label

import cv2
from jinja2.nodes import Break
from langid.langid import identifier
from sympy.printing.pretty.pretty_symbology import annotated
from ultralytics import YOLO
import shutil
import os
# charger modele
model = YOLO("yolov8n.pt")
image = cv2.imread("image.jpeg")
# verifier si image chargee
# if image is None:
#     print("Erreur: image non trouvee")
# else:
#     cv2.imshow("Reconnaissance d'objet",image)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
         break
         results = model(frame)
    #identifier les noms
         for r in results:
             for box in r.boxes:
                 # recuperer le nom de l'objet correspondant a l'index label = model.names[cls]
                 cls = int(box.cls[0])
                 label = model.names[cls]
                 conf = box.conf[0]
                 print(f"objet detecte : {label} ( {conf:.2f})")

    annotated_frame = results[0].plot()
    cv2.imshow("detection yolov8", annotated_frame)
    if cv2.waitKey(1) & 0XFF == 27: # touche ESC
        break
cap.release()
cv2.destroyAllWindows()

# charger image
#image = cv2.imread("image.jpg")
# Detection
results = model(image)
# Affichage
res_plotted = results[0].plot()

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        break
    results = model(frame)
    annotated_frame = results[0].plot()
    cv2.imshow("Detection",annotated_frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break
cap.release()
cv2.destroyAllWindows()

print("Modele charge avec succes !")
image_folder = "images"
output_folder = "sorted"
for image_name in os.listdir(image_folder):
    print("traitement :", image_name)

    image_path = os.path.join(image_folder, image_name)
    image = cv2.imread(image_path)

    if image is None:
        print("image non lue :", image_name)
        continue
    results = model(image)
    detected_classes = set()
    for r in results:
        for box in r.boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            detected_classes.add(class_name)
    for class_name in detected_classes:
            class_folder = os.path.join(output_folder, class_name)
            os.makedirs(class_folder, exist_ok=True)
            shutil.copy(image_path, os.path.join(class_folder, image_name))








