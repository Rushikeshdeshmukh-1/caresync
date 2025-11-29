# Simple Deployment Guide (No Docker)

## Quick Local Deployment

Your project is now configured to run as a single integrated server where FastAPI serves both the API and the React frontend.

### Steps to Deploy Locally:

1. **Build the Frontend** (already done):
   ```bash
   cd frontend
   npm run build
   ```

2. **Start the Server**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

3. **Access the Application**:
   - Open browser: `http://localhost:8000`
   - The React app will load automatically
   - API is available at `http://localhost:8000/api/*`

## Cloud Deployment Options (No Docker Required)

### Option 1: Render.com (Recommended - Free Tier Available)

**Steps:**
1. Push your code to GitHub
2. Go to [render.com](https://render.com) and sign up
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Build Command**: `cd frontend && npm install && npm run build && cd .. && pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**: Add `JWT_SECRET_KEY`, `RAZORPAY_KEY_ID`, etc.
6. Click "Create Web Service"

### Option 2: Railway.app (Easy Setup)

**Steps:**
1. Push code to GitHub
2. Go to [railway.app](https://railway.app) and sign up
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Python and Node.js
6. Add environment variables in Settings
7. Deploy automatically starts

### Option 3: Vercel (Frontend) + Render (Backend)

**Frontend on Vercel:**
1. Push to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import your repository
4. Set root directory to `frontend`
5. Deploy

**Backend on Render:**
1. Follow Render steps above but skip frontend build
2. Update frontend API calls to point to Render backend URL

### Option 4: PythonAnywhere (Simple Python Hosting)

**Steps:**
1. Sign up at [pythonanywhere.com](https://pythonanywhere.com)
2. Upload your code via Git or file upload
3. Create a new web app (Flask/Django, but use manual config)
4. Configure WSGI file to use `uvicorn`
5. Install dependencies in virtual environment
6. Reload web app

## Production Checklist

Before deploying to production:

- [ ] Change `JWT_SECRET_KEY` to a secure random value
- [ ] Use production Razorpay keys (not test keys)
- [ ] Set `DATABASE_URL` to PostgreSQL (not SQLite)
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS for your production domain
- [ ] Set up database backups
- [ ] Configure environment variables securely

## Current Status

✅ Frontend built successfully (`frontend/dist`)
✅ Backend configured to serve frontend
✅ Ready to deploy to any platform

**Test Locally**: `http://localhost:8000`
