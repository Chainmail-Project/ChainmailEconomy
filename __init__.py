import builtins
import os
import sqlite3

from Chainmail.Events import PlayerConnectedEvent, Events, CommandSentEvent
from Chainmail.MessageBuilder import MessageBuilder, Colours
from Chainmail.Player import Player
from Chainmail.Plugin import ChainmailPlugin


class ChainmailEconomy(ChainmailPlugin):
    def __init__(self, manifest: dict, wrapper: "Wrapper.Wrapper") -> None:
        super().__init__(manifest, wrapper)
        self.db = sqlite3.connect(os.path.join(manifest["path"], "economy.db"), check_same_thread=False)
        self.initialize_db()

        self.wrapper.EventManager.register_handler(Events.PLAYER_CONNECTED, self.handle_connection)
        self.balance = self.wrapper.CommandRegistry.register_command("!balance", "^!balance$", "Gets your account balance.", self.command_balance)
        self.transfer = self.wrapper.CommandRegistry.register_command("!transfer", "^!transfer ([\\w\\d_]+) ([\\d.]+)$", "Transfers money to another user.", self.command_transfer)
        self.setbalance_command = self.wrapper.CommandRegistry.register_command("!setbalance", "^!setbalance ([\\w\\d_]+) ([\\d.]+)$", "Sets the account balance for a user.", self.command_setbalance, True)

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

    def command_balance(self, event: CommandSentEvent):
        balance = self.get_balance(event.player)
        builder = MessageBuilder()
        builder.add_field("Your balance is ", Colours.gold)
        builder.add_field(str(balance), Colours.blue)
        event.player.send_message(builder)

    def command_transfer(self, event: CommandSentEvent):
        recipient = self.wrapper.PlayerManager.get_player(event.args[0][0])
        if recipient is None:
            builder = MessageBuilder()
            builder.add_field("The specified player could not be found.", Colours.red)
            event.player.send_message(builder)
            return
        amount = float(event.args[0][1])
        if self.get_balance(event.player) < amount:
            builder = MessageBuilder()
            builder.add_field("You do not have enough money.", Colours.red)
            event.player.send_message(builder)
            return
        self.set_balance(event.player, self.get_balance(event.player) - amount)
        self.set_balance(recipient, self.get_balance(recipient) + amount)
        builder = MessageBuilder()
        builder.add_field("Money sent!", Colours.gold)
        event.player.send_message(builder)

        builder = MessageBuilder()
        builder.add_field("You have recieved ", Colours.gold)
        builder.add_field(f"{str(amount)} ", Colours.blue)
        builder.add_field("from ", Colours.gold)
        builder.add_field(f"{str(event.player.username)}.", Colours.blue)
        recipient.send_message(builder)

    def command_setbalance(self, event: CommandSentEvent):
        recipient = self.wrapper.PlayerManager.get_player(event.args[0][0])
        if recipient is None:
            builder = MessageBuilder()
            builder.add_field("The specified player could not be found.", Colours.red)
            event.player.send_message(builder)
            return
        amount = float(event.args[0][1])
        self.set_balance(recipient, amount)
        builder = MessageBuilder()
        builder.add_field("Account balance successfully updated.", Colours.gold)
        event.player.send_message(builder)
