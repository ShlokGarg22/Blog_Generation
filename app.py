import boto3
import json
import botocore.config
from datetime import datetime
import os

def blog_generate_using_bedrock(blogtopic: str) -> str:
    config = botocore.config.Config(
        read_timeout=900,
        connect_timeout=900,
        retries={"max_attempts": 3}
    )
    
    client = boto3.client('bedrock-runtime', region_name='us-east-1', config=config)

    response = client.converse(
        modelId="meta.llama3-8b-instruct-v1:0",
        messages=[
            {
                "role": "user",
                "content": [
                    {"text": f"Write a 200 words blog on the topic {blogtopic}"}
                ]
            }
        ],
        inferenceConfig={
            "maxTokens": 512,
            "temperature": 0.5
        }
    )
    
    return response['output']['message']['content'][0]['text']

def save_blog_details_s3(s3_key, s3_bucket, generate_blog):
    s3 = boto3.client('s3')
    try:
        s3.put_object(Bucket=s3_bucket, Key=s3_key, Body=generate_blog)
    except Exception as e:
        print(f"Error saving blog to S3: {e}")
        raise e

def lambda_handler(event, context):
    try:
        # Check if invoked via API gateway with 'body' or directly with JSON
        if 'body' in event and isinstance(event['body'], str):
            body = json.loads(event['body'])
        else:
            body = event
            
        blogtopic = body.get('blog_topic')
        if not blogtopic:
            return {
                'statusCode': 400,
                'body': json.dumps("Missing 'blog_topic' in the requested event.")
            }

        generate_blog = blog_generate_using_bedrock(blogtopic=blogtopic)

        if generate_blog:
           
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            s3_key = f"blog-output/{current_time}.txt"
            
            s3_bucket = os.environ.get('S3_BUCKET_NAME', 'aws-bed-rock-course1')
            
            save_blog_details_s3(s3_key, s3_bucket, generate_blog)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    "message": "Blog generation is completed successfully.",
                    "blog": generate_blog
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps("No blog was generated.")
            }
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Internal server error: {str(e)}")
        }