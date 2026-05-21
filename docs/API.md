# BetBudAI API Documentation

## Base URL
```
Production: https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com
Development: http://localhost:5000
```

## Common Response Format
All endpoints return JSON:
```json
{
  "success": true,
  "data": {...},
  "timestamp": "2026-05-09T15:30:00Z",
  "version": "2.0"
}
```

## Endpoints

### Picks

#### GET /api/picks/today
Get today's official picks.

**Query Parameters:**
- `date` (optional): YYYY-MM-DD format, defaults to today UTC

**Response:**
```json
{
  "success": true,
  "date": "2026-05-09",
  "picks": [
    {
      "horse": "Venetia",
      "course": "Ascot",
      "race_time": "2026-05-09T15:05:00Z",
      "odds": 11.0,
      "stake": 6.0,
      "score": 94.5,
      "pick_rank": 1,
      "show_in_ui": true
    }
  ],
  "watchlist": [],
  "summary": {
    "total_picks": 5,
    "wins": 0,
    "places": 3,
    "losses": 1,
    "pending": 1,
    "strike_rate": 0.0,
    "roi": -39.8
  }
}
```

#### GET /api/picks/yesterday
Get yesterday's picks and results.

**Response:** Same format as `/api/picks/today`

#### GET /api/picks/featured
Get featured meeting analysis for the day.

**Query Parameters:**
- `date` (optional): YYYY-MM-DD format

**Response:**
```json
{
  "success": true,
  "date": "2026-05-09",
  "featured_course": "Ascot",
  "race_count": 8,
  "picks": [...]
}
```

### Results

#### GET /api/results/today
Get today's settled results.

**Response:**
```json
{
  "success": true,
  "date": "2026-05-09",
  "results": [...],
  "count": 5
}
```

#### GET /api/results/yesterday
Get yesterday's results.

**Response:** Same format as `/api/results/today`

### Authentication

#### POST /api/auth/login
User login.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secret123"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "email": "user@example.com",
    "username": "johndoe",
    "role": "free|pro|vip"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### POST /api/auth/register
User registration.

**Request:**
```json
{
  "email": "newuser@example.com",
  "password": "secret123",
  "full_name": "John Doe",
  "username": "johndoe"
}
```

#### POST /api/auth/verify-email
Verify email token.

**Request:**
```json
{
  "token": "verification_token_from_email"
}
```

### Admin

#### GET /api/admin/weights
Get current model weights (admin only).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "weights": {
    "recent_win": 16,
    "form_exact_course_win": 20,
    ...
  }
}
```

#### PUT /api/admin/weights
Update model weights (admin only).

**Request:**
```json
{
  "weights": {
    "recent_win": 18,
    "form_exact_course_win": 22,
    ...
  }
}
```

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "error": "Bad Request",
  "message": "Invalid parameter: date must be YYYY-MM-DD format"
}
```

### 401 Unauthorized
```json
{
  "success": false,
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": "Not Found",
  "message": "The requested resource was not found"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

## Rate Limiting
- 100 requests per minute per IP
- 1000 requests per hour per authenticated user

## Pagination
Results paginate automatically with cursors:
```json
{
  "success": true,
  "data": [...],
  "next_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "has_more": true
}
```

## Caching
- GET /api/picks/* - cached 5 minutes
- GET /api/results/* - cached 2 minutes
- Cache bypass: add `?_ts=<unix_timestamp>` query param

## WebSocket Events (Future)
Real-time updates on pick changes, new results, market movements.
```javascript
const ws = new WebSocket('wss://api.betbudai.com/ws');
ws.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  // { type: 'pick_updated', data: {...} }
});
```
