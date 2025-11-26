# React Frontend Setup Guide

## ✅ What's Been Created

A complete production-ready React frontend with:

1. **Patient Management**
   - Register new patients
   - Search and view patients
   - Patient detail page with tabs

2. **Problem List Management**
   - Add NAMASTE problems to patient records
   - Search NAMASTE terms and get ICD-11 suggestions
   - Dual coding (NAMASTE + ICD-11) for each problem
   - View all problems for a patient

3. **Dashboard**
   - Statistics cards
   - Quick actions

4. **Modern UI**
   - Responsive design
   - Sidebar navigation
   - Toast notifications
   - Modal dialogs

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The React app will run on `http://localhost:5173`

### 3. Make Sure Backend is Running

In a separate terminal:

```bash
cd ..
python run.py
```

Backend should be on `http://localhost:8000`

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Layout.jsx          # Main layout with sidebar
│   │   └── ProblemList.jsx     # Problem management component
│   ├── pages/
│   │   ├── Dashboard.jsx       # Dashboard page
│   │   ├── Patients.jsx        # Patient list page
│   │   ├── PatientDetail.jsx   # Patient detail with problems
│   │   ├── Encounters.jsx      # Encounters page
│   │   └── ...                 # Other pages
│   ├── services/
│   │   └── api.js              # API service layer
│   ├── App.jsx                 # Main app component
│   └── main.jsx                # Entry point
├── package.json
└── vite.config.js
```

## 🎯 Key Features

### Patient Problem Management

1. **Navigate to Patients** → Click on any patient
2. **Click "Problems" tab**
3. **Click "Add NAMASTE Problem"**
4. **Enter NAMASTE term** (e.g., "Jwara")
5. **Click search** → Get ICD-11 suggestions
6. **Select a suggestion** → Add to patient record

### Features

- ✅ Search NAMASTE terms
- ✅ Get ICD-11 code suggestions
- ✅ Add problems with dual coding
- ✅ View all patient problems
- ✅ Link problems to encounters
- ✅ Production-ready code structure

## 🔧 Configuration

### API URL

The frontend is configured to proxy API requests to `http://localhost:8000` by default.

To change this, edit `vite.config.js`:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://your-backend-url:8000',
      changeOrigin: true,
    },
  },
}
```

Or set environment variable:

```bash
# .env file
VITE_API_URL=http://localhost:8000
```

## 📦 Build for Production

```bash
npm run build
```

This creates optimized production files in the `dist` directory.

## 🎨 UI Components

- **Layout**: Sidebar navigation with collapsible menu
- **ProblemList**: Modal-based problem management
- **PatientDetail**: Tabbed patient information view
- **Dashboard**: Statistics and quick actions

## 🔗 Integration

The frontend integrates with all backend APIs:

- `/api/patients` - Patient management
- `/api/encounters` - Encounter management
- `/api/encounters/{id}/suggest-diagnosis` - NAMASTE-ICD-11 mapping
- `/api/encounters/{id}/diagnosis` - Add dual-coded diagnosis
- `/api/dashboard/stats` - Dashboard statistics

For detailed API documentation and frontend integration patterns, see [API_DOCUMENTATION.md](../API_DOCUMENTATION.md).

## 🐛 Troubleshooting

### Port Already in Use

If port 5173 is in use, Vite will automatically use the next available port.

### API Connection Issues

Make sure:
1. Backend is running on port 8000
2. CORS is enabled (if needed)
3. Check browser console for errors

### Module Not Found

Run `npm install` again to ensure all dependencies are installed.

## 📝 Next Steps

1. **Install dependencies**: `cd frontend && npm install`
2. **Start dev server**: `npm run dev`
3. **Open browser**: `http://localhost:5173`
4. **Test features**: Register patient → View patient → Add NAMASTE problem

## ✨ Production Features

- ✅ Error handling with toast notifications
- ✅ Loading states
- ✅ Responsive design
- ✅ Clean code structure
- ✅ API service layer
- ✅ React Router for navigation
- ✅ Modern React hooks
- ✅ Component-based architecture

