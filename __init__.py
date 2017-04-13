import os
import sqlite3

from Chainmail.Plugin import ChainmailPlugin


class ChainmailEconomy(ChainmailPlugin):
    def __init__(self, manifest: dict, wrapper: "Wrapper.Wrapper") -> None:
        super().__init__(manifest, wrapper)
        self.db = sqlite3.connect(os.path.join(manifest["path"], "economy.db"))
        self.initialize_db()

    def initialize_db(self):
        with self.db:
            self.db.execute("create table if not exists Balances (uuid text, balance real)")
