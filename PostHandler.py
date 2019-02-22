import json
from Post import Post
from User import User
from UserHandler import UserHandler

class PostHandler:

    def __init__(self, name="main"):
        with open("static/%s_posts.json" % name) as inFile:
            postsRaw = json.load(inFile)

        self.name = name

        self.posts = []
        self.postCount = 0

        for raw in postsRaw:
            self.posts.append(Post.fromDict(raw))
            self.postCount += 1

    def postFor(self, id):
        for post in self.posts:
            if int(post.id) == int(id): return post

        return None
    def children_of(self, pID):
        out = []

        for post in self.posts:
            if pID in post.parents:
                out.append(post)

        return out

    def post(self, msg, curUsr):
        newP = Post(msg, curUsr.id)
        self.posts.append(newP)
        self.postCount += 1
        curUsr.posted()

    def postReply(self, msg, curUsr, parentID):
        parent = self.postFor(parentID)

        new_index = self.posts.index(parent) + len(self.children_of(parentID)) + 1

        newP = Post(msg, curUsr.id, parents=parent.parents.append(parentID), level=parent.level+1)

        curUsr.replied()

        self.posts.insert(new_index, newP)
        self.postCount += 1

    def editPost(self, id, msg):
        post = self.postFor(id)
        post.modify(msg)

    def deletePost(self, id):
        print(id)
        p = self.postFor(id)
        print(p)

        self.posts.remove(p)

    def getRendered(self, usrHandler):
        out = []

        for post in self.posts:
            out.append(post.render(usrHandler))

        return out

    def clear(self):
        self.posts = []
        self.postCount = 0

    def close(self):
        out = []
        for post in self.posts:
            out.append(post.toJSON())

        with open("static/%s_posts.json" % self.name, 'w') as outFile:
            json.dump(out, outFile)
