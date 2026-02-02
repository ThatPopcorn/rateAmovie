# Admin Control Panel

A comprehensive CLI-based admin control panel for managing the Rate-A-Movie application.

## Features

- **User Authentication**: Secure login system integrated with the Flask app database
- **Admin Session Management**: Token-based sessions with automatic expiration
- **Commands List**: Pre-built SQL command templates for common operations
- **Raw SQL Input**: Execute custom SQL queries directly
- **User Management**: View, query, and delete users
- **Query Results**: Formatted display of database query results

## Installation

No additional dependencies are needed beyond the existing requirements in `requirements.txt`.

## Usage

### Starting the Control Panel

1. First, ensure the Flask app is running:
```bash
python run.py
```

2. In another terminal, start the control panel:
```bash
python controlpanel.py
```

Or specify a custom server URL:
```bash
python controlpanel.py http://your-server:5000
```

### Login

- Enter your username and password (must be a valid user in the database)
- You'll receive an admin token that's valid for 1 hour
- Token status is displayed in the main menu

### Main Menu Options

#### 1. View Commands List
Displays pre-built SQL command templates organized by category:
- **User Management**: View users, delete users, count users
- **Movie Management**: View movies, delete movies, count movies
- **Review Management**: View reviews, filter by movie/user
- **Analytics**: Average ratings, review counts, top-rated movies

#### 2. Raw SQL Command Input
Execute custom SQL queries interactively:
- Type any valid SQL command
- Results are displayed in JSON format
- Type `exit` to return to main menu
- Type `help` to see command examples

#### 3. User Management
Dedicated submenu for user operations:
- View all users
- Look up specific users by ID
- Delete users (with confirmation)

#### 4. Execute Query (Quick)
Quick one-off query execution without entering a submenu

#### 5. Logout
End your admin session

## Security Features

- **Password Hashing**: Passwords are verified against bcrypt hashes
- **Session Tokens**: Admin tokens are randomly generated and expire after 1 hour
- **Token Validation**: All API requests require valid authentication
- **Maximum Login Attempts**: 3 failed login attempts will lock you out
- **Error Handling**: Sensitive errors don't expose database structure

## Common Commands

### View All Users
```sql
SELECT id, username, email FROM users;
```

### View All Movies
```sql
SELECT * FROM movies;
```

### View Average Movie Rating
```sql
SELECT AVG(rating) as avg_rating FROM reviews;
```

### Top Rated Movies
```sql
SELECT m.title, AVG(r.rating) as avg_rating, COUNT(r.id) as review_count 
FROM movies m 
JOIN reviews r ON m.id = r.movie_id 
GROUP BY m.id 
ORDER BY avg_rating DESC 
LIMIT 10;
```

### Delete a User
```sql
DELETE FROM users WHERE id = {user_id};
```

## Database Tables

- **users**: User accounts (id, username, email, password_hash)
- **movies**: Movie entries (id, title, description, release_date, image_url, director, cast)
- **reviews**: Movie reviews (id, rating, content, user_id, movie_id, timestamp)
- **token_blacklist**: Revoked JWT tokens (for API session management)

## Troubleshooting

### Connection Error
If you get "Could not connect to the server" message:
- Make sure the Flask app is running on the correct URL
- Check if the server is listening on the correct port (default: 5000)
- Specify the correct URL: `python controlpanel.py http://your-server:port`

### Session Expired
If you get "Session expired" during a command:
- Your 1-hour token has expired
- Log out and log back in
- Select "Logout" and re-run the control panel

### Authentication Failed
- Verify username and password are correct
- Make sure the user exists in the database
- Check that the password was entered correctly

## API Endpoints (for reference)

The control panel uses these Flask API endpoints:

- `POST /api/hidden/v1/login` - Authenticate and get admin token
- `POST /api/hidden/v1/exec` - Execute SQL commands (requires X-Admin-Auth header)
- `POST /api/hidden/v1/logout` - End admin session

## Notes

- Admin tokens are stored in server memory and will reset on Flask app restart
- SQL commands are executed with full database access
- Use caution with DELETE and UPDATE commands
- Always maintain backups of important data
- The control panel is designed for administrative use only

## Performance Tips

- For large result sets, add LIMIT clause to queries
- Use WHERE conditions to filter results
- Consider database indexing for frequently queried fields

---

**Version**: 1.0  
**Last Updated**: 2026-02-02
