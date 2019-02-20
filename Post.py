from datetime import datetime
import json
from UserHandler import UserHandler
from User import User

class Post:

    def __init__(self, msg, senderID, parents=[], level=0):
        self.message = msg
        self.sender = senderID
        self.parents = parents
        self.level = level
        self.timestamp = datetime.now().strftime("%m/%d %H:%M:%S")
        self.id = hash(str(self.sender)+self.timestamp)

        self.editTime = "na"

    @staticmethod
    def fromDict(input):
        newP = Post(input['message'], input['sender'], parents=input['parents'], level=input['level'])
        newP.timestamp = input['timestamp']
        newP.id = input['id']

        return newP

    def toJSON(self):
        return {'message':self.message, 'sender':self.sender, 'parents':self.parents, 'level':self.level, 'timestamp':self.timestamp, 'id':self.id}

    def modify(self, newMsg):
        self.message = newMsg
        self.editTime = datetime.now().strftime("%m/%d %H:%M:%S")

    def render(self, usrHandler):
        srcUsr = usrHandler.usrFor(self.sender)
        print(self.sender)

        if srcUsr.ban_level > 0:
            bgCol = "rgb(230,50,50)"
            txtCol = "black"
        else:
            bgCol = "rgb(55,131,246)"
            txtCol = "white"

        margin = self.level * 20

        senderName = srcUsr.name
        senderSplash = srcUsr.splash if srcUsr.ban_level == 0 else "Spawn of Satan"

        postTime = self.timestamp
        editTime = "<h6>Edited: %s</h6>" % self.editTime if self.editTime != "na" else ""

        message = self.message if srcUsr.ban_level < 2 else "<b>THIS USER HAS BEEN EXCOMMUNICATED</b>"

        postID = self.id

        if usrHandler.current.ban_level == 0:
            button1 = "<button type=\"submit\" formaction=\"/replyPost\" class=\"btn btn-success\" style=\"border-top-left-radius: 0px\;\">Reply</button>"
        else:
            button1 = "<button type=\"submit\" formaction=\"/reprimand\" class=\"btn btn-danger\" style=\"border-top-left-radius: 0px\;\">XXX</button>"

        if usrHandler.current.equals(srcUsr):
            button2 = "<button type=\"submit\" formaction=\"/editPost\" class=\"btn btn-warning\">Edit</button>"
        else:
            button2 = ""

        if usrHandler.current.equals(srcUsr) or usrHandler.current.is_admin:
            button3 = "<button type=\"submit\" formaction=\"/deletePost\" class=\"btn btn-danger\">Delete</button>"
        else:
            button3 = ""

        return """
        <div class="row post-msg" style="
                margin-top: 5px;
                background-color: %s;
                border-radius: 10px;
                padding: 0px;
                margin-left: %ipx;
                color: %s">

            <div class="col-lg-auto" style="
                    border-right: dashed white 1px;
                    padding-top: 5px;
                    padding-bottom: 5px;">
                <h4>%s</h4>
                <h6>%s</h6>
            	<h6>%s</h6>
                %s
            </div>

            <div class="col-lg" style="
                    padding-top: 5px;
                    padding-bottom: 5px;">
                <p>%s</p>
            </div>

            <div class="col-lg-1" style="padding-right: 0px;">
                <form action="/replyPost" method="post">
                    <input type="hidden" name="msgID" value="%s">

                    <div class="btn-group-vertical" style="width: 100%%;">
                        %s

                        %s

                        %s
                    </div>
                </form>
            </div>
        </div>""" % (bgCol,margin,txtCol,senderName,senderSplash,postTime,editTime,message,postID,button1,button2,button3)
