import json
from Post import Post
from User import User
from UserHandler import UserHandler
import pymongo
import copy

class PostHandler:

    def __init__(self, database, name="main"):
        self.name = name

        self.posts = []
        self.postCount = 0

        for raw in database.find():
            self.posts.append(Post.fromDict(raw))
            self.postCount += 1

        self.database = database

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

        self.database.insert(newP.toJSON())

    def postReply(self, msg, curUsr, parentID):
        parent = self.postFor(parentID)
        if parent is None: return

        new_index = self.posts.index(parent) + len(self.children_of(parentID)) + 1

        plst = copy.copy(parent.parents)
        plst.append(parent.id)

        newP = Post(msg, curUsr.id, parents=plst, level=parent.level+1)

        curUsr.replied()

        self.posts.insert(new_index, newP)
        self.postCount += 1

        self.database.insert(newP.toJSON())

    def editPost(self, id, msg):
        post = self.postFor(id)
        if post is None: return
        post.modify(msg)

        self.database.update_one({"_id":post.id}, {"$set":{"message":post.message}})

    def deletePost(self, id):
        # print(id)
        p = self.postFor(id)
        # print(p)

        if p in self.posts: self.posts.remove(p)

        toDelete = []

        for po in self.posts:
            if int(id) in po.parents:
                toDelete.append(po.id)

        print(toDelete)

        for cid in toDelete:
            child = self.postFor(cid)
            if child in self.posts: self.posts.remove(child)

        self.database.delete_one({"_id":int(id)})


    def getRendered(self, usrHandler):
        out = []

        for post in self.posts:
            out.append(post.render(usrHandler))

        return out

    def clear(self):
        self.posts = []
        self.postCount = 0
        self.database.delete_many({})
