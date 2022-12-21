import praw
from prawcore import RequestException
import json
import schedule
import datetime
import time

with open("credentials.json") as f:
    creds = json.load(f)

reddit = praw.Reddit(
        client_id=creds['client_id'],
        client_secret=creds['client_secret'],
        user_agent=creds['user_agent'],
        redirect_uri=creds['redirect_uri'],
        refresh_token=creds['refresh_token'],
        ratelimit_seconds=900
)

def post(frequency):
    with open("./subreddits.json","r") as f:
        subredditsJson = json.loads(f.read())
    for subredditName, subredditData in subredditsJson.items():
        if subredditData["enabled"] and subredditData["frequency"] == frequency:
            subreddit = reddit.subreddit(subredditName)
            generatedSelftext = generateSelftext(subredditData["discordAllowed"])
            flairId = getFlairId(subreddit, subredditData["flair"])
            try:
                submission = subreddit.submit(title=subredditData["title"], flair_id=flairId, selftext=generatedSelftext)
                logMan(frequency + " post has been made in r/" + submission.subreddit.display_name)
            except praw.RedditAPIException as exception:
                for subException in exception.items:
                    logMan("ERROR {0}: {1}".format(subException.error_type, subException.message))
                    logMan("Failed to post on r/" + subredditName)

def checkMessages():
    hits=["server","dc","discord","minecraft","skyfall","invite"]
    unreadMessages = reddit.inbox.unread()
    for message in unreadMessages:
        shouldReply = False
        for hit in hits:
            if hit in message.body.lower() or hit in message.subject.lower():
                shouldReply = True
        if message.author.name == "welcomebot":
            shouldReply = False
        if shouldReply:
            logMan("Message received from u/" + message.author.name)
            replyMessage = "Hey there! Here's the discord invite: https://discord.gg/b9hXBPCgGY see you soon!"
            try:
                messageResponse = message.reply(replyMessage)
                logMan("Replied to u/" + message.author.name)
            except praw.RedditAPIException as exception:
                for subException in exception.items:
                    logMan("Failed to reply to {0}".format(message.author.name))
                    logMan("ERROR {0}: {1}".format(subException.error_type, subException.message))
        message.mark_read() 
    
def generateSelftext(discordAllowed):
    post = ""
    if discordAllowed:
        with open("./post","r") as f:
            post = f.read()
    else:
        with open("./postNoDiscord","r") as f:
            post = f.read()
    return post 

def getFlairId(subreddit, flairtext):
    if not flairtext:
        return None
    flairs = list(subreddit.flair.link_templates.user_selectable())
    flair_id = next(x for x in flairs if flairtext in x["flair_text"])["flair_template_id"]
    return flair_id

def logMan(logMessage):
    logMessage = "[" + str(datetime.datetime.now()) + "] " + logMessage + "\n"
    print(logMessage)
    with open("log","a") as f:
        f.write(logMessage)

schedule.every().friday.at("18:00").do(post, "weekly")
schedule.every().day.at("18:00").do(post, "daily")

logMan("Skyfall Poster is up and running!")

while True:
    try:
        schedule.run_pending()
        checkMessages()
        time.sleep(10)
    except RequestException as exception:
        logMan(str(exception))


    