import os
import hashlib
from typing import Optional
from pydantic import BaseModel
from faunadb import query as q
from faunadb.client import FaunaClient


class User(BaseModel):
    name: str
    email: str
    password: str


class UpdateUser(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class Post(BaseModel):
    title: str
    content: str


class UpdatePost(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


def hash_password(password):
    return hashlib.sha512(password.encode()).hexdigest()


def create_server_client():
    """
    :return: server_client
    """
    client = FaunaClient(secret="fnAEZmczZcACTLUwK1s910UUxFb4Zz3GePk31s2X")

    client.query(q.create_collection({"name": "users"}))
    client.query(q.create_index(
        {
            "name": "users_by_email",
            "source": q.collection("users"),
            "permissions": {"read": "public"},
            "terms": [{"field": ["data", "email"]}],
            "unique": True
        }
    ))

    client.query(q.create_collection({"name": "posts"}))
    client.query(q.create_index(
        {
            "name": "posts_by_email",
            "source": q.collection("users"),
            "terms": [{"field": ["data", "email"]}],
        }
    ))
    client.query(q.create_index(
        {
            "name": "posts_by_id",
            "source": q.collection("users"),
            "terms": [{"field": ["data", "id"]}],
        }
    ))

    return client
