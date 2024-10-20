import tensorflow as tf
import tf2onnx

# Function to load the frozen graph
def load_frozen_graph(frozen_graph_filename):
    with tf.io.gfile.GFile(frozen_graph_filename, "rb") as f:
        graph_def = tf.compat.v1.GraphDef()
        graph_def.ParseFromString(f.read())

    with tf.Graph().as_default() as graph:
        tf.import_graph_def(graph_def, name="")

    return graph


# Specify your frozen graph path
frozen_graph_path = "src/assets/mars-small128.pb"
graph = load_frozen_graph(frozen_graph_path)

# Define input and output names
input_names = ["images:0"]  # Use the full tensor name including the prefix
output_names = ["features:0"]  # Use the full tensor name including the prefix

# Convert the model to ONNX format
model_proto, _ = tf2onnx.convert.from_graph_def(
    graph.as_graph_def(),
    input_names=input_names,
    output_names=output_names,
    opset=13,  # Choose the opset version you need
)

# Save the ONNX model
onnx_model_path = "mars-small128.onnx"
with open(onnx_model_path, "wb") as f:
    f.write(model_proto.SerializeToString())

print(f"Model converted to ONNX and saved at {onnx_model_path}")
