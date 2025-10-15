from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from sqlalchemy.orm import Session
from app.models.auth_model import User, Tokens
from app.schemas.auth_schema import UserSignup, UserLogin
from app.auth_utils import create_access_token, create_refresh_token, decode_token
from passlib.context import CryptContext

router = APIRouter(prefix = "/api/auth", tags = ["Authentication"])

# Register user with username, email, password
@router.post("/signup")
def signup(data: UserSignup, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == data.email).first()
        if existing_user:
            db.rollback()
            raise HTTPException(status = status.HTTP_400_BAD_REQUEST, detail = "Email already registered")
        
        # Encrytion of password
        hashed_password = CryptContext(schemes=["bcrypt"], deprecated="auto").hash(data.password)
        new_user = User(username=data.username, email=data.email, password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "status": status.HTTP_201_CREATED,
            "message": "User registerion created successfully",
            "data": {
                "username": new_user.username,
                "email": new_user.email
            }
        }
    except HTTPException as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }


# Authenticaton with email and password
@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == data.email).first()

        # Email and password validation
        if not user or not CryptContext(schemes=["bcrypt"], deprecated="auto").verify(data.password, user.password):
            raise HTTPException(status = status.HTTP_401_UNAUTHORIZED, detail = "Invalid email or password")
        
        existing_token = db.query(Tokens).filter(Tokens.u_id == user.id).first()
        if existing_token:
            # Check access token validity
            access_payload = decode_token(existing_token.access_token)
            if access_payload:
                return {
                    "status": status.HTTP_202_ACCEPTED,
                    "message": "Login successful using existing access token",
                    "data": {
                        "access_token": existing_token.access_token,
                        "refresh_token": existing_token.refresh_token,
                        "token_type": "bearer",
                        "email": user.email,
                        "username": user.username
                    }
                }
            
            # Access expired → check refresh token
            refresh_payload = decode_token(existing_token.refresh_token)
            if refresh_payload:
                new_access_token = create_access_token(data={"sub": user.email, "user_type": user.user_type})
                existing_token.access_token = new_access_token
                db.commit()
                return {
                    "status": status.HTTP_202_ACCEPTED,
                    "message": "Login successful using refresh token to generate access token",
                    "data": {
                        "access_token": new_access_token,
                        "refresh_token": existing_token.refresh_token,
                        "token_type": "bearer",
                        "email": user.email,
                        "username": user.username
                    }
                }

            # Both expired → issue new pair
            new_access_token = create_access_token(data={"sub": user.email, "user_type": user.user_type})
            new_refresh_token = create_refresh_token(data={"sub": user.email,"user_type": user.user_type})
            existing_token.access_token = new_access_token
            existing_token.refresh_token = new_refresh_token
            db.commit()
            return {
                "status": status.HTTP_202_ACCEPTED,
                "message": "Login successful (new tokens issued)",
                "data": {
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token,
                    "token_type": "bearer",
                    "email": user.email,
                    "username": user.username
                }
            }

        else:
            # No token record → create new
            access_token = create_access_token(data={"sub": user.email, "user_type": user.user_type})
            refresh_token = create_refresh_token(data={"sub": user.email, "user_type": user.user_type})
            new_tokens = Tokens(u_id=user.id, access_token=access_token, refresh_token=refresh_token)
            db.add(new_tokens)
            db.commit()
            return {
                "status": status.HTTP_202_ACCEPTED,
                "message": "Login successful (new token entry created)",
                "data": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "email": user.email,
                    "username": user.username
                }
            }
    except Exception as e:
        db.rollback()
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "detail": e
        }
