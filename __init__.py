import builtins
import os
import sqlite3

from Chainmail.Events import PlayerConnectedEvent, Events
from Chainmail.Player import Player
from Chainmail.Plugin import ChainmailPlugin


class ChainmailEconomy(ChainmailPlugin):
    def __init__(self, manifest: dict, wrapper: "Wrapper.Wrapper") -> None:
        super().__init__(manifest, wrapper)
        self.db = sqlite3.connect(os.path.join(manifest["path"], "economy.db"), check_same_thread=False)
        self.initialize_db()

        self.wrapper.EventManager.register_handler(Events.PLAYER_CONNECTED, self.handle_connection)

        builtins.Economy = self

    def get_balance(self, player: Player) -> float:
        """
        Gets the account balance of a player
        :param player: The player to get the balance for
        :return: Their balance
        """
        with self.db:
            cursor = self.db.cursor()
            cursor.execute("select balance from Balances where uuid = ?", (player.uuid, ))
            balance = cursor.fetchone()
            if balance is None:
                cursor.execute("insert into Balances (uuid, balance) values (?, 0.0)", (player.uuid, ))
                return float(0)
            else:
                return balance[0]

    def set_balance(self, player: Player, balance: float) -> None:
        """
        Sets the account balance of a player
        :param player: The player to set the balance for
        :param balance: Their new balance
        """
        with self.db:
            cursor = self.db.cursor()
            cursor.execute("update balances set balance = ? where uuid = ?", (balance, player.uuid))

    def initialize_db(self):
        with self.db:
            self.db.execute("create table if not exists Balances (uuid text, balance real)")

    def handle_connection(self, event: PlayerConnectedEvent):
        self.get_balance(event.player)
