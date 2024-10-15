import json
from http import HTTPStatus
from math import factorial
from statistics import mean


async def app(scope, receive, send) -> None:
    if scope['type'] == 'lifespan':
        await handle_lifespan(scope, receive, send)
    elif scope['type'] == 'http':
        if scope['method'] != 'GET':
            await send_error(send, HTTPStatus.NOT_FOUND, 'Not found')
            return
        await handle_request(scope, receive, send)


async def handle_lifespan(scope, receive, send):
    while True:
        message = await receive()
        if message['type'] == 'lifespan.startup':
            await send({'type': 'lifespan.startup.complete'})
        elif message['type'] == 'lifespan.shutdown':
            await send({'type': 'lifespan.shutdown.complete'})
            break


async def handle_request(scope, receive, send):
    path_parts = scope['path'].split('/')

    if path_parts[1] == 'factorial':
        await get_factorial(scope, send)
    elif path_parts[1] == 'fibonacci':
        await get_fibonacci(path_parts, send)
    elif path_parts[1] == 'mean':
        await get_mean(receive, send)
    else:
        await send_error(send, HTTPStatus.NOT_FOUND, 'Not found')


async def get_factorial(scope, send):
    query_string = scope['query_string'].decode('utf-8')
    params = dict(param.split('=')
                  for param in query_string.split('&') if '=' in param)

    if 'n' not in params or params['n'].strip() == '':
        await send_error(send, HTTPStatus.UNPROCESSABLE_ENTITY, 'Input must be a non-empty number')
        return

    try:
        number = int(params['n'])
    except ValueError:
        await send_error(send, HTTPStatus.UNPROCESSABLE_ENTITY, 'Input must be a valid integer')
        return

    if number < 0:
        await send_error(send, HTTPStatus.BAD_REQUEST, 'Number must be non-negative')
        return

    result = factorial(number)
    await send_response(send, HTTPStatus.OK, {'result': result})


async def get_fibonacci(path_parts, send):
    if len(path_parts) < 3 or not path_parts[2]:
        await send_error(send, HTTPStatus.UNPROCESSABLE_ENTITY, 'Input must be a non-empty number')
        return

    try:
        number = int(path_parts[2])
    except ValueError:
        await send_error(send, HTTPStatus.UNPROCESSABLE_ENTITY, 'Input must be a valid integer')
        return

    if number < 0:
        await send_error(send, HTTPStatus.BAD_REQUEST, 'Number must be non-negative')
        return

    def fibonacci(n: int) -> int:
        if n == 0:
            return 0
        elif n == 1:
            return 1
        else:
            a, b = 0, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            return b

    result = fibonacci(number)
    await send_response(send, HTTPStatus.OK, {'result': result})


async def get_mean(receive, send):
    request_body = await receive()

    if request_body['type'] != 'http.request':
        await send_error(send, HTTPStatus.UNPROCESSABLE_ENTITY, 'Request must be of type http.request')
        return

    try:
        body = json.loads(request_body['body'].decode('utf-8'))
    except (json.JSONDecodeError, KeyError):
        await send_error(send, HTTPStatus.UNPROCESSABLE_ENTITY, 'Invalid JSON')
        return

    if body is None:
        await send_error(send, HTTPStatus.UNPROCESSABLE_ENTITY, 'Input must not be None')
        return

    if not isinstance(body, list):
        await send_error(send, HTTPStatus.UNPROCESSABLE_ENTITY, 'Input must be an array of numbers')
        return

    if len(body) == 0:
        await send_error(send, HTTPStatus.BAD_REQUEST, 'Array must not be empty')
        return

    try:
        numbers = [float(num) for num in body]
    except ValueError:
        await send_error(send, HTTPStatus.UNPROCESSABLE_ENTITY, 'All elements must be valid numbers')
        return

    mean_value = mean(numbers)
    await send_response(send, HTTPStatus.OK, {'result': mean_value})


async def send_error(send, status_code, message):
    await send_response(send, status_code, {"error": message})


async def send_response(send, status_code, response_message):
    response_body = json.dumps(response_message).encode('utf-8')
    await send({
        'type': 'http.response.start',
        'status': status_code,
        'headers': [(b'content-type', b'application/json')],
    })
    await send({
        'type': 'http.response.body',
        'body': response_body,
    })
