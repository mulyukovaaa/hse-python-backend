from locust import HttpUser, task, between
import uuid
import random

class ShopUser(HttpUser):
    wait_time = between(1, 3)  # Задержка между запросами от 1 до 3 секунд

    def on_start(self):
        """Будет выполнено, когда пользователь начинает."""
        self.item_ids = []
        self.cart_id = None
        self.create_items()

    def create_items(self):
        """Создание нескольких товаров для тестирования."""
        for _ in range(5):  # Создаём 5 товаров
            item_id = uuid.uuid4()
            response = self.client.post("/item", json={
                "name": f"Item {item_id}",
                "price": random.uniform(10, 100)
            })
            if response.status_code == 201:
                self.item_ids.append(item_id)

    @task(1)
    def create_cart(self):
        """Создание новой корзины."""
        response = self.client.post("/cart")
        if response.status_code == 201:
            self.cart_id = response.json()["id"]

    @task(2)
    def get_cart(self):
        """Получение информации о корзине."""
        if self.cart_id:
            self.client.get(f"/cart/{self.cart_id}")

    @task(3)
    def get_items(self):
        """Получение списка товаров."""
        self.client.get("/item")

    @task(4)
    def get_carts(self):
        """Получение списка корзин."""
        self.client.get("/cart")

