Connecting to the database:
ENCODED_DB_PASSWORD = os.environ.get('live_db_pass')
DATABASE_URL = f"postgresql://postgres.jtxtswhzzktficdkllbt:{ENCODED_DB_PASSWORD}@aws-1-us-west-2.pooler.supabase.com:5432/postgres

Connect to gemini:
private key for service account path: $GOOGLE_APPLICATION_CREDENTIALS

Model versions to use:
general use: gemini-3.1-flash-lite
advanced processing: gemini-3.1-pro-preview
embeddings: gemini-embedding-001

Front end deployments:
buckets: brightwheel-demo-admin, brightwheel-demo-client
github action secrets: AWS_ROLE_ARN, ADMIN_DISTRIBUTION_ID, CLIENT_DISTRIBUTION_ID

Backend deployment (dockerpush.sh requirements in .env):
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
ECR_URI=134267836285.dkr.ecr.us-east-1.amazonaws.com
