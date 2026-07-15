"""Interactive calibration workflow with camera-based evaluation tasks."""

from __future__ import annotations

import logging
import random
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

from app.config import ANIMATION_CONFIG, CAMERA_CONFIG, ENV_PATH, write_env_values
from app.state import NON_GESTURE_SIGNALS, AppState, Gesture
from app.view_3d import ThreeDView
from camera_handler import CameraHandler, CameraOutput

if TYPE_CHECKING:
    from mpl_toolkits.mplot3d.axes3d import Axes3D


@dataclass(slots=True)
class ConfigSnapshot:
    detection: float
    tracking: float
    smoothing: float
    history: int

    @classmethod
    def capture(cls) -> ConfigSnapshot:
        return cls(
            detection=CAMERA_CONFIG.min_detection_confidence,
            tracking=CAMERA_CONFIG.min_tracking_confidence,
            smoothing=ANIMATION_CONFIG.smoothing_factor,
            history=ANIMATION_CONFIG.gesture_history_length,
        )

    def apply(self) -> None:
        CAMERA_CONFIG.min_detection_confidence = self.detection
        CAMERA_CONFIG.min_tracking_confidence = self.tracking
        ANIMATION_CONFIG.smoothing_factor = self.smoothing
        ANIMATION_CONFIG.gesture_history_length = self.history

    def save(self) -> None:
        write_env_values(
            {
                'CAMERA_MIN_DETECTION_CONFIDENCE': f'{self.detection:.6g}',
                'CAMERA_MIN_TRACKING_CONFIDENCE': f'{self.tracking:.6g}',
                'ANIMATION_SMOOTHING_FACTOR': f'{self.smoothing:.6g}',
                'ANIMATION_GESTURE_HISTORY_LENGTH': str(self.history),
            }
        )


@dataclass(slots=True)
class CandidateSuggestion(ConfigSnapshot):
    seed: int


@dataclass(frozen=True, slots=True)
class TaskSpec:
    title: str
    description: str


TASK_LIBRARY: tuple[TaskSpec, ...] = (
    TaskSpec(
        title='Stability test',
        description=(
            'Hold an open hand at screen center for 3 seconds. Check if landmarks stay stable.'
        ),
    ),
    TaskSpec(
        title='Smooth rotation',
        description='Move an open hand left/right and up/down to rotate the 3D shape smoothly.',
    ),
    TaskSpec(
        title='Gesture switching',
        description='Alternate between POINTING and FIST to see if detection switches quickly.',
    ),
    TaskSpec(
        title='Color change',
        description='Use POINTING to cycle colors twice. Confirm current and next swatches update.',
    ),
    TaskSpec(
        title='Shape cycle',
        description=(
            'Show THUMBS_UP twice to advance the 3D shape. Check the label updates correctly.'
        ),
    ),
    TaskSpec(
        title='Victory reset',
        description='Perform the VICTORY gesture to snap the camera view back to the default pose.',
    ),
    TaskSpec(
        title='Stop rotation',
        description=(
            'Rotate with OPEN_HAND then close a FIST to freeze the view and release to resume.'
        ),
    ),
    TaskSpec(
        title='Edge tracking',
        description=(
            'Move your hand to the frame edges ensuring detection does not drop unexpectedly.'
        ),
    ),
    TaskSpec(
        title='Depth consistency',
        description=(
            'Move hand toward and away from camera. Verify gesture remains stable without flutter.'
        ),
    ),
    TaskSpec(
        title='Free play',
        description=(
            'Try any combination of gestures to build confidence in the current configuration.'
        ),
    ),
)


class CalibrationApp:
    TOTAL_CANDIDATES = 10
    TASKS_PER_CANDIDATE = 10
    UPDATE_INTERVAL_MS = 15

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title('Calibration Lab')
        self.root.geometry('1200x720')

        self.base_snapshot = ConfigSnapshot.capture()
        self.current_candidate: CandidateSuggestion | None = None
        self.current_candidate_votes: list[int] = []
        self.candidate_scores: list[float] = []
        self.candidate_index = 0
        self.task_index = 0
        self.positive_votes = 0
        self.negative_votes = 0
        self._update_job: str | None = None
        self._is_closing = False
        self._video_photo: ImageTk.PhotoImage | None = None

        self.camera_handler = CameraHandler()
        self.state = AppState()

        self._build_ui()
        self._start_candidate()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self._update_loop()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('Main.TFrame', background='#1b1f2a')
        style.configure('Secondary.TFrame', background='#242b3a')
        style.configure('Video.TLabel', background='#000000')
        style.configure(
            'Info.TLabel', background='#1b1f2a', foreground='#e5e9f0', font=('Segoe UI', 11)
        )
        style.configure(
            'Title.TLabel',
            background='#1b1f2a',
            foreground='#88c0d0',
            font=('Segoe UI', 14, 'bold'),
        )
        style.configure(
            'Emphasis.TLabel', background='#242b3a', foreground='#a3be8c', font=('Segoe UI', 11)
        )
        style.configure(
            'Warn.TLabel', background='#242b3a', foreground='#bf616a', font=('Segoe UI', 11)
        )
        style.configure(
            'Score.TLabel', background='#242b3a', foreground='#d8dee9', font=('Segoe UI', 10)
        )
        style.configure(
            'Better.TButton',
            background='#2e3440',
            foreground='#a3be8c',
            font=('Segoe UI', 12, 'bold'),
        )
        style.configure(
            'Worse.TButton',
            background='#2e3440',
            foreground='#bf616a',
            font=('Segoe UI', 12, 'bold'),
        )
        style.configure(
            'Neutral.TButton', background='#2e3440', foreground='#e5e9f0', font=('Segoe UI', 11)
        )
        style.map('Better.TButton', background=[('active', '#3b4252')])
        style.map('Worse.TButton', background=[('active', '#3b4252')])
        style.map('Neutral.TButton', background=[('active', '#3b4252')])

        main_frame = ttk.Frame(self.root, style='Main.TFrame', padding=16)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)

        # Left column: camera + 3D view + quick stats
        left_frame = ttk.Frame(main_frame, style='Main.TFrame')
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 12))
        left_frame.rowconfigure(0, weight=4)
        left_frame.rowconfigure(1, weight=3)

        self.video_label = ttk.Label(left_frame, style='Video.TLabel')
        self.video_label.grid(row=0, column=0, sticky='nsew')

        viz_panel = ttk.Frame(left_frame, style='Secondary.TFrame', padding=12)
        viz_panel.grid(row=1, column=0, sticky='nsew', pady=(12, 0))
        viz_panel.columnconfigure(0, weight=1)

        self.fig = plt.figure(facecolor='#242b3a', dpi=100)
        self.ax: Axes3D = self.fig.add_subplot(111, projection='3d')
        self.view_3d = ThreeDView(self.ax)
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_panel)  # type: ignore[no-untyped-call]
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)  # type: ignore[no-untyped-call]

        status_frame = ttk.Frame(viz_panel, style='Secondary.TFrame')
        status_frame.pack(fill=tk.X, pady=(12, 0))

        self.current_color_box = tk.Canvas(
            status_frame,
            width=22,
            height=22,
            bg=self.state.get_current_color(),
            highlightthickness=0,
        )
        self.current_color_box.pack(side=tk.LEFT)
        self.next_color_box = tk.Canvas(status_frame, width=22, height=22, highlightthickness=0)
        self.next_color_box.pack(side=tk.LEFT, padx=(8, 0))
        self._refresh_next_color_box()

        shape_name = self.state.shape_names[self.state.shape_index]
        self.shape_label = ttk.Label(
            status_frame,
            text=f'Shape: {shape_name}',
            style='Info.TLabel',
        )
        self.shape_label.pack(side=tk.LEFT, padx=12)

        self.gesture_label = ttk.Label(status_frame, text='Gesture: NONE', style='Info.TLabel')
        self.gesture_label.pack(side=tk.RIGHT)

        # Right column: tasks and scoring
        right_frame = ttk.Frame(main_frame, style='Secondary.TFrame', padding=16)
        right_frame.grid(row=0, column=1, sticky='nsew')
        right_frame.columnconfigure(0, weight=1)

        self.header_label = ttk.Label(right_frame, style='Title.TLabel')
        self.header_label.pack(anchor='w')

        self.candidate_info = ttk.Label(right_frame, style='Emphasis.TLabel', justify=tk.LEFT)
        self.candidate_info.pack(anchor='w', pady=(8, 12))

        self.progress = ttk.Progressbar(
            right_frame, maximum=self.TOTAL_CANDIDATES * self.TASKS_PER_CANDIDATE, length=280
        )
        self.progress.pack(fill=tk.X, pady=(0, 12))

        self.task_title = ttk.Label(right_frame, style='Title.TLabel')
        self.task_title.pack(anchor='w', pady=(4, 0))

        self.task_description = ttk.Label(
            right_frame, style='Info.TLabel', wraplength=360, justify=tk.LEFT
        )
        self.task_description.pack(anchor='w', pady=(6, 16))

        self.task_hint = ttk.Label(
            right_frame, style='Score.TLabel', wraplength=360, justify=tk.LEFT
        )
        self.task_hint.pack(anchor='w', pady=(0, 16))
        self.task_hint.config(text='Follow the description, then rate the candidate below.')

        button_frame = ttk.Frame(right_frame, style='Secondary.TFrame')
        button_frame.pack(fill=tk.X, pady=(6, 12))

        self.better_button = ttk.Button(
            button_frame,
            text='Better',
            style='Better.TButton',
            command=lambda: self._handle_vote(True),
        )
        self.better_button.pack(side=tk.LEFT, expand=True, padx=(0, 8))

        self.worse_button = ttk.Button(
            button_frame,
            text='Worse',
            style='Worse.TButton',
            command=lambda: self._handle_vote(False),
        )
        self.worse_button.pack(side=tk.LEFT, expand=True, padx=(8, 0))

        self.feedback_label = ttk.Label(right_frame, style='Emphasis.TLabel')
        self.feedback_label.pack(anchor='w', pady=(8, 0))

        self.candidate_progress_label = ttk.Label(
            right_frame, style='Score.TLabel', justify=tk.LEFT
        )
        self.candidate_progress_label.pack(anchor='w', pady=(4, 0))

        self.overall_progress_label = ttk.Label(right_frame, style='Score.TLabel', justify=tk.LEFT)
        self.overall_progress_label.pack(anchor='w', pady=(4, 0))

        self.score_summary_label = ttk.Label(right_frame, style='Score.TLabel', justify=tk.LEFT)
        self.score_summary_label.pack(anchor='w', pady=(4, 0))

    # ------------------------------------------------------------------
    # Candidate management
    # ------------------------------------------------------------------
    def _start_candidate(self) -> None:
        if self.candidate_index >= self.TOTAL_CANDIDATES:
            self._finish_calibration()
            return

        self.current_candidate_votes.clear()
        self.task_index = 0
        self.progress['value'] = self.candidate_index * self.TASKS_PER_CANDIDATE
        self.current_candidate = self._generate_candidate()
        self.current_candidate.apply()
        self.state.set_gesture_history_length(self.current_candidate.history)
        self.camera_handler.initialize_camera()
        self.feedback_label.config(text='')
        self._update_candidate_info()
        shape_name = self.state.shape_names[self.state.shape_index]
        self.shape_label.config(text=f'Shape: {shape_name}')
        self.current_color_box.config(bg=self.state.get_current_color())
        self._refresh_next_color_box()
        self._update_task_label()

    def _generate_candidate(self) -> CandidateSuggestion:
        seed = random.randint(1000, 9999)
        rng = random.Random(seed)
        detection = self._randomise(
            self.base_snapshot.detection,
            delta_range=(0.05, 0.12),
            value_range=(0.15, 0.98),
            rng=rng,
        )
        tracking = self._randomise(
            self.base_snapshot.tracking,
            delta_range=(0.05, 0.12),
            value_range=(0.10, 0.98),
            rng=rng,
        )
        smoothing = self._randomise(
            self.base_snapshot.smoothing,
            delta_range=(0.03, 0.08),
            value_range=(0.01, 0.35),
            rng=rng,
        )
        history = int(
            round(
                self._randomise(
                    float(self.base_snapshot.history),
                    delta_range=(1.0, 2.5),
                    value_range=(3.0, 20.0),
                    rng=rng,
                )
            )
        )
        history = max(1, min(30, history))
        return CandidateSuggestion(detection, tracking, smoothing, history, seed)

    @staticmethod
    def _randomise(
        base: float,
        *,
        delta_range: tuple[float, float],
        value_range: tuple[float, float],
        rng: random.Random,
    ) -> float:
        delta = rng.uniform(*delta_range)
        value = base + rng.choice((-1.0, 1.0)) * delta
        return max(value_range[0], min(value_range[1], value))

    # ------------------------------------------------------------------
    # Task progression
    # ------------------------------------------------------------------
    def _handle_vote(self, is_better: bool) -> None:
        if self.current_candidate is None:
            return

        self.current_candidate_votes.append(1 if is_better else 0)
        if is_better:
            self.positive_votes += 1
            self.feedback_label.config(text='Marked as Better', foreground='#a3be8c')
        else:
            self.negative_votes += 1
            self.feedback_label.config(text='Marked as Worse', foreground='#bf616a')

        self.task_index += 1
        self.progress['value'] = self.candidate_index * self.TASKS_PER_CANDIDATE + self.task_index

        if self.task_index >= self.TASKS_PER_CANDIDATE:
            self._close_candidate()
        else:
            self._update_task_label()
        self._update_score_summary()

    def _close_candidate(self) -> None:
        assert self.current_candidate is not None
        positive = sum(self.current_candidate_votes)
        ratio = positive / self.TASKS_PER_CANDIDATE
        self.candidate_scores.append(ratio)

        keep_candidate = positive >= (self.TASKS_PER_CANDIDATE / 2)
        messagebox.showinfo(
            title=f'Candidate {self.candidate_index + 1} summary',
            message=(
                f'Better votes: {positive} / {self.TASKS_PER_CANDIDATE}\n'
                f'Batch score: {ratio * 100:.1f}%\n'
                f'{"Candidate accepted." if keep_candidate else "Candidate rejected."}'
            ),
            parent=self.root,
        )

        if keep_candidate:
            self.base_snapshot = ConfigSnapshot(
                detection=self.current_candidate.detection,
                tracking=self.current_candidate.tracking,
                smoothing=self.current_candidate.smoothing,
                history=self.current_candidate.history,
            )
        else:
            self.base_snapshot.apply()

        self.candidate_index += 1
        self._start_candidate()

    def _update_candidate_info(self) -> None:
        assert self.current_candidate is not None
        candidate_text = (
            f'Candidate {self.candidate_index + 1} / {self.TOTAL_CANDIDATES}\n'
            f'Seed {self.current_candidate.seed}\n'
            f'Detection {self.current_candidate.detection:.2f}  |  '
            f'Tracking {self.current_candidate.tracking:.2f}\n'
            f'Smoothing {self.current_candidate.smoothing:.2f}  |  '
            f'History {self.current_candidate.history}'
        )
        self.candidate_info.config(text=candidate_text)
        self._update_score_summary()

    def _update_task_label(self) -> None:
        task = TASK_LIBRARY[self.task_index % len(TASK_LIBRARY)]
        self.header_label.config(text=f'Task {self.task_index + 1} of {self.TASKS_PER_CANDIDATE}')
        self.task_title.config(text=task.title)
        self.task_description.config(text=task.description)
        positive = sum(self.current_candidate_votes)
        vote_count = len(self.current_candidate_votes)
        self.candidate_progress_label.config(
            text=(
                f'Better votes this candidate: {positive} / {vote_count}\n'
                f'Worse votes this candidate: {vote_count - positive} / {vote_count}'
            )
        )
        total_tasks = self.candidate_index * self.TASKS_PER_CANDIDATE + self.task_index
        maximum_tasks = self.TOTAL_CANDIDATES * self.TASKS_PER_CANDIDATE
        self.overall_progress_label.config(
            text=f'Overall progress: {total_tasks} / {maximum_tasks}'
        )

    def _update_score_summary(self) -> None:
        overall_votes = self.positive_votes + self.negative_votes
        if overall_votes:
            balance = self.positive_votes - self.negative_votes
            score = max(0.0, min(100.0, 50.0 + (balance / overall_votes) * 50.0))
            self.score_summary_label.config(
                text=(
                    f'Total better votes: {self.positive_votes}, '
                    f'worse: {self.negative_votes}, score: {score:.1f}'
                )
            )
        else:
            self.score_summary_label.config(text='No votes collected yet.')

    def _finish_calibration(self) -> None:
        self.better_button.config(state=tk.DISABLED)
        self.worse_button.config(state=tk.DISABLED)
        overall_score = (
            100.0 * (sum(self.candidate_scores) / len(self.candidate_scores))
            if self.candidate_scores
            else 50.0
        )
        self.base_snapshot.apply()
        self.state.set_gesture_history_length(self.base_snapshot.history)
        settings_message = f'Settings saved to {ENV_PATH.name}.'
        try:
            self.base_snapshot.save()
        except OSError:
            logging.exception('Could not save calibration settings.')
            settings_message = 'Settings could not be saved; see the application log.'
        accepted_candidates = sum(score >= 0.5 for score in self.candidate_scores)
        messagebox.showinfo(
            title='Calibration complete',
            message=(
                'Calibration completed.\n'
                f'Accepted candidates: {accepted_candidates} / {self.TOTAL_CANDIDATES}\n'
                f'Final calibration score: {overall_score:.1f}\n'
                f'{settings_message}'
            ),
            parent=self.root,
        )
        self.progress['value'] = self.TOTAL_CANDIDATES * self.TASKS_PER_CANDIDATE
        self.overall_progress_label.config(text='Overall progress: completed')
        self._update_score_summary()
        self.camera_handler.initialize_camera()

    # ------------------------------------------------------------------
    # Camera + gesture loop
    # ------------------------------------------------------------------
    def _update_loop(self) -> None:
        if self._is_closing:
            return
        camera_output = self.camera_handler.process_frame()
        self._draw_video(camera_output)
        self._process_gestures(camera_output)
        self._update_view()
        self._update_job = self.root.after(self.UPDATE_INTERVAL_MS, self._update_loop)

    def _draw_video(self, camera_output: CameraOutput) -> None:
        if camera_output.frame is None:
            self._video_photo = None
            self.video_label.config(text='Camera unavailable', image='')
            return
        frame_rgb = cv2.cvtColor(camera_output.frame, cv2.COLOR_BGR2RGB)
        self._video_photo = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
        self.video_label.config(image=self._video_photo, text='')

    def _process_gestures(self, camera_output: CameraOutput) -> None:
        active_gesture = self.state.record_gesture(camera_output.gesture)
        if camera_output.gesture in NON_GESTURE_SIGNALS:
            self.gesture_label.config(text=f'Gesture: {camera_output.gesture.value}')
            return
        self.gesture_label.config(text=f'Gesture: {active_gesture.value}')

        if active_gesture is Gesture.OPEN_HAND and camera_output.coords:
            target_y = (camera_output.coords[0] - 0.5) * -360
            target_x = (camera_output.coords[1] - 0.5) * 180
            self.state.target_angle_y = target_y
            self.state.target_angle_x = target_x

        if active_gesture != self.state.last_action_gesture:
            handler = {
                Gesture.POINTING: self._handle_color_change,
                Gesture.THUMBS_UP: self._handle_shape_change,
                Gesture.VICTORY: self._handle_view_reset,
                Gesture.FIST: self._handle_rotation_stop,
            }.get(active_gesture)
            if handler:
                handler()
            self.state.last_action_gesture = active_gesture

    def _update_view(self) -> None:
        smoothing = ANIMATION_CONFIG.smoothing_factor
        self.state.angle_x += (self.state.target_angle_x - self.state.angle_x) * smoothing
        self.state.angle_y += (self.state.target_angle_y - self.state.angle_y) * smoothing
        self.view_3d.draw(self.state)
        self.canvas.draw()  # type: ignore[no-untyped-call]

    # ------------------------------------------------------------------
    # Gesture helpers
    # ------------------------------------------------------------------
    def _handle_color_change(self) -> None:
        self.state.next_color()
        self.current_color_box.config(bg=self.state.get_current_color())
        self._refresh_next_color_box()

    def _handle_shape_change(self) -> None:
        self.state.next_shape()
        shape_name = self.state.shape_names[self.state.shape_index]
        self.shape_label.config(text=f'Shape: {shape_name}')

    def _handle_view_reset(self) -> None:
        self.state.target_angle_x, self.state.target_angle_y = 30.0, 45.0

    def _handle_rotation_stop(self) -> None:
        self.state.target_angle_x = self.state.angle_x
        self.state.target_angle_y = self.state.angle_y

    def _refresh_next_color_box(self) -> None:
        next_idx = (self.state.color_index + 1) % len(self.state.colors)
        self.next_color_box.config(bg=self.state.colors[next_idx])

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def _on_close(self) -> None:
        if messagebox.askyesno('Exit calibration', 'Stop calibration and close?', parent=self.root):
            self._is_closing = True
            if self._update_job is not None:
                self.root.after_cancel(self._update_job)
                self._update_job = None
            self.base_snapshot.apply()
            self.camera_handler.release()
            plt.close(self.fig)
            self.root.destroy()


def calibrate() -> None:
    app = CalibrationApp()
    app.root.mainloop()


if __name__ == '__main__':  # pragma: no cover - manual helper
    calibrate()
