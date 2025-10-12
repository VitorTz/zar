from dotenv import load_dotenv
from fastapi import status
from src import util
import requests
import os

load_dotenv()


class Client:

    def __init__(self):
        self.__base_url = "http://localhost:8000"
        self.__session = requests.Session()

    @property
    def base_url(self) -> str:
        return self.__base_url
    
    @property
    def session(self) -> requests.Session:
        return self.__session
    
    @property
    def headers(self) -> dict:
        return dict(self.__session.headers)
    
    @headers.setter
    def headers(self, headers: dict):
        self.__session.headers.update(headers)
    
    def get(self, endpoint: str, json: dict = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, json=json)
        return response
    
    def post(self, endpoint: str, json: dict = None, data = None, files = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=json, files=files, data=data)
        return response
    
    def put(self, endpoint: str, json: dict = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(url, json=json)
        return response
    
    def delete(self, endpoint: str, json: dict = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, json=json)
        return response
    
    def get_and_print(self, endpoint: str, json: dict = None) -> None:
        try:
            response: requests.Response = self.get(endpoint, json=json)
            response.raise_for_status()
            data = response.json()
            print(f"=================== {endpoint} ===================")
            print(data)
            print(f"=================== {endpoint} ===================\n\n")
        except requests.exceptions.HTTPError as e:
            print(f"Erro get_and_print {endpoint}: {e.response.text}")


class User(Client):

    def __init__(self, email: str, password: str):
        super().__init__()
        self.__email = email
        self.__password = password

    @property
    def email(self) -> str:
        return self.__email
    
    @property
    def password(self) -> str:
        return self.__password
    
    @property
    def me(self) -> dict:
        r = self.get("/auth/me")
        return r.json()

    @property
    def is_authenticated(self) -> bool:
        r = self.get("/auth/me")
        return r.status_code == status.HTTP_200_OK

    def signup(self) -> None:
        r = self.post("/auth/signup", json={"email": self.email, "password": self.password})
        print(f"[SIGNUP [{r.status_code}] | {self.email}]")

    def login(self) -> None:
        r = self.post("/auth/login", json={"email": self.email, "password": self.password})
        print(f"[LOGIN {self.email}] [{r.status_code}]")

    def logout(self) -> None:
        r = self.post("/auth/logout")
        print(r.status_code, r.json())

    def sessions(self) -> None:
        r = self.get("/auth/sessions")
        print(r.status_code, '\n', [util.print_dict(i) for i in r.json()['results']])

    def create_url(self, url: str) -> None:
        r = self.post("/shorten", data={"url": url})
        print(r.status_code, r.json())
    
    def list_urls(self) -> None:
        r = self.get("/user/urls")
        print(r.status_code, r.json())


class Admin(Client):

    def __init__(self):
        super().__init__()
        self.headers = {
            "Authorization": f"Bearer {os.getenv("ADMIN_TOKEN")}"
        }
    
    def show_users(self) -> None:
        r = self.get("/admin/users")
        util.print_dict(r.json())

    def delete_user(self, user_id: str):
        r = self.delete("/admin/users", json={"user_id": user_id})
        print("DELETE USER", r.status_code)

    def delete_all_users(self):
        self.delete("/admin/users/all")


def main():
    user = User("vitor.fsz@proton.me", "75045658")
    user.login()
    util.print_dict(user.me)

if __name__ == "__main__":
    main()