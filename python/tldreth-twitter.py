# write a python script according to the requirements described in ../requirements.md
# the script should be able to run on a Mac OS X system
# the script should be passed with all the tests in ./test/test_tldreth.py
import os
from dotenv import load_dotenv
import tweepy
from datetime import datetime, timedelta
import pytz
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Initialize Tweepy client
auth = tweepy.OAuthHandler(os.environ.get("TWITTER_API_KEY"), os.environ.get("TWITTER_API_SECRET_KEY"))
auth.set_access_token(os.environ.get("TWITTER_ACCESS_TOKEN"), os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"))
twitter_api = tweepy.API(auth)

def get_recent_tweets(username):
    now = datetime.now(pytz.utc)
    yesterday = now - timedelta(days=1)
    
    recent_tweets = []
    tweets = twitter_api.user_timeline(screen_name=username, count=100, tweet_mode="extended")
    
    for tweet in tweets:
        if tweet.created_at > yesterday and len(tweet.full_text.split()) >= 100:
            recent_tweets.append({
                'text': tweet.full_text,
                'url': f"https://twitter.com/{username}/status/{tweet.id}",
                'created_at': tweet.created_at
            })
    
    return recent_tweets

def generate_title_and_summary(tweet):
    prompt = f"Generate a news title and a summary (max 200 words) for this tweet:\n\n{tweet['text']}"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates titles and summaries for tweets."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        n=1,
        temperature=0.7,
    )
    
    content = response.choices[0].message.content.strip().split("\n\n")
    title = content[0].strip()
    summary = content[1].strip()
    
    return title, summary

def generate_daily_summary(summaries):
    prompt = f"Summarize the following daily summaries into a concise weekly report:\n\n{summaries}"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates concise summaries."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    output_filename = f"tldreth-{today}.md"
    
    with open("twitter-kol.md", "r") as f:
        usernames = [line.strip() for line in f.readlines()]
    
    all_summaries = []
    output_content = f"# tldreth {today}\nSign Up | View Online\n\n## Ethereum news today:\n"
    
    for username in usernames:
        tweets = get_recent_tweets(username)
        for tweet in tweets:
            title, summary = generate_title_and_summary(tweet['text'])
            all_summaries.append(summary)
            output_content += f"\n[**{title}**]({tweet['url']})\n{summary}\n"
    
    daily_summary = generate_daily_summary("\n".join(all_summaries))
    output_content = f"{output_content}\n{daily_summary}\n\nIf you have any comments or feedback, just respond to this email!\n\nThanks for reading,\nBob Jiang"
    
    with open(output_filename, "w") as f:
        f.write(output_content)

if __name__ == "__main__":
    main()
