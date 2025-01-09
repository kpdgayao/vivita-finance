from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class User:
    email: str
    name: str
    role: str
    password: str

class Auth:
    def __init__(self):
        # Initialize with predefined users
        self.users = {
            "gabe@vivita.ph": User(
                email="gabe@vivita.ph",
                name="Gabe",
                role="Executive Director",
                password="vivita2024"
            ),
            "kevin@vivita.ph": User(
                email="kevin@vivita.ph",
                name="Kevin",
                role="Finance and Admin Officer",
                password="vivita2024"
            ),
            "agnes@vivita.ph": User(
                email="agnes@vivita.ph",
                name="Agnes",
                role="Resident Engineer",
                password="vivita2024"
            ),
            "candy@vivita.ph": User(
                email="candy@vivita.ph",
                name="Candy",
                role="Programs Lead",
                password="vivita2024"
            ),
            "hazel@vivita.ph": User(
                email="hazel@vivita.ph",
                name="Hazel",
                role="Operations Coordinator",
                password="vivita2024"
            ),
            "franz@vivita.ph": User(
                email="franz@vivita.ph",
                name="Franz",
                role="Technical Lead",
                password="vivita2024"
            ),
            "nina@vivita.ph": User(
                email="nina@vivita.ph",
                name="Nina",
                role="Communications Officer",
                password="vivita2024"
            )
        }
        
    def sign_in(self, email: str, password: str) -> Optional[Dict]:
        user = self.users.get(email)
        if user and user.password == password:
            return {
                "email": user.email,
                "name": user.name,
                "role": user.role
            }
        return None
            
    def get_current_user(self) -> Optional[Dict]:
        # This is just a placeholder since we're not maintaining sessions
        return None
            
    def sign_out(self) -> bool:
        return True  # Always succeeds since we're not maintaining sessions
