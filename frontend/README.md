# Frontend — Recruiter Screening Dashboard

Modern, glassmorphic recruiter dashboard featuring dynamic candidate scorecards, quartile grouping, custom HR query evaluations, and an interactive multi-agent orbital reloader.

---

## 📁 Architecture
- `index.html`: Clean HTML5 semantic layout.
- `css/style.css`: Modern CSS styling tokens, glassmorphism dark-mode theme, orbital radar loader animations, and shimmer skeleton placeholders.
- `js/app.js`: Client-side logic, dynamic `API_BASE_URL` resolver, live candidate filtering & search, modal inspectors, and report download handling.
- `nginx.conf`: Production reverse-proxy config forwarding `/api/*` to the FastAPI backend.
- `Dockerfile`: Production Nginx Alpine container.

---

## 🚀 Running Locally

### Option A: Static Web Server (Python / Node / Live Server)
You can open `index.html` directly or serve it using Python:
```bash
python3 -m http.server 3000
```
Then visit `http://localhost:3000`. It will automatically connect to your backend running on `http://localhost:8000`.

### Option B: Node.js / NPM
```bash
npx serve -l 3000
```

---

## 🐳 Docker Deployment

```bash
docker build -t resume-screener-frontend .
docker run -p 3000:80 resume-screener-frontend
```
