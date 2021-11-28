import os
from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient


adminClient = FaunaClient(secret=os.environ.get('FAUNA_KEY'))
result = adminClient.query(
  q.create_key(
    {"database": q.database("cms-fastapi"), "role": "server"}
  )
)

key = result['secret']
serverClient = FaunaClient(secret=key)


