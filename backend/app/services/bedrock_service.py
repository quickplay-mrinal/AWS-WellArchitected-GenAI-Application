import boto3
import json
from typing import Dict, List, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class BedrockService:
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=settings.AWS_REGION
        )
        self.bedrock_agent_runtime = boto3.client(
            'bedrock-agent-runtime',
            region_name=settings.AWS_REGION
        )
        self.model_id = settings.BEDROCK_MODEL_ID
        self.inference_profile_arn = settings.BEDROCK_INFERENCE_PROFILE_ARN
        self.kb_id = settings.BEDROCK_KNOWLEDGE_BASE_ID
    
    def invoke_claude(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 4096) -> str:
        """Invoke Claude Sonnet 4 model"""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": messages,
            }
            
            if system_prompt:
                body["system"] = system_prompt
            
            # Use inference profile if available, otherwise use model ID
            model_identifier = self.inference_profile_arn if self.inference_profile_arn else self.model_id
            
            response = self.bedrock_runtime.invoke_model(
                modelId=model_identifier,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
        
        except Exception as e:
            logger.error(f"Error invoking Bedrock: {e}")
            raise
    
    def query_knowledge_base(self, query: str, max_results: int = 5) -> List[Dict]:
        """Query Bedrock Knowledge Base"""
        try:
            if not self.kb_id:
                logger.warning("Knowledge Base ID not configured")
                return []
            
            response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            return response.get('retrievalResults', [])
        
        except Exception as e:
            logger.error(f"Error querying Knowledge Base: {e}")
            return []
    
    def analyze_scan_results(self, scan_results: Dict) -> str:
        """Analyze AWS scan results using Claude"""
        system_prompt = """You are an AWS Well-Architected Framework expert. 
Analyze the provided AWS account scan results and provide detailed recommendations 
based on the 6 pillars: Operational Excellence, Security, Reliability, 
Performance Efficiency, Cost Optimization, and Sustainability."""
        
        prompt = f"""Analyze the following AWS account scan results and provide comprehensive recommendations:

{json.dumps(scan_results, indent=2)}

Please provide:
1. Executive Summary
2. Pillar-wise Analysis (for each of the 6 pillars)
3. Critical Issues and Risks
4. Prioritized Recommendations
5. Best Practices to Implement

Format your response in a structured manner."""
        
        return self.invoke_claude(prompt, system_prompt, max_tokens=8000)
    
    def get_pillar_recommendations(self, pillar: str, resources: Dict) -> str:
        """Get specific pillar recommendations"""
        kb_results = self.query_knowledge_base(f"AWS Well-Architected {pillar} pillar best practices")
        
        context = "\n".join([result.get('content', {}).get('text', '') for result in kb_results])
        
        prompt = f"""Based on the following Well-Architected Framework documentation:

{context}

Analyze these AWS resources for the {pillar} pillar:

{json.dumps(resources, indent=2)}

Provide specific, actionable recommendations."""
        
        return self.invoke_claude(prompt, max_tokens=4096)

bedrock_service = BedrockService()
