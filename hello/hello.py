"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from rxconfig import config
from typing import List, Tuple
import asyncio
import os
import pathlib
import at25
from at25 import WALL, FIRST, CHANCE, EMPTY, DELETED, DEALER
import hashlib, secrets

def delete_oldcsvs(path_to_save):

    # ディレクトリ内のCSVファイルを特定ファイルを除いて取得し、更新日時順にソート
    except_csv_files = ["aat25_init.csv",]
    csv_files = [
        os.path.join(path_to_save, f)
        for f in os.listdir(path_to_save)
        if f.endswith(".csv") and f not in except_csv_files
    ]
    csv_files.sort(key=os.path.getmtime, reverse=True)

    # 最新100個以外のファイルを削除
    files_to_delete = csv_files[100:]  # 100個目以降のファイル
    for file in files_to_delete:
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except Exception as e:
            print(f"Error deleting {file}: {e}")

    print(f"{except_csv_files}を除く古いCSVファイルの削除が完了しました。")

udir = rx.get_upload_dir()
conf_yaml = "config_default.yaml"
csvs_dir = "csvs"
conf_path = os.path.join(udir, conf_yaml)
save_path = os.path.join(udir, csvs_dir)

delete_oldcsvs(save_path)

class AT25(rx.Base):
    game: at25.Attack25

class GameState(rx.State):
    game_state: AT25 = AT25(
        game = at25.Attack25(conf_path, save_path)
    )

    n_row = game_state.game.get_n_row()
    n_col = game_state.game.get_n_col()

    panels_height = 75
    panels_width = panels_height * (16 / 9)

    height = panels_height / n_row
    width = panels_width / n_col
    n_panels =  n_row * n_col
    font_height = height // 2

    panels_list = list(range(n_panels))
    game_player_names = game_state.game.get_player_names()

    players: list[int] = game_state.game.get_player_ids()
    
    colors = {
        EMPTY: "#7F7F7FFF", 
        WALL: "#000000FF", 
        FIRST: "#7F7F7FFF", 
        CHANCE: "#FFFF00FF",
    } | game_state.game.get_player_colors()

    audiofiles = {
        EMPTY: "gray.mp3", 
        WALL: "gray.mp3", 
        FIRST: "gray.mp3", 
        } | {i: f"color{i}.mp3" for i in players}

    VTRQ_FIRSTPIC = "lastpic_sample.jpg" 
    VTRQ_MP4 = "vtrq_sample.mp4"
    VTRQ_LASTPIC = "lastpic_sample.jpg"

    selected_value: str = ""
    select_choices: list[str] = sorted((rx.get_upload_dir() / pathlib.Path(("csvs"))).glob('*.csv'))

    panels = [EMPTY for _ in range(n_panels)]
    points = {p: 0 for p in players}

    panel_colors = list()
    for panel in panels:
        panel_colors.append(colors[panel])

    visible = ["visible" for _ in range(n_panels)]

    @rx.event
    def change_value(self, value: str):
        """Change the select value var."""
        self.selected_value = value
        print("from change value: ", self.selected_value)

    @rx.event
    def get_board_panels(self):
        return self.game_state.game.get_board_panels()
    def get_player_colors(self):
        return self.game_state.game.get_player_colors()
    def get_player_ids(self):
        return self.game_state.game.get_player_ids()

    # 25
    denied_panels = [True for _ in range(n_panels)]

    # hard_coded
    n_audios = 7
    audios = ["" for _ in range(n_audios)]
    playing = [False for _ in range(n_audios)]

    # 4 FIXED?
    player_names: dict[int, str] = game_player_names

    # 1
    player: int = EMPTY
    winner: int = EMPTY
    deny_player_button = False
    set_at_chance = False

    @rx.event
    def load_state(self):
        self.game_state.game.load_state(self.selected_value)
        tmp_panels = self.game_state.game.get_board_panels()
        for i in range(self.n_panels):
            self.panels[i] = tmp_panels[i]
        for p in self.players:
            self.points[p] = self.panels.count(p)
        for i, panel in enumerate(self.panels):
            self.panel_colors[i] = self.colors[panel]
        for i in range(self.n_panels):
            self.denied_panels[i] = True
        for i in range(self.n_audios):
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

        if p in self.players:
            self.deny_player_button = False
            for i in range(self.n_panels):
                self.denied_panels[i-1] = True
            selectable_panels = self.game_state.game.get_selectable_panels(p)
            for i in selectable_panels:
                self.denied_panels[i] = False
            for i in range(self.n_audios):
                self.audios[i] = self.audiofiles[self.player]
            # get selectable panels from game
            print("from set_player: selectable panels:", 
                  [int(i + 1) for i in selectable_panels])
            # set denied panels
            print("from set_player: current player:", self.player)
            print(self.denied_panels)
        elif p == DEALER:
            # todo: move to select winner
            pass
        else:
            self.deny_player_button = False
            for i in range(self.n_panels):
                self.denied_panels[i] = True

    @rx.event
    async def delete_panels(self):
        if self.winner not in self.players:
            return
        panels_to_delete = self.game_state.game.get_player_panels(self.winner)
        for i in panels_to_delete:
            self.visible[i] = "collapse"
            yield
            await asyncio.sleep(0.5)
            print("changed_panel:", i + 1)
        await asyncio.sleep(2.0)
        
    @rx.event
    async def set_panel(self, panel_idx):
        if self.player not in self.players:
            return

        elif self.set_at_chance:
            print("atchance")
            for i in range(self.n_panels):
                self.denied_panels[i] = True
            yield
            self.panels[panel_idx] = CHANCE
            self.panel_colors[panel_idx] = self.colors[CHANCE]
            self.game_state.game.set_at_chance(panel_idx)
            for p in self.players:
                self.points[p] = self.panels.count(p)
            self.set_at_chance = False

        else:
            self.deny_player_button = True
            for i in range(self.n_panels):
                self.denied_panels[i] = True
            yield

            selectable_panels = self.game_state.game.get_selectable_panels(self.player)
            if panel_idx not in selectable_panels:
                print("from set_panel: unselectable: ", panel_idx)

            else:
                is_at_chance = self.game_state.game.is_atchance()
                panels_to_flip = self.game_state.game.to_get_panels(panel_idx, self.player)
                for a_i, i in enumerate(panels_to_flip):
                    self.panels[i] = self.player
                    self.panel_colors[i] = self.colors[self.player]
                    self.playing[a_i % self.n_audios] = False
                    yield
                    self.playing[a_i % self.n_audios] = True
                    for p in self.players:
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
                    for i in range(self.n_panels):
                        if self.panels[i] != EMPTY:
                            self.denied_panels[i] = False
                    yield
                    self.set_at_chance = True
                    return
                    #todo

        for i in range(self.n_audios):
            self.playing[i] = False
        self.player = EMPTY
        yield

        self.deny_player_button = False
        for i in range(self.n_panels):
            self.denied_panels[i] = True
        yield
        ## IF NEXT IS ATCHANCE, RING BELL

        ## IF 
        print(self.game_state.game.get_board_panels)
        print("from set_panel: current player:", self.player)

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

class LoginState(rx.State):
    PASS_HEX_DIGEST = 'b1fab726a375cb2d0e0c5321d35bbfdae5eb76e6'
    SALT = 'sa-10!'
    SUCCESS = "Successful Login!"
    FAILURE = "Incorrect Password..."

    form_data: dict = {}
    message = ""
    open_dialog = True

    @rx.event
    async def handle_submit(self, form_data: dict):
        """Handle the form submit."""
        input_pass: str = form_data["input"]
        m = hashlib.sha1()
        m.update(input_pass.encode())
        m.update(self.SALT.encode())
        if secrets.compare_digest(m.hexdigest(), self.PASS_HEX_DIGEST):
            self.message = self.SUCCESS
            yield
            await asyncio.sleep(1.0)
            self.open_dialog = False
        else:
            self.message = self.FAILURE

def mydialog():
    return rx.dialog.root(
        rx.dialog.content(
            rx.form.root(
                rx.hstack(
                    rx.input(
                        name="input",
                        placeholder="Enter text...",
                        type="text",
                        required=True,
                    ),
                    rx.button("Submit", type="submit"),
                    width="100%",
                ),
                on_submit=LoginState.handle_submit,
                reset_on_submit=False,
            ),
            rx.divider(),
            rx.hstack(
                rx.heading("Results:"),
                rx.badge(
                    LoginState.message.to_string()
                ),
            ),
        ),
        open=LoginState.open_dialog,
    )

def index() -> rx.Component:
    return rx.vstack(
        # mydialog(),
        rx.hstack(
            rx.select(
                GameState.select_choices,
                value=GameState.selected_value,
                on_change=GameState.change_value,
            ),
            rx.button(
                GameState.selected_value,
                on_click=GameState.load_state(),
            ),
            rx.text(
                "Click right to set winner",
            ),
            rx.foreach(
                GameState.players,
                lambda i: rx.button(
                    GameState.player_names[i],
                    on_click=GameState.set_winner(i),
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
            on_click=GameState.delete_panels(),
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
                    rx.Var.range(GameState.n_panels),
                    lambda i: rx.button(
                        f"{i + 1}", 
                        # color="black",
                        style=rx.cond(
                            GameState.denied_panels[i],
                            mydefaultcolor("#000000FF"),
                            myblinkcolor(GameState.colors[GameState.player].to_string(use_json=False)),
                        ),
                        border_style="solid",
                        border_width="0.1vh",
                        border_color="#000000FF",
                        height=rx.Var.to_string(GameState.height)+ "vh",
                        background_color=GameState.panel_colors[i],
                        visibility=GameState.visible[i],
                        font_size=rx.Var.to_string(GameState.font_height)+ "vh",
                        text_align="center",
                        on_click=GameState.set_panel(i),
                        disabled=GameState.denied_panels[i].bool(),
                        z_index=z_panels,
                    ),
                ),
                columns=rx.Var.to_string(GameState.n_col),
                spacing="0",
                width=rx.Var.to_string(GameState.panels_width) + "vh",
            ),
            rx.cond(
                BackgroundState.bg == BG_HIDDEN,
                rx.box(
                    width=rx.Var.to_string(GameState.panels_width) + "vh",
                    height=rx.Var.to_string(GameState.panels_height) + "vh",
                    background_color="transparent",
                    position="absolute",
                    z_index=3,
                ),
                rx.cond(
                    BackgroundState.bg == BG_SHOW,
                    rx.video(
                        url=rx.get_upload_url(GameState.VTRQ_MP4),
                        width=rx.Var.to_string(GameState.panels_width) + "vh",
                        height=rx.Var.to_string(GameState.panels_height) + "vh",
                        position="absolute",
                        controls=False,
                        playing=VideoPlayingState.playing.bool(),
                        on_ended=[
                            BackgroundState.show_lastpic()
                        ],
                        z_index=2,
                    ),
                    rx.image(
                        src=rx.get_upload_url(GameState.VTRQ_LASTPIC),
                        width=rx.Var.to_string(GameState.panels_width) + "vh",
                        height=rx.Var.to_string(GameState.panels_height) + "vh",
                        position="absolute",
                        z_index=3,
                    ),


                ),
            ),
            width="100%",
        ),
        rx.hstack(
            rx.foreach(
                GameState.players,
                lambda i: rx.button(
                    GameState.points[i].to_string(use_json=False),
                    style=rx.cond(
                        GameState.player == i,
                        myblinkborder(GameState.colors[i].to_string(use_json=False)),
                        mydefaultborder(GameState.colors[i].to_string(use_json=False)),
                    ),
                    height=rx.Var.to_string(GameState.height)+ "vh",
                    width=rx.Var.to_string(GameState.height)+ "vh",
                    background_color="black",
                    color="white",
                    font_size=rx.Var.to_string(GameState.font_height)+ "vh",
                    text_align="center",
                    z_index=1,
                    on_click=GameState.set_player(i),
                    disabled=GameState.deny_player_button.bool(),
                ),
            ),
            justify="center",
            spacing="9",
            width="100%",
            z_index=5,

        ),
        rx.hstack(
            rx.foreach(
                GameState.audios,
                lambda a, i: rx.audio(
                    url=rx.get_upload_url(a.to_string(use_json=False)),
                    controls=False,
                    visibility="collapse",
                    width="10px",
                    height="10px",
                    playing=GameState.playing[i].bool(),
                ),
            ),
        ),
    )

app = rx.App()
app.add_page(index)
