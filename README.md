## 👥 Authors

- **Riyam Patel (rp4334)**
- **Sakshi Sawant (sss10106)**
  
# Photo Search Application

An intelligent photo album web application that enables natural language search using AWS AI services. Upload photos and search them using conversational queries like "show me cats" or "find pictures of dogs and grass."

## 🎯 Project Overview

This cloud-native application demonstrates the integration of multiple AWS services to create an intelligent search layer for photo albums. The system automatically labels uploaded photos using AI and makes them searchable through natural language processing.

### Key Features

- **Natural Language Search**: Search photos using conversational queries
- **Automatic Image Labeling**: AI-powered label detection using Amazon Rekognition
- **Custom Labels**: Add your own labels during photo upload
- **Real-time Indexing**: Photos are automatically indexed upon upload
- **Responsive Web Interface**: Clean, modern UI for uploading and searching photos
- **Secure API**: API Gateway with API key authentication
- **Infrastructure as Code**: Complete CloudFormation template for easy deployment
- **CI/CD Pipeline**: Automated deployment using AWS CodePipeline

## 🏗️ Architecture

The application consists of the following components:

```
Frontend (S3) → API Gateway → Lambda Functions → OpenSearch/Lex/Rekognition
                              ↓
                         Photos S3 Bucket
```

### AWS Services Used

- **Amazon S3**: Storage for frontend files and photo uploads
- **AWS Lambda**: Serverless functions for indexing and searching
- **Amazon API Gateway**: REST API endpoints
- **Amazon OpenSearch**: Photo metadata indexing and search
- **Amazon Rekognition**: Automatic image label detection
- **Amazon Lex**: Natural language query disambiguation
- **AWS CloudFormation**: Infrastructure provisioning
- **AWS CodePipeline**: CI/CD automation
- **AWS CodeBuild**: Build automation

## 📁 Project Structure

```
photo-search-app/
├── photo-search-frontend/
│   ├── index.html          # Main HTML page
│   └── app.js              # Frontend JavaScript logic
├── photo-search-backend/
│   ├── index-photos/
│   │   └── index.py        # LF1: Photo indexing Lambda
│   └── search-photos/
│       └── index.py        # LF2: Search Lambda
├── buildspec-backend.yml    # CodeBuild spec for backend
├── buildspec-frontend.yml   # CodeBuild spec for frontend
├── cloudformation.yaml      # Infrastructure template
└── README.md               # This file
```

## 🚀 Getting Started

### Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Basic understanding of AWS services
- (Optional) GitHub account for CI/CD

### Quick Deployment with CloudFormation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/photo-search-app.git
cd photo-search-app
```

2. **Deploy the CloudFormation stack**
```bash
aws cloudformation create-stack \
  --stack-name photo-search-app \
  --template-body file://cloudformation.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=PhotosBucketName,ParameterValue=photos-<your-unique-name> \
    ParameterKey=FrontendBucketName,ParameterValue=frontend-<your-unique-name>
```

3. **Wait for stack creation**
```bash
aws cloudformation wait stack-create-complete --stack-name photo-search-app
```

4. **Get the outputs**
```bash
aws cloudformation describe-stacks --stack-name photo-search-app --query 'Stacks[0].Outputs'
```

### Manual Setup

#### Step 1: Create OpenSearch Domain

1. Go to Amazon OpenSearch Service console
2. Create a new domain named `photos`
3. Choose deployment type (Development for testing, Production for live)
4. Configure fine-grained access control:
   - Enable fine-grained access control
   - Create master user with username and password
   - Note down the credentials
5. Set network configuration (VPC or public access)
6. Wait for domain creation (15-30 minutes)

#### Step 2: Deploy Lambda Functions

**Index Photos Lambda (LF1):**

1. Create deployment package:
```bash
cd photo-search-backend/index-photos
pip install urllib3 -t .
zip -r index-photos.zip .
```

2. Create Lambda function:
```bash
aws lambda create-function \
  --function-name index-photos \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler index.lambda_handler \
  --zip-file fileb://index-photos.zip \
  --timeout 30 \
  --environment Variables="{
    ES_ENDPOINT=https://your-opensearch-domain.region.es.amazonaws.com,
    OS_USER=master-username,
    OS_PASS=master-password
  }"
```

**Search Photos Lambda (LF2):**

1. Create deployment package:
```bash
cd photo-search-backend/search-photos
pip install urllib3 -t .
zip -r search-photos.zip .
```

2. Create Lambda function:
```bash
aws lambda create-function \
  --function-name search-photos \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler index.lambda_handler \
  --zip-file fileb://search-photos.zip \
  --timeout 30 \
  --environment Variables="{
    ES_ENDPOINT=https://your-opensearch-domain.region.es.amazonaws.com,
    OS_USER=master-username,
    OS_PASS=master-password,
    LEX_BOT_ID=your-bot-id,
    LEX_BOT_ALIAS_ID=your-bot-alias-id,
    LEX_LOCALE_ID=en_US
  }"
```

#### Step 3: Configure Amazon Lex Bot

1. Go to Amazon Lex V2 console
2. Create a new bot named `PhotoSearchBot`
3. Create intent `SearchIntent` with training utterances:
   - "show me {keywords}"
   - "find {keywords}"
   - "photos of {keywords}"
   - "{keywords}"
   - "show me photos with {keywords}"
4. Add slot `keywords` of type `AMAZON.AlphaNumeric`
5. Build and test the bot
6. Note down Bot ID and Alias ID

#### Step 4: Set Up API Gateway

1. Import the Swagger definition (if available) or create manually
2. Create two resources:
   - `PUT /photos` → Connect to S3 proxy
   - `GET /search?q={query}` → Connect to search-photos Lambda
3. Create usage plan and API key
4. Deploy to `prod` stage
5. Note down API Gateway endpoint and API key

#### Step 5: Configure S3 Buckets

**Photos Bucket:**
```bash
aws s3 mb s3://photos-your-unique-name

# Add S3 trigger to invoke index-photos Lambda
aws s3api put-bucket-notification-configuration \
  --bucket photos-your-unique-name \
  --notification-configuration file://s3-notification.json
```

**Frontend Bucket:**
```bash
aws s3 mb s3://frontend-your-unique-name
aws s3 website s3://frontend-your-unique-name --index-document index.html
```

Make bucket public:
```bash
aws s3api put-bucket-policy \
  --bucket frontend-your-unique-name \
  --policy file://bucket-policy.json
```

#### Step 6: Deploy Frontend

1. Update `app.js` with your API Gateway endpoint and API key:
```javascript
const API_BASE = "https://your-api-id.execute-api.region.amazonaws.com/prod";
const API_KEY = "your-api-key";
```

2. Upload to S3:
```bash
cd photo-search-frontend
aws s3 sync . s3://frontend-your-unique-name/
```

3. Access your application at:
```
http://frontend-your-unique-name.s3-website-region.amazonaws.com
```

## 🔧 Configuration

### Environment Variables

**index-photos Lambda:**
- `ES_ENDPOINT`: OpenSearch domain endpoint
- `OS_USER`: OpenSearch master username
- `OS_PASS`: OpenSearch master password

**search-photos Lambda:**
- `ES_ENDPOINT`: OpenSearch domain endpoint
- `OS_USER`: OpenSearch master username
- `OS_PASS`: OpenSearch master password
- `LEX_BOT_ID`: Amazon Lex bot ID
- `LEX_BOT_ALIAS_ID`: Amazon Lex bot alias ID
- `LEX_LOCALE_ID`: Locale ID (default: en_US)

### API Configuration

Update these values in `app.js`:
```javascript
const API_BASE = "https://your-api-gateway-url";
const API_KEY = "your-api-key";
```

## 💡 Usage

### Uploading Photos

1. Open the web application
2. Click "Choose image file"
3. Select a photo from your device
4. (Optional) Add custom labels like "vacation, beach, family"
5. Click "Upload"
6. Wait a few seconds for automatic indexing

### Searching Photos

1. Type a query in the search box:
   - Single keyword: "cat"
   - Multiple keywords: "cat and dog"
   - Natural language: "show me photos of cats"
2. Press Enter or click "Search"
3. View matching photos with their labels

### API Usage

**Upload a photo:**
```bash
curl -X PUT \
  "https://your-api-id.execute-api.region.amazonaws.com/prod/photos?objectKey=mycat.jpg" \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: image/jpeg" \
  -H "x-amz-meta-customLabels: fluffy, persian, pet" \
  --data-binary "@mycat.jpg"
```

**Search photos:**
```bash
curl -X GET \
  "https://your-api-id.execute-api.region.amazonaws.com/prod/search?q=cat" \
  -H "x-api-key: your-api-key"
```

## 🔄 CI/CD Pipeline

The project includes CodePipeline configurations for automated deployment.

### Backend Pipeline

1. Source: GitHub repository (backend folder)
2. Build: CodeBuild using `buildspec-backend.yml`
3. Deploy: Updates Lambda functions automatically

### Frontend Pipeline

1. Source: GitHub repository (frontend folder)
2. Build: CodeBuild using `buildspec-frontend.yml`
3. Deploy: Syncs to S3 frontend bucket

### Setting Up Pipelines

1. Create CodeBuild projects using the provided buildspec files
2. Create CodePipeline with GitHub source
3. Connect build and deploy stages
4. Push commits to trigger automatic deployment

## 🧪 Testing

### Test Photo Upload and Indexing

1. Upload a test photo via the UI or API
2. Check CloudWatch Logs for index-photos Lambda
3. Verify document in OpenSearch:
```bash
curl -X GET "https://your-opensearch-endpoint/photos/_search?pretty" \
  -u "master-username:master-password"
```

### Test Search Functionality

1. Search for a known label
2. Verify results match expected photos
3. Check CloudWatch Logs for search-photos Lambda

### Test Lex Integration

Test the bot in Lex console:
- Input: "show me cats and dogs"
- Expected: Keywords slot contains "cats" and "dogs"

## 🛠️ Troubleshooting

### Photos Not Appearing in Search

1. Check index-photos Lambda logs in CloudWatch
2. Verify S3 trigger is configured correctly
3. Confirm OpenSearch credentials are correct
4. Check OpenSearch domain is accessible

### Search Returns Empty Results

1. Verify photos are indexed in OpenSearch
2. Check search-photos Lambda logs
3. Test Lex bot independently
4. Verify API Gateway integration

### CORS Errors

1. Enable CORS on API Gateway methods
2. Redeploy API after changes
3. Clear browser cache

### Permission Issues

Ensure Lambda execution role has:
- `s3:GetObject` and `s3:HeadObject` for photos bucket
- `rekognition:DetectLabels`
- `lex:RecognizeText`
- CloudWatch Logs permissions

## 📊 Cost Optimization

The application was designed with cost optimization in mind:

- **Serverless Architecture**: Pay only for actual usage
- **OpenSearch**: Can be paused when not in use
- **S3**: Standard tier for infrequent access
- **Lambda**: Free tier covers most development usage

**Cost-saving tips:**
- Delete OpenSearch domain when not actively developing
- Use S3 lifecycle policies to archive old photos
- Monitor Lambda invocations and optimize timeout values

## 🔒 Security Best Practices

1. **API Keys**: Rotate regularly, don't commit to Git
2. **OpenSearch**: Use fine-grained access control
3. **S3 Buckets**: 
   - Keep photos bucket private
   - Use signed URLs for photo access in production
4. **IAM Roles**: Follow principle of least privilege
5. **Secrets**: Use AWS Secrets Manager for credentials

## 📝 Assignment Requirements

This project fulfills all requirements for CSGY 9223 Assignment 3:

- ✅ OpenSearch domain for photo indexing
- ✅ S3 bucket for photo storage
- ✅ Lambda function (LF1) for photo indexing
- ✅ S3 PUT event trigger
- ✅ Rekognition integration for automatic labeling
- ✅ Custom labels via S3 metadata
- ✅ Lambda function (LF2) for search
- ✅ Amazon Lex bot for query disambiguation
- ✅ API Gateway with PUT /photos and GET /search
- ✅ API key authentication
- ✅ Frontend application with upload and search
- ✅ CodePipeline for backend and frontend
- ✅ CloudFormation template for infrastructure

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is part of an academic assignment for NYU's Cloud Computing course.

## 🙏 Acknowledgments

- NYU Tandon School of Engineering
- CSGY 9223: Cloud Computing and Big Data Systems
- AWS Documentation and Tutorials
- Course instructors and TAs

## 📞 Support

For issues and questions:
- Check CloudWatch Logs for Lambda errors
- Review OpenSearch domain health
- Verify all environment variables are set correctly
- Consult AWS documentation for service-specific issues

## 🗺️ Roadmap

Future enhancements:
- [ ] Face detection and recognition
- [ ] Photo tagging by location (geolocation)
- [ ] Advanced search filters (date, size, etc.)
- [ ] Photo albums and collections
- [ ] Social sharing features
- [ ] Mobile app integration
- [ ] Video support
- [ ] Multi-language support

---
**Note**: Remember to replace placeholder values (YOUR_ACCOUNT_ID, your-unique-name, etc.) with your actual AWS resource identifiers before deploying.
