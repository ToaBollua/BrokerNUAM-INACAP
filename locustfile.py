from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        # Loguearse primero
        self.client.post("/accounts/login/", {
            "username": "admin", 
            "password": "admin",
            "csrfmiddlewaretoken": ""
        })

    @task
    def load_dashboard(self):
        self.client.get("/")

    @task
    def load_admin(self):
        self.client.get("/admin/")