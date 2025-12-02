# GitHub Upload Guide for KnowAllEdge

## Prerequisites

1. **GitHub Account**: You have account `arnav-156` ✅
2. **Git Installed**: Verify with `git --version`
3. **GitHub CLI (optional)**: For easier authentication

## Step 1: Create .gitignore

First, let's ensure sensitive files aren't uploaded:

```bash
# Navigate to project root
cd intuitscape-main

# The .gitignore should already exist, but verify it includes:
# - .env
# - *.db
# - __pycache__/
# - node_modules/
# - .venv/
# - *.log
```

## Step 2: Initialize Git Repository

```bash
# Initialize git (if not already done)
git init

# Check status
git status
```

## Step 3: Create Repository on GitHub

### Option A: Using GitHub Website
1. Go to https://github.com/new
2. Repository name: `knowalledge` or `KnowAllEdge`
3. Description: "AI-powered learning platform with knowledge graphs, gamification, and analytics"
4. Choose Public or Private
5. **DO NOT** initialize with README (we already have one)
6. Click "Create repository"

### Option B: Using GitHub CLI
```bash
gh repo create knowalledge --public --description "AI-powered learning platform"
```

## Step 4: Add Files to Git

```bash
# Add all files
git add .

# Check what will be committed
git status

# Create first commit
git commit -m "Initial commit: KnowAllEdge learning platform

- Complete React frontend with knowledge graph visualization
- Flask backend with Gemini AI integration
- Gamification system with achievements and leaderboards
- Learning analytics and study tools
- Production-ready with security, monitoring, and testing
- Multi-language support (6 languages)
- PWA with offline support"
```

## Step 5: Connect to GitHub

```bash
# Add remote (replace with your actual repo URL)
git remote add origin https://github.com/arnav-156/knowalledge.git

# Verify remote
git remote -v
```

## Step 6: Push to GitHub

```bash
# Push to main branch
git branch -M main
git push -u origin main
```

## Step 7: Verify Upload

1. Go to https://github.com/arnav-156/knowalledge
2. Verify files are uploaded
3. Check README.md displays correctly

## Important Files to Verify

After upload, check these files on GitHub:
- ✅ README.md - Should display project information
- ✅ package.json - Should show "KNOWALLEDGE-frontend"
- ✅ .gitignore - Should exclude sensitive files
- ✅ LICENSE - Add if needed

## Recommended: Add GitHub Actions

Your project already has CI/CD workflows in `.github/workflows/`:
- `test.yml` - Runs tests on every push
- `deploy.yml` - Handles deployment

These will automatically run once pushed to GitHub!

## Recommended: Add Topics/Tags

On GitHub repository page, add topics:
- `ai`
- `machine-learning`
- `education`
- `knowledge-graph`
- `react`
- `flask`
- `gemini-ai`
- `learning-platform`
- `gamification`
- `pwa`

## Recommended: Enable GitHub Pages (Optional)

If you want to host documentation:
1. Go to Settings → Pages
2. Source: Deploy from a branch
3. Branch: main, folder: /docs (if you create one)

## Troubleshooting

### Authentication Issues

If you get authentication errors:

```bash
# Use Personal Access Token
# 1. Go to GitHub Settings → Developer settings → Personal access tokens
# 2. Generate new token with 'repo' scope
# 3. Use token as password when pushing
```

Or use SSH:
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to GitHub: Settings → SSH and GPG keys

# Change remote to SSH
git remote set-url origin git@github.com:arnav-156/knowalledge.git
```

### Large Files

If you have files > 100MB:
```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "*.db"
git lfs track "*.zip"

# Add .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

### Sensitive Data

If you accidentally committed sensitive data:
```bash
# Remove from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all
```

## Post-Upload Checklist

- [ ] Repository is public/private as intended
- [ ] README displays correctly
- [ ] .gitignore is working (no .env or .db files uploaded)
- [ ] CI/CD workflows are enabled
- [ ] Topics/tags are added
- [ ] Repository description is set
- [ ] License is added (if applicable)
- [ ] Issues and Discussions are enabled (optional)

## Next Steps

1. **Add Collaborators** (if needed): Settings → Collaborators
2. **Set up Branch Protection**: Settings → Branches
3. **Configure Secrets**: Settings → Secrets → Actions (for CI/CD)
4. **Add Project Board**: Projects tab (for task management)
5. **Enable Security Features**: Settings → Security

## Useful Git Commands

```bash
# Check status
git status

# View commit history
git log --oneline

# Create new branch
git checkout -b feature/new-feature

# Push branch
git push -u origin feature/new-feature

# Pull latest changes
git pull origin main

# View differences
git diff
```

---

**Ready to upload!** 🚀

Your KnowAllEdge project is now ready to be shared with the world on GitHub.
