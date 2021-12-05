import os
import jwt
import uuid
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
    sc = FaunaClient(secret='fnAEZmczZcACTLUwK1s910UUxFb4Zz3GePk31s2X')
secret_key = "WZSqFa847EZhAuc9965"


@app.post('/register')
def register(user: User):
    try:
        sc.query(q.get(q.match(q.index("users_by_email"), user.email)))
        return {
            "msg": "error",
            "detail": "Email has been used."
        }
    except:
        sc.query(q.create(q.collection('users'), {
            'data': {
                "email": user.email,
                "name": user.name,
                "password": hash_password(user.password),
                "pid": str(uuid.uuid4())
            }
        }))
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
            }, secret_key, "HS256")
            return {
                "msg": "success",
                "data": {
                    "token": token
                }
            }
        else:
            return {
                "msg": "error",
                "detail": "Email or password is incorrect"
            }
    except Exception as e:
        return {
            "msg": "error",
            "detail": e
        }


# token required
@app.get("/get-user")
def get_user(x_access_token: str = Header(None)):
    try:
        data = jwt.decode(x_access_token, secret_key,
                          algorithms=['HS256'])
    except Exception:
        return {
            'msg': 'error',
            'details': 'Token is invalid'
        }
    try:
        user = sc.query(q.get(q.match(q.index("users_by_email"), data['email'])))
    except:
        return {
            'msg': 'error',
            'details': 'User not found'
        }
    user_id = user['ref'].id()
    user = user['data']
    return {
        "id": user_id,
        "email": user["email"],
        "name": user["name"]
    }


@app.post("/update-user")
def update_user(user: UpdateUser, x_access_token: str = Header(None)):
    try:
        data = jwt.decode(x_access_token, secret_key,
                          algorithms=['HS256'])
    except Exception:
        return {
            'msg': 'error',
            'details': 'Token is invalid'
        }
    try:
        resp = sc.query(q.get(q.match(q.index("users_by_email"), data['email'])))
    except:
        return {
            'msg': 'error',
            'details': 'User not found'
        }
    uid = resp['ref'].id()
    data = {}
    if user.email is not None:
        data["email"] = user.email
    if user.name is not None:
        data["name"] = user.name
    if user.password is not None:
        data["password"] = hash_password(user.password)

    sc.query(q.update(q.ref(q.collection("users"), uid), {"data": data}))
    return {
        "msg": "success",
        "details": "User updated successfully"
    }


@app.delete('/delete-user')
def delete_user(x_access_token: str = Header(None)):
    try:
        data = jwt.decode(x_access_token, secret_key,
                          algorithms=['HS256'])
    except Exception:
        return {
            'msg': 'error',
            'details': 'Token is invalid'
        }
    try:
        resp = sc.query(q.get(q.match(q.index("users_by_email"), data['email'])))
    except:
        return {
            'msg': 'error',
            'details': 'User not found'
        }
    uid = resp['ref'].id()
    sc.query(q.delete(q.ref(q.collection("users"), uid)))
    return {
        "msg": "success",
        "details": "User deleted successfully"
    }


@app.post('/create-post')
def create_post(post: Post, x_access_token: str = Header(None)):
    try:
        data = jwt.decode(x_access_token, secret_key,
                          algorithms=['HS256'])
    except Exception:
        return {
            'msg': 'error',
            'details': 'Token is invalid'
        }
    try:
        resp = sc.query(q.get(q.match(q.index("users_by_email"), data['email'])))
    except:
        return {
            'msg': 'error',
            'details': 'User not found'
        }
    author = resp['data']['name']
    sc.query(q.create(q.collection('posts'), {
        'data': {
            "author": author,
            "title": post.title,
            "content": post.content,
            "pid": str(uuid.uuid4())
        }
    }))
    return {
        "msg": "success",
        "details": "Post created successfully"
    }


@app.post('/edit-post/{post_id}')
def edit_post(post_id: str, post: UpdatePost, x_access_token: str = Header(None)):
    try:
        data = jwt.decode(x_access_token, secret_key,
                          algorithms=['HS256'])
    except Exception:
        return {
            'msg': 'error',
            'details': 'Token is invalid'
        }
    try:
        resp = sc.query(q.get(q.match(q.index("users_by_email"), data['email'])))
    except:
        return {
            'msg': 'error',
            'details': 'User not found'
        }
    user_name = resp['data']['name']
    try:
        result = sc.query(q.get(q.ref(q.collection("posts"), post_id)))
    except:
        return {
            'msg': 'error',
            'details': "Post not found"
        }

    post_res = result['data']
    if post_res['author'] != user_name:
        return {
            "msg": "error",
            "details": "You do not have permission to perform action"
        }
    data = {}
    if post.title is not None:
        data['title'] = post.title
    if post.content is not None:
        data['content'] = post.content

    sc.query(q.update(q.ref(q.collection("posts"), post_id), {"data": data}))
    return {
        "msg": "success",
        "details": "Post updated successfully"
    }


@app.delete('/delete-post/{post_id}')
def delete_post(post_id: str, x_access_token: str = Header(None)):
    try:
        data = jwt.decode(x_access_token, secret_key,
                          algorithms=['HS256'])
    except Exception:
        return {
            'msg': 'error',
            'details': 'Token is invalid'
        }
    try:
        resp = sc.query(q.get(q.match(q.index("users_by_email"), data['email'])))
    except:
        return {
            'msg': 'error',
            'details': 'User not found'
        }
    user_name = resp['data']['name']
    try:
        result = sc.query(q.get(q.ref(q.collection("posts"), post_id)))
    except:
        return {
            'msg': 'error',
            'details': "Post not found"
        }
    post_res = result['data']
    if post_res['author'] != user_name:
        return {
            "msg": "error",
            "details": "You do not have permission to perform action"
        }
    sc.query(q.delete(q.ref(q.collection("posts"), post_id)))
    return {
        "msg": "success",
        "details": "Post deleted successfully"
    }


# get all posts by user
@app.get('/all-posts')
def all_posts(x_access_token: str = Header(None)):
    try:
        data = jwt.decode(x_access_token, secret_key,
                          algorithms=['HS256'])
    except Exception:
        return {
            'msg': 'error',
            'details': 'Token is invalid'
        }
    try:
        resp = sc.query(q.get(q.match(q.index("users_by_email"), data['email'])))
    except:
        return {
            'msg': 'error',
            'details': 'User not found'
        }
    author = resp['data']['name']
    try:
        result = sc.query(q.get(q.match(q.index("posts_by_author"), author)))
        print(result)
    except:
        return {
            'msg': 'error',
            'details': "Posts not found"
        }



# get all posts
# get post by id







