import os
from datetime import datetime

import pandas
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
password = os.environ.get('EMAIL_PWD')
smtp_server = "smtp-mail.outlook.com"
smpt_port = "587"


def reddit_auth(clientid: str, clientsecret: str, username: str, pwd: str) -> str:
    """
    Function to get the access token from Reddit API
    :param clientid: Client ID of the App
    :param clientsecret: Client Secret of the app
    :param username: Username of the account
    :param pwd: Password of the account
    :return: access_token if the response is OK else -1
    """
    auth = HTTPBasicAuth(clientid, clientsecret)
    data = {'grant_type': 'password',
            'username': username,
            'password': pwd}
    headers = {'User-Agent': 'MyBot/2.0.1'}

    res = requests.post('https://www.reddit.com/api/v1/access_token',
                        auth=auth, data=data, headers=headers)
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
    headers = {'User-Agent': 'MyBot/0.0.1', 'Authorization': f"bearer {token}"}
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
    if len(result.json()) > 0:
        records =[]
        for post in result.json()['data']['children']:
            # append relevant data to dataframe
            records.append({
                'subreddit': post['data']['subreddit'],
                'title': post['data']['title'],
                'url': post['data']['url'],
                'upvote_ratio': post['data']['upvote_ratio'],
                'ups': post['data']['ups'],
                'downs': post['data']['downs'],
                'score': post['data']['score']
            })
        df = pd.DataFrame.from_records(records)
        df = df.sort_values('score', ascending=False)
        return df.reset_index(drop=True)
    else:
        return -1


def send_mail(news_df):
    message = MIMEMultipart("alternative")
    message["Subject"] = f"Reddit News Update for {datetime.now().date()}"
    message["From"] = sender_email
    message["To"] = receiver_email

    head = f"""\
    Please find below the news update for today:
    """

    body = """\
    <html>
      <head></head>
      <body>
        {0}
      </body>
    </html>
    """.format(news_df.to_html())

    part1 = MIMEText(head, "plain")
    message.attach(part1)

    part2 = MIMEText(body, "html")
    message.attach(part2)

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, smpt_port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())


if __name__ == '__main__':
    # Get the access token
    token = reddit_auth(client_id, client_secret, user_name, password)
    # Call the API
    result = get_data_from_api(reddit_news_url, token)
    # Parse the data
    data = parse_post_data(result)
    # Convert the data to CSV
    data.to_csv(output_file)
    # Send out email
    send_mail(data)
