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

    conf_path = os.path.join(ldir, conf_yaml)
    save_path = udir
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
    } | {EMPTY: "None"}

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

    # audiofiles: dict[int, str] = {
    #     EMPTY: "gray.mp3", 
    #     WALL: "gray.mp3", 
    #     FIRST: "gray.mp3", 
    #     } | {i: f"color{i}.mp3" for i in players}

    audiofiles: dict[int, str] = {i: f"color{i}.mp3" for i in players}

    game_id: int = game_state.game.get_game_id()

    # vtrq_filename = f"vtrq_{game_id}.mp4"
    vtrq_filename = f"vtrq.mp4"
    vtrq_file = vtrq_filename
    vtrq_filepath = rx.get_upload_dir() / pathlib.Path(vtrq_filename)
    vtrq_set = False
    orig_filename: str

    @rx.var(cache=False)
    def vtrq_filepath_url(self) -> str:
        return str(self.vtrq_filepath)

    @rx.event
    def rename_vtrq(self, orig_filename):
        self.orig_filename = orig_filename
        print("do rename_vtrq")
        print(orig_filename)
        orig_filepath = rx.get_upload_dir() / pathlib.Path(orig_filename)
        print(orig_filepath)
        print(self.vtrq_filepath)
        orig_filepath.rename(self.vtrq_filepath)
        self.vtrq_set = True

    @rx.event
    def delete_oldmp4s(self):
        path_to_save = rx.get_upload_dir()
        mp4_files = [
            os.path.join(path_to_save, f)
            for f in os.listdir(path_to_save)
            if f.endswith(".mp4")
        ]
        mp4_files.sort(key=os.path.getmtime, reverse=True)

        # 最新5個以外のファイルを削除
        files_to_delete = mp4_files[5:]  # 100個目以降のファイル
        for file in files_to_delete:
            try:
                os.remove(file)
                print(f"Deleted: {file}")
            except Exception as e:
                print(f"Error deleting {file}: {e}")

        print("古いMP4ファイルの削除が完了しました。")

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
            # self.vtrq_mp4 = self.VTRQ_MP4_DEFAULT
            return rx.toast.warning("INVALID password.")

    selected_value: str = ""
    select_choices: list[str] = sorted(rx.get_upload_dir().glob('*.csv'),
                                       key=os.path.getmtime, reverse=True)

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

    # audios = ["" for _ in range(N_AUDIOS)]
    # playing = [False for _ in range(N_AUDIOS)]

    atchance_chime_playing: bool = False
    # atchance_deden_playing: bool = False
    # panel_win_playing: bool = False
    # success_playing: bool = False
    # failure_playing: bool = False

    disable_deden_button: bool = True
    # at_chance_deden_playing: bool = False
    # 4 FIXED?
    # player_names: dict[int, str] = game_player_names

    #### when playing chime ended, stop playing and show deden button
    @rx.event
    def stop_chime_disable_deden(self):
        self.atchance_chime_playing = False
        self.disable_deden_button = False

    ### when playing deden ended, stop playing and hide deden button
    @rx.event
    def stop_hide_deden(self):
        # self.at_chance_deden_playing = False
        self.disable_deden_button = True

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
        # for i in range(N_AUDIOS):
        #     self.audios[i] = ""
        #     self.playing[i] = False
        self.player = EMPTY
        self.winner = EMPTY
        self.deny_player_button = False
        self.set_at_chance = False

    
    @rx.var(cache=False)
    def player_radio_labels(self) -> list[str]:
        return [(f"{self.game_player_names[i]} ({self.points[i]})") for i in self.players]
    @rx.var(cache=False)
    def label_players(self) -> dict[str, int]:
       return {l: i for l, i in zip(self.player_radio_labels, self.players)}
    

    winner_unset: bool = True
    winner_panels_undeleted: bool = True
    prestarting_vtrq: bool = True
    vtrq_unjudged: bool = True
    all_panels_undeleted: bool = True
    prestarting_vtrq_ans: bool = True

    @rx.event
    def revert_winner_states(self):
        self.winner_unset = True
        self.winner_panels_undeleted = True
        self.prestarting_vtrq = True
        self.vtrq_unjudged = True
        self.all_panels_undeleted = True
        self.prestarting_vtrq_ans = True
        yield

    radio_unselected: bool = True
    radio_selected_winner: int = EMPTY

    @rx.event
    def select_player_radio(self, item: str):
        print(item)
        self.radio_unselected = False
        radio_selected_winner = self.label_players[item]
        self.radio_selected_winner = radio_selected_winner
    @rx.event
    def set_winner_form(self, form_data: dict):
        """Handle the form submit."""
        print(form_data)
        winner = self.label_players[form_data["radio_choice"]]
        self.winner = winner
        self.winner_unset = False
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
            # for i in range(N_AUDIOS):
            #     self.audios[i] = self.audiofiles[self.player]
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

        self.winner_panels_undeleted = False
        panels_to_delete = self.game_state.game.get_player_panels(self.winner)
        for i in panels_to_delete:
            self.visible[i] = "collapse"
            yield
            await asyncio.sleep(0.5)
            print("changed_panel:", i + 1)
        await asyncio.sleep(2.0)

    @rx.event
    def start_vtrq(self):
        self.prestarting_vtrq = False
        
    @rx.event
    def judge_vtrq(self):
        self.vtrq_unjudged = False

    @rx.event
    async def delete_all_panels(self):
        self.all_panels_undeleted = False
        for i in range(self.n_panels):
            if self.visible[i] == "visible":
                self.visible[i] = "collapse"
                yield
                await asyncio.sleep(0.5)
                print("changed_panel:", i + 1)
        await asyncio.sleep(2.0)

    @rx.event
    def start_vtrq_ans(self):
        self.prestarting_vtrq_ans = False

    @rx.event(background=True)
    async def set_panel(self, panel_idx):
        async with self:
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
                        # self.playing[a_i % N_AUDIOS] = False
                        # yield
                        yield rx.call_script(f"playAudio{self.player}()")
                        print(f"called_script: playAudio{self.player}()")
                        # self.playing[a_i % N_AUDIOS] = True
                        for p in self.players:
                            self.points[p] = self.panels.count(p)
                        yield
                        await asyncio.sleep(0.5)
                        print("changed_panel:", i + 1)
                        # print("from playing:", self.playing)
                        print("from set_panel:", panel_idx)
                        # print(self.audios)
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

            # for i in range(N_AUDIOS):
            #     self.playing[i] = False
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
            self.select_choices = sorted(rx.get_upload_dir().glob('*.csv'))

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
    vtrq_ans: str
    valid_vtrq_ans: bool = False
    replaying: bool = False

    udir = rx.get_upload_dir()
    vtrq_ans = "A. " + pathlib.Path(os.path.join(udir, "vtrq_ans.txt")).read_text()
    
    @rx.event
    def switch_playing(self, is_replay=False):
        self.playing = not self.playing
        if self.replaying:
            self.replaying = not self.replaying
            self.valid_vtrq_ans = True
        elif is_replay:
            self.replaying = not self.replaying
            self.valid_vtrq_ans = False

    # @rx.event
    # def set_vtrq_ans(self, input: dict):
    #     self.vtrq_ans = "A. " + input["vtrq_ans"]

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
    return {"border": f"1vmin solid {color}"}

def myblinkborder(color):
    return {
                f"@keyframes blinkBorder{color[1:]}": {
                "0%": {"border": f"1vmin solid {color}"},
                "100%": {"border": f"1vmin solid {color[:-2]}00"},
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

class UploadState(rx.State):
    uploading: bool = False
    status: str = ""
    filename: str
    not_complete_upload = True
    progress: int = 0
    total_bytes: int = 0

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        self.not_complete_upload = True
        """Handle the upload of file(s).
        """
        file: rx.UploadFile
        if isinstance(files, list):
            file = files[0]
        else:
            file = files

        self.filename = file.filename
        outfile = rx.get_upload_dir() / pathlib.Path(self.filename)

        # Save the file.
        self.total_bytes = 0
        chunk_size = 1_000_000
        with outfile.open("wb") as file_object:
            while chunk := await file.read(chunk_size):
                file_object.write(chunk)
                self.total_bytes += chunk_size

        self.status = f"{self.filename} uploaded!"
        self.not_complete_upload = False

    @rx.event
    def handle_upload_progress(self, progress: dict):
        self.uploading = True
        self.progress = round(progress["progress"] * 100)
        if self.progress >= 100:
            self.uploading = False

    @rx.event
    def cancel_upload(self):
        self.uploading = False
        return rx.cancel_upload("upload_vtrq")

    @rx.event
    def switch_not_complete_upload(self):
        self.not_complete_upload = not self.not_complete_upload

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
        rx.scroll_area(
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
                rx.popover.root(
                    rx.popover.trigger(
                        rx.button("Load Panels", variant="soft"),
                    ),
                    rx.popover.content(
                        rx.flex(
                            rx.select(
                                GameState.select_choices,
                                value=GameState.selected_value,
                                on_change=GameState.change_value,
                            ),
                            rx.button(
                                "Load",
                                on_click=GameState.load_state(),
                                disabled=(GameState.selected_value=="")
                            ),
                        ),
                        style={"width": 360},
                        side="right",
                    ),
                    modal=True,
                ),
                # rx.text(
                #     "Load Panels⇒", size="2", width="10em",
                # ),
                # rx.select(
                #     GameState.select_choices,
                #     value=GameState.selected_value,
                #     on_change=GameState.change_value,
                # ),
                # rx.button(
                #     "Load",
                #     on_click=GameState.load_state(),
                #     disabled=(GameState.selected_value=="")
                # ),
                rx.popover.root(
                    rx.popover.trigger(
                        rx.button("Select the winner", variant="soft"),
                    ),
                    rx.popover.content(
                        rx.flex(
                rx.card(
                    rx.form.root(
                        rx.radio_group(
                            GameState.player_radio_labels,
                            name="radio_choice",
                            direction="row",
                            disabled=AudioPlayingState.panel_win_playing.bool(),
                            on_change=GameState.select_player_radio,
                            padding="0",
                        ),
                        rx.hstack(
                            rx.box(
                                GameState.game_player_names[GameState.radio_selected_winner],
                                color="black",
                                background_color=GameState.colors[GameState.radio_selected_winner],
                                # color_scheme= lambda l: GameState.label_colors[l],
                            ),
                            rx.button(
                                "You Win", 
                                type="submit", 
                                disabled=AudioPlayingState.panel_win_playing.bool() | GameState.radio_unselected.bool(),
                            ),
                            padding="0",

                        ),
                        on_submit=[
                            GameState.set_winner_form,
                            AudioPlayingState.switch_panel_win,
                        ],
                        reset_on_submit=True,
                        padding="0",
                    ),
                ),
                        ),
                        # style={"width": "30em"},
                        side="right",
                        padding="0",
                    ),
                    modal=True,
                ),
                # rx.text(
                #     "Select the winner...", size="2", width="100px",
                # ),
                # rx.card(
                #     rx.form.root(
                #         rx.radio_group(
                #             GameState.player_radio_labels,
                #             name="radio_choice",
                #             direction="row",
                #             disabled=AudioPlayingState.panel_win_playing.bool(),
                #             on_change=GameState.select_player_radio,
                #             padding="0",
                #         ),
                #         rx.hstack(
                #             rx.box(
                #                 GameState.game_player_names[GameState.radio_selected_winner],
                #                 color="black",
                #                 background_color=GameState.colors[GameState.radio_selected_winner],
                #                 # color_scheme= lambda l: GameState.label_colors[l],
                #             ),
                #             rx.button(
                #                 "You Win", 
                #                 type="submit", 
                #                 disabled=AudioPlayingState.panel_win_playing.bool() | GameState.radio_unselected.bool(),
                #             ),
                #             padding="0",

                #         ),
                #         on_submit=[
                #             GameState.set_winner_form,
                #             AudioPlayingState.switch_panel_win,
                #         ],
                #         reset_on_submit=True,
                #         padding="0",
                #     ),
                #     width="30em",
                # ),
                # rx.foreach(
                #     GameState.players,
                #     lambda i: rx.button(
                #         f"{GameState.game_player_names[i]} ({GameState.points[i]})",
                #         background_color=GameState.colors[i],
                #         color='black',
                #         on_click=GameState.set_winner(i),
                #     ),
                # ),
                rx.upload(
                    rx.button(
                        "Select File",
                        color="blue",
                        bg="white",
                        border=f"1px solid blue",
                        width="8em",
                    ),
                    rx.text(
                        "or Drag and drop",
                        width="10em",
                    ),
                    border="1px dotted yellow",

                    accept={
                        "video/mp4": [".mp4"],
                    },
                    max_size=100_000_000, # 100MB
                    multiple=False,
                    id="upload_vtrq",
                    padding="0",
                ),
                rx.text(rx.selected_files("upload_vtrq")),
                # rx.button(
                #     "Upload VTR",
                #     type="button",
                #     on_click=UploadState.handle_upload(
                #             rx.upload_files(
                #                 upload_id="upload_vtrq", 
                #                 on_upload_progress=UploadState.handle_upload_progress,
                #             )
                #     ),
                # ),
                rx.vstack(
                rx.cond(
                    ~UploadState.uploading.bool(),
                    rx.button(
                        "Upload VTR",
                        on_click=UploadState.handle_upload(
                            rx.upload_files(
                                upload_id="upload_vtrq",
                                on_upload_progress=UploadState.handle_upload_progress,
                            ),
                        ),
                        size="1",
                        disabled=(rx.selected_files("upload_vtrq").length() == 0)
                    ),
                    rx.button(
                        "Cancel",
                        on_click=UploadState.cancel_upload,
                        size="1",
                    ),
                ),
                rx.progress(value=UploadState.progress, max=100, width="100%"),
                rx.text(
                    f"Uploaded: {UploadState.total_bytes / 1_000_000} MB",
                    size="1",
                    width="10em"
                ),
                padding="0",
                ),
                # rx.progress(value=UploadState.progress, max=100),
                rx.vstack(
                rx.button(
                    "Prepare VTRQ",
                    type="button",
                    disabled=UploadState.not_complete_upload,
                    on_click=[
                        GameState.rename_vtrq(UploadState.filename),
                        UploadState.switch_not_complete_upload(),
                    ]
                ),
                rx.cond(
                    GameState.vtrq_set,
                    rx.text(GameState.orig_filename + "->" + GameState.vtrq_filename),
                    rx.text("")
                ),
                ),
                # rx.form(
                #     rx.hstack(
                #         rx.input(
                #             placeholder="vtrq_pass",
                #             name="vtrq_pass",
                #             type="password",
                #         ),
                #         rx.button("Submit", type="submit"),
                #     ),
                #     on_submit=GameState.auth_vtrq,
                #     reset_on_submit=True,
                # ),
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
        background_color=rx.color("gray", 7),
    ),
    ),

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
        logindialog(),
        # lateral_menu(),
        rx.scroll_area(
            rx.hstack(
                rx.button(
                    rx.icon("music"),
                    "アタックチャンス!",
                    visibility="visible",
                    on_click=AudioPlayingState.switch_deden(),
                    disabled=(AudioPlayingState.atchance_deden_playing | 
                              GameState.disable_deden_button),
                ),


                rx.popover.root(
                    rx.popover.trigger(
                        rx.button("勝者決定", variant="soft",
                        disabled=~GameState.winner_unset.bool()),
                    ),
                    rx.popover.content(
                        rx.flex(
                rx.card(
                    rx.form.root(
                        rx.radio_group(
                            GameState.player_radio_labels,
                            name="radio_choice",
                            direction="row",
                            disabled=AudioPlayingState.panel_win_playing.bool(),
                            on_change=GameState.select_player_radio,
                            padding="0",
                        ),
                        rx.hstack(
                            rx.box(
                                GameState.game_player_names[GameState.radio_selected_winner],
                                color="black",
                                background_color=GameState.colors[GameState.radio_selected_winner],
                                # color_scheme= lambda l: GameState.label_colors[l],
                            ),
                            rx.button(
                                "You Win", 
                                type="submit", 
                                disabled=AudioPlayingState.panel_win_playing.bool() | GameState.radio_unselected.bool(),
                            ),
                            padding="0",

                        ),
                        on_submit=[
                            GameState.set_winner_form,
                            AudioPlayingState.switch_panel_win,
                        ],
                        reset_on_submit=True,
                        padding="0",
                    ),
                ),
                        ),
                        # style={"width": "30em"},
                        side="right",
                        padding="0",
                    ),
                    modal=True,
                ),

                rx.button(
                    "勝者パネル消す",
                    disabled=(GameState.winner_unset | 
                    ~GameState.winner_panels_undeleted.bool()),
                    _hover={
                        "color": "red",
                        "background-position": "right center",
                        "background-size": "200%" + " auto",
                        "-webkit-animation2": "pulse 2s infinite",
                    },
                    on_click=[
                        BackgroundState.show_video(),
                        GameState.delete_panels(),
                    ],
                ),
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
                rx.button(
                    "ラストクイズスタート",
                    disabled=(GameState.winner_panels_undeleted | 
                    ~GameState.prestarting_vtrq.bool()),
                    _hover={
                        "color": "red",
                        "background-position": "right center",
                        "background-size": "200%" + " auto",
                        "-webkit-animation2": "pulse 2s infinite",
                    },
                    on_click=[
                        GameState.start_vtrq(),
                        AudioPlayingState.switch_vtrq(),
                        VideoPlayingState.switch_playing(),
                    ],
                ),
                rx.box(
                    rx.hstack(
                        rx.text(f"正誤判定:", size="1", width="60px"),
                        rx.icon_button(
                            rx.icon("check"), 
                            color_scheme="green",
                            on_click=[
                                GameState.judge_vtrq(),
                                AudioPlayingState.switch_success(),
                            ],
                            disabled=(
                                AudioPlayingState.success_playing.bool() | 
                                AudioPlayingState.failure_playing.bool() |
                                GameState.prestarting_vtrq.bool() |
                                ~GameState.vtrq_unjudged.bool()),
                        ),
                        rx.icon_button(
                            rx.icon("x"), 
                            color_scheme="red",
                            on_click=[
                                GameState.judge_vtrq(),
                                AudioPlayingState.switch_failure(),
                            ],
                            
                            disabled=(
                                AudioPlayingState.success_playing.bool() | 
                                AudioPlayingState.failure_playing.bool() |
                                GameState.prestarting_vtrq.bool() |
                                ~GameState.vtrq_unjudged.bool()),
                        ),
                    ),
                ),
                rx.button(
                    "全パネル消す",
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
                    ],
                    disabled=(GameState.vtrq_unjudged | 
                    ~GameState.all_panels_undeleted.bool()),

                ),
                rx.button(
                    "ラスト正解再生",
                    _hover={
                        "color": "red",
                        "background-position": "right center",
                        "background-size": "200%" + " auto",
                        "-webkit-animation2": "pulse 2s infinite",
                    },
                    on_click=[
                        VideoPlayingState.switch_playing(True),
                        GameState.start_vtrq_ans(),
                    ],
                    disabled=(GameState.all_panels_undeleted | 
                    ~GameState.prestarting_vtrq_ans.bool()),
                ),
                # rx.box(
                # rx.form(
                #     rx.hstack(
                #         rx.input(
                #             placeholder="vtrq_ans",
                #             name="vtrq_ans",
                #             type="vtrq_ans",
                #         ),
                #         rx.button("Submit", type="submit"),
                #     ),
                #     on_submit=VideoPlayingState.set_vtrq_ans,
                #     reset_on_submit=True,
                # ),
                # width="15em"
                # ),

                rx.popover.root(
                    rx.popover.trigger(
                        rx.button("パネルロード", variant="soft"),
                    ),
                    rx.popover.content(
                        rx.flex(
                            rx.select(
                                GameState.select_choices,
                                value=GameState.selected_value,
                                on_change=GameState.change_value,
                            ),
                            rx.button(
                                "Load",
                                on_click=[
                                    GameState.load_state(),
                                    GameState.revert_winner_states(),
                                ],
                                disabled=(GameState.selected_value=="")
                            ),
                        ),
                        style={"width": 360},
                        side="right",
                    ),
                    modal=True,
                ),

                rx.text(f"Game ID: {GameState.game_id}", size="1", width="400px"),

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
                            border_width="0.1vmin",
                            border_color="#000000FF",
                            height=rx.Var.to_string(GameState.height)+ "vmin",
                            width=rx.Var.to_string(GameState.width)+ "vmin",
                            background_color=GameState.panel_colors[i],
                            visibility=GameState.visible[i],
                            font_size=rx.Var.to_string(GameState.font_height)+ "vmin",
                            text_align="center",
                            on_click=GameState.set_panel(i),
                            disabled=GameState.denied_panels[i].bool(),
                            z_index=z_panels,
                        ),
                    ),
                    columns=rx.Var.to_string(GameState.n_col),
                    spacing="0",
                    width=rx.Var.to_string(GameState.panels_width) + "vmin",
                ),
                rx.cond(
                    BackgroundState.bg == BG_HIDDEN,
                    rx.box(
                        width=rx.Var.to_string(GameState.panels_width) + "vmin",
                        height=rx.Var.to_string(GameState.panels_height) + "vmin",
                        background_color="transparent",
                        position="absolute",
                        z_index=3,
                    ),
                    rx.video(
                        # url=rx.get_upload_url(GameState.vtrq_filename),
                        url=rx.get_upload_url(GameState.vtrq_file),
                        width=rx.Var.to_string(GameState.panels_width) + "vmin",
                        height=rx.Var.to_string(GameState.panels_height) + "vmin",
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
                    #         width=rx.Var.to_string(GameState.panels_width) + "vmin",
                    #         height=rx.Var.to_string(GameState.panels_height) + "vmin",
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
                    #         width=rx.Var.to_string(GameState.panels_width) + "vmin",
                    #         height=rx.Var.to_string(GameState.panels_height) + "vmin",
                    #         position="absolute",
                    #         z_index=3,
                    #     ),


                    # ),
                ),
                rx.cond(
                    VideoPlayingState.valid_vtrq_ans.bool(),
                    rx.box(
                        VideoPlayingState.vtrq_ans,
                        z_index=10000,
                        background_color="#FF7628FF",
                        border_radius="1vmin",
                        font_size=rx.Var.to_string(GameState.font_height*1.5)+ "vmin",
                        font_weight="bolder",
                        position="absolute",
                        top=rx.Var.to_string(GameState.height*4)+ "vmin",

                    ),
                ),
                width="100%",
            ),
            rx.text(""),
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
                                height="5vmin",
                                width=rx.Var.to_string(GameState.width)+ "vmin",
                                text_align="center",
                                background_color=GameState.colors[i].to_string(use_json=False),
                                style=rx.cond(
                                    GameState.winner == i,
                                    mygamingbgcolor(GameState.colors[i].to_string(use_json=False)),
                                    mydefaultbgcolor(GameState.colors[i].to_string(use_json=False)),
                                ),
                                color="black",
                                font_size=rx.Var.to_string(GameState.player_font_size)+ "vmin",
                                font_weight="bolder",
                                border_radius="1vmin",
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
                            height=rx.Var.to_string(GameState.height)+ "vmin",
                            width=rx.Var.to_string(GameState.width)+ "vmin",
                            background_color="black",
                            color="white",
                            font_size=rx.Var.to_string(GameState.font_height)+ "vmin",
                            text_align="center",
                            z_index=1,
                            on_click=GameState.set_player(i),
                            disabled=GameState.deny_player_button.bool(),
                        ),
                    ),
                ),
                justify="center",
                spacing="5",
                width="100%",
                z_index=5,

            ),
            rx.vstack(
                # rx.foreach(
                #     GameState.audios,
                #     lambda a, i: rx.audio(
                #         url="/" + a.to_string(use_json=False),
                #         controls=False,
                #         visibility="collapse",
                #         width="1vmin",
                #         height="1vmin",
                #         playing=GameState.playing[i].bool(),
                #     ),
                # ),
                rx.audio(
                    url="/atchance_chime.mp3",
                    controls=False,
                    visibility="collapse",
                    width="1vmin",
                    height="1vmin",
                    playing=GameState.atchance_chime_playing.bool(),
                    on_ended=GameState.stop_chime_disable_deden(),
                ),
                rx.audio(
                    url="/atchance_deden.mp3",
                    controls=False,
                    visibility="collapse",
                    width="1vmin",
                    height="1vmin",
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
                    width="1vmin",
                    height="1vmin",
                    playing=AudioPlayingState.panel_win_playing.bool(),
                    on_ended=AudioPlayingState.switch_panel_win(),
                ),
                rx.audio(
                    url="/success.mp3",
                    controls=False,
                    visibility="collapse",
                    width="1vmin",
                    height="1vmin",
                    playing=AudioPlayingState.success_playing.bool(),
                    on_ended=AudioPlayingState.switch_success(),
                ),
                rx.audio(
                    url="/failure.mp3",
                    controls=False,
                    visibility="collapse",
                    width="1vmin",
                    height="1vmin",
                    playing=AudioPlayingState.failure_playing.bool(),
                    on_ended=AudioPlayingState.switch_failure(),
                ),
                rx.audio(
                    url="/vtrq.mp3",
                    controls=False,
                    visibility="collapse",
                    width="1vmin",
                    height="1vmin",
                    playing=AudioPlayingState.vtrq_playing.bool(),
                    on_ended=AudioPlayingState.switch_vtrq(),
                ),
            ),
            rx.foreach(
                GameState.audiofiles,
                lambda i, m: rx.script(f"""
    let playAudio{i[0]} = () => {{
        let audioSrc = "{i[1]}"
        let audio = new Audio(audioSrc)
        audio.play()
    }}
    """
                ),
            ),
            justify="end",
            spacing="3",
            on_mount=[
                GameState.delete_oldcsvs,
                GameState.delete_oldmp4s,
            ],
    )

app = rx.App(
    theme=rx.theme(
        appearance="dark",
        has_background=True,
        # radius="large",
        # accent_color="teal",
    ),
)
app.add_page(index)
