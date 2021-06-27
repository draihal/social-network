# -------------------FastApi tutorial---------------------
# https://fastapi.tiangolo.com/tutorial
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from fastapi import (
    Body,
    Cookie,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Request,
    UploadFile,
)
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, EmailStr, Field
from starlette.exceptions import HTTPException as StarletteHTTPException


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


class Item(BaseModel):
    name: str = Field(..., example="Foo")
    description: Optional[str] = Field(None, example="A very nice Item")
    price: float = Field(..., example=35.4)
    tax: Optional[float] = Field(None, example=3.2)

    # class Config:  # or
    #     schema_extra = {
    #         "example": {
    #             "name": "Foo",
    #             "description": "A very nice Item",
    #             "price": 35.4,
    #             "tax": 3.2,
    #         }
    #     }


class User(BaseModel):
    username: str
    full_name: Optional[str] = None


app = FastAPI()

fake_items_db = [
    {"item_name": "Foo"},
    {"item_name": "Bar"},
    {"item_name": "Baz"},
]


@app.get("/")
async def root() -> dict:
    return {"message": "Hello World"}


# http://127.0.0.1:8000/items/foo?short=1
# http://127.0.0.1:8000/items/foo?short=True
# http://127.0.0.1:8000/items/foo?short=true
# http://127.0.0.1:8000/items/foo?short=on
# http://127.0.0.1:8000/items/foo?short=yes
@app.get("/items/{item_id}")
async def read_item(
    item_id: str, q: Optional[str] = None, short: bool = False
) -> dict:
    item = {"item_id": item_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {
                "description": "This is an amazing item that has a long description"
            }
        )
    return item


# http://127.0.0.1:8000/items/foo-item?needy=sooooneedy
@app.get("/items2/{item_id}")
async def read_user_item2(
    item_id: str, needy: str, skip: int = 0, limit: Optional[int] = None
) -> dict:
    item = {"item_id": item_id, "needy": needy}
    return item


# http://127.0.0.1:8000/items/?skip=0&limit=10
@app.get("/fake_items_db/")
async def read_fake_items_db(
    skip: int = 0, limit: int = 10
) -> List[Dict[str, Any]]:
    return fake_items_db[skip : skip + limit]


@app.get("/users/me")
async def read_user_me() -> dict:
    return {"user_id": "the current user"}


@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
    user_id: int, item_id: str, q: Optional[str] = None, short: bool = False
) -> dict:
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {
                "description": "This is an amazing item that has a long description"
            }
        )
    return item


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName) -> dict:
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


@app.get("/files/{file_path:path}")
async def read_file(file_path: str) -> dict:
    return {"file_path": file_path}


# -------------------Request Body part---------------------
@app.post("/items/")
async def create_item(
    item: Item = Body(
        ...,
        examples={
            "normal": {
                "summary": "A normal example",
                "description": "A **normal** item works correctly.",
                "value": {
                    "name": "Foo",
                    "description": "A very nice Item",
                    "price": 35.4,
                    "tax": 3.2,
                },
            },
            "converted": {
                "summary": "An example with converted data",
                "description": "FastAPI can convert price `strings` to actual `numbers` automatically",
                "value": {
                    "name": "Bar",
                    "price": "35.4",
                },
            },
            "invalid": {
                "summary": "Invalid data is rejected with an error",
                "value": {
                    "name": "Baz",
                    "price": "thirty five point four",
                },
            },
        },
    ),
) -> dict:
    item_dict = item.dict()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict


@app.put("/items2/{item_id}")
async def create_item2(
    item_id: int,
    item: Item = Body(
        ...,
        example={
            "name": "Foo",
            "description": "A very nice Item",
            "price": 35.4,
            "tax": 3.2,
        },
    ),
) -> dict:
    return {"item_id": item_id, **item.dict()}


# declare body, path and query parameters, all at the same time
# If the parameter is also declared in the path,
# it will be used as a path parameter.
# If the parameter is of a singular type (like int, float, str, bool, etc)
# it will be interpreted as a query parameter.
# If the parameter is declared to be of the type of a Pydantic model,
# it will be interpreted as a request body.
@app.put("/items3/{item_id}")
async def create_item3(
    item_id: int, item: Item, q: Optional[str] = None
) -> dict:
    result = {"item_id": item_id, **item.dict()}
    if q:
        result.update({"q": q})  # type: ignore
    return result


# ----------------Query Parameters and String Validations---------------------
@app.get("/items/")
async def read_items(
    q: Optional[str] = Query(
        None,
        min_length=3,
        max_length=50,
        regex="^fixedquery$",
        title="Query string",
        description="Query string for the items to search in the database that have a good match",
        alias="item-query",  # == ?item-query=foobaritems
        deprecated=True,
    )
    # q: str = Query(..., min_length=3)
    # -----
    # http://localhost:8000/items/?q=foo&q=bar
    # q: Optional[List[str]] = Query(None)
    # To declare a query parameter with a type of list,
    # like in the example above, you need to explicitly use Query,
    # otherwise it would be interpreted as a request body.
) -> dict:
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})  # type: ignore
    return results


# ----------------Path Parameters and Numeric Validations---------------------
@app.get("/items4/{item_id}")
async def read_items4(
    item_id: int = Path(..., title="The ID of the item to get"),
    q: Optional[str] = Query(None, alias="item-query"),
) -> dict:
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})  # type: ignore
    return results


# Order the parameters as you need, tricks
# async def read_items(
#     *, item_id: int = Path(..., title="The ID of the item to get"), q: str
# ):


# ----------------Body - Multiple Parameters---------------------
@app.put("/items5/{item_id}")
async def update_item5(
    *,
    item_id: int = Path(..., title="The ID of the item to get", ge=0, le=1000),
    q: Optional[str] = None,
    item: Optional[Item] = None,
) -> dict:
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})  # type: ignore
    if item:
        results.update({"item": item})  # type: ignore
    return results


# Multiple body parameters
# {
#     "item": {
#         "name": "Foo",
#         "description": "The pretender",
#         "price": 42.0,
#         "tax": 3.2
#     },
#     "user": {
#         "username": "dave",
#         "full_name": "Dave Grohl"
#     }
# }
@app.put("/items6/{item_id}")
async def update_item6(item_id: int, item: Item, user: User) -> dict:
    results = {"item_id": item_id, "item": item, "user": user}
    return results


# Singular values in body
# {
#     "item": {
#         "name": "Foo",
#         "description": "The pretender",
#         "price": 42.0,
#         "tax": 3.2
#     },
#     "user": {
#         "username": "dave",
#         "full_name": "Dave Grohl"
#     },
#     "importance": 5
# }
@app.put("/items7/{item_id}")
async def update_item7(
    item_id: int, item: Item, user: User, importance: int = Body(...)
) -> dict:
    results = {
        "item_id": item_id,
        "item": item,
        "user": user,
        "importance": importance,
    }
    return results


# Embed a single body parameter
# {
#     "item": {
#         "name": "Foo",
#         "description": "The pretender",
#         "price": 42.0,
#         "tax": 3.2
#     }
# }
# instead of:
# {
#     "name": "Foo",
#     "description": "The pretender",
#     "price": 42.0,
#     "tax": 3.2
# }
@app.put("/items8/{item_id}")
async def update_item8(
    item_id: int, item: Item = Body(..., embed=True)
) -> dict:
    results = {"item_id": item_id, "item": item}
    return results


# ----------------Extra Data Types---------------------
@app.put("/items9/{item_id}")
async def read_items9(
    item_id: UUID,
    start_datetime: Optional[datetime] = Body(None),
    end_datetime: Optional[datetime] = Body(None),
    repeat_at: Optional[time] = Body(None),
    process_after: Optional[timedelta] = Body(None),
) -> dict:
    start_process = start_datetime + process_after  # type: ignore
    duration = end_datetime - start_process  # type: ignore
    return {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "repeat_at": repeat_at,
        "process_after": process_after,
        "start_process": start_process,
        "duration": duration,
    }


# ----------------Cookie Parameters---------------------
@app.get("/items10/")
async def read_items10(ads_id: Optional[str] = Cookie(None)) -> dict:
    return {"ads_id": ads_id}


# ----------------Header Parameters---------------------
@app.get("/items11/")
async def read_items11(user_agent: Optional[str] = Header(None)) -> dict:
    return {"User-Agent": user_agent}


# ----------------Response Model---------------------
@app.post("/items12/", response_model=Item)
async def create_item12(item: Item) -> Item:
    return item


class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: Optional[str] = None


class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None


@app.post("/user/", response_model=UserOut)
async def create_user(user: UserIn):  # type: ignore
    return user


# Response Model encoding parameters
class Item2(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: float = 10.5
    tags: List[str] = []


items = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {
        "name": "Bar",
        "description": "The bartenders",
        "price": 62,
        "tax": 20.2,
    },
    "baz": {
        "name": "Baz",
        "description": None,
        "price": 50.2,
        "tax": 10.5,
        "tags": [],
    },
}


@app.get(
    "/items13/{item_id}",
    response_model=Item2,
    response_model_exclude_unset=True,
    # response_model_exclude_defaults=True,
    # response_model_exclude_none=True,
    # response_model_include={"name", "description"},
    # response_model_exclude={"tax"}
)
async def read_item13(item_id: str):  # type: ignore
    return items[item_id]


# ----------------Response Model---------------------
# application/x-www-form-urlencoded
@app.post("/login/")
async def login(username: str = Form(...), password: str = Form(...)) -> dict:
    return {"username": username}


# ----------------Request Files---------------------
# pip install python-multipart !!!
# multipart/form-data

# Have in mind that this means that the whole contents will be stored in memory.
# This will work well for small files.
@app.post("/files/")
async def create_file(file: bytes = File(...)) -> dict:
    return {"file_size": len(file)}


# "spooled" file: A file stored in memory up to a maximum size limit,
# and after passing this limit it will be stored in disk.
# This means that it will work well for large files like images,
# videos, large binaries, etc. without consuming all the memory.
# You can get metadata from the uploaded file.
# It has a file-like async interface.
# It exposes an actual Python SpooledTemporaryFile object that
# you can pass directly to other libraries that expect a file-like object.
@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)) -> dict:
    return {"filename": file.filename}


# UploadFile inherits directly from Starlette's UploadFile,
# but adds some necessary parts to make it compatible with Pydantic
#  and the other parts of FastAPI.


@app.post("/files/")
async def create_files(files: List[bytes] = File(...)) -> dict:
    return {"file_sizes": [len(file) for file in files]}


@app.post("/uploadfiles/")
async def create_upload_files(files: List[UploadFile] = File(...)) -> dict:
    return {"filenames": [file.filename for file in files]}


@app.get("/")
async def main() -> HTMLResponse:
    content = """
<body>
    <form action="/files/" enctype="multipart/form-data" method="post">
        <input name="files" type="file" multiple>
        <input type="submit">
    </form>
    <form action="/uploadfiles/" enctype="multipart/form-data" method="post">
        <input name="files" type="file" multiple>
        <input type="submit">
    </form>
</body>
    """
    return HTMLResponse(content=content)


# ----------------Request Forms and Files---------------------
@app.post("/files2/")
async def create_file2(
    file: bytes = File(...),
    fileb: UploadFile = File(...),
    token: str = Form(...),
) -> dict:
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
    }


# ----------------Handling Errors---------------------
items = {"foo": "The Foo Wrestlers"}


@app.get("/items-header/{item_id}")
async def read_item_header(item_id: str) -> dict:
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "There goes my error"},
        )
    return {"item": items[item_id]}


class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name


@app.exception_handler(UnicornException)
async def unicorn_exception_handler(
    request: Request, exc: UnicornException
) -> JSONResponse:
    return JSONResponse(
        status_code=418,
        content={
            "message": f"Oops! {exc.name} did something. There goes a rainbow..."
        },
    )


@app.get("/unicorns/{name}")
async def read_unicorn(name: str) -> dict:
    if name == "yolo":
        raise UnicornException(name=name)
    return {"unicorn_name": name}


# 1 validation error
# path -> item_id
#   value is not a valid integer (type=type_error.integer)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> PlainTextResponse:
    return PlainTextResponse(str(exc), status_code=400)


@app.get("/items15/{item_id}")
async def read_item15(item_id: int) -> dict:
    if item_id == 3:
        raise HTTPException(status_code=418, detail="Nope! I don't like 3.")
    return {"item_id": item_id}


# -------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> PlainTextResponse:
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


@app.get("/items16/{item_id}")
async def read_item16(item_id: int) -> dict:
    if item_id == 3:
        raise HTTPException(status_code=418, detail="Nope! I don't like 3.")
    return {"item_id": item_id}


# {
#   "detail": [
#     {
#       "loc": [
#         "body",
#         "size"
#       ],
#       "msg": "value is not a valid integer",
#       "type": "type_error.integer"
#     }
#   ],
#   "body": {
#     "title": "towel",
#     "size": "XL"
#   }
# }
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(
#     request: Request, exc: RequestValidationError
# ):
#     return JSONResponse(
#         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#         content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
#     )


# -------------
# from fastapi.exception_handlers import (
#     http_exception_handler,
#     request_validation_exception_handler,
# )
# @app.exception_handler(StarletteHTTPException)
# async def custom_http_exception_handler(request, exc):
#     print(f"OMG! An HTTP error!: {repr(exc)}")
#     return await http_exception_handler(request, exc)


# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request, exc):
#     print(f"OMG! The client sent invalid data!: {exc}")
#     return await request_validation_exception_handler(request, exc)


# -------------Tags------------
@app.post(
    "/items17/",
    response_model=Item,
    tags=["items"],
    summary="Create an item",
    response_description="The created item",
    # deprecated=True,
    description="Create an item with all the information, name, description, price, tax and a set of unique tags",
)
async def create_item17(item: Item) -> Item:
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
    #  Markdown
    return item


@app.get("/items18/", tags=["items"])
async def read_items18() -> List[Dict[str, Union[str, int]]]:
    return [{"name": "Foo", "price": 42}]


@app.get("/users19/", tags=["users"])
async def read_users19() -> List[Dict[str, str]]:
    return [{"username": "johndoe"}]


# ----------------JSON Compatible Encoder---------------------
fake_db = {}


class Item3(BaseModel):
    title: str
    timestamp: datetime
    description: Optional[str] = None


# It receives an object, like a Pydantic model,
# and returns a JSON compatible version.
# The result of calling it is something that can be
# encoded with the Python standard json.dumps().
# It doesn't return a large str containing the data in JSON format
# (as a string). It returns a Python standard data structure
# (e.g. a dict) with values and sub-values that are all compatible with JSON.
# jsonable_encoder is actually used by FastAPI internally to convert data.
# But it is useful in many other scenarios.
@app.put("/items20/{id}")
def update_item20(id: str, item: Item) -> None:
    json_compatible_item_data = jsonable_encoder(item)
    fake_db[id] = json_compatible_item_data
