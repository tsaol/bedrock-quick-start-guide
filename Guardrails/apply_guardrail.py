import boto3

bedrockRuntimeClient = boto3.client('bedrock-runtime', region_name="INPUT_YOUR_REGION")

guardrail_id = 'ENTER_GUARDRAIL_ID'
guardrail_version = 'ENTER_GUARDRAIL_VERSION'

input = "what time is it now?"

def main():
    response = bedrockRuntimeClient.apply_guardrail(guardrailIdentifier = guardrail_id,guardrailVersion=guardrail_version, source='INPUT|OUTPU', content=[{"text": {"text": input}}])

    ## guardrail respoinse 
    '''
    {
	'ResponseMetadata': {
		'RequestId': 'f9a2a52b-f477-4198-8ed2-230ecf20a414',
		'HTTPStatusCode': 200,
		'HTTPHeaders': {
			'date': 'Sun, 08 Sep 2024 07:20:42 GMT',
			'content-type': 'application/json',
			'content-length': '647',
			'connection': 'keep-alive',
			'x-amzn-requestid': 'f9a2a52b-f477-4198-8ed2-230ecf20a414'
		},
		'RetryAttempts': 0
	},
	'usage': {
		'topicPolicyUnits': 1,
		'contentPolicyUnits': 1,
		'wordPolicyUnits': 0,
		'sensitiveInformationPolicyUnits': 0,
		'sensitiveInformationPolicyFreeUnits': 0,
		'contextualGroundingPolicyUnits': 0
	},
	'action': 'GUARDRAIL_INTERVENED',
	'outputs': [{
		'text': 'I apologize, but I cannot process that request as it may be harmful or inappropriate.'
	}],
	'assessments': [{
		'contentPolicy': {
			'filters': [{
				'type': 'INSULTS',
				'confidence': 'HIGH',
				'action': 'BLOCKED'
			}]
		}
	}]
}
    '''
    guardrailResult = response["action"]
    print(f'Guradrail action: {guardrailResult}')

    output = response["outputs"][0]["text"]
    print(f'Final response: {output}')

if __name__ == "__main__":
    main()

