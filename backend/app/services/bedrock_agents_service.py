import boto3
import json
from typing import Dict, List, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class BedrockAgentsService:
    """
    Multi-Agent Architecture for Well-Architected Framework Assessment
    Each pillar has a specialized AI agent
    """
    
    def __init__(self):
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=settings.AWS_REGION)
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=settings.AWS_REGION)
        self.model_id = settings.BEDROCK_MODEL_ID
        
        # Define specialized agents for each pillar
        self.agents = {
            'operational_excellence': {
                'name': 'Operational Excellence Agent',
                'system_prompt': """You are an AWS Operational Excellence expert specializing in:
- Infrastructure as Code (IaC) best practices
- CI/CD pipeline optimization
- Monitoring and observability
- Incident response and management
- Automation and orchestration
- Change management
- Operational readiness

Analyze AWS resources and provide specific, actionable recommendations for operational excellence.""",
                'focus_areas': ['automation', 'monitoring', 'cicd', 'incident_management']
            },
            'security': {
                'name': 'Security Agent',
                'system_prompt': """You are an AWS Security expert specializing in:
- Identity and Access Management (IAM)
- Data protection and encryption
- Infrastructure protection
- Detective controls
- Incident response
- Compliance and governance
- Security best practices

Analyze AWS resources and identify security vulnerabilities with remediation steps.""",
                'focus_areas': ['iam', 'encryption', 'network_security', 'compliance']
            },
            'reliability': {
                'name': 'Reliability Agent',
                'system_prompt': """You are an AWS Reliability expert specializing in:
- High availability architecture
- Disaster recovery planning
- Backup and restore strategies
- Fault tolerance
- Auto-scaling and load balancing
- Multi-AZ and multi-region deployments
- Resilience testing

Analyze AWS resources and recommend improvements for reliability and availability.""",
                'focus_areas': ['high_availability', 'disaster_recovery', 'fault_tolerance', 'backup']
            },
            'performance_efficiency': {
                'name': 'Performance Efficiency Agent',
                'system_prompt': """You are an AWS Performance Efficiency expert specializing in:
- Resource selection and optimization
- Compute optimization (EC2, Lambda, ECS)
- Storage optimization (S3, EBS, EFS)
- Database performance tuning
- Network optimization
- Caching strategies
- Performance monitoring

Analyze AWS resources and identify performance optimization opportunities.""",
                'focus_areas': ['compute', 'storage', 'database', 'network', 'caching']
            },
            'cost_optimization': {
                'name': 'Cost Optimization Agent',
                'system_prompt': """You are an AWS Cost Optimization expert specializing in:
- Right-sizing resources
- Reserved Instances and Savings Plans
- Spot Instances utilization
- Storage lifecycle policies
- Cost allocation and tagging
- Unused resource identification
- Cost monitoring and budgets

Analyze AWS resources and identify cost-saving opportunities with ROI calculations.""",
                'focus_areas': ['rightsizing', 'pricing_models', 'unused_resources', 'storage_optimization']
            },
            'sustainability': {
                'name': 'Sustainability Agent',
                'system_prompt': """You are an AWS Sustainability expert specializing in:
- Carbon footprint reduction
- Energy-efficient architectures
- Resource utilization optimization
- Serverless and managed services
- Regional selection for sustainability
- Workload optimization
- Sustainable practices

Analyze AWS resources and recommend improvements for environmental sustainability.""",
                'focus_areas': ['carbon_footprint', 'energy_efficiency', 'resource_utilization', 'serverless']
            }
        }
    
    def invoke_agent(self, agent_type: str, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Invoke a specialized agent for a specific pillar
        
        Args:
            agent_type: Type of agent (operational_excellence, security, etc.)
            prompt: User prompt/question
            context: Additional context (scan results, resources, etc.)
        
        Returns:
            Agent response
        """
        try:
            if agent_type not in self.agents:
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            agent = self.agents[agent_type]
            system_prompt = agent['system_prompt']
            
            # Add context to prompt if provided
            if context:
                prompt = f"""Context:
{json.dumps(context, indent=2)}

Question/Task:
{prompt}"""
            
            # Invoke Claude with agent-specific system prompt
            messages = [{"role": "user", "content": prompt}]
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "messages": messages,
                "system": system_prompt,
                "temperature": 0.7,
            }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
        
        except Exception as e:
            logger.error(f"Error invoking {agent_type} agent: {e}")
            raise
    
    def analyze_pillar(self, pillar: str, scan_results: Dict) -> Dict:
        """
        Analyze a specific pillar using its specialized agent
        
        Args:
            pillar: Pillar name (operational_excellence, security, etc.)
            scan_results: AWS scan results
        
        Returns:
            Analysis results with recommendations
        """
        try:
            agent_type = pillar.lower().replace(' ', '_').replace('-', '_')
            
            prompt = f"""Analyze the following AWS infrastructure for the {pillar} pillar:

Provide:
1. Current State Assessment (score 1-10)
2. Key Findings (strengths and weaknesses)
3. Critical Issues (high priority)
4. Recommendations (specific, actionable)
5. Implementation Steps
6. Expected Impact

Format your response in a structured manner."""
            
            response = self.invoke_agent(agent_type, prompt, scan_results)
            
            return {
                'pillar': pillar,
                'agent': self.agents[agent_type]['name'],
                'analysis': response,
                'focus_areas': self.agents[agent_type]['focus_areas']
            }
        
        except Exception as e:
            logger.error(f"Error analyzing {pillar}: {e}")
            return {
                'pillar': pillar,
                'error': str(e)
            }
    
    def comprehensive_assessment(self, scan_results: Dict) -> Dict:
        """
        Run comprehensive assessment using all specialized agents
        
        Args:
            scan_results: Complete AWS scan results
        
        Returns:
            Comprehensive assessment from all agents
        """
        try:
            logger.info("Starting comprehensive multi-agent assessment")
            
            assessments = {}
            
            # Run each agent in parallel (can be optimized with threading)
            for pillar_key, agent_info in self.agents.items():
                pillar_name = pillar_key.replace('_', ' ').title()
                logger.info(f"Running {agent_info['name']} assessment")
                
                assessment = self.analyze_pillar(pillar_key, scan_results)
                assessments[pillar_key] = assessment
            
            # Generate executive summary using orchestrator
            executive_summary = self._generate_executive_summary(assessments, scan_results)
            
            return {
                'executive_summary': executive_summary,
                'pillar_assessments': assessments,
                'overall_score': self._calculate_overall_score(assessments),
                'priority_recommendations': self._extract_priority_recommendations(assessments)
            }
        
        except Exception as e:
            logger.error(f"Error in comprehensive assessment: {e}")
            raise
    
    def _generate_executive_summary(self, assessments: Dict, scan_results: Dict) -> str:
        """Generate executive summary from all agent assessments"""
        try:
            summary_prompt = f"""Based on the following pillar assessments, create an executive summary:

{json.dumps(assessments, indent=2)}

Provide:
1. Overall Infrastructure Health (1-10)
2. Top 5 Critical Issues
3. Top 5 Quick Wins
4. Strategic Recommendations
5. Estimated Cost Impact
6. Implementation Timeline

Keep it concise and executive-friendly."""
            
            response = self.invoke_agent('operational_excellence', summary_prompt)
            return response
        
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return "Error generating executive summary"
    
    def _calculate_overall_score(self, assessments: Dict) -> float:
        """Calculate overall Well-Architected score"""
        # This is a simplified version - can be enhanced with actual scoring logic
        return 7.5  # Placeholder
    
    def _extract_priority_recommendations(self, assessments: Dict) -> List[Dict]:
        """Extract and prioritize recommendations from all agents"""
        recommendations = []
        
        for pillar, assessment in assessments.items():
            if 'analysis' in assessment:
                recommendations.append({
                    'pillar': pillar,
                    'agent': assessment.get('agent'),
                    'summary': assessment['analysis'][:200] + '...'  # First 200 chars
                })
        
        return recommendations

# Singleton instance
bedrock_agents_service = BedrockAgentsService()
