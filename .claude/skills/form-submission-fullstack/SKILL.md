---
name: form-handling-nextjs-php
description: Handle forms from Next.js frontend, send data to PHP backend, and store in MySQL database. Use when building form submission features.
---

# Form Handling: Next.js → PHP → MySQL

This skill teaches Claude how to build complete form workflows from frontend to database.

## When to Use This Skill

- Building any form that needs to submit data to the backend
- Creating user registration, contact forms, profile updates, etc.
- Handling form validation and errors

## Frontend: Next.js Form Pattern

### 1. Create the Form Component

```jsx
"use client";
import { useState } from "react";

export default function MyForm() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    message: "",
  });
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus("");

    try {
      const response = await fetch("/api/submit-form", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (response.ok) {
        setStatus("success");
        setFormData({ name: "", email: "", message: "" }); // Reset form
      } else {
        setStatus("error: " + result.message);
      }
    } catch (error) {
      setStatus("error: Network error");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        name="name"
        value={formData.name}
        onChange={handleChange}
        placeholder="Name"
        required
      />
      <input
        type="email"
        name="email"
        value={formData.email}
        onChange={handleChange}
        placeholder="Email"
        required
      />
      <textarea
        name="message"
        value={formData.message}
        onChange={handleChange}
        placeholder="Message"
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? "Sending..." : "Submit"}
      </button>
      {status && <p>{status}</p>}
    </form>
  );
}
```

### 2. Create Next.js API Route

File: `app/api/submit-form/route.js`

```javascript
export async function POST(request) {
  try {
    const formData = await request.json();

    // Send to PHP backend
    const response = await fetch(
      "http://your-backend.com/api/form-handler.php",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      }
    );

    const result = await response.json();

    if (response.ok) {
      return Response.json({ success: true, message: "Form submitted!" });
    } else {
      return Response.json(
        { success: false, message: result.message || "Submission failed" },
        { status: 400 }
      );
    }
  } catch (error) {
    return Response.json(
      { success: false, message: "Server error" },
      { status: 500 }
    );
  }
}
```

## Backend: PHP Handler Pattern

### File: `api/form-handler.php`

```php
<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// Database connection
$host = 'localhost';
$dbname = 'your_database';
$username = 'your_username';
$password = 'your_password';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch(PDOException $e) {
    echo json_encode(['success' => false, 'message' => 'Database connection failed']);
    exit;
}

// Get POST data
$data = json_decode(file_get_contents('php://input'), true);

// Validate data
if (empty($data['name']) || empty($data['email']) || empty($data['message'])) {
    echo json_encode(['success' => false, 'message' => 'All fields are required']);
    exit;
}

// Sanitize inputs
$name = htmlspecialchars(trim($data['name']));
$email = filter_var(trim($data['email']), FILTER_SANITIZE_EMAIL);
$message = htmlspecialchars(trim($data['message']));

// Validate email
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    echo json_encode(['success' => false, 'message' => 'Invalid email address']);
    exit;
}

// Insert into database
try {
    $sql = "INSERT INTO form_submissions (name, email, message, created_at)
            VALUES (:name, :email, :message, NOW())";

    $stmt = $pdo->prepare($sql);
    $stmt->execute([
        ':name' => $name,
        ':email' => $email,
        ':message' => $message
    ]);

    echo json_encode([
        'success' => true,
        'message' => 'Form submitted successfully',
        'id' => $pdo->lastInsertId()
    ]);
} catch(PDOException $e) {
    echo json_encode(['success' => false, 'message' => 'Failed to save data']);
}
?>
```

## Database: MySQL Table Structure

```sql
CREATE TABLE form_submissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
);
```

## Important Rules

1. **Always use prepared statements** in PHP to prevent SQL injection
2. **Always sanitize and validate** user inputs
3. **Always handle errors** gracefully in both frontend and backend
4. **Always use try-catch** blocks for database operations
5. **Always return JSON** responses from PHP
6. **Use loading states** in the frontend for better UX
7. **Reset form** after successful submission

## Common Patterns

### For File Uploads

- Use FormData instead of JSON
- Add enctype="multipart/form-data" to form
- Use $\_FILES in PHP
- Validate file types and sizes

### For Multiple Forms

- Create reusable form components
- Share validation logic
- Use the same error handling pattern

### For Complex Validation

- Add client-side validation before submission
- Add server-side validation in PHP
- Return specific field errors

## Example Usage

When user asks: "Create a contact form"
Claude should:

1. Create the Next.js form component with state management
2. Create the Next.js API route
3. Create the PHP backend handler
4. Provide the MySQL table structure
5. Include proper error handling at all levels

```

---

### **Step 3: Save and Use It!**

1. Save this file to `~/.claude/skills/form-handling-nextjs-php/SKILL.md`
2. Restart Claude Code
3. Now just ask: **"Build me a contact form"**

Claude will **automatically**:
- Use your exact patterns
- Follow your specific structure
- Include all error handling
- Use your database connection style
- Follow your naming conventions

---

## 🎯 **Why This Works So Well**

Before the skill:
```

You: "Build a contact form"
Claude: "Sure, how do you want it structured?"
You: "Use Next.js for frontend, PHP for backend..."
Claude: "How should I handle the data?"
You: "Use prepared statements, validate inputs..."

```

After the skill:
```

You: "Build a contact form"
Claude: _Uses skill automatically_
Done! Here's your form with all your patterns! ✨
