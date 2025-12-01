# Form Builder Deployment Guide

## Repository Information
- **Source Code**: `landoncolvig/opex-technologies` (development)
- **Deployment Target**: `opex-technologies/opex-technologies.github.io` (production)
- **Live URL**: https://opex-technologies.github.io/
- **GitHub Pages**: Builds from `main` branch, `/` (root) folder

## Deployment Process

### Important: Two-Repository Setup
This project uses a **two-repository workflow**:
1. **Development**: Code is developed in `landoncolvig/opex-technologies/Q4 form scoring project/frontend/form-builder`
2. **Production**: Built files are deployed to `opex-technologies/opex-technologies.github.io` main branch (organization's default GitHub Pages site)

### Step 1: Build the Application
```bash
cd "/Users/landoncolvig/Documents/opex-technologies/Q4 form scoring project/frontend/form-builder"
npm run build
```

This creates optimized production files in the `dist/` directory.

### Step 2: Deploy to Production

The deployment repository is `opex-technologies/opex-technologies.github.io` which serves the Form Builder at the root domain.

#### Manual Deployment (Recommended Process)
```bash
# Step 1: Build the application
cd "/Users/landoncolvig/Documents/opex-technologies/Q4 form scoring project/frontend/form-builder"
npm run build

# Step 2: Clone the deployment repository
cd /tmp
rm -rf opex-technologies.github.io
git clone https://github.com/opex-technologies/opex-technologies.github.io.git

# Step 3: Clear old files and copy new build
cd opex-technologies.github.io
rm -rf * .DS_Store

# Step 4: Copy entire dist directory contents (including assets/)
cd "/Users/landoncolvig/Documents/opex-technologies/Q4 form scoring project/frontend/form-builder/dist"
cp -r . /tmp/opex-technologies.github.io/

# Step 5: Commit and push
cd /tmp/opex-technologies.github.io
git add -A
git commit -m "Deploy Form Builder [your message]"
git push origin main
```

**IMPORTANT**: Make sure to copy the entire `dist/` directory including the `assets/` subdirectory. The build creates:
- `index.html` (main page)
- `vite.svg` (favicon)
- `assets/index-[hash].js` (JavaScript bundle)
- `assets/index-[hash].css` (CSS bundle)

#### Automated Deployment Script (Recommended)
```bash
# Run the deployment script
npm run deploy
```

The `npm run deploy` command is configured in `package.json` to use `gh-pages`, but this needs to be updated to use the correct repository.

### Step 3: Verify Deployment

1. Wait 2-5 minutes for GitHub Pages to rebuild
2. Visit https://opextechnologies.com/ or https://opex-technologies.github.io/
3. Hard refresh: `Cmd + Shift + R` (Mac) or `Ctrl + Shift + R` (Windows)
4. Check browser console for any errors
5. Test question loading in template editor

### Configuration Files

**package.json** - Deploy script:
```json
{
  "scripts": {
    "deploy": "npm run build && gh-pages -d dist"
  }
}
```

**vite.config.js** - Base path for assets:
```javascript
export default defineConfig({
  base: '/',
  plugins: [react()],
})
```

**Git Remotes**:
- Development: `https://github.com/landoncolvig/opex-technologies.git`
- Deployment: `https://github.com/opex-technologies/opex-technologies.github.io.git` (organization's default GitHub Pages site)

## Troubleshooting

### Deployment Not Showing Up
1. **Check GitHub Pages settings** in the deployment repository
   - Go to https://github.com/opex-technologies/opex-technologies.github.io/settings/pages
   - Ensure "Source" is set to "Deploy from a branch"
   - Branch should be `main` and folder should be `/ (root)`

2. **Clear CDN cache** - GitHub Pages CDN can cache aggressively
   - Wait 5-10 minutes after deployment
   - Try incognito/private mode
   - Add query parameter: `?v=timestamp`

3. **Verify files are in the correct repository**
   ```bash
   # Check what's deployed
   curl -s https://opex-technologies.github.io/ | grep "index-"
   ```

### Questions Not Loading
- Check browser console for errors
- Verify API endpoints in `.env` file
- Ensure authentication is working
- Check Network tab for failed API requests

## Environment Variables

The production environment uses:
- `VITE_API_URL`: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api
- `VITE_AUTH_API_URL`: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api
- `VITE_RESPONSE_SCORER_API_URL`: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/response-scorer-api
- `VITE_ENV`: production

These are set in `/Q4 form scoring project/frontend/form-builder/.env`

## Post-Deployment Checklist

- [ ] Form Builder loads at root URL
- [ ] Login works
- [ ] Questions load in template editor (all ~1,041 questions)
- [ ] Category filter works
- [ ] Search works
- [ ] Template creation/editing works
- [ ] Form preview works
- [ ] Deployment works (correct URL: `https://opex-technologies.github.io/forms/template_name.html`)
- [ ] Duplicate template works
- [ ] Edit published templates works
- [ ] Form submission works (success message displays, progress bar shows 100%)
- [ ] All modals have keyboard support (Escape key)
- [ ] All icon buttons have ARIA labels
- [ ] No console errors

## Recent Updates (December 2025)

### Form Builder UI Improvements
- **Edit Published Templates**: Templates can now be edited in both "draft" and "published" status (only "archived" templates are blocked)
- **Duplicate Template**: New "Duplicate" button in template editor creates a copy with " (Copy)" suffix
- **Fixed Deployed URL**: URLs now correctly display as `https://opex-technologies.github.io/forms/...` (removed duplicate repo name in path)
- **URL Fix Helper**: Template list automatically corrects legacy malformed URLs for display

### Deployed Forms Improvements
- **Success Message**: Fixed success message display after form submission (moved outside form element)
- **Progress Bar**: Progress bar now shows 100% on successful submission
- **Styling**: Updated form styling with light gray header background for better logo visibility
- **Form Submission**: Fixed payload format to work with webhook (`formName` and `formData` structure)
- **Debug Logging**: Added console logging for troubleshooting submissions

### Backend API Changes
- **PUT /form-builder/templates/:id**: Now allows editing published templates (was draft-only)
- **POST /form-builder/templates/:id/duplicate**: New endpoint to duplicate templates with all questions
- **GitHub Pages URL**: Fixed URL construction for `*.github.io` repositories

### Environment Variables (Cloud Function)
- `GITHUB_REPO_OWNER`: `opex-technologies`
- `GITHUB_REPO_NAME`: `opex-technologies.github.io`
- `GITHUB_BRANCH`: `main`

## Notes

- GitHub Pages can take **up to 10 minutes** to update after a push
- The deployment repository is `opex-technologies.github.io` (organization's default GitHub Pages site)
- There is also a `client-pages` repository which is NOT used for the Form Builder
- Always verify deployment by checking the live site in incognito mode
- Make sure to deploy the entire `dist/` directory including the `assets/` subdirectory
