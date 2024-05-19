import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from flask import redirect, url_for, session, request

cred = credentials.Certificate('credentials.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def add_message(user_id, message, sender):
  doc_ref = db.collection(u'users').document(user_id).collection(u'messages').document()
  doc_ref.set({
      u'message': message,
      u'sender': sender,
      u'timestamp': firestore.SERVER_TIMESTAMP
  })
    
def get_messages(user_id):
  messages_ref = db.collection(u'users').document(user_id).collection(u'messages')
  messages = messages_ref.order_by(u'timestamp').stream()

  messages_list = []
  for message in messages:
    message_dict = message.to_dict()
    timestamp = message_dict['timestamp']
    message_dict['timestamp'] = [timestamp.strftime('%H:%M'), timestamp.strftime('%d %b %Y')]
    messages_list.append(message_dict)

  return messages_list

def create_user(username, password):
  user_doc = db.collection('users').document(username).get()
  if user_doc.exists:
    return False
  else:
    user_data = {'password': generate_password_hash(password)}
    db.collection('users').document(username).set(user_data)
    return True
    
def login_user(username, password):
  user_doc = db.collection('users').document(username).get().to_dict()
  if user_doc and check_password_hash(user_doc['password'], password):
    return True
  else:
    return False