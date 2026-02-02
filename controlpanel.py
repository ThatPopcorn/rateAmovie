#!/usr/bin/env python3
"""
Admin Control Panel for Rate-A-Movie
Provides CLI interface for admin operations including login, command execution, and raw SQL queries.
"""

import sys
import os
import getpass
import requests
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db, bcrypt
from app.models import User

class AdminControlPanel:
    """CLI Control Panel for admin operations"""
    
    def __init__(self, server_url: str = "http://localhost:5000"):
        self.server_url = server_url
        self.admin_token = None
        self.admin_token_expires = None
        self.authenticated_user = None
        self.session = requests.Session()
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_header(self, title: str):
        """Print a formatted header"""
        print("\n" + "=" * 60)
        print(f"  {title.center(56)}")
        print("=" * 60)
    
    def print_menu(self, title: str, items: list):
        """Print a formatted menu"""
        print(f"\n{title}")
        print("-" * 60)
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item}")
        print("-" * 60)
    
    def login_with_credentials(self, username: str = None, password: str = None) -> bool:
        """Authenticate user and generate admin token"""
        print("\n" + "=" * 60)
        print("  ADMIN CONTROL PANEL - LOGIN")
        print("=" * 60)
        
        if not username:
            username = input("\nUsername: ").strip()
            if not username:
                print("❌ Username cannot be empty")
                return False
        
        if not password:
            password = getpass.getpass("Password: ")
            if not password:
                print("❌ Password cannot be empty")
                return False
        
        try:
            # Query local database to authenticate
            user = User.query.filter_by(username=username).first()
            
            if not user or not user.check_password(password):
                print("❌ Invalid username or password")
                return False
            
            # Check if user is an admin (you can add admin flag to User model)
            # For now, we'll proceed with authentication
            self.authenticated_user = user
            
            # Make request to Flask app to generate admin token
            response = self.session.post(
                f"{self.server_url}/api/hidden/v1/login",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('token')
                expires_in = data.get('expires_in', 3600)
                self.admin_token_expires = time.time() + expires_in
                
                print(f"\n✅ Successfully logged in as: {username}")
                print(f"🔑 Admin Token: {self.admin_token[:20]}...")
                print(f"⏰ Token expires at: {datetime.fromtimestamp(self.admin_token_expires).strftime('%Y-%m-%d %H:%M:%S')}")
                return True
            else:
                print(f"❌ Authentication failed: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the server. Make sure the Flask app is running.")
            print(f"   Trying to connect to: {self.server_url}")
            return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def is_token_valid(self) -> bool:
        """Check if admin token is still valid"""
        if not self.admin_token or not self.admin_token_expires:
            return False
        return time.time() < self.admin_token_expires
    
    def execute_sql_command(self, sql_command: str) -> Optional[Dict[str, Any]]:
        """Execute a SQL command via the admin API"""
        if not self.is_token_valid():
            print("❌ Admin session expired. Please login again.")
            return None
        
        try:
            headers = {'X-Admin-Auth': self.admin_token}
            response = self.session.post(
                f"{self.server_url}/api/hidden/v1/exec",
                json={'sql': sql_command},
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                print("❌ Session expired. Please login again.")
                self.admin_token = None
                return None
            elif response.status_code == 404:
                print("❌ Invalid authentication token")
                return None
            else:
                return response.json()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the server")
            return None
        except Exception as e:
            print(f"❌ Error executing command: {str(e)}")
            return None
    
    def display_commands_list(self):
        """Display list of available admin commands"""
        self.clear_screen()
        self.print_header("AVAILABLE ADMIN COMMANDS")
        
        commands = [
            ("User Management", [
                "VIEW ALL USERS: SELECT * FROM users;",
                "VIEW USER BY ID: SELECT * FROM users WHERE id = {id};",
                "COUNT USERS: SELECT COUNT(*) as total_users FROM users;",
                "DELETE USER: DELETE FROM users WHERE id = {id};",
            ]),
            ("Movie Management", [
                "VIEW ALL MOVIES: SELECT * FROM movies;",
                "VIEW MOVIE BY ID: SELECT * FROM movies WHERE id = {id};",
                "COUNT MOVIES: SELECT COUNT(*) as total_movies FROM movies;",
                "DELETE MOVIE: DELETE FROM movies WHERE id = {id};",
            ]),
            ("Review Management", [
                "VIEW ALL REVIEWS: SELECT * FROM reviews;",
                "VIEW REVIEWS FOR MOVIE: SELECT * FROM reviews WHERE movie_id = {id};",
                "VIEW USER REVIEWS: SELECT * FROM reviews WHERE user_id = {id};",
                "DELETE REVIEW: DELETE FROM reviews WHERE id = {id};",
            ]),
            ("Analytics", [
                "AVERAGE MOVIE RATING: SELECT AVG(rating) as avg_rating FROM reviews;",
                "MOVIES BY REVIEW COUNT: SELECT m.id, m.title, COUNT(r.id) as review_count FROM movies m LEFT JOIN reviews r ON m.id = r.movie_id GROUP BY m.id ORDER BY review_count DESC;",
                "TOP RATED MOVIES: SELECT m.title, AVG(r.rating) as avg_rating, COUNT(r.id) as review_count FROM movies m JOIN reviews r ON m.id = r.movie_id GROUP BY m.id ORDER BY avg_rating DESC LIMIT 10;",
            ])
        ]
        
        for category, cmd_list in commands:
            print(f"\n📋 {category}:")
            print("-" * 58)
            for cmd in cmd_list:
                print(f"  → {cmd}")
        
        print("\n" + "=" * 60)
        print("  💡 You can also enter raw SQL commands in the command input menu")
        print("=" * 60)
        input("\nPress Enter to continue...")
    
    def raw_command_input(self):
        """Interactive raw SQL command input"""
        self.clear_screen()
        self.print_header("RAW SQL COMMAND INPUT")
        
        print("\n📝 Enter your SQL command (type 'exit' to return to main menu)")
        print("   Tip: Use 'help' to see command examples")
        print("-" * 60)
        
        while True:
            try:
                sql_command = input("\n> ").strip()
                
                if sql_command.lower() == 'exit':
                    break
                elif sql_command.lower() == 'help':
                    self.display_commands_list()
                    continue
                elif not sql_command:
                    continue
                
                print("\n⏳ Executing command...")
                result = self.execute_sql_command(sql_command)
                
                if result:
                    if result.get('status') == 'success':
                        if result.get('data'):
                            self._display_query_results(result.get('data'))
                        else:
                            print(f"✅ {result.get('message', 'Command executed successfully')}")
                    else:
                        print(f"❌ Error: {result.get('error', 'Unknown error')}")
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Command cancelled")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def _display_query_results(self, data: list):
        """Display query results in a formatted table"""
        if not data:
            print("📭 No results found")
            return
        
        print(f"\n📊 Query Results ({len(data)} rows):")
        print("-" * 60)
        
        # Display as JSON for better readability with complex data
        print(json.dumps(data, indent=2, default=str))
    
    def user_management_menu(self):
        """User management submenu"""
        while True:
            self.clear_screen()
            self.print_header("USER MANAGEMENT")
            
            options = [
                "View all users",
                "View user by ID",
                "Delete user",
                "Back to main menu"
            ]
            self.print_menu("Select an option:", options)
            
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == '1':
                result = self.execute_sql_command("SELECT id, username, email, created_at FROM users LIMIT 50;")
                if result and result.get('status') == 'success':
                    self._display_query_results(result.get('data', []))
                input("\nPress Enter to continue...")
            
            elif choice == '2':
                try:
                    user_id = int(input("\nEnter user ID: ").strip())
                    result = self.execute_sql_command(f"SELECT id, username, email FROM users WHERE id = {user_id};")
                    if result and result.get('status') == 'success':
                        self._display_query_results(result.get('data', []))
                    input("\nPress Enter to continue...")
                except ValueError:
                    print("❌ Invalid user ID")
            
            elif choice == '3':
                try:
                    user_id = int(input("\nEnter user ID to delete: ").strip())
                    confirm = input(f"⚠️  Are you sure you want to delete user {user_id}? (yes/no): ").strip().lower()
                    if confirm == 'yes':
                        result = self.execute_sql_command(f"DELETE FROM users WHERE id = {user_id};")
                        if result and result.get('status') == 'success':
                            print("✅ User deleted successfully")
                        input("\nPress Enter to continue...")
                except ValueError:
                    print("❌ Invalid user ID")
            
            elif choice == '4':
                break
    
    def main_menu(self):
        """Display main menu and handle navigation"""
        while True:
            if not self.is_token_valid():
                print("\n❌ Your admin session has expired")
                self.admin_token = None
                break
            
            self.clear_screen()
            self.print_header("ADMIN CONTROL PANEL")
            
            token_status = "✅ Valid" if self.is_token_valid() else "❌ Expired"
            print(f"\n👤 User: {self.authenticated_user.username}")
            print(f"🔐 Session: {token_status}")
            if self.is_token_valid():
                expires_at = datetime.fromtimestamp(self.admin_token_expires).strftime('%H:%M:%S')
                print(f"⏰ Expires at: {expires_at}")
            
            options = [
                "View Commands List",
                "Raw SQL Command Input",
                "User Management",
                "Execute Query (quick)",
                "Logout"
            ]
            self.print_menu("\nSelect an option:", options)
            
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == '1':
                self.display_commands_list()
            
            elif choice == '2':
                self.raw_command_input()
            
            elif choice == '3':
                self.user_management_menu()
            
            elif choice == '4':
                sql = input("\nEnter SQL query: ").strip()
                if sql:
                    print("\n⏳ Executing...")
                    result = self.execute_sql_command(sql)
                    if result:
                        if result.get('status') == 'success':
                            if result.get('data'):
                                self._display_query_results(result.get('data'))
                            else:
                                print(f"✅ {result.get('message', 'Command executed')}")
                        else:
                            print(f"❌ Error: {result.get('error', 'Unknown error')}")
                    input("\nPress Enter to continue...")
            
            elif choice == '5':
                print("\n✅ Logged out successfully")
                break
    
    def run(self):
        """Main entry point"""
        self.clear_screen()
        print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║          🎬 RATE-A-MOVIE ADMIN CONTROL PANEL 🎬          ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")
        
        # Login screen
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            if self.login_with_credentials():
                self.main_menu()
                break
            else:
                attempt += 1
                if attempt < max_attempts:
                    print(f"\n⚠️  Login failed. Attempts remaining: {max_attempts - attempt}")
                    input("Press Enter to try again...")
                else:
                    print("\n❌ Maximum login attempts exceeded")
                    sys.exit(1)


def main():
    """Entry point for the control panel"""
    # Check if server URL is provided as argument
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    control_panel = AdminControlPanel(server_url=server_url)
    try:
        control_panel.run()
    except KeyboardInterrupt:
        print("\n\n👋 Control panel closed")
        sys.exit(0)


if __name__ == '__main__':
    main()
