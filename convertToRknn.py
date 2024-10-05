from rknn.api import RKNN

# Set paths for your ONNX model and output RKNN file
onnx_model_path = "src/assets/bestV5.onnx"  # Replace with your YOLOv5 ONNX model path
rknn_model_path = "bestV5.rknn"  # Replace with your desired output path for RKNN

# Create RKNN object
rknn = RKNN()

# Step 1: Configure the RKNN model
print("--> Configuring model")
rknn.config(
    mean_values=[[0, 0, 0]],  # Adjust mean values for your model (optional)
    std_values=[
        [255, 255, 255]
    ],  # Normalize if your model was trained with images between 0-255
    target_platform="rk3588",  # Set the target platform (rk356x, rk3588, etc.)
)

# Step 2: Load the ONNX model
print("--> Loading ONNX model")
ret = rknn.load_onnx(model=onnx_model_path)
if ret != 0:
    print("Failed to load ONNX model")
    exit(ret)

# Step 3: Build the RKNN model
print("--> Building RKNN model")
ret = rknn.build(do_quantization=False)  # Set to True for quantization
if ret != 0:
    print("Failed to build RKNN model")
    exit(ret)

# Step 4: Export the RKNN model to file
print("--> Exporting RKNN model")
ret = rknn.export_rknn(rknn_model_path)
if ret != 0:
    print("Failed to export RKNN model")
    exit(ret)

print("Model successfully converted to RKNN format!")

# Step 5: Release resources
rknn.release()
