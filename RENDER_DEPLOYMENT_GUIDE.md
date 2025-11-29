# Deploy to Render.com - Step by Step Guide

## Prerequisites
- GitHub account
- Render.com account (free)

## Step 1: Prepare Your Code

✅ **Already Done:**
- Frontend built (`frontend/dist`)
- `render.yaml` configuration created
- `.gitignore` file created

## Step 2: Push to GitHub

Open a terminal and run:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - CareSync Platform"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

## Step 3: Deploy on Render

1. **Go to Render.com**
   - Visit: https://render.com
   - Click "Get Started" or "Sign Up"
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New +" button (top right)
   - Select "Web Service"
   - Click "Connect a repository"
   - Find and select your repository

3. **Configure Service** (Render will auto-detect from `render.yaml`)
   - **Name**: caresync-platform (or your choice)
   - **Environment**: Python 3
   - **Build Command**: `cd frontend && npm install && npm run build && cd .. && pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free

4. **Add Environment Variables**
   Click "Advanced" → "Add Environment Variable":
   
   - `JWT_SECRET_KEY`: (Click "Generate" or use a secure random string)
   - `RAZORPAY_KEY_ID`: your_razorpay_key_id (optional for now)
   - `RAZORPAY_KEY_SECRET`: your_razorpay_secret (optional for now)
   - `DATABASE_URL`: sqlite:///./terminology.db

5. **Deploy**
   - Click "Create Web Service"
   - Wait 5-10 minutes for deployment
   - Render will show build logs

## Step 4: Access Your Application

Once deployed, Render will provide a URL like:
- `https://caresync-platform.onrender.com`

Your app will be live at this URL!

## Important Notes

### Database Persistence
- SQLite on Render's free tier is **ephemeral** (resets on restart)
- For production, upgrade to PostgreSQL:
  1. In Render dashboard, create a new PostgreSQL database
  2. Copy the "Internal Database URL"
  3. Update `DATABASE_URL` environment variable
  4. Redeploy

### Free Tier Limitations
- App sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds
- 750 hours/month free

### Upgrade to Paid ($7/month)
- No sleep
- Faster performance
- Persistent disk storage

## Troubleshooting

**Build fails?**
- Check build logs in Render dashboard
- Ensure `requirements.txt` has all dependencies
- Verify Node.js version compatibility

**App won't start?**
- Check "Logs" tab in Render
- Verify environment variables are set
- Ensure port is `$PORT` (Render provides this)

**Database errors?**
- Run migrations manually via Render Shell
- Or upgrade to PostgreSQL

## Alternative: Quick Deploy Button

Add this to your GitHub README for one-click deploy:

```markdown
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)
```

## Need Help?

- Render Docs: https://render.com/docs
- Community: https://community.render.com
- Support: support@render.com
