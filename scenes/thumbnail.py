"""YouTube thumbnail in the video's visual style.

    .venv/bin/python -m tools.thumbnail      # -> output/thumbnail.png (1920x1080) + .jpg (1280x720)
"""
from agentic_video.prelude import *

TITLE, SUBTITLE, BYLINE = "Agentic AI", "Introduction", "by anon14none"


class Thumbnail(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ---- text only: title / subtitle / byline, centred, clear hierarchy
        title = Text(TITLE, font=EN_FONT, font_size=88, weight="MEDIUM", color=FG)
        sub = Text(SUBTITLE, font=EN_FONT, font_size=40, weight="LIGHT", color=FG)
        by = Text(BYLINE, font=EN_FONT, font_size=24, weight="LIGHT", color=MUTED)
        stack = VGroup(title, sub, by).arrange(DOWN, buff=0.45)
        stack[2].shift(DOWN * 0.35)                       # a little extra air before the credit
        stack.move_to(ORIGIN)
        self.add(stack)
