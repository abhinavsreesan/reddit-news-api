import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from email.mime.text import MIMEText

import pandas
import pandas as pd
import requests
from discord import SyncWebhook
from requests.auth import HTTPBasicAuth

# Reddit API URL to Call
reddit_news_url = 'https://oauth.reddit.com/r/news/hot'

# Output File Name
output_file = f'data/news_{datetime.now().date()}.csv'

# Reddit API Config Details
client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
user_name = os.environ.get('USER_NAME')
password = os.environ.get('PASSWORD')

# Email Config
sender_email = os.environ.get('SENDER_EMAIL')
receiver_email = os.environ.get('RECEIVER_EMAIL')
email_password = os.environ.get('EMAIL_PWD')
smtp_server = "smtp.gmail.com"
smpt_port = "465"

# Discord Config
web_hook = os.environ.get('DISCORD_WEBHOOK')


def reddit_auth() -> str:
    """
    Function to get the access token from Reddit API
    :param clientid: Client ID of the App
    :param clientsecret: Client Secret of the app
    :param username: Username of the account
    :param pwd: Password of the account
    :return: access_token if the response is OK else -1
    """
    auth = HTTPBasicAuth(client_id, client_secret)
    data = {'grant_type': 'password',
            'username': user_name,
            'password': password}
    headers = {'User-Agent': 'Github1', 'Content-Type': 'application/x-www-form-urlencoded'}

    res = requests.post('https://www.reddit.com/api/v1/access_token', auth=auth, data=data, headers=headers)
    if res.status_code == 200:
        access_token = res.json()['access_token']
        return access_token
    else:
        return -1


def get_data_from_api(api_url: str, token: str) -> requests:
    """
    Function to get data from the Reddit API
    :param api_url: URL of the Reddit API
    :param token: Token received from the Auth URL
    :return: Return the request output if status is OK else -1
    """
    headers = {'User-Agent': 'Github', 'Authorization': f"bearer {token}"}
    res = requests.get(api_url, headers=headers)
    if res.status_code == 200:
        return res
    else:
        return -1


def parse_post_data(result: str) -> pandas.DataFrame:
    """
    Function to parse the Reddit API output into a pandas datafrome
    :param result: Output from the API Request
    :return: A pandas dataframe if the API output has data else -1
    """
    webhook = SyncWebhook.from_url(web_hook)
    webhook.send(f"News For {datetime.now().date()}")
    if len(result.json()) > 0:
        records =[]
        for post in result.json()['data']['children']:
            current_record = {
                'subreddit': post['data']['subreddit'],
                'title': post['data']['title'],
                'url': post['data']['url'],
                'upvote_ratio': post['data']['upvote_ratio'],
                'ups': post['data']['ups'],
                'downs': post['data']['downs'],
                'score': post['data']['score']
            }
            # append relevant data to dataframe
            records.append(current_record)
            webhook.send(f"{post['data']['title']} : {post['data']['url']}")
        df = pd.DataFrame.from_records(records)
        df = df.sort_values('score', ascending=False)
        return df.reset_index(drop=True)
    else:
        return -1


def send_mail(news_df):
    today = datetime.now()
    date_formatted = today.strftime("%B %d, %Y")
    subject = f'Reddit News for {date_formatted}'
    body = """\
        <html>
          <head></head>
          <body>
            {0}
          </body>
        </html>
        """.format(news_df.to_html())
    em = EmailMessage()
    em['From'] = sender_email
    em['To'] = receiver_email
    em['Subject'] = subject
    body_html = MIMEText(body, "html")
    em.set_content(body_html)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, smpt_port, context=context) as smtp:
        smtp.login(sender_email, email_password)
        smtp.sendmail(sender_email, receiver_email, em.as_string())


def send_discord_message(file_path):
    webhook = SyncWebhook.from_url(web_hook)
    webhook.send(file=file_path)


if __name__ == '__main__':
    # Get the access token
    token = reddit_auth()
    # Call the API
    result = get_data_from_api(reddit_news_url, token)
    # Parse the data
    data = parse_post_data(result)
    # Convert the data to CSV
    data.to_csv(output_file)
    # Send out email
    # send_mail(data)
    #send_discord_message(data)
