from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status

SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
bearer_scheme = HTTPBearer()

'''
Function to create access token using "ACCESS_TOKEN_EXPIRE_MINUTES", "SECRET_KEY", "ALGORITHM" and data dictionary given
- function is called in login api in auth.py router
'''
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


'''
Function to create refresh token using "REFRESH_TOKEN_EXPIRE_MINUTES", "SECRET_KEY", "ALGORITHM" and data dictionary given
- function is called in login api in auth.py router
'''
def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


'''
Function to decode access and refresh token using "token", "SECRET_KEY" and "ALGORITHM"
- function is called in login api in auth.py router
'''
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload if "exp" in payload else None
    except JWTError:
        return None


'''
Function is used to get the current user logged in credentials using decoding of access token
'''
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    data = credentials.credentials
    try:
        payload = jwt.decode(data, SECRET_KEY, algorithms=[ALGORITHM])
        email: str=payload.get('sub')
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )