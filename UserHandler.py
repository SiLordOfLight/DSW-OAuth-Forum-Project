from User import User
import json

class UserHandler:

    def __init__(self):
        with open("static/admins.json") as adminFile:
            self.admins = json.load(adminFile)

        with open("static/users.json") as inFile:
            usrRaw = json.load(inFile)

        self.users = []

        for raw in usrRaw:
            self.users.append(User.fromDict(raw))

        self.added = []
        for usr in self.users:
            self.added.append(usr.name)

        self.current = None

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

    def has(self, name):
        return name in self.added

    def login(self, name):
        for user in self.users:
            if user.name == name:
                self.current = user
                return

    def banCurrent(self):
        self.current.ban()

    def makeAdmin(self, id):
        usr = self.usrFor(id)
        usr.is_admin = True

        self.admins.append(id)

        with open("static/admins.json", 'w') as adminFile:
            json.dump(self.admins, adminFile)

    def unAdmin(self, id):
        usr = self.usrFor(id)
        usr.is_admin = False

        self.admins.remove(id)

        with open("static/admins.json", 'w') as adminFile:
            json.dump(self.admins, adminFile)

    def close(self):
        out = []
        for usr in self.users:
            out.append(usr.toJSON())

        with open("static/users.json", 'w') as outFile:
            json.dump(out, outFile)