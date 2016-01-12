#!/usr/bin/env python
"""Listens for incoming emails that represent new comments being posted to a blog entry.
Then we recompile / publish the affected article.
"""

import email.parser, json, poplib, time

import make
from page_info import config, Comment, get_pages

secrets = json.loads(open("secret.json").read())

comments_addr = config["social"]["comment_email"]
comments_user, comments_domain = comments_addr.split("@")

comments_dns = config["mx"][comments_domain]


# Keep track of the number of messages seen, so that we can identify new ones
num_messages_seen = 0
def get_new_messages():
    """Return all messages that *haven't* been handled since starting the daemon"""
    global num_messages_seen

    email_conn = poplib.POP3_SSL(comments_dns["pop_domain"])
    email_conn.user(comments_addr)
    email_conn.pass_(secrets["email"][comments_addr]["password"])

    msg_count = len(email_conn.list()[1])
    for msg_idx in range(num_messages_seen, msg_count):
        msgraw = email_conn.retr(msg_idx + 1) # 1-based indexing
        msgstr = "\n".join(part.decode("utf-8") for part in msgraw[1])
        msg = email.parser.Parser().parsestr(msgstr)
        yield msg
    num_messages_seen = msg_count

    # Some resources may now need to be re-made
    make.make()
    make.publish()

def process_email(message):
    """Check if the message is a comment,
    and if so, save it to disk & regenerate the effected pages"""
    subject = message["subject"]
    tags = []
    # Parse tags
    in_tag = False
    for char in subject:
        if char == "[":
            tags.append("")
            in_tag = True
        elif char == "]":
            in_tag = False
        elif in_tag:
            tags[-1] += char

    # Extract the comment body
    for part in message.walk():
        if part.get_content_type():
            charset = part.get_content_charset()
            content = part.get_payload(decode=True)
            body = content.decode(charset)
            break
    else:
        print("Warning: email contained no body!", message)
        return

    print("received message with tags:", tags, "and body:", body)

    # Find which article this message pertains to
    articles = [b for b in get_pages().blog_entries.values() if b.friendly_path in tags]
    if len(articles) != 1:
        print("[WARN] user attempted to post a comment to %i blog entries" %len(articles))
        return

    article = articles

    # Save the comment to disk
    comment = Comment(page=article, body=body)
    comment.save()

    make.new_dependency(article)

if __name__ == "__main__":
    while True:
        for m in get_new_messages():
            process_email(m)
        time.sleep(config["comments"]["check_interval"])
