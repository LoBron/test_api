import sqlalchemy
import pydantic
import databases
from fastapi import FastAPI
from typing import List

DATABASE_URL = 'postgresql://postgres:1@localhost:5432/test'

metadata = sqlalchemy.MetaData()

posts = sqlalchemy.Table(
    'posts',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('author', sqlalchemy.String),
    sqlalchemy.Column('body', sqlalchemy.String),
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

class PostAdd(pydantic.BaseModel):
    author: str
    body: str

class Post(pydantic.BaseModel):
    id: int
    author: str
    body: str


app = FastAPI(title='async_blog')
database = databases.Database(DATABASE_URL)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event('shutdown')
async def shutdown():
    await database.disconnect()


@app.post("/posts/", response_model=Post)
async def create(post:PostAdd):
    query = posts.insert().values(body=post.body, author=post.author)
    id_ = await database.execute(query)
    return {"id": id_, **post.dict()}

@app.get("/posts/", response_model=List[Post])
async def get_all():
    query = posts.select()
    return await database.fetch_all(query)

@app.put("/posts/{post_id}", response_model=Post)
async def update(post_id: int, payload: PostAdd):
    query = posts.update().where(posts.c.id == post_id).values(body=payload.body, author=payload.author)
    await database.execute(query)
    return {'id': post_id, **payload.dict()}

@app.delete("/posts/{post_id}")
async def remove(post_id: int):
    query = posts.delete().where(posts.c.id == post_id)
    await database.execute(query)
    return {'message': f'Post {post_id} deleted'}