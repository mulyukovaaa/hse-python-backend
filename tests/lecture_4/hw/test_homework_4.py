import datetime
from http import HTTPStatus

import pytest
from starlette.testclient import TestClient

from lecture_4.demo_service.api.main import create_app
from lecture_4.demo_service.api.contracts import *
from lecture_4.demo_service.core.users import UserInfo, UserService, password_is_longer_than_8


@pytest.fixture
def client():
    demo_service = create_app()

    user_service = UserService(
        password_validators=[
            password_is_longer_than_8,
            lambda pwd: any(char.isdigit() for char in pwd),
        ]
    )

    user_service.register(
        UserInfo(
            username="admin",
            name="admin",
            birthdate=datetime.fromtimestamp(0.0),
            role=UserRole.ADMIN,
            password="superSecretAdminPassword123"
        )
    )

    demo_service.state.user_service = user_service

    with TestClient(demo_service) as client:
        yield client


@pytest.fixture
def user_data():
    return {
        "username": "testuser",
        "name": "Test User",
        "birthdate": "1990-01-01T00:00:00",
        "password": "password1234"
    }

@pytest.fixture
def user_data_wrong():
    return {
        "username": "badgay",
        "name": "John",
        "birthdate": "1992-01-01T00:00:00",
        "password": "password"
    }


@pytest.fixture
def user_data_2():
    return {
        "username": "kaka",
        "name": "kakaUser",
        "birthdate": "1990-01-01T00:00:00",
        "password": "qwerty1234"
    }


@pytest.fixture
def admin_credentials():
    return {
        "username": "admin",
        "password": "superSecretAdminPassword123"
    }


def test_register_user_success(client, user_data):
    response = client.post("/user-register", json=user_data)
    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["name"] == user_data["name"]
    assert data["role"] == UserRole.USER


def test_register_user_bad_password(client, user_data_wrong):
    response = client.post("/user-register", json=user_data_wrong)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()['detail'] == "invalid password"


def test_register_user_invalid_data(client):
    invalid_user_data = {
        "username": "",
        "name": "",
        "birthdate": "1990-01-01T00:00:00",
        "password": "short"
    }
    response = client.post("/user-register", json=invalid_user_data)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "detail" in response.json()


def test_register_existing_user(client, user_data):
    client.post("/user-register", json=user_data)

    response = client.post("/user-register", json=user_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["detail"] == "username is already taken"


def test_get_user_by_myself(client, user_data):
    client.post("/user-register", json=user_data)

    credentials = {"username": user_data["username"], "password": user_data["password"]}
    auth_response = client.post("/user-get",
                                auth=(credentials['username'], credentials['password']),
                                params={"username": user_data["username"]})

    assert auth_response.status_code == HTTPStatus.OK
    data = auth_response.json()
    assert data["username"] == user_data["username"]
    assert data["name"] == user_data["name"]


def test_get_user_by_himself(client, user_data, user_data_2):
    register_response = client.post("/user-register", json=user_data)
    user_id = register_response.json()["uid"]
    register_response2 = client.post("/user-register", json=user_data_2)

    assert register_response.status_code == HTTPStatus.OK
    assert register_response2.status_code == HTTPStatus.OK

    credentials = {"username": user_data_2["username"], "password": user_data_2["password"]}
    auth_response = client.post("/user-get",
                                auth=(credentials['username'], credentials['password']),
                                params={"id": user_id})

    assert auth_response.status_code == HTTPStatus.NOT_FOUND


def test_get_user_bad_credentials(client, user_data):
    client.post("/user-register", json=user_data)

    invalid_credentials = {"username": user_data["username"], "password": "wrongpassword"}
    response = client.post("/user-get", auth=(invalid_credentials['username'], invalid_credentials['password']),
                           params={"username": user_data["username"]})

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_user_both_id_and_username(client, user_data):
    client.post("/user-register", json=user_data)

    response = client.post("/user-get",
                           auth=(user_data['username'], user_data['password']),
                           params={"id": 1, "username": user_data["username"]})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["detail"] == "both id and username are provided"


def test_get_user_without_auth(client, user_data):
    client.post("/user-register", json=user_data)

    response = client.post("/user-get",
                           auth=(user_data['username'], user_data['password']))

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["detail"] == "neither id nor username are provided"


def test_get_user_neither_id_nor_username(client, user_data):
    client.post("/user-register", json=user_data)

    response = client.post("/user-get")

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


def test_promote_user_success(client, user_data, admin_credentials):
    register_response = client.post("/user-register", json=user_data)
    assert register_response.status_code == HTTPStatus.OK
    user_id = register_response.json()["uid"]

    promote_response = client.post("/user-promote", params={"id": user_id},
                                   auth=(admin_credentials['username'], admin_credentials['password']))
    assert promote_response.status_code == HTTPStatus.OK

    get_user_response = client.post("/user-get", params={"id": user_id},
                                    auth=(admin_credentials['username'], admin_credentials['password']))
    assert get_user_response.status_code == HTTPStatus.OK
    assert get_user_response.json()["role"] == UserRole.ADMIN


def test_promote_non_existing_user(client, admin_credentials):
    response = client.post("/user-promote", params={"id": 9999},
                           auth=(admin_credentials['username'], admin_credentials['password']))

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["detail"] == "user not found"


def test_promote_user_without_admin(client, user_data, admin_credentials):
    register_response = client.post("/user-register", json=user_data)
    assert register_response.status_code == HTTPStatus.OK
    user_id = register_response.json()["uid"]

    promote_response = client.post("/user-promote", params={"id": user_id},
                                   auth=(user_data['username'], user_data['password']))
    assert promote_response.status_code == 403


def test_promote_user_without_admin_header(client, user_data):
    auth_headers_user = {
        "Authorization": "Basic dGVzdDpxd2VydHk="
    }
    first_post_resp = client.post("/user-register", json=user_data)
    assert first_post_resp.status_code == 200

    resp = client.post("/user-promote",
                    params={'username': user_data['username']},
                    headers=auth_headers_user)
    assert resp.status_code == HTTPStatus.UNAUTHORIZED




