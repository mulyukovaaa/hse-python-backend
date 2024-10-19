from http import HTTPStatus
from typing import Optional, Dict
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Query, Response
from lecture_2.hw.shop_api.models import (
    WannaCreateItem,
    Item,
    Cart,
    CartInItem,
    CartAnswerList,
    UpdateItem)

app = FastAPI(title='Shop API')
#
items: Dict[UUID, Item] = {}
carts: Dict[UUID, Cart] = {}


def check_item_exist(id_check: UUID):
    if id_check not in items:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Item {id_check} does not exist")


def check_cart_exist(id_check: UUID):
    if id_check not in carts:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Cart {id_check} does not exist")


@app.post('/item', status_code=HTTPStatus.CREATED)
def create_item(request: WannaCreateItem):
    new_id = uuid4()
    item = Item(
        id=new_id,
        name=request.name,
        price=request.price
    )
    items[new_id] = item
    return item.model_dump()


@app.post('/cart', status_code=HTTPStatus.CREATED)
def create_cart(response: Response):
    new_id = uuid4()
    cart = Cart(id=new_id)
    carts[new_id] = cart
    response.headers['location'] = f"/cart/{new_id}"
    return {'id': new_id}


def get_cart_response(cart: Cart):
    item_counts = {}
    for item_id in cart.items:
        item_counts[item_id] = item_counts.get(item_id, 0) + 1

    items_list = []
    for item_id, count in item_counts.items():
        item = items.get(item_id)
        if item:
            items_list.append(
                CartInItem(
                    id=item_id,
                    name=item.name,
                    quantity=count,
                    available=not item.deleted
                )
            )

    price = sum(item.quantity * items[item.id].price for item in items_list if item.available)
    return CartAnswerList(
        id=cart.id,
        items=items_list,
        price=price,
    )


@app.get('/cart/{id_req}')
def get_cart(id_req: UUID):
    check_cart_exist(id_req)
    return get_cart_response(carts[id_req])


@app.get('/item/{id_req}')
def get_item(id_req: UUID):
    check_item_exist(id_req)
    item = items[id_req]
    if item.deleted:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Item {id} was deleted")
    return item.model_dump()


@app.delete('/item/{id_req}')
def delete_item(id_req: UUID):
    check_item_exist(id_req)
    items[id_req].deleted = True


@app.post('/cart/{cart_id}/add/{item_id}')
def add_item_to_cart(cart_id: UUID, item_id: UUID):
    check_cart_exist(cart_id)
    check_item_exist(item_id)
    carts[cart_id].items.append(item_id)


@app.patch('/item/{item_id}')
def patch_item(response: Response, item_id: UUID, request: UpdateItem):
    check_item_exist(item_id)
    curr_item = items[item_id]
    if curr_item.deleted:
        response.status_code = HTTPStatus.NOT_MODIFIED
        return curr_item
    if request.name is not None:
        curr_item.name = request.name
    if request.price:
        curr_item.price = request.price
    return curr_item


@app.put('/item/{item_id}')
def put_item(item_id: UUID, request: WannaCreateItem):
    check_item_exist(item_id)
    curr_item = items[item_id]
    curr_item.name = request.name
    curr_item.price = request.price
    return curr_item


@app.get('/cart')
def get_carts_params(
        offset: Optional[int] = Query(0, ge=0),
        limit: Optional[int] = Query(10, gt=0),
        min_price: Optional[float] = Query(None, ge=0),
        max_price: Optional[float] = Query(None, ge=0),
        min_quantity: Optional[int] = Query(None, ge=0),
        max_quantity: Optional[int] = Query(None, ge=0)):
    carts_list = [get_cart_response(cart) for cart in carts.values()]
    carts_filtered = [
        cart for cart in carts_list
        if (min_price is None or cart.price >= min_price) and
           (max_price is None or cart.price <= max_price) and
           (min_quantity is None or sum(item.quantity for item in cart.items) >= min_quantity) and
           (max_quantity is None or sum(item.quantity for item in cart.items) <= max_quantity)
    ]
    return carts_filtered[offset: min(len(carts_list), offset + limit)]


@app.get('/item')
def get_items(
        offset: Optional[int] = Query(0, ge=0),
        limit: Optional[int] = Query(10, gt=0),
        min_price: Optional[float] = Query(None, ge=0),
        max_price: Optional[float] = Query(None, ge=0),
        show_deleted: Optional[bool] = Query(True)):
    items_filtered = [
        item for item in items.values()
        if (not min_price or item.price >= min_price) and
           (not max_price or item.price <= max_price) and
           (show_deleted or not item.deleted)
    ]
    return items_filtered[offset: min(len(items_filtered), offset + limit)]
