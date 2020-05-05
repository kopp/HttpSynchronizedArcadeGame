"""
Demonstrate how to synchronize the status between two games over an HTTP server.

Based on https://arcade.academy/examples/sprite_move_keyboard_better.html#sprite-move-keyboard-better
"""


from http_synced_dictionary import HttpSyncedDictionary

import arcade
import os
from uuid import uuid4 as get_random_id
from random import randint
import argparse


SPRITE_SCALING = 0.5

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Better Move Sprite with Keyboard Example"

MOVEMENT_SPEED = 5


class Player(arcade.Sprite):

    def __init__(self, image, scaling, synched_status: HttpSyncedDictionary, identifier, is_local):
        super().__init__(image, scaling)
        self.synched_status = synched_status
        self.identifier = identifier
        self.is_local = is_local

    def set_center(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y

        if self.is_local:
            status = self.synched_status.get(self.identifier, {})
            status["center_x"] = self.center_x
            status["center_y"] = self.center_y
            self.synched_status.update({self.identifier: status})

    def set_change(self, change_x, change_y):
        self.change_x = change_x
        self.change_y = change_y

        if self.is_local:
            status = self.synched_status.get(self.identifier)
            status["change_x"] = self.change_x
            status["change_y"] = self.change_y
            self.synched_status.update({self.identifier: status})

    def update(self):
        status = self.synched_status.get(self.identifier)

        if not self.is_local:
            self.center_x = status["center_x"]
            self.center_y = status["center_y"]

        self.center_x += status["change_x"]
        self.center_y += status["change_y"]

        if self.left < 0:
            self.left = 0
        elif self.right > SCREEN_WIDTH - 1:
            self.right = SCREEN_WIDTH - 1

        if self.bottom < 0:
            self.bottom = 0
        elif self.top > SCREEN_HEIGHT - 1:
            self.top = SCREEN_HEIGHT - 1

        if self.is_local:
            status["center_x"] = self.center_x
            status["center_y"] = self.center_y
            self.synched_status.update({self.identifier: status})


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self, status: HttpSyncedDictionary, identifier):
        """
        Initializer
        """

        # Call the parent class initializer
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Set the working directory (where we expect to find files) to the same
        # directory this .py file is in. You can leave this out of your own
        # code, but it is needed to easily run the examples using "python -m"
        # as mentioned at the top of this program.
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        self.synched_status = status
        self.identifier = identifier

        # Variables that will hold sprite lists
        self.player_list = None

        # Set up the player info
        self.player_sprite = None

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        # Set the background color
        arcade.set_background_color(arcade.color.AMAZON)

    def setup(self):
        """ Set up the game and initialize the variables. """

        # Sprite lists
        self.player_list = arcade.SpriteList()

        # Set up the player
        self.player_sprite = Player(
            ":resources:images/animated_characters/female_person/femalePerson_idle.png",
            SPRITE_SCALING,
            self.synched_status,
            self.identifier,
            True,
        )
        width, height = self.get_size()
        x = randint(50, width - 50)
        y = randint(50, height - 50)
        self.player_sprite.set_center(x, y)
        self.player_list.append(self.player_sprite)

    def on_draw(self):
        """
        Render the screen.
        """

        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw all the sprites.
        self.player_list.draw()

    def _update_player_movement_based_on_key_input(self):
        change_x = 0
        change_y = 0

        if self.up_pressed and not self.down_pressed:
            change_y = MOVEMENT_SPEED
        elif self.down_pressed and not self.up_pressed:
            change_y = -MOVEMENT_SPEED
        if self.left_pressed and not self.right_pressed:
            change_x = -MOVEMENT_SPEED
        elif self.right_pressed and not self.left_pressed:
            change_x = MOVEMENT_SPEED

        self.player_sprite.set_change(change_x, change_y)

    def _add_missing_remote_players(self):
        known_players = set([player.identifier for player in self.player_list])
        all_statii = self.synched_status.get()
        for identifier, status in all_statii.items():
            if identifier not in known_players:
                print("Found new player ", identifier)
                new_player = Player(
                    ":resources:images/animated_characters/female_person/femalePerson_idle.png",
                    SPRITE_SCALING,
                    self.synched_status,
                    identifier,
                    False,
                )
                new_player.set_center(status["center_x"], status["center_y"])
                self.player_list.append(new_player)

    def on_update(self, delta_time):
        """ Movement and game logic """

        self._update_player_movement_based_on_key_input()

        self._add_missing_remote_players()

        # Call update to move the sprite
        # If using a physics engine, call update on it instead of the sprite
        # list.
        self.player_list.update()

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.DOWN:
            self.down_pressed = True
        elif key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True

        elif key in [arcade.key.ESCAPE, arcade.key.Q]:
            raise SystemExit

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False
        elif key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play a simple game with a HTTP backed multi-player-mode")
    parser.add_argument("--server",
                        help="URI to the server to use for synchronization.",
                        default="http://localhost:5000/update",
                        )
    parser.add_argument("--identifier",
                        help="Unique identifier for the sprite controlled by this instance of the game.",
                        default=str(get_random_id()),
                        )
    args = parser.parse_args()

    print("This game is identified by {}".format(args.identifier))
    print("For synchronization, the server {} is used.".format(args.server))

    status = HttpSyncedDictionary(args.server, keys_to_filter=[args.identifier])
    status.start()

    window = MyGame(status, args.identifier)
    window.setup()
    arcade.run()

    status.stop()
