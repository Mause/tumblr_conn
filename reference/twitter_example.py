import requests
from requests_oauthlib import OAuth1
from flask import Flask, request, redirect, session
from urlparse import parse_qs
import os

app = Flask(__name__)

# This information is obtained upon registration of a new client on twitter
key = u"<your client key>"
secret = u"<your client secret>"
request_url = u"https://api.twitter.com/oauth/request_token"
auth_url = u"http://api.twitter.com/oauth/authorize"
access_url = u"https://api.twitter.com/oauth/access_token"
update_url = u"http://api.twitter.com/1/statuses/update.json"


@app.route("/")
def demo():
    """ Step 1 of the authentication workflow, obtain a temporary
    resource owner key and use it to redirect the user. The user
    will authorize the client (our flask app) to access its resources
    and perform actions in its name (aka get feed and post updates)."""

    # In this step you will need to supply your twitter provided key and secret
    twitter = OAuth1(key, client_secret=secret)

    # We will be using the default method of supplying parameters, which is
    # in the authorization header.
    r = requests.post(request_url, auth=twitter)

    # Extract the temporary resource owner key from the response
    token = parse_qs(r.content)[u"oauth_token"][0]

    # Create the redirection url and send the user to twitter
    # This is the start of Step 2
    auth = u"{url}?oauth_token={token}".format(url=auth_url, token=token)
    return redirect(auth)


@app.route("/callback", methods=["GET", "POST"])
def callback():
    """ Step 2 & 3 of the workflow. The user has now been redirected back to
    the callback URL you defined when you registered your client on twitter.
    This marks the end of step 2. In step 3 we will obtain the resource owner
    credentials. The callback url query will include 2 extra parameters that we
    need, the verifier and token (which is the same temporary key that we
    obtained in step 1."""

    verifier = request.args.get(u"oauth_verifier")
    token = request.args.get(u"oauth_token")

    # In this step we also use the verifier
    twitter = OAuth1(key, client_secret=secret, resource_owner_key=token,
                     verifier=verifier)
    r = requests.post(access_url, auth=twitter)

    # This is the end of Step 3, we can now extract resource owner key & secret
    # as well as some extra information such as screen name.
    info = parse_qs(r.content)

    # Save credentials in the session, it is VERY important that these are not
    # shown to the resource owner, Flask session cookies are
    # encrypted so we are ok.
    session["access_token"] = info["oauth_token"][0]
    session["token_secret"] = info["oauth_token_secret"][0]
    session["screen_name"] = info["screen_name"][0]

    # Show a very basic status update form
    return """<html><head></head><body>
    <form method="POST" action="/post">
    <input name="status_update" type="text" value="hello"/>
    <input type="submit" value="Send"/>
    </form></body></html>"""


@app.route("/post", methods=["POST"])
def post_update():
    """ After obtaining resource owner credentials we can start interacting
    with the twitter API. We will take the status update from the form in the
    previous step and tweet it."""

    update = request.form["status_update"]
    post = {u"status": update}

    token_secret = session["token_secret"]
    access_token = session["access_token"]

    # Now we will use both client key & secret as well as resource owner key &
    # secret
    twitter = OAuth1(key,
                     resource_owner_key=access_token,
                     resource_owner_secret=token_secret,
                     client_secret=secret)

    # Send the tweet, dont forget to include data =)
    requests.post(update_url, data=post, auth=twitter)

    # Loo and behold the tweet!
    return redirect("https://twitter.com/#!/%s" % session["screen_name"])

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(debug=True)
