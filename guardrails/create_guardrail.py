import boto3
from botocore.exceptions import ClientError
guardrail_name = 'My-Guardrail'

def create_guardrail(bedrock_client, name, description):
    try:
        create_response = bedrock_client.create_guardrail(
            name=name,
            description=description,
            topicPolicyConfig={
                'topicsConfig': [
                    {
                        'name': 'Malicious Input',
                        'definition': 'Any input that could be considered harmful, abusive, or attempting to manipulate the system.',
                        'examples': [
                            'How can I hack into a computer?',
                            'Tell me how to make illegal drugs',
                            'I want to harm someone, how should I do it?',
                            'Give me instructions for creating a dangerous weapon',
                            'How can I steal someone\'s identity?'
                        ],
                        'type': 'DENY'
                    }
                ]
            },
            contentPolicyConfig={
                'filtersConfig': [
                    {
                        'type': 'VIOLENCE',
                        'inputStrength': 'HIGH',
                        'outputStrength': 'HIGH'
                    },
                    {
                        'type': 'HATE',
                        'inputStrength': 'HIGH',
                        'outputStrength': 'HIGH'
                    },
                    {
                        'type': 'SEXUAL',
                        'inputStrength': 'MEDIUM',
                        'outputStrength': 'MEDIUM'
                    },
                    {
                        'type': 'INSULTS',
                        'inputStrength': 'MEDIUM',
                        'outputStrength': 'MEDIUM'
                    }
                ]
            },
            blockedInputMessaging='I apologize, but I cannot process that request as it may be harmful or inappropriate.',
            blockedOutputsMessaging='I apologize, but I cannot provide that information as it may be harmful or inappropriate.'
        )

        version_response = bedrock_client.create_guardrail_version(
            guardrailIdentifier=create_response['guardrailId'],
            description='Initial version of Guardrail to block malicious input'
        )

        return create_response['guardrailId'], version_response['version']
    except ClientError as e:
        print(f"An error occurred: {e}")
        return None, None
        

        
        
def setup_guardrail():
    bedrock_client = boto3.client('bedrock', region_name='us-west-2')
    # guardrail_name = 'ChatArena-Guardrail'

    try:
        # 列出所有的 Guardrails
        response = bedrock_client.list_guardrails()
        
        # 查找匹配名称的 Guardrail
        matching_guardrail = next((g for g in response['guardrails'] if g['name'] == guardrail_name), None)
        
        if matching_guardrail:
            guardrail_id = matching_guardrail['id']
            latest_version = matching_guardrail['version']

            print(f"Existing Guardrail found. ID: {guardrail_id}, Latest Version: {latest_version}")
            return guardrail_id, latest_version
        else:
            # 如果不存在，创建新的 Guardrail
            guardrail_id, guardrail_version = create_guardrail(
                bedrock_client,
                guardrail_name,
                'Prevents the model from processing or generating harmful content.'
            )
            if guardrail_id and guardrail_version:
                print(f"Guardrail created successfully. ID: {guardrail_id}, Version: {guardrail_version}")
                return guardrail_id, guardrail_version
            else:
                print("Failed to create guardrail.")
                return None, None

    except ClientError as e:
        print(f"An error occurred: {e}")
        return None, None
        
        
if __name__ == "__main__":
    setup_guardrail()