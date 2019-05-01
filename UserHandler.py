from User import User
import json
import pymongo

class UserHandler:

    def __init__(self, database):
        self.users = []

        for raw in database.find():
            self.users.append(User.fromDict(raw))

        self.added = []
        for usr in self.users:
            self.added.append(usr.name)

        self.current = None

        self.admins = [usr for usr in self.users if usr.is_admin]

        self.database = database

    def usrFor(self, id):
        for usr in self.users:
            if usr.id == id: return usr

        return None

    def usrForName(self, nm):
        for usr in self.users:
            if usr.name == nm: return usr

        return None

    def newUsr(self, name):
        status = name in self.admins

        newU = User(name, status)

        self.users.append(newU)
        self.added.append(name)

        self.current = newU

        self.database.insert(newU.toJSON())

    def has(self, name):
        return name in self.added

    def login(self, name):
        for user in self.users:
            if user.name == name:
                self.current = user
                return

    def banCurrent(self):
        self.current.ban()
        self.database.update_one({'_id':self.current.id}, {'ban_level':self.current.ban_level})

    def makeAdmin(self, id):
        usr = self.usrFor(id)
        usr.is_admin = True

        self.admins.append(id)
        self.database.update_one({'_id':usr.id}, {'is_admin':usr.is_admin})

    def unAdmin(self, id):
        usr = self.usrFor(id)
        usr.is_admin = False

        self.admins.remove(id)
        self.database.update_one({'_id':usr.id}, {'is_admin':usr.is_admin})

