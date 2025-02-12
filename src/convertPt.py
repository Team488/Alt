# from ultralytics import YOLO
# m = YOLO("yolov11s.pt")
# m.export(format="onnx", simplify=False, device='cpu')

from rknn.api import RKNN

# Create RKNN object
rknn = RKNN()

# Load ONNX model
# INT8
print('--> Configuring model')
rknn.config(mean_values=[[0, 0, 0]], std_values=[[255, 255, 255]], 
            quantized_dtype='w8a8', 
            target_platform='rk3588')
print('done')

modelPrefix = "yolov11s"

print('--> Loading ONNX model')
ret = rknn.load_onnx(model=f'{modelPrefix}_fp32.onnx')
if ret != 0:
    print('Load ONNX model failed!')
    exit(ret)
print('done')


print('--> Building model')
dataset = './dataset.txt'  
# ret = rknn.build(do_quantization=True, dataset=dataset)
ret = rknn.build(do_quantization=False)
if ret != 0:
    print('Build model failed!')
    exit(ret)
print('done')

print('--> Exporting RKNN model')
rknn.export_rknn(f'./{modelPrefix}_fp32.rknn')
print('done')

rknn.release()
