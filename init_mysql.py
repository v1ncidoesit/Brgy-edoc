from app import get_db

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # USERS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        fullname VARCHAR(200) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        contact VARCHAR(20),
        birthdate DATE,
        civil_status VARCHAR(50),
        address VARCHAR(255),
        fathers_name VARCHAR(150),
        mothers_name VARCHAR(150),
        birthplace VARCHAR(150),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # REQUESTS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        full_name VARCHAR(150) NOT NULL,
        email VARCHAR(150) NOT NULL,
        document_type VARCHAR(150) NOT NULL,
        address VARCHAR(255) NOT NULL,
        contact VARCHAR(20),
        purpose TEXT NOT NULL,
        status VARCHAR(50) DEFAULT 'Pending',
        date_submitted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("MySQL tables created successfully!")

if __name__ == "__main__":
    init_db()
