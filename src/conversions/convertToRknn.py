from rknn.api import RKNN

# Create RKNN object
rknn = RKNN()

rknn.config(target_platform="rk3588")
# Load TensorFlow frozen model
ret = rknn.load_tensorflow(
    tf_pb="src/assets/mars-small128.pb",
    inputs=["images"],  # Input node name
    outputs=["features"],  # Output node name
    input_size_list=[[None, 128, 64, 3]],
)  # Input shape (not including batch size)

if ret != 0:
    print("Load model failed!")
    exit(ret)

# Convert model to RKNN
ret = rknn.build(
    do_quantization=False
)  # Set do_quantization=True if you want to quantize
if ret != 0:
    print("Build model failed!")
    exit(ret)

# Save the RKNN model
rknn.export_rknn("model.rknn")
