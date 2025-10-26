import praw          # For Reddit API
import requests      
import os            
import re            
import time      
import json    

# Open and read the JSON file of API keys
with open('../reddit_api_key.json', 'r') as file:
    data = json.load(file)
#print(data)
    
CLIENT_ID = data['CLIENT_ID']
CLIENT_SECRET = data['CLIENT_SECRET']	
USER_AGENT = data['USER_AGENT']
#print(CLIENT_ID)
#print(CLIENT_SECRET)
#print(USER_AGENT)

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

TOPIC_LIST = [
    "christmas"
    "fruitcake",
    "meatloaf",
    "new year’s",
    "pie",
	"fried rice",
    "beef noodles",
    "ramen",
    "alfredo chicken pasta",
    "xiaolongbao",
    "egg salad sandwich",
    "oyakodon",
    "bibimbap",
    "Kung Pao Chicken",
    "Nasi Goreng",
    "Pad Thai",
    "Bulgogi",
    "Samosas",
    "Mapo Tofu"
]
   
SUBREDDIT_NAME = "recipes" 

def save_image_local(url, topic_name):
    if not url:
        print("image not foud in the URL")
        return None
    if "preview" in url:
        filename_postfix = url.split("/")[3].split("?")[0][:-4]
        file_extension = "png"
    else:
        filename_postfix = url[18:-4]
        file_extension = "jpg"

    filename = f"{topic_name.replace(' ', '_').capitalize()}_{filename_postfix}.{file_extension}"
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status() # check http error
        
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        
        return filename
    except requests.exceptions.RequestException as e:
        # download failed (404 or overtime)
        print(f"image download {url} error: {e}")
        return None

def get_recipe_info(topic):
    # Formatting (to get points)
    print(f"\n#############################################################")
    print(f"Topic: {topic.capitalize()}")

    best_submission = None
    max_upvotes = -1

    # 1. Search and filter the best post
    try:
        # Search r/recipes，sort with popularity
        search_results = reddit.subreddit(SUBREDDIT_NAME).search(
            query=topic,
            sort='hot',
            limit=50,
            time_filter='all'
        )
        
        for submission in search_results:
            # Check 'link flair text' property to make sure the post is a recipe
            flair = getattr(submission, 'link_flair_text', None)
            valid_categories = ["beef", "dessert", "fruit\vegetarian", "pork", "poultry", "recipe", "seafood"]
            if flair and any(category in flair.lower() for category in valid_categories):
                if submission.score > max_upvotes:
                    max_upvotes = submission.score
                    best_submission = submission
    
    except Exception as e:
        print(f"Error during the search of {topic}: {e}")
        return
    
    if not best_submission:
        print(f"No '{topic.capitalize()}' related and 'Recipes' tagged best recipe")
        return
        
    # 2. Recipt Title (to get points)
    recipe_title = best_submission.title
    print(f"\n{recipe_title}")

    # 3. Recipe Content (to get points)
    recipe_content = ""
    
    if best_submission.selftext:
        recipe_content = best_submission.selftext
    else:
        best_submission.comments.replace_more(limit=0)
        top_comments = best_submission.comments.list()
        if top_comments:
            top_comments.sort(key=lambda c: getattr(c, 'score', 0), reverse=True)
            if top_comments[0].score >= 1 and len(top_comments[0].body) > 50:
                 recipe_content = f"Recipe from the comments：\n{top_comments[0].body}"

    # remove Markdown characters or html entities.(e.g. &#x200B;)
    cleaned_content = re.sub(r'&#x200B;|\*\*\*|\*\*|>', '', recipe_content).strip()
    
    print("\n==== Recipe Contents Start ====")
    print(cleaned_content)
    print("==== Recipe Contents End ====")

    # 4. Save the image to local drive (to get points)
    image_url = best_submission.url
    saved_file = None
    
    # image_url may not be an image
    # checking preview
    if image_url.endswith(('.jpg', '.png', '.gif', '.heic', '.webp')):
        saved_file = save_image_local(image_url, topic)
    elif hasattr(best_submission, 'preview') and 'images' in best_submission.preview:
        # try PRAW preview (more reliable)
        try: 
            preview_url = best_submission.preview['images']['source']['url']
        except TypeError:
            preview_url = best_submission.preview['images'][0]['source']['url']

        saved_file = save_image_local(preview_url, topic)

    if saved_file:
        print(f"\nSaved local file: {saved_file}")
    else:
        print(f"\nImage image not found or not downloadable.")
        
    # 5. username of the post (to get points)
    try:
        username = best_submission.author.name
    except AttributeError:
        username = "[deleted or unknown]"
        
    print(f"Source: u/{username}")
    print(f"#############################################################")


if __name__ == "__main__":
    for required_topic in TOPIC_LIST:
        get_recipe_info(required_topic)
        #print(f"getting recipes of {required_topic}")
        time.sleep(2) # to comply the reddit rate limit
    print("\nAll recipes are collected！")
