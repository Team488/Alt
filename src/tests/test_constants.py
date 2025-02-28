from tools.Constants import (
    CameraIntrinsics,
    CameraIntrinsicsPredefined,
    CameraExtrinsics,
)


def test_creation() -> None:
    intr = CameraIntrinsics(fx_pix=10, fy_pix=100)
    assert intr.getFx() == 10
    assert intr.getFy() == 100


def test_predefinedIntrinsics() -> None:
    extr = CameraIntrinsicsPredefined.OV9782COLOR
    extr2 = CameraIntrinsicsPredefined.OV9782COLOR
    assert extr == extr2
    assert extr.getCx() == extr2.getCx()
