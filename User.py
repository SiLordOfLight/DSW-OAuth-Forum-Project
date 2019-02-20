from random import randint

class User:

    splashes = {0: "Newbie", 1:"Vogon", 2:"Human", 4:"Hitchhiker", 8:"Towel-carrier", 16:"Editor", 32:"Cricket-Player", 64:"God", 128:"Mouse", 256:"42"}

    def __init__(self, name, admin=False):
        self.name = name
        self.is_admin = admin
        self.ban_level = 0
        self.post_count = 0.0
        self.splash = "Newbie"
        self.hard_splash = False

        self.id = hash(name + str(randint(0,2000)))

    @staticmethod
    def fromDict(input):
        newU = User(input['name'], admin=input['is_admin'])
        newU.ban_level = input['ban_level']
        newU.post_count = input['post_count']
        newU.splash = input['splash']
        newU.hard_splash = input['hard_splash']
        newU.id = input['id']

        return newU

    def toJSON(self):
        return {'name':self.name, 'is_admin':self.is_admin, 'ban_level':self.ban_level, 'post_count':self.post_count, 'splash':self.splash, 'hard_splash':self.hard_splash, 'id':self.id}

    def equals(self, other):
        return self.id == other.id

    def ban(self):
        self.ban_level += 1

    def posted(self):
        self.post_count += 1
        self.recalculateSplash()

    def replied(self):
        self.post_count += 0.5
        self.recalculateSplash()

    def deleted(self):
        self.post_count -= 1
        self.recalculateSplash()

    def recalculateSplash(self):
        if self.hard_splash: return

        for k,v in User.splashes.items():
            if self.post_count > k:
                self.splash = v