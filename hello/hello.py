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
import yaml

# def delete_oldcsvs(path_to_save):

#     # ディレクトリ内のCSVファイルを特定ファイルを除いて取得し、更新日時順にソート
#     except_csv_files = ["aat25_init.csv",]
#     csv_files = [
#         os.path.join(path_to_save, f)
#         for f in os.listdir(path_to_save)
#         if f.endswith(".csv") and f not in except_csv_files
#     ]
#     csv_files.sort(key=os.path.getmtime, reverse=True)

#     # 最新100個以外のファイルを削除
#     files_to_delete = csv_files[100:]  # 100個目以降のファイル
#     for file in files_to_delete:
#         try:
#             os.remove(file)
#             print(f"Deleted: {file}")
#         except Exception as e:
#             print(f"Error deleting {file}: {e}")

#     print(f"{except_csv_files}を除く古いCSVファイルの削除が完了しました。")

# INIT_PLAYING_VIDEO = False
# ldir = "/"
# udir = rx.get_upload_dir()

# conf_yaml = "config_default.yaml"
# csvs_dir = "csvs"

# conf_path = os.path.join(ldir, conf_yaml)
# save_path = os.path.join(udir, csvs_dir)
# conf_txt = pathlib.Path(conf_path).read_text()

# delete_oldcsvs(save_path)

# hard_coded
N_AUDIOS = 7

class AT25(rx.Base):
    game: at25.Attack25

class GameState(rx.State):
    ldir = "_data"
    udir = rx.get_upload_dir()

    conf_yaml = "config_default.yaml"
    csvs_dir = "csvs"

    conf_path = os.path.join(ldir, conf_yaml)
    save_path = os.path.join(udir, csvs_dir)
    # conf_txt = pathlib.Path(conf_path).read_text()

    game_state: AT25 = AT25(
        game = at25.Attack25(conf_path, save_path)
    )

    n_row = game_state.game.get_n_row()
    n_col = game_state.game.get_n_col()

    panels_height = 60
    panels_width = panels_height * (16 / 9)

    height = panels_height / n_row
    width = panels_width / n_col
    n_panels =  n_row * n_col
    font_height = height // 2
    player_font_size = font_height // 2

    panels_list = list(range(n_panels))
    players: list[int] = game_state.game.get_player_ids()
    print(players)
    game_player_names: dict[int, str] = {
        i: f"player{i}" for i in players
    }

    on_edit = {i: False for i in players}
    on_edit_player: int = None
    deny_player_nameplates = {i: False for i in players}

    @rx.event
    def delete_oldcsvs(self):
        path_to_save = self.save_path

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

    @rx.event
    def edit_player_name(self, i):
        self.on_edit_player = i
        self.on_edit[self.on_edit_player] = True
        for j in self.players:
            if j != self.on_edit_player:
                self.deny_player_nameplates[j] = True

    @rx.event
    def set_player_name(self, input: dict):
        print("on_edit:", self.on_edit)
        self.game_player_names[self.on_edit_player] = input["input"]
        print("player_names:", self.game_player_names)
        self.on_edit[self.on_edit_player] = False
        for j in self.players:
            if j != self.on_edit_player:
                self.deny_player_nameplates[j] = False
        print("on_edit:", self.on_edit)

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

    game_id: int = game_state.game.get_game_id()

    VTRQ_MP4_DEFAULT = "vtrq_sample.mp4"
    vtrq_mp4 = VTRQ_MP4_DEFAULT
    vtrq_lastpic = "lastpic_sample.jpg"

    @rx.event
    def auth_vtrq(self, form_data: dict):
        PASS_HEX_DIGEST = 'b1fab726a375cb2d0e0c5321d35bbfdae5eb76e6' # 
    # PASS_HEX_DIGEST = '61eda3174e4614a3f02c467ea444d260192d4f35' # EMPTY PASSWORD
        SALT = 'sa-10!'

        input_pass: str = form_data["vtrq_pass"]
        m = hashlib.sha1()
        m.update(input_pass.encode())
        m.update(SALT.encode())
        if secrets.compare_digest(m.hexdigest(), PASS_HEX_DIGEST):
            self.vtrq_mp4 = "vtrq_masterpiece.mp4"
            return rx.toast.success("valid password.")
        else:
            self.vtrq_mp4 = self.VTRQ_MP4_DEFAULT
            return rx.toast.warning("INVALID password.")

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

    def get_board_panels(self):
        return self.game_state.game.get_board_panels()
    def get_player_colors(self):
        return self.game_state.game.get_player_colors()
    def get_player_ids(self):
        return self.game_state.game.get_player_ids()

    # 25
    denied_panels = [True for _ in range(n_panels)]

    audios = ["" for _ in range(N_AUDIOS)]
    playing = [False for _ in range(N_AUDIOS)]

    atchance_chime_playing: bool = False
    # atchance_deden_playing: bool = False
    # panel_win_playing: bool = False
    # success_playing: bool = False
    # failure_playing: bool = False

    visible_deden_button: str = "collapse"
    # at_chance_deden_playing: bool = False
    # 4 FIXED?
    # player_names: dict[int, str] = game_player_names

    #### when playing chime ended, stop playing and show deden button
    @rx.event
    def stop_chime_show_deden(self):
        self.atchance_chime_playing = False
        self.visible_deden_button = "visible"

    ### when playing deden ended, stop playing and hide deden button
    @rx.event
    def stop_hide_deden(self):
        # self.at_chance_deden_playing = False
        self.visible_deden_button = "collapse"

    ### when playing panel_win ended, stop playing
    # @rx.event
    # def stop_panel_win(self):
    #     self.panel_win_playing = False

    # @rx.event
    # def play_deden(self):
    #     self.atchance_deden_playing = True
        ### when playing ended, stop playing and hide deden button
        # yield
        # await asyncio.sleep(2.0)
        # self.at_chance_deden_playing = False
        # self.visible_deden_button = "collapse"
        # yield

    # @rx.event
    # def play_success(self):
    #     self.success_playing = True
    # @rx.event
    # def play_failure(self):
    #     self.failure_playing = True

    # @rx.event
    # def stop_success(self):
    #     self.success_playing = False
    # @rx.event
    # def stop_failure(self):
    #     self.failure_playing = False

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
        for i in range(N_AUDIOS):
            self.audios[i] = ""
            self.playing[i] = False
        self.player = EMPTY
        self.winner = EMPTY
        self.deny_player_button = False
        self.set_at_chance = False

    
    @rx.var
    def player_radio_labels(self) -> list[str]:
        return [(f"{self.game_player_names[i]} ({self.points[i]})") for i in self.players]
    @rx.var
    def label_players(self) -> dict[str, int]:
       return {l: i for l, i in zip(self.player_radio_labels, self.players)}
    

    radio_unselected = True

    @rx.event
    def select_player_radio(self, _: str):
        self.radio_unselected = False

    @rx.event
    def set_winner_form(self, form_data: dict):
        """Handle the form submit."""
        print(form_data)
        winner = self.label_players[form_data["radio_choice"]]
        self.winner = winner
        print("from set_winner_form: winner:", 
              winner, self.game_player_names[winner])
        # self.panel_win_playing = True

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
            for i in range(N_AUDIOS):
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
    async def delete_all_panels(self):
        for i in range(self.n_panels):
            if self.visible[i] == "visible":
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
            self.game_state.game.set_at_chance(panel_idx)
            for p in self.players:
                self.points[p] = self.panels.count(p)

            prev_color = self.panel_colors[panel_idx]
            for _ in range(4):
                self.panel_colors[panel_idx] = prev_color
                yield
                await asyncio.sleep(0.5)
                self.panel_colors[panel_idx] = self.colors[EMPTY]
                yield
                await asyncio.sleep(0.5)

            self.panel_colors[panel_idx] = self.colors[CHANCE]
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
                    self.playing[a_i % N_AUDIOS] = False
                    yield
                    self.playing[a_i % N_AUDIOS] = True
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

        for i in range(N_AUDIOS):
            self.playing[i] = False
        self.player = EMPTY
        yield

        for i in range(self.n_panels):
            self.denied_panels[i] = True
        yield
        ## IF NEXT IS ATCHANCE, RING BELL
        if self.game_state.game.is_atchance():
            # play zingle
            self.atchance_chime_playing = True
            yield
            #### when playing ended, stop playing and show deden button
            # await asyncio.sleep(7.0)
            # self.atchance_chime_playing = False
            # yield
            # visible button deden
            # self.visible_deden_button = "visible"

        self.deny_player_button = False
        yield

        print(self.game_state.game.get_board_panels)
        print("from set_panel: current player:", self.player)
        self.select_choices = sorted((rx.get_upload_dir() / pathlib.Path(("csvs"))).glob('*.csv'))

BG_HIDDEN=101
BG_SHOW=102
BG_LASTPIC=103

class BackgroundState(rx.State):
    bg = BG_HIDDEN

    @rx.event
    def hidden(self):
        self.bg = BG_HIDDEN
        yield
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
    def switch_playing(self):
        self.playing = not self.playing

class AudioPlayingState(rx.State):
    atchance_deden_playing: bool = False
    panel_win_playing: bool = False
    success_playing: bool = False
    failure_playing: bool = False
    vtrq_playing: bool = False

    @rx.event
    def switch_deden(self):
        self.atchance_deden_playing = not self.atchance_deden_playing
    @rx.event
    def switch_panel_win(self, _: dict = None):
        self.panel_win_playing = not self.panel_win_playing
        # print("from switch_panel_win:", fd)
    @rx.event
    def switch_success(self):
        self.success_playing = not self.success_playing
    @rx.event
    def switch_failure(self):
        self.failure_playing = not self.failure_playing
    @rx.event
    def switch_vtrq(self):
        self.vtrq_playing = not self.vtrq_playing

# class VisibleState(rx.State):
#     is_visible: bool = False  # Controls button visibility

#     def toggle_visibility(self):
#         self.is_visible = not self.is_visible

# z_ripple = 100
z_panels = 5

# def myripple():
#     return {
#                 "@keyframes ripple": {
#                 "0%": {"box-shadow": f"0 0 0 0 #FFC700FF"},
#                 "70%": {"box-shadow": f"0 0 0 20px #FFC70000"},
#                 "100%": {"box-shadow": f"0 0 0 0 #FFC70000"},
#                 # "z-index": z_ripple,
#                 # "position": "relative",
#                 },
#                 "animation": "ripple 2s infinite",
#                 "z-index": z_ripple,
#             }

################# CSS Style sheets ################
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

def mydefaultbgcolor(color):
    return {"background-color": f"{color}"}
def mygamingbgcolor(color):
    return {
        f"@keyframes gamingbgcolor{color[1:]}": {
            "0%": {"background-color": f"{color}", "box-shadow": f"0 0 0 0 {color}"},
            "30%": {"background-color": f"#FFFF00FF", "box-shadow": f"0 0 0 20px {color[:-2]}80"},
            "100%": {"background-color": f"{color}", "box-shadow": f"0 0 0 20px {color[:-2]}00"},
        },
        "animation": f"gamingbgcolor{color[1:]} 1s ease infinite"
    }
#################################


class LoginState(rx.State):
    PASS_HEX_DIGEST = 'b1fab726a375cb2d0e0c5321d35bbfdae5eb76e6' # 
    # PASS_HEX_DIGEST = '61eda3174e4614a3f02c467ea444d260192d4f35' # EMPTY PASSWORD
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

class AhoState(rx.State):
    mes: str = "do noth"

    @rx.event
    def do_nothing(self, form_data: dict):
        print(self.mes)
        print(form_data)

# class SetNameState(rx.State):
#     player_idx: int

#     def set_player_idx(self, idx):
#         self.player_idx = idx
#     def handle_submit(self, form_data: dict):
#         print("handle_submit:", form_data)
#         return GameState.set_player_name(self.player_idx, form_data["input"])

# def namedialog(i: int):
#     print("from_namedialog:", i)
#     SetNameState.set_player_idx(i)
#     return rx.dialog.root(
#         rx.dialog.content(
#             rx.form.root(
#                 rx.hstack(
#                     rx.input(
#                         name="input",
#                         placeholder="Enter text...",
#                         type="text",
#                         required=True,
#                     ),
#                     rx.button("Submit", type="submit",),
#                     rx.dialog.close(
#                         rx.button("Close Dialog", size="3"),
#                     ),
#                     width="100%",
#                 ),
#                 on_submit=SetNameState.handle_submit,
#                 reset_on_submit=False,
#             ),
#         ),
#         open=GameState.on_edit[i].bool(),
#     )

def logindialog():
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

# class AIConfState(rx.State):
#     yaml_content: str = ""
#     open: bool = True
#     default_value: str = conf_txt

#     def do_nothing(self):
#         print("do nothing!!!!")
#         return

#     def update_yaml(self, form_data: dict):
#         print(self.default_value)
#         # Here you would process the YAML content
#         self.yaml_content = form_data["yaml_content"]
#         if self.default_value == self.yaml_content:
#             is_toasted = rx.toast.success("YAML content has no difference...")
#         else:
#             is_toasted = rx.toast.success("YAML content updated successfully!")
#         self.open = not is_toasted
#         print(yaml.safe_load(self.yaml_content))
#         return is_toasted
# # class ConfigState(rx.State):
# #     conf_at25: dict

# #     def load_conf(self):
# #         with open(conf_path, "r") as f:
# #             self.conf_at25 = yaml.safe_load(f)

# def ai_yaml_editor():
#     return rx.dialog.root(
#         # rx.dialog.trigger(
#         #     rx.button("Edit YAML Content")
#         # ),
#         rx.dialog.content(
#             rx.dialog.title("Update YAML Content"),
#             rx.dialog.description("Edit your YAML configuration below"),
#             rx.form(
#                 rx.vstack(
#                     rx.text_area(
#                         placeholder="Enter YAML content",
#                         value=AIConfState.default_value,
#                         name="yaml_content",
#                         height="200px",
#                         width="400px",
#                         on_change=AIConfState.do_nothing(),
#                     ),
#                     rx.flex(
#                         rx.dialog.close(
#                             rx.button(
#                                 "Cancel",
#                                 variant="soft",
#                                 color_scheme="gray",
#                             ),
#                         ),
#                         rx.dialog.close(
#                             rx.button(
#                                 "Save",
#                                 type="submit"
#                             ),
#                         ),
#                         spacing="3",
#                         justify="end",
#                     ),
#                 ),
#                 on_submit=AIConfState.update_yaml,
#             ),
#             max_width="450px",
#         ),
#         open = AIConfState.open
#     )

class DrawerState(rx.State):
    is_open: bool = False

    @rx.event
    def toggle_drawer(self):
        self.is_open = not self.is_open

def drawer_content():
    return rx.drawer.content(
        rx.flex(
            rx.hstack(
                rx.drawer.close(
                    rx.icon_button(
                        rx.icon("x"),
                        on_click=DrawerState.toggle_drawer,
                        type="button",
                        color_scheme="red",
                    ),
                    # rx.button(
                    #     "Close",
                    #     on_click=DrawerState.toggle_drawer,
                    # ),
                ),
                rx.text(
                    "Load⇒", size="2", width="60px",
                ),
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
                    "Select the winner...", size="2", width="400px",
                ),
                rx.form.root(
                    rx.radio_group(
                        GameState.player_radio_labels,
                        name="radio_choice",
                        direction="row",
                        disabled=AudioPlayingState.panel_win_playing.bool(),
                        on_change=GameState.select_player_radio(),
                    ),
                    rx.button(
                        "You Win", 
                        type="submit", 
                        disabled=AudioPlayingState.panel_win_playing.bool() | GameState.radio_unselected.bool(),
                    ),
                    on_submit=[
                        GameState.set_winner_form,
                        AudioPlayingState.switch_panel_win,
                    ],
                    reset_on_submit=True,
                ),

                # rx.foreach(
                #     GameState.players,
                #     lambda i: rx.button(
                #         f"{GameState.game_player_names[i]} ({GameState.points[i]})",
                #         background_color=GameState.colors[i],
                #         color='black',
                #         on_click=GameState.set_winner(i),
                #     ),
                # ),
                rx.form(
                    rx.hstack(
                        rx.input(
                            placeholder="vtrq_pass",
                            name="vtrq_pass",
                            type="password",
                        ),
                        rx.button("Submit", type="submit"),
                    ),
                    on_submit=GameState.auth_vtrq,
                    reset_on_submit=True,
                ),
                # rx.button(
                #     "Click Me to set video",
                #     _hover={
                #         "color": "red",
                #         "background-position": "right center",
                #         "background-size": "200%" + " auto",
                #         "-webkit-animation2": "pulse 2s infinite",
                #     },
                #     on_click=[
                #         VideoPlayingState.stop_playing(),
                #         BackgroundState.show_video(),
                #     ],
                # ),
                # rx.button(
                #     "Click Me to delete_panels",
                #     _hover={
                #         "color": "red",
                #         "background-position": "right center",
                #         "background-size": "200%" + " auto",
                #         "-webkit-animation2": "pulse 2s infinite",
                #     },
                #     on_click=GameState.delete_panels(),
                # ),
                # rx.button(
                #     "Click Me to play video",
                #     _hover={
                #         "color": "red",
                #         "background-position": "right center",
                #         "background-size": "200%" + " auto",
                #         "-webkit-animation2": "pulse 2s infinite",
                #     },
                #     on_click=VideoPlayingState.start_playing(),
                # ),
                rx.text(f"Game ID: {GameState.game_id}", size="1", width="400px"),

            ),
            align_items="start",
            direction="column",
            spacing="1"
        ),
        height="75px",
        width="100%",
        padding="0em",
        background_color=rx.color("grass", 7),
    )

def lateral_menu():
    return rx.drawer.root(
        rx.drawer.trigger(
            rx.button(
                "Open Drawer",
                on_click=DrawerState.toggle_drawer,
            )
        ),
        rx.drawer.overlay(),
        rx.drawer.portal(drawer_content()),
        open=DrawerState.is_open,
        dismissible=False,
        direction="top",
        modal=False,
    )


def index() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            lateral_menu(),
            rx.button(
                "deden",
                visibility=GameState.visible_deden_button,
                on_click=AudioPlayingState.switch_deden(),
                disabled=AudioPlayingState.atchance_deden_playing,
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
                on_click=[
                    AudioPlayingState.switch_vtrq(),
                    VideoPlayingState.switch_playing(),
                ],
            ),
            rx.icon_button(
                rx.icon("check"), 
                color_scheme="green",
                on_click=AudioPlayingState.switch_success(),
                disabled=AudioPlayingState.success_playing.bool() | AudioPlayingState.failure_playing.bool(),
            ),
            rx.icon_button(
                rx.icon("x"), 
                color_scheme="red",
                on_click=AudioPlayingState.switch_failure(),
                disabled=AudioPlayingState.success_playing.bool() | AudioPlayingState.failure_playing.bool(),
            ),
            rx.button(
                "Click Me to delete all panels",
                _hover={
                    "color": "red",
                    "background-position": "right center",
                    "background-size": "200%" + " auto",
                    "-webkit-animation2": "pulse 2s infinite",
                },
                on_click=[
                    BackgroundState.hidden(),
                    BackgroundState.show_video(),
                    GameState.delete_all_panels(),
                ]

            ),
            rx.button(
                "Click Me to replay video",
                _hover={
                    "color": "red",
                    "background-position": "right center",
                    "background-size": "200%" + " auto",
                    "-webkit-animation2": "pulse 2s infinite",
                },
                on_click=VideoPlayingState.switch_playing(),
            ),

        ),
        rx.text(f""),
        # rx.text(f"Game ID: {GameState.game_id}"),
        # rx.cond(
        #     LoginState.open_dialog,
        #     logindialog(),
        #     ai_yaml_editor(),
        # ),
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
                rx.video(
                    url=rx.get_upload_url(GameState.vtrq_mp4),
                    width=rx.Var.to_string(GameState.panels_width) + "vh",
                    height=rx.Var.to_string(GameState.panels_height) + "vh",
                    position="absolute",
                    muted=True,
                    controls=False,
                    playing=VideoPlayingState.playing.bool(),
                    on_ended=VideoPlayingState.switch_playing(),
                    # on_ended=[
                    #     BackgroundState.show_lastpic()
                    # ],
                    z_index=2,
                ),
                # rx.cond(
                #     BackgroundState.bg == BG_SHOW,
                #     rx.video(
                #         url=rx.get_upload_url(GameState.vtrq_mp4),
                #         width=rx.Var.to_string(GameState.panels_width) + "vh",
                #         height=rx.Var.to_string(GameState.panels_height) + "vh",
                #         position="absolute",
                #         controls=False,
                #         playing=VideoPlayingState.playing.bool(),
                #         on_ended=[
                #             BackgroundState.show_lastpic()
                #         ],
                #         z_index=2,
                #     ),
                #     rx.image(
                #         src=rx.get_upload_url(GameState.vtrq_lastpic),
                #         width=rx.Var.to_string(GameState.panels_width) + "vh",
                #         height=rx.Var.to_string(GameState.panels_height) + "vh",
                #         position="absolute",
                #         z_index=3,
                #     ),


                # ),
            ),
            width="100%",
        ),
        rx.hstack(
            rx.foreach(
                GameState.players,
                lambda i: rx.vstack(
                    rx.cond(
                        GameState.on_edit[i].bool(),
                        rx.form.root(
                            rx.hstack(
                                rx.input(
                                    name="input",
                                    placeholder="Enter text...",
                                    type="text",
                                    required=True,
                                ),
                                rx.button("Submit", type="submit",),
                            ),
                            on_submit=GameState.set_player_name,
                            reset_on_submit=False,
                        ),
                        rx.button(
                            GameState.game_player_names[i],
                            width=rx.Var.to_string(GameState.width)+ "vh",
                            text_align="center",
                            background_color=GameState.colors[i].to_string(use_json=False),
                            style=rx.cond(
                                GameState.winner == i,
                                mygamingbgcolor(GameState.colors[i].to_string(use_json=False)),
                                mydefaultbgcolor(GameState.colors[i].to_string(use_json=False)),
                            ),
                            color="black",
                            font_size=rx.Var.to_string(GameState.player_font_size)+ "vh",
                            font_weight="bolder",
                            border_radius="4px",
                            on_double_click=GameState.edit_player_name(i),
                            disabled=GameState.deny_player_nameplates[i].bool(),
                        ),
                    ),
                    rx.button(
                        GameState.points[i].to_string(use_json=False),
                        style=rx.cond(
                            GameState.player == i,
                            myblinkborder(GameState.colors[i].to_string(use_json=False)),
                            mydefaultborder(GameState.colors[i].to_string(use_json=False)),
                        ),
                        height=rx.Var.to_string(GameState.height)+ "vh",
                        width=rx.Var.to_string(GameState.width)+ "vh",
                        background_color="black",
                        color="white",
                        font_size=rx.Var.to_string(GameState.font_height)+ "vh",
                        text_align="center",
                        z_index=1,
                        on_click=GameState.set_player(i),
                        disabled=GameState.deny_player_button.bool(),
                    ),
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
                    url="/" + a.to_string(use_json=False),
                    controls=False,
                    visibility="collapse",
                    width="10px",
                    height="10px",
                    playing=GameState.playing[i].bool(),
                ),
            ),
            rx.audio(
                url="/atchance_chime.mp3",
                controls=False,
                visibility="collapse",
                width="10px",
                height="10px",
                playing=GameState.atchance_chime_playing.bool(),
                on_ended=GameState.stop_chime_show_deden(),
            ),
            rx.audio(
                url="/atchance_deden.mp3",
                controls=False,
                visibility="collapse",
                width="10px",
                height="10px",
                playing=AudioPlayingState.atchance_deden_playing.bool(),
                on_ended=[
                    GameState.stop_hide_deden(),
                    AudioPlayingState.switch_deden(),
                ]
                          
            ),
            rx.audio(
                url="/panel_win.mp3",
                controls=False,
                visibility="collapse",
                width="10px",
                height="10px",
                playing=AudioPlayingState.panel_win_playing.bool(),
                on_ended=AudioPlayingState.switch_panel_win(),
            ),
            rx.audio(
                url="/success.mp3",
                controls=False,
                visibility="collapse",
                width="10px",
                height="10px",
                playing=AudioPlayingState.success_playing.bool(),
                on_ended=AudioPlayingState.switch_success(),
            ),
            rx.audio(
                url="/failure.mp3",
                controls=False,
                visibility="collapse",
                width="10px",
                height="10px",
                playing=AudioPlayingState.failure_playing.bool(),
                on_ended=AudioPlayingState.switch_failure(),
            ),
            rx.audio(
                url="/vtrq.mp3",
                controls=False,
                visibility="collapse",
                width="10px",
                height="10px",
                playing=AudioPlayingState.vtrq_playing.bool(),
                on_ended=AudioPlayingState.switch_vtrq(),
            ),
        ),
        justify="end",
        spacing="5",
        on_mount=GameState.delete_oldcsvs,
    )

app = rx.App()
app.add_page(index)
