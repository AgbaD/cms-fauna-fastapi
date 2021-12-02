import os
import jwt
import uuid
from typing import Optional
from pydantic import BaseModel
from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient
from datetime import datetime, timedelta
from fastapi import FastAPI, Path, Query, Header
from utils import User, UpdateUser, UserLogin, Post, UpdatePost
from utils import hash_password, create_server_client


app = FastAPI()
# server_client
try:
    sc = create_server_client()
except:
    sc = FaunaClient(secret=os.environ.get('FAUNA_SERVER_SECRET'))


@app.post('/register')
def register(user: User):
    try:
        sc.query(q.get(q.match(q.index("users_by_email"), user.email)))
        return {
            "msg": "error",
            "detail": "Email has been used."
        }
    except:
        sc.query(q.create(q.collection('users'),
                {
                    'data': {
                        "email": user.email,
                        "name": user.name,
                        "password": hash_password(user.password),
                        "pid": str(uuid.uuid4())
                    }
                }
        ))
        return {
            "msg": "success",
            "detail": "Created Successfully"
        }


@app.post('/login')
def login(user: UserLogin):
    try:
        resp = sc.query(q.get(q.match(q.index("users_by_email"), user.email)))
        if hash_password(user.password) == resp['data']['password']:
            token = jwt.encode({
                'email': resp['data']['email'],
                'exp': datetime.utcnow() + timedelta(minutes=30)
            }, os.environ.get('SECRET_KEY'), "HS256")
            return {
                "msg": "success",
                "data": {
                    "token": token
                }
            }
    except:
        pass
    return {
        "msg": "error",
        "detail": "Email or password is incorrect"
    }


# token required
@app.get("/get-user")
def get_user(x_access_token: str = Header(None)):
    try:
        data = jwt.decode(x_access_token, os.environ.get('SECRET_KEY'),
                          algorithms=['HS256'])
        user = sc.query(q.get(q.match(q.index("users_by_email"), data['email'])))
        user = user['data']
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"]
        }
    except Exception:
        return {
            'status': 'error',
            'msg': 'Token is invalid'
        }


@app.post("/update-user/{user_id}")
def update_user(user: UpdateUser, x_access_token: str = Header(None)):
    try:
        data = jwt.decode(x_access_token, os.environ.get('SECRET_KEY'),
                          algorithms=['HS256'])
        resp = sc.query(q.get(q.match(q.index("users_by_email"), data['email'])))
        uid = resp['data']['id']
        data = {}
        if user.email is not None:
            data["email"] = user.email
        if user.name is not None:
            data["name"] = user.name
        if user.password is not None:
            data["password"] = hash_password(user.password)

        sc.query(q.replace(q.ref(q.collection("users"), uid), {"data": data}))
        return {
            "msg": "success",
            "detail": "User updated successfully"
        }
    except Exception:
        return {
            'status': 'error',
            'msg': 'Token is invalid'
        }





















