from tools.calibration import charuco_calibration, takeCalibrationPhotos

takeCalibrationPhotos(
    cameraPath=1, photoPath="calib", timePerPicture=2, frameShape=(800, 600)
)
charuco_calibration(calibPath="calibout.json", imagesPath="calib")
