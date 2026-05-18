Connecting to the database:
ENCODED_DB_PASSWORD = os.environ.get('live_db_pass')
DATABASE_URL = f"postgresql://postgres.jtxtswhzzktficdkllbt:{ENCODED_DB_PASSWORD}@aws-1-us-west-2.pooler.supabase.com:5432/postgres

Connect to gemini:
private key for service account path: $GOOGLE_APPLICATION_CREDENTIALS

Model versions to use:
general use: gemini-3.1-flash-lite
advanced processing: gemini-3.1-pro-preview
embeddings: gemini-embedding-001
