# Streamlit Cloud Deployment Guide

## Quick Setup

1. **Main file path in Streamlit Cloud:**
   ```
   src/gui/app.py
   ```
   (Use forward slashes `/`, not backslashes `\`)

2. **Python version:**
   - Python 3.9 or higher

3. **Requirements:**
   - All dependencies are in `requirements.txt`
   - Streamlit Cloud will automatically install them

## Deployment Steps

1. Go to [Streamlit Cloud](https://streamlit.io/cloud)
2. Connect your GitHub repository: `tahaaamir21/File-Compression-For-Cloud-Storage`
3. Set the **Main file path** to: `src/gui/app.py`
4. Click **Deploy**

## Important Notes

- The app uses relative imports with fallback to absolute imports
- All `__init__.py` files are included for proper package structure
- The `.streamlit/config.toml` file configures the app settings
- Cloud bucket files (`.cloud_bucket/`) are ignored and won't be deployed

## Troubleshooting

If you get "file does not exist" error:
- Make sure the path uses forward slashes: `src/gui/app.py`
- Verify the file exists in your GitHub repository
- Check that all files are committed and pushed to GitHub

