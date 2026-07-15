import matplotlib.pyplot as plt
import pytest
from mpl_toolkits.mplot3d.axes3d import Axes3D

from app.state import AppState
from app.view_3d import ThreeDView


@pytest.fixture()
def axes() -> Axes3D:
    figure = plt.figure()
    axes_3d: Axes3D = figure.add_subplot(111, projection='3d')
    yield axes_3d
    plt.close(figure)


@pytest.mark.parametrize('shape', ['CUBE', 'PYRAMID', 'SPHERE'])
def test_draw_supported_shape(axes: Axes3D, shape: str) -> None:
    state = AppState(shapes=(shape,), shape_names=(shape,))

    ThreeDView(axes).draw(state)

    assert axes.get_xlabel() == 'OŚ X'
    assert axes.get_ylabel() == 'OŚ Y'
    assert axes.get_zlabel() == 'OŚ Z'


def test_draw_rejects_unsupported_shape(axes: Axes3D) -> None:
    state = AppState(shapes=('INVALID',), shape_names=('Invalid',))

    with pytest.raises(ValueError, match='Unsupported shape: INVALID'):
        ThreeDView(axes).draw(state)
