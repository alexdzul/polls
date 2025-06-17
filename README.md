# 📊 Polls API

A REST API developed with Django and Django REST Framework to manage polls and their voting options.

## 🎯 Educational Purpose

The main objective of this repository is purely educational, designed to help understand the basic structure and implementation of a Django project with Django REST Framework. This project serves as a practical example for learning how to build REST APIs using Django's powerful ecosystem.

## 🚀 Features

- **Poll Management**: Create, read, update and delete polls
- **Option Management**: Each poll can have multiple voting options
- **RESTful API**: Complete endpoints following REST standards
- **Django Admin**: Integrated administration panel for web management
- **SQLite Database**: Simple configuration ready to use

## 🛠️ Technologies

- **Django 5.2.3**: Python web framework
- **Django REST Framework 3.16.0**: Toolkit for REST APIs
- **SQLite**: Lightweight included database

## 📁 Project Structure

```
polls/
├── mysite/                 # Main project configuration
│   ├── settings.py        # Django settings
│   ├── urls.py           # Main URLs
│   └── wsgi.py           # WSGI configuration
├── polls/                 # Main application
│   ├── models.py         # Question and Choice models
│   ├── admin.py          # Admin configuration
│   └── api/              # API endpoints
│       ├── serializers.py # API serializers
│       ├── views.py      # API ViewSets
│       └── urls.py       # API URLs
├── requirements.txt       # Project dependencies
├── manage.py             # Command line utility
└── db.sqlite3           # SQLite database
```

## 🏗️ Data Models

### Question (Poll)
- `question_text`: Question text (max. 200 characters)
- `pub_date`: Publication date
- `choices`: Relationship with answer options

### Choice (Option)
- `choice_text`: Option text (max. 200 characters)
- `votes`: Number of votes (default: 0)
- `question`: Relationship with parent poll

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/polls.git
   cd polls
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

## 📚 API Endpoints

The API is available at: `http://localhost:8000/polls/api/`

### Polls (Questions)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/polls/api/questions/` | List all polls |
| `POST` | `/polls/api/questions/` | Create new poll |
| `GET` | `/polls/api/questions/{id}/` | Get specific poll |
| `PUT` | `/polls/api/questions/{id}/` | Update complete poll |
| `PATCH` | `/polls/api/questions/{id}/` | Partial poll update |
| `DELETE` | `/polls/api/questions/{id}/` | Delete poll |

### Data Format

**Poll structure:**
```json
{
  "id": 1,
  "question": "What's your favorite color?",
  "choices": [
    {
      "id": 1,
      "choice_text": "Blue"
    },
    {
      "id": 2,
      "choice_text": "Red"
    }
  ]
}
```

**Create new poll:**
```json
{
  "question": "What's your favorite programming language?",
  "choices": [
    {
      "choice_text": "Python"
    },
    {
      "choice_text": "JavaScript"
    },
    {
      "choice_text": "Java"
    }
  ]
}
```

## 🔍 Usage Examples

### Create a poll
```bash
curl -X POST http://localhost:8000/polls/api/questions/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What's your favorite framework?",
    "choices": [
      {"choice_text": "Django"},
      {"choice_text": "Flask"},
      {"choice_text": "FastAPI"}
    ]
  }'
```

### Get all polls
```bash
curl http://localhost:8000/polls/api/questions/
```

### Update a poll
```bash
curl -X PUT http://localhost:8000/polls/api/questions/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What's your favorite web framework?",
    "choices": [
      {"id": 1, "choice_text": "Django"},
      {"choice_text": "Express.js"}
    ]
  }'
```

## 🎛️ Administration Panel

Access the admin panel at: `http://localhost:8000/admin/`

The panel allows:
- Manage polls and options from a web interface
- View and edit all data
- Manage users and permissions

## 🧪 Testing

Run the tests:
```bash
python manage.py test polls
```

## 🤝 Contributing

1. Fork the project
2. Create a branch for your feature (`git checkout -b feature/new-functionality`)
3. Commit your changes (`git commit -am 'Add new functionality'`)
4. Push to the branch (`git push origin feature/new-functionality`)
5. Create a Pull Request

## 📄 License

This project is under the MIT License. See the `LICENSE` file for more details.

## 📞 Contact

If you have questions or suggestions, feel free to create an issue in the repository.

---

⭐ Don't forget to give the project a star if it was useful to you! 