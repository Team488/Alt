from rknn.api import RKNN

# Set paths for your ONNX model and output RKNN file
onnx_model_path = "mars-small128.onnx"  # Replace with your YOLOv5 ONNX model path
rknn_model_path = "mars-small128.rknn"  # Replace with your desired output path for RKNN

# Create RKNN object
rknn = RKNN()

# Step 1: Configure the RKNN model
print("--> Configuring model")
rknn.config(
    target_platform="rk3588",  # Set the target platform (rk356x, rk3588, etc.)
)

# Step 2: Load the ONNX model
print("--> Loading ONNX model")
ret = rknn.load_onnx(
    model=onnx_model_path, inputs=["images:0"], input_size_list=[[32, 128, 64, 3]]
)
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
