# Backend

## Large model file (`model.safetensors`) and GitHub push limit

The model file at `backend/models/mood_regression_model/model.safetensors` is ~255MB, which exceeds normal GitHub limits unless tracked with Git LFS.

### One-time setup (macOS)

```bash
brew install git-lfs
git lfs install
```

### Convert this repo to use Git LFS for safetensors

Run from repository root:

```bash
git lfs track "backend/models/mood_regression_model/*.safetensors"
git add .gitattributes

# Rewrite commits so large file becomes LFS object
git lfs migrate import --include="backend/models/mood_regression_model/*.safetensors"
```

### Push rewritten branch

```bash
git push origin feature/model --force-with-lease
```

### Fresh clone users

Anyone cloning this repo should run:

```bash
git lfs install
git lfs pull
```

## Alternative (no Git LFS)

Store the model in external storage (Hugging Face/S3/Drive) and download it at app startup.
