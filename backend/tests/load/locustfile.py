from locust import HttpUser, task, between
import random

class KnowledgeBaseUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def search_query(self):
        queries = [
            "машинное обучение",
            "конституция рф",
            "язык java",
            "жизненный цикл",
            "fastapi",
            "maven"
        ]
        random_query = random.choice(queries)
        self.client.get(f"/api/v1/documents/search?q={random_query}", name="/api/v1/documents/search")
