from flask import Flask, request, jsonify
from helper.openai_api import chat_completion
from helper.twilio_api import send_message
from flask_caching import Cache
import random

app = Flask(__name__)

# Store conversation state per user
conversations = {}

# Initialize caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# List of mood-based response templates
mood_responses = {
    'happy': {
        'template': "I'm glad to hear that you're feeling happy!",
        'followup': [
            "Keep spreading the positivity! 😄",
            "What's making you feel happy today?",
            "Happiness is contagious. Have a fantastic day! 🌞"
        ]
    },
    'sad': {
        'template': "I'm sorry to hear that you're feeling sad. Is there anything I can do to help?",
        'followup': [
            "Remember, you're not alone. I'm here to listen.",
            "Take some time for self-care and do something that brings you joy.",
            "Sending you virtual hugs. Stay strong! 🤗"
        ]
    },
    'angry': {
        'template': "I understand that you're feeling angry. Take a deep breath and let's work through it together.",
        'followup': [
            "Anger is a natural emotion. Let's find a constructive way to channel it.",
            "It's okay to be angry. Let's talk it out and find a solution.",
            "Take a moment to pause and reflect. We'll address the anger together. 😊"
        ]
    },
    'confused': {
        'template': "I can sense your confusion. Don't worry, I'm here to provide clarity and answers.",
        'followup': [
            "Confusion is an opportunity for growth. Let's explore and find answers together.",
            "What specifically are you confused about? Let's break it down step by step.",
            "Curiosity and confusion often go hand in hand. Embrace the journey of discovery! 🚀"
        ]
    },
    'neutral': {
        'template': "It seems like you're in a neutral mood. How can I assist you today?",
        'followup': [
            "Feel free to ask me anything you'd like to know.",
            "I'm here to help. What can I do for you?",
            "Let's make the most of this conversation. How can I make your day better? 😊"
        ]
    },
    'excited': {
        'template': "Wow! Your excitement is contagious. What's got you so thrilled?",
        'followup': [
            "Your enthusiasm is inspiring. Share your excitement with me!",
            "I love seeing your excitement. What's the best part about it?",
            "Embrace the thrill and enjoy the ride! 🎉"
        ]
    },
    'grateful': {
        'template': "Expressing gratitude is a beautiful thing. I'm grateful to have this conversation with you.",
        'followup': [
            "Gratitude uplifts the spirit. What are you grateful for today?",
            "Gratefulness brings joy. Share something you're thankful for!",
            "Your positive outlook is admirable. Keep the gratitude flowing! 🙏"
        ]
    },
    'frustrated': {
        'template': "I can sense your frustration. Let's work together to find a solution.",
        'followup': [
            "Frustration can be an opportunity for growth. How can I assist you in overcoming your frustrations?",
            "Let's break down the source of your frustration and brainstorm potential solutions.",
            "Remember, challenges are stepping stones to success! 💪"
        ]
    },
    'curious': {
        'template': "Your curiosity is admirable. Feel free to ask me anything you'd like to know.",
        'followup': [
            "Curiosity is the key to learning. What knowledge are you seeking today?",
            "I'm here to satisfy your curiosity. Ask me any question!",
            "Keep the curiosity alive. The pursuit of knowledge knows no bounds! 🧠"
        ]
    },
    'tired': {
        'template': "I understand that you're feeling tired. Take a break and recharge. I'll be here when you're ready.",
        'followup': [
            "Self-care is important. Take some time to relax and rejuvenate.",
            "Rest is crucial for well-being. Make sure to take care of yourself.",
            "Remember, a refreshed mind and body perform at their best! 💤"
        ]
    }
}


@app.route('/')
def home():
    return jsonify({
        'status': 'OK',
        'webhook_url': 'BASEURL/twilio/receiveMessage',
        'message': 'The webhook is ready.',
        'video_url': 'https://youtu.be/y9NRLnPXsb0'
    })


@app.route('/twilio/receiveMessage', methods=['POST'])
def receive_message():
    try:
        # Extract incoming parameters from Twilio
        message = request.form['Body']
        sender_id = request.form['From']

        # Retrieve or create conversation state for the user
        if sender_id not in conversations:
            conversations[sender_id] = {
                'user_id': random.randint(1, 1000000),
                'context': [],
                'mood': 'neutral',
                'bot_name': 'salmon bhai',
                'developer_name': 'aditya kaushal'
            }
        conversation = conversations[sender_id]

        # Check if the message contains any bad words
        if contains_bad_word(message.lower()):
            response = generate_savage_reply()

            # Add user turn to conversation context
            conversation['context'].append({
                'role': 'user',
                'message': message
            })

            # Add bot turn to conversation context
            conversation['context'].append({
                'role': 'bot',
                'message': response
            })
        else:
            # Add user turn to conversation context
            conversation['context'].append({
                'role': 'user',
                'message': message
            })

            # Detect user mood
            mood = detect_mood(message)

            # Update conversation mood
            conversation['mood'] = mood

            # Print user's response
            print("User:", message)

            # Generate response
            response = generate_response(conversation)

            # Print bot's reply
            print("Bot:", response)

            # Add bot turn to conversation context
            conversation['context'].append({
                'role': 'bot',
                'message': response
            })

            # Learn from user interaction
            learn_from_interaction(conversation)

        # Send the response back to Twilio
        send_message(sender_id, response)
    except Exception as e:
        print(f"Error: {e}")
    return 'OK', 200

def contains_bad_word(message):
    bad_words = ['maderchod','arse','arsehole','as useful as tits on a bull','balls','bastard','beaver','beef curtains','bell','bellend','bent','berk','bint','bitch','blighter','blimey','blimey oreilly','bloodclaat','bloody','bloody hell','blooming','bollocks','bonk','bugger','bugger me','bugger off','built like a brick shit-house','bukkake','bullshit','cack','cad','chav','cheese eating surrender monkey','choad','chuffer','clunge','cobblers','cock','cock cheese','cock jockey','cock-up','cocksucker','cockwomble','codger','cor blimey','corey','cow','crap','crikey','cunt','daft','daft cow','damn','dick','dickhead','did he bollocks!','did i fuck as like!','dildo','dodgy','duffer','fanny','feck','flaps','fuck','fuck me sideways!','fucking cunt','fucktard','gash','ginger','git','gob shite','goddam','gorblimey','gordon bennett','gormless','he is a knob','hell','hobknocker','Id rather snort my own cum','jesus christ','jizz','knob','knobber','knobend','knobhead','ligger','like fucking a dying mans handshake','mad as a hatter','manky','minge','minger','minging','motherfucker','munter','muppet','naff','nitwit','nonce','numpty','nutter','off their rocker','penguin','pillock','pish','piss off','piss-flaps','pissed','pissed off','play the five-fingered flute','plonker','ponce','poof','pouf','poxy','prat','prick','prick','prickteaser','punani','punny','pussy','randy','rapey','rat arsed','rotter','rubbish','scrubber','shag','shit','shite','shitfaced','skank','slag','slapper','slut','snatch','sod','sod-off','son of a bitch','spunk','stick it up your arse!','swine','taking the piss','tart','tits','toff','tosser','trollop','tuss','twat','twonk','u fukin wanker','wally','wanker','wankstain','wazzack','whore'] # Define a list of bad words
    message = message.lower()
    for word in bad_words:
        if word in message:
            return True
    return False


def generate_savage_reply():
    replies = [
        "Oh, did you think I'd get offended by that? Nice try!",
        "You must be a keyboard warrior with that language!",
        "My developer programmed me to ignore bad words. Better luck next time!",
        "Is that the best insult you can come up with? I'm disappointed!",
        "Sorry, I don't speak bad word language. Try again with something creative!",
    ]
    return random.choice(replies)



def detect_mood(message: str) -> str:
    # Convert the message to lowercase for case-insensitive matching
    message = message.lower()

    # Define keyword lists for different moods
    happy_keywords = ['happy', 'joyful', 'excited', 'delighted']
    sad_keywords = ['sad', 'depressed', 'unhappy', 'heartbroken']
    angry_keywords = ['angry', 'frustrated', 'mad', 'irritated']
    confused_keywords = ['confused', 'puzzled', 'bewildered', 'uncertain']
    neutral_keywords = ['neutral', 'okay', 'fine', 'normal']

    # Check if any of the mood keywords are present in the message
    if any(keyword in message for keyword in happy_keywords):
        return 'happy'
    elif any(keyword in message for keyword in sad_keywords):
        return 'sad'
    elif any(keyword in message for keyword in angry_keywords):
        return 'angry'
    elif any(keyword in message for keyword in confused_keywords):
        return 'confused'
    elif any(keyword in message for keyword in neutral_keywords):
        return 'neutral'
    else:
        return 'neutral'  # Default to neutral mood if no keywords match


def generate_response(conversation):
    # Get the current user mood
    mood = conversation['mood']

    # Get the mood-based response template
    response_template = mood_responses[mood]['template']

    # Generate response from OpenAI
    user_messages = [turn['message'] for turn in conversation['context'] if turn['role'] == 'user']
    prompt = '\n'.join(user_messages)
    response = chat_completion(prompt, str(conversation['user_id']), language='en')
    # Add developer name
    response += "\n\n- *Made by Aditya Kaushal*"

    return response


def learn_from_interaction(conversation):
    # TODO: Implement learning logic based on user interaction
    pass


if __name__ == '__main__':
    app.run()
