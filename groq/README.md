# 🧪 Guía de Pruebas con Postman - PulmoMed

> **Propósito**: Documentación de endpoints para pruebas locales con Postman  
> **Base URL**: `http://localhost:8000/api/v1`  
> **Última actualización**: Febrero 2026

---

## 📋 Índice

1. [Configuración Inicial](#1-configuración-inicial)
2. [Autenticación](#2-autenticación)
3. [Cursos](#3-cursos)
4. [Exámenes](#4-exámenes)
5. [Profesor Virtual (IA)](#5-profesor-virtual-ia)
6. [Colección de Postman](#6-colección-de-postman)

---

## 1. Configuración Inicial

### 1.1 Requisitos

```bash
# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env con las variables necesarias
cp .env.example .env
```

### 1.2 Variables de Entorno (`.env`)

```env
# Base de datos PostgreSQL
DATABASE_URL=postgresql+asyncpg://pulmomed:pulmomed_secret@localhost:5432/pulmomed_db

# JWT (cambiar en producción)
JWT_SECRET_KEY=tu-clave-secreta-cambiar-en-prod

# Groq para pruebas (obtener en https://console.groq.com/keys)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.1-8b-instant
```

### 1.3 Iniciar el servidor

```bash
# Opción 1: Directamente con Python
python main.py

# Opción 2: Con uvicorn (recarga automática)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 2. Autenticación

### 2.1 Registrar Usuario

```http
POST /api/v1/auth/register
Content-Type: application/json

{
    "email": "profesor@universidad.edu",
    "password": "MiPassword123!",
    "full_name": "Dr. Juan García",
    "role": "professor"
}
```

**Roles disponibles**:
| Rol | Descripción |
|-----|-------------|
| `student` | Estudiante (por defecto) |
| `professor` | Profesor (puede crear cursos/exámenes) |
| `admin` | Administrador (acceso total) |

**Response** (201 Created):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "profesor@universidad.edu",
    "full_name": "Dr. Juan García",
    "role": "professor",
    "is_active": true,
    "created_at": "2026-02-02T10:30:00Z"
}
```

---

### 2.2 Iniciar Sesión (Login)

#### Opción A: Form Data (OAuth2 estándar)

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=profesor@universidad.edu&password=MiPassword123!
```

#### Opción B: JSON (para Unity/móviles)

```http
POST /api/v1/auth/login/json
Content-Type: application/json

{
    "email": "profesor@universidad.edu",
    "password": "MiPassword123!"
}
```

**Response** (200 OK):
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "profesor@universidad.edu",
        "full_name": "Dr. Juan García",
        "role": "professor"
    }
}
```

---

### 2.3 Obtener Usuario Actual

```http
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "profesor@universidad.edu",
    "full_name": "Dr. Juan García",
    "role": "professor",
    "is_active": true
}
```

---

### 2.4 Cerrar Sesión

```http
POST /api/v1/auth/logout
Authorization: Bearer {access_token}
```

---

## 3. Cursos

> ⚠️ **Requiere rol `professor` o `admin`**

### 3.1 Crear Curso

```http
POST /api/v1/courses/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "name": "Oncología Pulmonar I",
    "description": "Curso introductorio sobre cáncer de pulmón",
    "semester": "2026-1",
    "max_students": 30
}
```

**Response** (201 Created):
```json
{
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Oncología Pulmonar I",
    "description": "Curso introductorio sobre cáncer de pulmón",
    "enrollment_code": "ABC123XY",  // Código para que estudiantes se inscriban
    "is_active": true,
    "max_students": 30,
    "semester": "2026-1",
    "professor_id": "550e8400-e29b-41d4-a716-446655440000",
    "professor_name": "Dr. Juan García",
    "student_count": 0,
    "created_at": "2026-02-02T10:45:00Z"
}
```

---

### 3.2 Listar Mis Cursos (Profesor)

```http
GET /api/v1/courses/my-courses
Authorization: Bearer {access_token}
```

---

### 3.3 Inscribir Estudiante (con código)

> **Rol requerido**: `student`

```http
POST /api/v1/courses/enroll
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "enrollment_code": "ABC123XY"
}
```

---

### 3.4 Ver Cursos Inscritos (Estudiante)

```http
GET /api/v1/courses/enrolled
Authorization: Bearer {access_token}
```

---

## 4. Exámenes

### 4.1 Crear Examen (Profesor)

```http
POST /api/v1/exams/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "title": "Examen Parcial - Estadificación TNM",
    "description": "Evaluación sobre el sistema de estadificación tumoral",
    "course_id": "660e8400-e29b-41d4-a716-446655440001",
    "exam_type": "module_eval",
    "time_limit_minutes": 45,
    "passing_score": 70,
    "max_attempts": 2,
    "shuffle_questions": true
}
```

**Tipos de examen**:
| Tipo | Preguntas | Descripción |
|------|-----------|-------------|
| `mini_quiz` | 5-10 | Quiz rápido |
| `module_eval` | 15-25 | Evaluación de módulo |
| `full_exam` | 30-50 | Examen completo |
| `ai_personalized` | 4 | Quiz generado por IA |

**Response** (201 Created):
```json
{
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "title": "Examen Parcial - Estadificación TNM",
    "description": "Evaluación sobre el sistema de estadificación tumoral",
    "course_id": "660e8400-e29b-41d4-a716-446655440001",
    "course_name": "Oncología Pulmonar I",
    "exam_type": "module_eval",
    "exam_type_display": "Evaluación de Módulo (15-25 preguntas)",
    "status": "draft",
    "time_limit_minutes": 45,
    "passing_score": 70,
    "max_attempts": 2,
    "shuffle_questions": true,
    "question_count": 0,
    "min_questions": 15,
    "max_questions": 25,
    "created_at": "2026-02-02T11:00:00Z"
}
```

---

### 4.2 Agregar Pregunta al Examen

```http
POST /api/v1/exams/{exam_id}/questions
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "question_text": "¿Cuál es el tamaño máximo de un tumor T1 según la clasificación TNM?",
    "question_type": "multiple_choice",
    "options": [
        "≤ 1 cm",
        "≤ 2 cm",
        "≤ 3 cm",
        "≤ 4 cm"
    ],
    "correct_answer": "≤ 3 cm",
    "points": 10,
    "explanation": "Según TNM 8th Edition, T1 incluye tumores ≤ 3 cm"
}
```

**Tipos de pregunta**:
| Tipo | Descripción |
|------|-------------|
| `multiple_choice` | Opción múltiple (una correcta) |
| `true_false` | Verdadero/Falso |
| `open_ended` | Respuesta abierta (calificación manual) |

---

### 4.3 Listar Mis Exámenes (Profesor)

```http
GET /api/v1/exams/my-exams
Authorization: Bearer {access_token}
```

---

### 4.4 Ver Examen con Preguntas (Profesor)

```http
GET /api/v1/exams/{exam_id}
Authorization: Bearer {access_token}
```

**Response**: Incluye todas las preguntas con respuestas correctas.

---

### 4.5 Publicar Examen

```http
PATCH /api/v1/exams/{exam_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "status": "published"
}
```

> ⚠️ **Validación**: El examen debe tener el número mínimo de preguntas según su tipo.

---

### 4.6 Ver Exámenes Disponibles (Estudiante)

```http
GET /api/v1/exams/available
Authorization: Bearer {access_token}
```

Solo muestra exámenes publicados de cursos donde el estudiante está inscrito.

---

### 4.7 Iniciar Examen (Estudiante)

```http
POST /api/v1/exams/{exam_id}/start
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
    "attempt_id": "880e8400-e29b-41d4-a716-446655440003",
    "exam": {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "title": "Examen Parcial - Estadificación TNM",
        "time_limit_minutes": 45,
        "passing_score": 70,
        "question_count": 15,
        "questions": [
            {
                "id": "990e8400-e29b-41d4-a716-446655440004",
                "question_text": "¿Cuál es el tamaño máximo de un tumor T1?",
                "question_type": "multiple_choice",
                "options": ["≤ 1 cm", "≤ 2 cm", "≤ 3 cm", "≤ 4 cm"],
                "points": 10
                // ⚠️ NO incluye correct_answer
            }
        ]
    },
    "started_at": "2026-02-02T14:00:00Z",
    "time_remaining_minutes": 45
}
```

---

### 4.8 Enviar Respuestas (Estudiante)

```http
POST /api/v1/exams/{exam_id}/attempts/{attempt_id}/submit
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "answers": [
        {
            "question_id": "990e8400-e29b-41d4-a716-446655440004",
            "answer": "≤ 3 cm"
        },
        {
            "question_id": "990e8400-e29b-41d4-a716-446655440005",
            "answer": "true"
        }
    ]
}
```

**Response** (200 OK):
```json
{
    "attempt_id": "880e8400-e29b-41d4-a716-446655440003",
    "exam_id": "770e8400-e29b-41d4-a716-446655440002",
    "exam_title": "Examen Parcial - Estadificación TNM",
    "status": "completed",
    "score": 85.5,
    "total_points": 100,
    "earned_points": 85,
    "passed": true,
    "passing_score": 70,
    "started_at": "2026-02-02T14:00:00Z",
    "submitted_at": "2026-02-02T14:32:00Z"
}
```

---

### 4.9 Ver Mis Intentos (Estudiante)

```http
GET /api/v1/exams/{exam_id}/my-attempts
Authorization: Bearer {access_token}
```

---

## 5. Profesor Virtual (IA)

### 5.1 Consultar al Profesor IA

```http
POST /api/v1/consultar_profesor
Content-Type: application/json

{
    "age": 62,
    "is_smoker": true,
    "pack_years": 35,
    "has_adequate_diet": false,
    "sensitive_tumor_volume": 12.5,
    "resistant_tumor_volume": 0.8,
    "active_treatment": "chemotherapy",
    "current_day": 45
}
```

**Response** (200 OK):
```json
{
    "explicacion": "**Análisis del Estado Actual:**\n\nEl paciente de 62 años presenta un tumor con volumen total de 13.3 cm³...",
    "recomendacion": "Según las guías NCCN 2024, para pacientes con NSCLC estadio II-III...",
    "fuentes": [
        "NCCN Guidelines v3.2024",
        "SEER Database 2015-2020"
    ],
    "advertencia": "⚠️ Simulación educativa únicamente",
    "retrieved_chunks": 5,
    "llm_model": "llama-3.1-8b-instant",
    "processing_time_ms": 1250
}
```

---

### 5.2 Health Check

```http
GET /api/v1/health
```

**Response**:
```json
{
    "status": "ok",
    "rag_status": "operational",
    "llm_status": "groq",
    "version": "2.1"
}
```

---

## 6. Colección de Postman

### 6.1 Variables de Entorno

Crear un Environment en Postman con estas variables:

| Variable | Valor Inicial | Descripción |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8000/api/v1` | URL base de la API |
| `access_token` | _(vacío)_ | Se llena al hacer login |
| `professor_email` | `profesor@test.com` | Email de prueba |
| `professor_password` | `Test123456!` | Password de prueba |
| `student_email` | `estudiante@test.com` | Email estudiante |
| `exam_id` | _(vacío)_ | ID del examen creado |
| `course_id` | _(vacío)_ | ID del curso creado |

### 6.2 Script Post-Login

Agregar en la pestaña "Tests" del endpoint Login:

```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("access_token", jsonData.access_token);
    console.log("Token guardado!");
}
```

### 6.3 Header Authorization

En los endpoints que requieren auth, usar:

```
Authorization: Bearer {{access_token}}
```

---

## 🔧 Troubleshooting

### Error: "No se pudieron validar las credenciales"

- Verifica que el token no haya expirado (30 min por defecto)
- Haz login nuevamente para obtener un nuevo token

### Error: "Examen no encontrado" o "Curso no encontrado"

- Verifica que el UUID sea correcto
- Verifica que el examen/curso exista y esté publicado
- Verifica que estés inscrito en el curso (para estudiantes)

### Error: "Se requiere rol de profesor"

- Solo usuarios con `role: professor` o `role: admin` pueden crear cursos/exámenes
- Registra un usuario con rol correcto

### La IA no responde o da timeout

1. Verifica que `GROQ_API_KEY` esté configurada en `.env`
2. Verifica conexión a internet
3. Si usas Ollama, verifica que esté corriendo: `curl http://localhost:11434/api/tags`

---

## 📁 Estructura de Archivos Relevante

```
PulmoMed-Backend/
├── .env                    # Variables de entorno (crear)
├── .env.example            # Plantilla de variables
├── main.py                 # Entry point
├── requirements.txt        # Dependencias Python
├── app/
│   ├── api/
│   │   ├── auth_endpoint.py    # /auth/*
│   │   ├── course_endpoint.py  # /courses/*
│   │   ├── exam_endpoint.py    # /exams/*
│   │   └── teacher_endpoint.py # /api/v1/*
│   ├── core/
│   │   ├── config.py          # Configuración
│   │   └── database.py        # PostgreSQL
│   └── llm/
│       ├── groq_client.py     # ✨ Nuevo: Cliente Groq
│       └── ollama_client.py   # Cliente Ollama/Mock
└── groq/
    └── README.md              # Esta guía
```

---

## 🚀 Flujo de Prueba Rápida

```bash
# 1. Crear profesor
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"prof@test.com","password":"Test123!","full_name":"Prof Test","role":"professor"}'

# 2. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"email":"prof@test.com","password":"Test123!"}' | jq -r '.access_token')

# 3. Crear curso
curl -X POST http://localhost:8000/api/v1/courses/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Curso Test","description":"Descripción"}'

# 4. Consultar IA
curl -X POST http://localhost:8000/api/v1/consultar_profesor \
  -H "Content-Type: application/json" \
  -d '{"age":60,"is_smoker":true,"pack_years":30,"sensitive_tumor_volume":10}'
```

---

**¿Dudas?** Revisa la documentación interactiva en http://localhost:8000/docs
