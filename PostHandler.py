import json
from Post import Post
from User import User
from UserHandler import UserHandler

class PostHandler:

    def __init__(self, name="main"):
        with open("static/%s_posts.json" % name) as inFile:
            postsRaw = json.load(inFile)

        self.posts = []
        self.postCount = 0

        for raw in postsRaw:
            self.posts.append(Post.fromDict(raw))
            self.postCount += 1

    def postFor(self, id):
        for post in self.posts:
            if post.id == id: return post

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

    def postReply(self, msg, curUsr, parentID):
        parent = self.postFor(parentID)

        new_index = self.posts.index(parent) + len(self.children_of(parentID))

        newP = Post(msg, curUsr.id, parents=parent.parents.append(parentID), level=parent.level+1)

        self.posts.insert(new_index, newP)
        self.postCount += 1

    def editPost(self, id, msg):
        post = self.postFor(id)
        post.modify(msg)

    def deletePost(self, id):
        self.posts.remove(self.postFor(id))

    def getRendered(self, curUsr, usrHandler):
        out = []

        for post in self.posts:
            out.append(post.render(curUsr, usrHandler))

        return out

    def close(self):
        out = []
        for post in self.posts:
            out.append(post.toJSON())

        with open("static/%s_posts.json" % name, 'w') as outFile:
            json.dump(out, outFile)
