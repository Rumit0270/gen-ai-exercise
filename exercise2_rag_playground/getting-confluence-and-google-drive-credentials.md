# Google Drive and Confluence Authentication Setup

## Service Account Setup for Google Drive

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Note your **Project ID**

### 2. Enable Google Drive API

1. Navigate to **APIs & Services → Library**
2. Search for **"Google Drive API"**
3. Click **Enable**

### 3. Create Service Account

1. Go to **IAM & Admin → Service Accounts**
2. Click **Create Service Account**
3. **Name**: `rag-playground-service`
4. **Description**: `Service account for RAG document access`
5. Click **Create and Continue**
6. Skip optional steps, click **Done**

### 4. Generate Service Account Key

1. Click on your service account
2. Go to **Keys** tab
3. Click **Add Key → Create New Key**
4. Choose **JSON** format
5. Download and save as `google_credentials.json`

### 5. Share Documents with Service Account

1. Open your Google Drive documents
2. Click **Share** on each document
3. Add the service account email from the JSON file (`client_email`)
4. Set permission to **"Viewer"**
5. Click **Send**

**Service account email format:**

```
your-service-name@your-project-id.iam.gserviceaccount.com
```

### 6. Extract Document IDs

From your Google Drive URLs:

**Google Document:**

```
https://docs.google.com/document/d/<DOCUMENT_ID>/edit
```

**PDF File:**

```
https://drive.google.com/file/d/<FILE_ID>/view
```

## Confluence API Setup

### 1. Generate Confluence API Token

1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **Create API token**
3. **Label**: `RAG-Playground-Access`
4. **Copy the token and add it to .env file**

### 2. Get Confluence Page Details

1. Navigate to your Code of Conduct page
2. **Copy the full URL**
3. **Extract Page ID** from URL:
   ```
   https://company.atlassian.net/wiki/spaces/HR/pages/<PAGE_ID>/Code-of-Conduct
   ```
4. **Extract Base URL**:
   ```
   https://company.atlassian.net/wiki
   ```

### 3. Test Confluence Access

```bash
curl -u "your.email@company.com:your_api_token" \
  "https://company.atlassian.net/wiki/rest/api/content/123456"
```
