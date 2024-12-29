"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from rxconfig import config
from typing import List, Tuple
import asyncio
import os
import pathlib
import at25
from at25 import WALL, FIRST, CHANCE, EMPTY, DELETED, DEALER

udir = rx.get_upload_dir()
print(udir, type(udir))

conf_yaml = "config_default.yaml"
conf_path = os.path.join(udir, "config_default.yaml")
save_path = os.path.join(udir, "csvs")
game = at25.Attack25(conf_path, save_path)

print("FROM AT25")
print(game.get_player_names())
print(game.get_player_colors())

RED = 1
GREEN = 2
WHITE = 3
BLUE = 4

COLORS = {
    EMPTY: "#7F7F7FFF", 
    WALL: "#000000FF", 
    FIRST: "#7F7F7FFF", 
    CHANCE: "#FFFF00FF",
}
COLORS = COLORS | game.get_player_colors()
PLAYERS = game.get_player_ids()
n_players = game.get_n_players()

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
    # RED: "color1.wav", 
    # GREEN: "color2.wav", 
    # WHITE: "color3.wav",
    # BLUE: "color4.wav",
    }
AUDIOFILES = AUDIOFILES | {i: f"color{i}.wav" for i in PLAYERS}

n_row = game.get_n_row()
n_col = game.get_n_col()

panels_height = 75
panels_width = panels_height * (16 / 9)

height = panels_height / n_row
width = panels_width / n_col
n_panels =  n_row * n_col
font_height = height // 2

panels_list = list(range(n_panels))
game_player_names = game.get_player_names()

class SelectState(rx.State):
    value: str = ""
    choices: list[str] = sorted((rx.get_upload_dir() / pathlib.Path(("csvs"))).glob('*.csv'))
    @rx.event
    def change_value(self, value: str):
        """Change the select value var."""
        self.value = value
        print("from change value: ", self.value)

    @rx.event
    def load_game_state(self):
        game.load_state(self.value)
        print(game.board.board)

class PanelsState(rx.State):
    # 25 # game states
    panels = [EMPTY for _ in range(n_panels)]
    points = {p: 0 for p in PLAYERS}
    colors = [COLORS[panel] for panel in panels]
    visible = ["visible" for _ in range(n_panels)]

    # 25
    denied_panels = [True for _ in range(n_panels)]
    audios = ["" for _ in range(n_panels)]
    playing = [False for _ in range(n_panels)]

    # 4 FIXED?
    player_names: dict[int, str] = game_player_names

    # 1
    player: int = EMPTY
    winner: int = EMPTY
    deny_player_button = False
    set_at_chance = False
    # deny_panel_button = True
    # white_playing = [False for _ in range(n_panels)]
    # red_playing = [False for _ in range(n_panels)]

    @rx.event
    def load_state(self):
        tmp_panels = game.get_board_panels()
        for i in range(n_panels):
            self.panels[i] = tmp_panels[i]
        for p in PLAYERS:
            self.points[p] = self.panels.count(p)
        for i, panel in enumerate(self.panels):
            self.colors[i] = COLORS[panel]
        for i in range(n_panels):
            self.denied_panels[i] = True
            self.audios[i] = ""
            self.playing[i] = False

        self.player = EMPTY
        self.winner = EMPTY
        self.deny_player_button = False
        self.set_at_chance = False


    def set_winner(self, i):
        self.winner = i
        print("from set_winner: winner:", i, self.player_names[i])

    @rx.event
    def set_player(self, p):
        self.player = p

        if p in PLAYERS:
            self.deny_player_button = False
            for i in range(n_panels):
                self.denied_panels[i-1] = True
            selectable_panels = game.get_selectable_panels(p)
            for i in selectable_panels:
                self.denied_panels[i] = False
            for i in range(n_panels):
                self.audios[i] = AUDIOFILES[self.player]
            # get selectable panels from game
            print("from set_player: selectable panels:", 
                  [int(i + 1) for i in selectable_panels])
            # set denied panels
            print("from set_player: current player:", self.player)
            print(self.denied_panels)
        elif p == DEALER:
            # move to select winner
            pass
        else:
            self.deny_player_button = False
            for i in range(n_panels):
                self.denied_panels[i] = True

    @rx.event
    async def delete_panels(self):
        if self.winner not in PLAYERS:
            return
        panels_to_delete = game.get_player_panels(self.winner)
        for i in panels_to_delete:
            self.visible[i] = "collapse"
            yield
            await asyncio.sleep(0.5)
            print("changed_panel:", i + 1)
        await asyncio.sleep(2.0)
        
    @rx.event
    async def set_panel(self, panel_idx):
        if self.player not in PLAYERS:
            return

        elif self.set_at_chance:
            print("atchance")
            for i in range(n_panels):
                self.denied_panels[i] = True
            yield
            self.panels[panel_idx] = CHANCE
            self.colors[panel_idx] = COLORS[CHANCE]
            game.set_at_chance(panel_idx)
            for p in PLAYERS:
                self.points[p] = self.panels.count(p)
            self.set_at_chance = False
            # await asyncio.sleep(0.5)

        else:
            self.deny_player_button = True
            # self.deny_panel_button = True
            for i in range(n_panels):
                self.denied_panels[i] = True
            yield

            selectable_panels = game.get_selectable_panels(self.player)
            if panel_idx not in selectable_panels:
                print("from set_panel: unselectable: ", panel_idx)

            else:
                is_at_chance = game.is_atchance()
                panels_to_flip = game.to_get_panels(panel_idx, self.player)
                for i in panels_to_flip:
                    self.panels[i] = self.player
                    # self.audios[i] = AUDIOFILES[self.player]
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

                ## IF NOW IS ATCHANCE, SET CHANCE PANEL
                if is_at_chance:
                    for i in range(n_panels):
                        if self.panels[i] != EMPTY:
                            self.denied_panels[i] = False
                    yield
                    self.set_at_chance = True
                    return
                    #todo

        for i in range(n_panels):
            self.playing[i] = False
        self.player = EMPTY
        yield

        self.deny_player_button = False
        # self.deny_panel_button = True
        for i in range(n_panels):
            self.denied_panels[i] = True
        yield
        ## IF NEXT IS ATCHANCE, RING BELL

        ## IF 
        print(game.get_board_panels)
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

z_ripple = 100
z_panels = 5

def myripple():
    return {
                "@keyframes ripple": {
                "0%": {"box-shadow": f"0 0 0 0 #FFC700FF"},
                "70%": {"box-shadow": f"0 0 0 20px #FFC70000"},
                "100%": {"box-shadow": f"0 0 0 0 #FFC70000"},
                # "z-index": z_ripple,
                # "position": "relative",
                },
                "animation": "ripple 2s infinite",
                "z-index": z_ripple,
            }
def mydefaultborder(color):
    return {"border": f"1vh solid {color}"}

def myblinkborder(color):
    return {
                f"@keyframes blinkBorder{color[1:]}": {
                "0%": {"border": f"1vh solid {color}"},
                "100%": {"border": f"1vh solid {color[:-2]}00"},
                },
                "animation": f"blinkBorder{color[1:]} 0.5s ease infinite alternate"
            }
def myblinkcolor(color):
    return {
                f"@keyframes blinkColor{color[1:]}": {
                "0%": {"color": f"{color}"},
                "30%": {"color": f"{color}"},
                "100%": {"color": "#000000FF"},
                },
                "animation": f"blinkColor{color[1:]} 1s ease infinite"
            }
def mydefaultcolor(color):
    return {"color": f"{color}"}

# @keyframes blinkBorder {
#   0% {
#     border: 6px solid #cc2200;
#   }
#   100% {
#     border: 6px solid #efefef;
#   }
# }
# .btn {
#   animation: blinkBorder 1s ease infinite alternate;
# }

def index() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.select(
                SelectState.choices,
                value=SelectState.value,
                on_change=SelectState.change_value,
            ),
            rx.button(
                SelectState.value,
                on_click=[
                    SelectState.load_game_state(),
                    PanelsState.load_state(),
                ]
            ),
            rx.text(
                "Click right to set winner",
            ),
            rx.foreach(
                ForeachPlayerState.players,
                lambda i: rx.button(
                    PanelsState.player_names[i],
                    on_click=PanelsState.set_winner(i),
                ),
            ),
        ),
        rx.button(
            "Click Me to set video",
             _hover={
                "color": "red",
                "background-position": "right center",
                "background-size": "200%" + " auto",
                "-webkit-animation2": "pulse 2s infinite",
            },
            on_click=BackgroundState.show_video(),
        ),
        rx.button(
            "Click Me to delete_panels",
             _hover={
                "color": "red",
                "background-position": "right center",
                "background-size": "200%" + " auto",
                "-webkit-animation2": "pulse 2s infinite",
            },
            on_click=PanelsState.delete_panels(),
        ),
        rx.button(
            "Click Me to play video",
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
                        # color="black",
                        style=rx.cond(
                            PanelsState.denied_panels[i],
                            mydefaultcolor("#000000FF"),
                            myblinkcolor(ColorsState.colors[PanelsState.player]),
                        ),
                        # _enabled=myblinkcolor(),
                        # radius="none",
                        border_style="solid",
                        border_width="0.1vh",
                        border_color="#000000FF",
                        height=rx.Var.to_string(height)+ "vh",
                        background_color=PanelsState.colors[i],
                        visibility=PanelsState.visible[i],
                        font_size=rx.Var.to_string(font_height)+ "vh",
                        text_align="center",
                        on_click=PanelsState.set_panel(i),
                        disabled=PanelsState.denied_panels[i].bool(),
                        z_index=z_panels,
                    ),
                ),
                columns=rx.Var.to_string(n_col),
                spacing="0",
                width=rx.Var.to_string(panels_width) + "vh",
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
            width="100%",
        ),
        rx.hstack(
            rx.foreach(
                ForeachPlayerState.players,
                lambda i: rx.button(
                    PanelsState.points[i].to_string(use_json=False),
                    # border_style="solid",
                    # border_width="1vh",
                    # border_color=ColorsState.colors[i],
                    # _enabled=[
                    #     myripple(),
                    #     myblinkborder(ColorsState.colors[i]),
                    # ],
                    # style=myblinkborder(ColorsState.colors[i]),
                    # rx.cond(
                    # PanelsState.player == i,
#                   style=mydefaultborder(ColorsState.colors[i]),
                    #)
                    # style=mydefaultborder(ColorsState.colors[i]),
                    style=rx.cond(
                        PanelsState.player == i,
                        myblinkborder(ColorsState.colors[i]),
                        mydefaultborder(ColorsState.colors[i]),
                    ),
                    # _enabled=myblinkborder(ColorsState.colors[i]),
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
        rx.hstack(
            rx.foreach(
                PanelsState.audios,
                lambda a, i: rx.audio(
                    # url=PanelsState.audios[i], # error
                    # url=PanelsState.audios[i].to_string(),
                    url=rx.get_upload_url(a.to_string(use_json=False)),
                    controls=False,
                    visibility="collapse",
                    width="10px",
                    height="10px",
                    playing=PanelsState.playing[i].bool(),
                ),
            ),
        ),
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
