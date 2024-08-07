from werkzeug.exceptions import NotFound
from functools import wraps
import requests
from src.config import Config
from google.oauth2.credentials import Credentials
from werkzeug.exceptions import ExpectationFailed
import requests
from google.auth.transport.requests import Request
from src.models.user import User
from src.orm import db

def get_resource_by_id(self, model,model_id, user_id=None, owner_id=None):
        query = model.query.filter(self._model.id == model_id)
        query = query.filter(model.user_id == user_id) if user_id else query
        query = query.filter(model.owner_id == owner_id) if owner_id else query
        return query.first()

def get_user_by_id(self, user_id, model=User):
        user = get_resource_by_id(model,user_id)
        if not user:
            raise NotFound(f'User {user_id} not found')
        return user
    
def auth2_token(scopes,provider=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            selected_provider = provider
            if selected_provider is None:
                selected_provider = kwargs.get('provider_name').value
            if selected_provider in ('aws','frameio'):
                return f(*args,**kwargs)
            if selected_provider == 'dropbox':
                return f(*args,**{**kwargs,**dropbox_authentication(*args,**kwargs)})
            if selected_provider == 'tiktok':
                return f(*args,**{**kwargs,**tiktok_authentication(*args,**kwargs)})
            selected_scopes = scopes
            if selected_scopes is None:
                selected_scopes = getattr(GoogleScopes,selected_provider.upper()).value
            kwargs['scopes'] = selected_scopes
            return f(*args,**{**kwargs,**google_authentication(*args,**kwargs)})
        return wrapper
    return decorator

def google_authentication(*args,**kwargs):
    token_url = "https://oauth2.googleapis.com/token"
    client_id = Config.GOOGLE_CLIENT_ID
    client_secret = Config.GOOGLE_CLIENT_SECRET
    token  = kwargs.get('access_token')
    refresh_token = kwargs.get('refresh_token')
    credentials = Credentials.from_authorized_user_info({
        'token': token,
        'refresh_token': refresh_token,
        'token_uri': token_url,
        'client_id': client_id,
        'client_secret': client_secret,
        'scopes': kwargs.get('scopes')
        })
    if not credentials.refresh_token:
        raise ExpectationFailed('When you initially obtain the OAuth 2.0 token, make sure that your authorization process includes the offline_access')
    if credentials.expired:
        credentials.refresh(Request())
                
    new_access_token = credentials.token
            
    new_refresh_token = credentials.refresh_token
    return dict(credentials=credentials,new_access_token=new_access_token,new_refresh_token=new_refresh_token)

def dropbox_authentication(*args,**kwargs):
    token_url = 'https://api.dropboxapi.com/oauth2/token'
    payload = dict(grant_type='refresh_token',refresh_token = kwargs.get('refresh_token'),client_id=Config.DROPBOX_CLIENT_ID,client_secret=Config.DROPBOX_CLIENT_SECRET)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        }
    try:
        response = requests.post(token_url,data=payload,headers=headers)
        response_json = response.json()
        return response_json
    except Exception as ex:
        print("Error while refreshing the token:", ex)
        raise ExpectationFailed(ex)
    
def tiktok_authentication(*args, **kwargs):
    url = "https://open-api.tiktok.com/oauth/refresh_token/"
    payload = dict(grant_type='refresh_token',refresh_token = kwargs.get('refresh_token'),client_id=Config.TIKTOK_CLIENT_ID)
    try:
        response = requests.post(url,params=payload)
        response_json = response.json()
        return response_json
    except Exception as ex:
        print("Error while refreshing the token:", ex)
        raise ExpectationFailed(ex)  

def save(instance, flush=False):
        db.session.add(instance)
        if flush:
            db.session.flush()
            db.session.refresh(instance)
        return instance