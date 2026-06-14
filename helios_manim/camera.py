"""Camera zoom helpers for the "big graph, then zoom into a part" beat.

Works with manim's :class:`MovingCameraScene`: the camera *frame* is itself a
Mobject, so zooming is just animating its ``width`` and ``center``. These helpers
compute the right target so a chosen region lands fully on-screen at the correct
aspect, padded by :data:`STYLE.frame_margin`.

Typical use::

    class Demo(MovingCameraScene):
        def construct(self):
            pipe = Pipeline.from_topology(...)   # auto-fitted, zoomed out
            self.add(pipe)
            self.play(focus(self.camera, [pipe.nodes["a"], pipe.nodes["b"]]))
            self.play(reset(self.camera))
"""

from __future__ import annotations

import numpy as np
from manim import ORIGIN, VGroup, config

from .style import STYLE


def region_of(mobjects, margin: float = STYLE.frame_margin):
    """Padded bounding box of ``mobjects`` as ``(center, width, height)``."""
    group = VGroup(*mobjects)
    center = group.get_center()
    width = group.width + 2 * margin
    height = group.height + 2 * margin
    return center, width, height


def focus(camera, mobjects, margin: float = STYLE.frame_margin):
    """Animate the camera frame to contain ``mobjects`` at the frame aspect.

    Returns an animation for ``self.play(...)``. The target width is chosen so
    the (padded) region fits whether it's wide or tall::

        target_w = max(bbox_w, bbox_h * frame_aspect) + 2*margin
    """
    center, _, _ = region_of(mobjects, margin=0.0)
    group = VGroup(*mobjects)
    aspect = config.frame_width / config.frame_height
    target_w = max(group.width, group.height * aspect) + 2 * margin
    return camera.frame.animate.move_to(center).set_width(target_w)


def reset(camera):
    """Animate the camera frame back to the full default frame, centred."""
    return camera.frame.animate.move_to(ORIGIN).set_width(config.frame_width)
