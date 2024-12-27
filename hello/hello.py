"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from rxconfig import config
from typing import List, Tuple
import asyncio

udir = rx.get_upload_dir()
print(udir, type(udir))

filename = "red.wav"
import os
import pathlib
print(os.getcwd())
filepath = pathlib.Path(os.path.join("./assets", filename))
print(filepath, type(filepath))
upload_path = pathlib.Path(os.path.join(udir, filename))
print(upload_path, type(upload_path))
with open(filepath, "rb") as f:
    fileb = f.read()
    upload_path.write_bytes(fileb)

EMPTY = 0
WALL = -1
FIRST = -2
RED = 1
GREEN = 2
WHITE = 3
BLUE = 4

COLORS = {
    EMPTY: "gray", 
    WALL: "black", 
    FIRST: "gray", 

    RED: "red", 
    GREEN: "green",
    WHITE: "white",
    BLUE: "blue",
    }

PLAYERS = [RED, WHITE]
n_players = len(PLAYERS)
class ForeachPlayerState(rx.State):
    players: list[int] = PLAYERS

class ColorsState(rx.State):
    colors: dict[int, str] = {p: COLORS[p] for p in PLAYERS}

VTRQ_MP4 = "vtrq_sample.mp4"
VTRQ_LASTPIC = "lastpic_sample.jpg"

AUDIOFILES = {
    EMPTY: "gray.wav", 
    WALL: "gray.wav", 
    FIRST: "gray.wav", 
    RED: "red.wav", 
    GREEN: "green.wav", 
    WHITE: "white.wav",
    BLUE: "blue.wav",
    }

n_col = 5
n_row = 5
height = 15

n_panels =  n_col * n_row
width = height * (16 / 9)
font_height = height // 2
panels_height = n_col * height
panels_width = n_row * width


panels_list = list(range(n_panels))
import random
random.seed(1)
random.shuffle(panels_list)
 
def get_audioidx(i, color):
    if i not in range(n_panels):
        return None
    if color in {EMPTY, WALL, FIRST}:
        return None
    return i + (color - 1) * n_panels

class PointsState(rx.State):
    points = {p: 0 for p in PLAYERS}

    @rx.event
    def set_point(self, player, point):
        self.points[player] = point

class PanelsState(rx.State):
    player = EMPTY
    panels = [EMPTY for _ in range(n_panels)]
    colors = [COLORS[panel] for panel in panels]
    audios = [pathlib.Path('red.wav') for _ in range(n_panels)]
    playing = [False for _ in range(n_panels)]
    points = {p: 0 for p in PLAYERS}

    deny_player_button = False
    deny_panel_button = True
    # white_playing = [False for _ in range(n_panels)]
    # red_playing = [False for _ in range(n_panels)]

    @rx.event
    def set_player(self, p):
        self.player = p
        if p in PLAYERS:
            self.deny_player_button = False
            self.deny_panel_button = False
            print("from set_player: current player:", self.player)
        else:
            self.deny_player_button = False
            self.deny_panel_button = True
            print("from set_player: current player:", self.player)


    @rx.event
    async def set_panel(self, panel_idx):
        if self.player not in PLAYERS:
            return
        
        self.deny_player_button = True
        self.deny_panel_button = True
        yield

        for i in range(panel_idx, n_panels):
            self.panels[i] = self.player
            self.audios[i] = AUDIOFILES[self.player]
            self.colors[i] = COLORS[self.player]
            self.playing[i] = True
            for p in PLAYERS:
                self.points[p] = self.panels.count(p)
            yield
            await asyncio.sleep(0.5)
            print("changed_panel:", i + 1)
            print("from playing:", self.playing)
            print("from set_panel:", panel_idx)
            print(self.audios)
        await asyncio.sleep(2.0)

        for i in range(n_panels):
            self.playing[i] = False
        self.player = EMPTY

        self.deny_player_button = False
        self.deny_panel_button = True
        yield
        print("from set_panel: current player:", self.player)

print(PanelsState.audios[0].to_string())
print(PanelsState.playing[0].bool())
print(PanelsState.colors[0])
print(PanelsState.audios[0])

# def myaudio_dynamic():
#     return rx.foreach(
#         rx.Var.range(n_panels),
#         lambda i: rx.audio(
#             # url=PanelsState.audios[i], # error
#             # url=PanelsState.audios[i].to_string(),
#             url=PanelsState.audios[i].to_string(), 
#             controls=True,
#             playing=PanelsState.playing[i].bool(),
#         ),
#     ),

# def myaudio(color):
#     return rx.foreach(
#         rx.Var.range(n_panels),
#         lambda i: rx.audio(
#             url=AUDIOFILES[color],
#             controls=False,
#             playing=PanelsState.playing[i + n_panels * (color - 1)].bool(),
#         ),
#     ),

class CountState(rx.State):
    count: int = 0

    @rx.event
    def increment(self):
        self.count += 1

    @rx.event
    def decrement(self):
        self.count -= 1


def counter():
    return rx.flex(
        rx.button(
            "Decrement",
            color_scheme="red",
            on_click=CountState.decrement,
            disabled=True,
        ),
        rx.heading(CountState.count),
        rx.button(
            "Increment",
            color_scheme="grass",
            on_click=CountState.increment,
        ),
        spacing="3",
    )
class FlexState(rx.State):
    width_str = "80%"

BG_HIDDEN=101
BG_SHOW=102
BG_LASTPIC=103
class BackgroundState(rx.State):
    bg = BG_HIDDEN
    
    @rx.event
    def show_video(self):
        self.bg = BG_SHOW
        yield
    @rx.event
    def show_lastpic(self):
        self.bg = BG_LASTPIC
        yield

class VideoPlayingState(rx.State):
    playing: bool = False

    @rx.event
    def start_playing(self):
        self.playing: bool = True
    @rx.event
    def stop_playing(self):
        self.playing: bool = False

class VisibleState(rx.State):
    is_visible: bool = False  # Controls button visibility

    def toggle_visibility(self):
        self.is_visible = not self.is_visible

        
def myripple():
    return {
                "@keyframes ripple": {
                "0%": {"box-shadow": "0 0 0 0 #1B85FB"},
                "70%": {"box-shadow": "0 0 0 20px rgb(27 133 251 / 0%)"},
                "100%": {"box-shadow": "0 0 0 0 rgb(27 133 251 / 0%)"},
                },
                "animation": "ripple 2s infinite"
            }

def index() -> rx.Component:
    return rx.vstack(
        counter(),

        rx.button(
            "Button Text",
            background_color="transparent"
        ),

        # Using rgba with 0 opacity
        rx.button(
            "Button Text", 
            background_color="rgba(0,0,0,0)"
        ),
        rx.vstack(
                rx.button("Toggle", on_click=VisibleState.toggle_visibility),
                rx.cond(
                    VisibleState.is_visible,
                    rx.button("Hidden Button"),  # Shown when is_visible is True
                    rx.text(""),  # Shown when is_visible is False
                ),
        ),
        rx.box(
            "Animated Content",
            style={
                "@keyframes example": {
                    "0%": {"opacity": 0},
                    "100%": {"opacity": 1}
                },
                "animation": "example 2s infinite"
            },
            _hover=myripple()
        ),
        rx.flex(
            rx.grid(
                rx.foreach(
                    rx.Var.range(9),
                    lambda i: rx.button(
                        f"{i + 1}", 
                    ),
                ),
                columns="3",
                spacing="0",
                width="90%",
                z_index=5,
            ),
        ),
        rx.button(
            "Hover Me to set video",
             _hover={
                "color": "red",
                "background-position": "right center",
                "background-size": "200%" + " auto",
                "-webkit-animation2": "pulse 2s infinite",
            },
            on_click=BackgroundState.show_video(),
        ),
        rx.button(
            "Hover Me to play video",
             _hover={
                "color": "red",
                "background-position": "right center",
                "background-size": "200%" + " auto",
                "-webkit-animation2": "pulse 2s infinite",
            },
            on_click=VideoPlayingState.start_playing(),
        ),
        rx.center(
            rx.grid(
                rx.foreach(
                    rx.Var.range(n_panels),
                    lambda i: rx.button(
                        f"{i + 1}", 
                        color="black",
                        _enabled=myripple(),
                        height=rx.Var.to_string(height)+ "vh",
                        background_color=PanelsState.colors[i],
                        # background_color="transparent",
                        # hidden=True,
                        font_size=rx.Var.to_string(font_height)+ "vh",
                        text_align="center",
                        on_click=PanelsState.set_panel(i),
                        disabled=PanelsState.deny_panel_button.bool(),

                    ),
                ),
                columns=rx.Var.to_string(n_col),
                spacing="0",
                width=rx.Var.to_string(panels_width) + "vh",
                z_index=5,
            ),
            rx.cond(
                BackgroundState.bg == BG_HIDDEN,
                rx.box(
                    width=rx.Var.to_string(panels_width) + "vh",
                    height=rx.Var.to_string(panels_height) + "vh",
                    background_color="transparent",
                    position="absolute",
                    # top="40px",
                    # left="40px",
                    z_index=3,
                ),
                rx.cond(
                    BackgroundState.bg == BG_SHOW,
                    rx.video(
                        url=rx.get_upload_url(VTRQ_MP4),
                        width=rx.Var.to_string(panels_width) + "vh",
                        height=rx.Var.to_string(panels_height) + "vh",
                        position="absolute",
                        controls=False,
                        playing=VideoPlayingState.playing.bool(),
                        on_ended=[
                            BackgroundState.show_lastpic()
                        ],
                        z_index=2,
                    ),
                    rx.image(
                        src=rx.get_upload_url(VTRQ_LASTPIC),
                        width=rx.Var.to_string(panels_width) + "vh",
                        height=rx.Var.to_string(panels_height) + "vh",
                        position="absolute",
                        z_index=3,
                    ),


                ),
            ),
            # rx.video(
            #     # url="https://drive.google.com/file/d/1pW_TSjvkKC7BuUN4dj9wKCphqGqcYzWe/",
            #     # url="https://drive.google.com/file/d/1pW_TSjvkKC7BuUN4dj9wKCphqGqcYzWe/view?usp=drive_link",
            #     url="https://www.youtube.com/embed/VcZ_Kt6Dwb4",
            #     width="400px",
            #     height="auto",
            #     # url="/vtrq_sample.mp4",
            #     # width="90%",
            #     # height=rx.Var.to_string(panels_height) + "vh",
            #     # position="absolute",
            #     controls=False,
            #     playing=VideoPlayingState.playing.bool(),
            #     on_ended=VideoPlayingState.stop_playing(),
            #     # z_index=20,
            # ),
            rx.box(
                width=rx.Var.to_string(panels_width) + "vh",
                height=rx.Var.to_string(panels_height) + "vh",
                background_color="transparent",
                position="absolute",
                # top="40px",
                # left="40px",
                z_index=2,
            ),
            # rx.box(
            #     width="90%",
            # ),
            # rx.logo(),
            width="100%",
        ),
        rx.hstack(
            rx.foreach(
                ForeachPlayerState.players,
                lambda i: rx.button(
                    PanelsState.points[i].to_string(use_json=False),
                    border_style="solid",
                    border_width="1vh",
                    border_color=ColorsState.colors[i],
                    _enabled=myripple(),
                    height=rx.Var.to_string(height)+ "vh",
                    width=rx.Var.to_string(height)+ "vh",
                    background_color="black",
                    color="white",
                    font_size=rx.Var.to_string(font_height)+ "vh",
                    text_align="center",
                    # position="absolute",
                    # top="40px",
                    # left="40px",
                    z_index=1,
                    on_click=PanelsState.set_player(i),
                    disabled=PanelsState.deny_player_button.bool(),
                ),
            ),
            justify="center",
            spacing="9",
            width="100%",
            z_index=5,

        ),
        # rx.button(
        #     PanelsState.points[WHITE].to_string(use_json=False),
        #     _enabled=myripple(),
        #     height=rx.Var.to_string(height)+ "vh",
        #     width=rx.Var.to_string(player_width)+ "vh",
        #     background_color="white",
        #     color="black",
        #     font_size=rx.Var.to_string(font_height)+ "vh",
        #     text_align="center",
        #     # position="absolute",
        #     # top="40px",
        #     # left="40px",
        #     z_index=1,
        #     on_click=PanelsState.set_player(WHITE),
        #     disabled=PanelsState.deny_player_button.bool(),
        # ),
        # rx.button(
        #     width="10%",
        #     height="10vh",
        #     _enabled=myripple(),
        #     background_color="red",
        #     # position="absolute",
        #     # top="40px",
        #     # left="40px",
        #     z_index=1,
        #     on_click=PanelsState.set_player(RED),
        #     disabled=PanelsState.deny_player_button.bool(),
        # ),
        # myaudio(),
        rx.grid(
            rx.foreach(
                PanelsState.audios,
                lambda a, i: rx.audio(
                    # url=PanelsState.audios[i], # error
                    # url=PanelsState.audios[i].to_string(),
                    url=rx.get_upload_url(a.to_string(use_json=False)),
                    controls=False,
                    playing=PanelsState.playing[i].bool(),
                ),
            ),
        )
        # rx.foreach(
        #     rx.Var.range(n_panels),
        #     lambda i: rx.audio(
        #         url="/red.wav",
        #         controls=False,
        #         playing=PanelsState.playing[i + n_panels * (RED - 1)].bool(),
        #     ),
        # ),
        # rx.foreach(
        #     rx.Var.range(n_panels),
        #     lambda i: rx.audio(
        #         url="/red.wav",
        #         controls=False,
        #         playing=PanelsState.red_playing[i].bool(),
        #     ),
        # ),
    )

app = rx.App()
app.add_page(index)
