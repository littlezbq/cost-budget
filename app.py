from fastapi import FastAPI
import uvicorn
from starlette.middleware.cors import CORSMiddleware

from routers import common
from routers import model_train

app = FastAPI()

origins = [
    "http://localhost:8001",
    "http://localhost:8000",
    "http://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# 添加路由
app.include_router(common.router)
app.include_router(model_train.router)

@app.get("/hello")
async def hello_world():
    return "hello world"


if __name__ == "__main__":
    uvicorn.run(app="app:app", host="0.0.0.0", reload=False, port=8001)
