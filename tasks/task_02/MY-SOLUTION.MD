1. SQL injection vulnerability
    - get_user_by_username should use something like this:
    cursor = db.execute(
        "SELECT * FROM users WHERE username = :username",
        {"username": username},
    )
    - instead of f-string
2. Storing plain-text password
    - use bcrypt to hash password and store hash in database
    - bcrypt.gensalt(rounds=12)
    - bcrypt.hashpw(password.encode("utf-8"), salt)
3. Login should use bcrypt to check password
    - bcrypt.checkpw(password.encode("utf-8"), hashed_password)
    - keep exire in jwt token about 15 minutes or 1 hour
4. Add refresh token mechanism
    - add refresh token to database
    - add refresh token to jwt token when user login/register for 7 days
    - when access token is expired, user can use refresh token to get new access token
    - when refresh token is expired, user need to login again entierly 
    - or use jwt.decode with options={"verify_exp": False} to get new token
