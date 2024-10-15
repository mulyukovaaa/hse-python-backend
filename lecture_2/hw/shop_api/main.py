from fastapi import FastAPI # type: ignore

app = FastAPI(title="Shop API")

carts_db = {}
items_db = {}

