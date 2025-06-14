'''
Moduł odpowiedzialny za renderowanie sceny 3D.
'''
import numpy as np
from matplotlib.axes import Axes
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from app.state import AppState


class ThreeDView:
    '''Zarządza rysowaniem obiektów 3D na kanwie Matplotlib.'''
    def __init__(self, ax: Axes):
        self.ax = ax

    def draw(self, state: AppState) -> None:
        '''Rysuje obiekt na podstawie bieżącego stanu aplikacji.'''
        self.ax.cla()
        shape_type = state.get_current_shape()
        color = state.get_current_color()

        if shape_type == 'CUBE':
            self._draw_cube(color)
        elif shape_type == 'PYRAMID':
            self._draw_pyramid(color)
        elif shape_type == 'SPHERE':
            self._draw_sphere(color)

        self._configure_axes(state)

    def _draw_cube(self, color: str) -> None:
        v = np.array([[-.5,-.5,-.5], [.5,-.5,-.5], [.5,.5,-.5], [-.5,.5,-.5],
                      [-.5,-.5,.5], [.5,-.5,.5], [.5,.5,.5], [-.5,.5,.5]])
        faces = [[v[j] for j in i] for i in [[0,1,2,3], [4,5,6,7], [0,1,5,4],
                                             [2,3,7,6], [0,3,7,4], [1,2,6,5]]]
        self.ax.add_collection3d(
            Poly3DCollection(faces, facecolors=color, linewidths=1, edgecolors='k', alpha=0.9)
        )

    def _draw_pyramid(self, color: str) -> None:
        v = np.array([[-0.5,-0.5,-0.5], [0.5,-0.5,-0.5], [0.5,0.5,-0.5],
                      [-0.5,0.5,-0.5], [0,0,0.5]])
        faces = [[v[i] for i in j] for j in [[0,1,4], [1,2,4], [2,3,4], [3,0,4], [0,1,2,3]]]
        self.ax.add_collection3d(
            Poly3DCollection(faces, facecolors=color, linewidths=1, edgecolors='k', alpha=0.9)
        )

    def _draw_sphere(self, color: str) -> None:
        u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:20j]
        x = 0.5 * np.cos(u) * np.sin(v)
        y = 0.5 * np.sin(u) * np.sin(v)
        z = 0.5 * np.cos(v)
        self.ax.plot_surface(x, y, z, color=color, alpha=0.9)

    def _configure_axes(self, state: AppState) -> None:
        '''Konfiguruje wygląd osi, limity i widok kamery.'''
        self.ax.set_facecolor('#f0f0f0')
        self.ax.set_xlabel('OŚ X', color='red')
        self.ax.set_ylabel('OŚ Y', color='green')
        self.ax.set_zlabel('OŚ Z', color='blue')  # type: ignore[attr-defined]

        self.ax.set_box_aspect((1, 1, 1))  # type: ignore[attr-defined]
        self.ax.set_xlim(-0.7, 0.7)
        self.ax.set_ylim(-0.7, 0.7)
        self.ax.set_zlim(-0.7, 0.7)  # type: ignore[attr-defined]

        self.ax.view_init(elev=state.angle_x, azim=state.angle_y) # type: ignore[attr-defined]
