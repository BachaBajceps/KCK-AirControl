"""Rendering of the Matplotlib 3D scene."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

if TYPE_CHECKING:
    from mpl_toolkits.mplot3d.axes3d import Axes3D

    from app.state import AppState


class ThreeDView:
    """Draw the selected shape and configure its 3D axes."""

    def __init__(self, axes: Axes3D) -> None:
        self.axes = axes

    def draw(self, state: AppState) -> None:
        self.axes.clear()
        shape_type = state.get_current_shape()
        color = state.get_current_color()

        if shape_type == 'CUBE':
            self._draw_cube(color)
        elif shape_type == 'PYRAMID':
            self._draw_pyramid(color)
        elif shape_type == 'SPHERE':
            self._draw_sphere(color)
        else:
            raise ValueError(f'Unsupported shape: {shape_type}')

        self._configure_axes(state)

    def _draw_cube(self, color: str) -> None:
        vertices = np.array(
            [
                [-0.5, -0.5, -0.5],
                [0.5, -0.5, -0.5],
                [0.5, 0.5, -0.5],
                [-0.5, 0.5, -0.5],
                [-0.5, -0.5, 0.5],
                [0.5, -0.5, 0.5],
                [0.5, 0.5, 0.5],
                [-0.5, 0.5, 0.5],
            ]
        )
        face_indices = (
            (0, 1, 2, 3),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (2, 3, 7, 6),
            (0, 3, 7, 4),
            (1, 2, 6, 5),
        )
        faces = [[vertices[index] for index in face] for face in face_indices]
        self.axes.add_collection3d(
            Poly3DCollection(
                faces,
                facecolors=color,
                linewidths=1,
                edgecolors='black',
                alpha=0.9,
            )
        )

    def _draw_pyramid(self, color: str) -> None:
        vertices = np.array(
            [
                [-0.5, -0.5, -0.5],
                [0.5, -0.5, -0.5],
                [0.5, 0.5, -0.5],
                [-0.5, 0.5, -0.5],
                [0.0, 0.0, 0.5],
            ]
        )
        face_indices = (
            (0, 1, 4),
            (1, 2, 4),
            (2, 3, 4),
            (3, 0, 4),
            (0, 1, 2, 3),
        )
        faces = [[vertices[index] for index in face] for face in face_indices]
        self.axes.add_collection3d(
            Poly3DCollection(
                faces,
                facecolors=color,
                linewidths=1,
                edgecolors='black',
                alpha=0.9,
            )
        )

    def _draw_sphere(self, color: str) -> None:
        azimuth = np.linspace(0.0, 2.0 * np.pi, 30)
        elevation = np.linspace(0.0, np.pi, 20)
        azimuth_grid, elevation_grid = np.meshgrid(azimuth, elevation)
        x = 0.5 * np.cos(azimuth_grid) * np.sin(elevation_grid)
        y = 0.5 * np.sin(azimuth_grid) * np.sin(elevation_grid)
        z = 0.5 * np.cos(elevation_grid)
        self.axes.plot_surface(x, y, z, color=color, alpha=0.9)

    def _configure_axes(self, state: AppState) -> None:
        self.axes.set_facecolor('#f0f0f0')
        self.axes.set_xlabel('OŚ X', color='red')
        self.axes.set_ylabel('OŚ Y', color='green')
        self.axes.set_zlabel('OŚ Z', color='blue')
        self.axes.set_xlim(-0.7, 0.7)
        self.axes.set_ylim(-0.7, 0.7)
        self.axes.set_zlim(-0.7, 0.7)
        self.axes.set_box_aspect((1.0, 1.0, 1.0))
        self.axes.view_init(elev=state.angle_x, azim=state.angle_y)
