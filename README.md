# CategoryTree

**CategoryTree** is a backend API for managing a hierarchical category tree and similarity relationships.  
It supports full CRUD for categories and bidirectional similarity connections, with built-in tools to analyze the similarity graph.

---

## Features

- Nested categories (arbitrarily deep)
- Create, edit, move, and delete categories
- Bidirectional similarity between categories (A ↔ B)
- Management command to analyze the similarity graph:
  - Find the longest rabbit hole (graph diameter)
  - Identify rabbit islands (connected components)

---

## Prerequisites

- Python 3.10 (recommended: 3.10.16)
- Dependencies listed in `requirements.txt`

---

## Installation

### (Optional) Set up a virtual environment  
[Python venv documentation](https://docs.python.org/3/library/venv.html)

```bash
python -m venv venv
source venv/bin/activate
```

### Install requirements

```bash
pip install -r requirements.txt
```

### Apply migrations

```bash
./manage.py migrate
```

### (Optional) Set up sample data

```bash
./manage.py reset_db -c 2000 -s 50000
```

This will:

- Flush the database
- Create a default superuser
- Generate categories (`-c`) and similarities (`-s`)

---

## Usage

### Run the server

```bash
./manage.py runserver
```

- API documentation: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- Admin panel: [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

## Graph Analysis

### Run the similarity analysis

```bash
./manage.py analyze_similarity
```

This will output:

- **Longest rabbit hole** (longest shortest path through similar categories)
- **Rabbit islands** (disconnected similarity components)

### Modes

- `full` (default): Full BFS from every node  
  Slow but accurate — around 1.5–2 minutes for 2000 categories and 200,000 similarities

- `fast`: Uses a double BFS approximation  
  Much faster, but I can't prove that it can't error out

#### Examples

```bash
./manage.py analyze_similarity --mode fast
./manage.py analyze_similarity -m full
```

---

## API Docs

API documentation is auto-generated using `drf-spectacular`.

- [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

---

## Database Reset

To completely reset the database (and delete media files), run:

```bash
./manage.py reset_db
```

Use `-c` and `-s` to generate new sample categories and similarities.

---

## Common Commands

| Action                   | Command                                  |
|--------------------------|-------------------------------------------|
| Run development server   | `./manage.py runserver`                  |
| Reset DB and add data    | `./manage.py reset_db -c 1000 -s 30000`  |
| Analyze similarities     | `./manage.py analyze_similarity`         |
| Fast similarity analysis | `./manage.py analyze_similarity -m fast` |
| View API documentation   | `http://localhost:8000/api/docs/`        |

---

## Testing

To run tests:

```bash
./manage.py test
```

---

## Flake

To install and run flake:

```bash
pip install flake8
flake8 ./ --exclude='*venv,**migrations*,*settings*'
```
