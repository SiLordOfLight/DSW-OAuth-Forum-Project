from User import User
import json

class UserHandler:

    def __init__(self, admins):
        self.admins = admins

        with open("static/users.json") as inFile:
            usrRaw = json.load(inFile)

        self.users = []

        for raw in usrRaw:
            self.users.append(User.fromDict(raw))

        self.added = []
        for usr in self.users:
            self.added.append(usr.name)

    def usrFor(self, id):
        for usr in self.users:
            if usr.id == id: return usr

        return None

    def newUsr(self, name):
        status = name in self.admins

        newU = User(name, status)

        self.users.append(newU)
        self.added.append(name)

    def has(self, name):
        return name in self.added

    def close(self):
        out = []
        for usr in self.users:
            out.append(usr.toJSON())

        with open("static/users.json", 'w') as outFile:
            json.dump(out, outFile)