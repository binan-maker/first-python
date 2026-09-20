import bcrypt

# The password you want to use
password = "password123"

# Generate the hash
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

print("Your hashed password is:")
print(hashed_password.decode('utf-8'))