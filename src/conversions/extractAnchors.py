from ultralytics import YOLO

# Load the YOLO model (assuming a .pt file)
model = YOLO("src/bestV8.pt")

# Extract anchors
anchors = (
    model.model.model[-1].anchors if hasattr(model.model.model[-1], "anchors") else None
)

# Print the extracted anchors
if anchors:
    print("Model Anchors:", anchors)
else:
    print("Anchors not found in the model.")
