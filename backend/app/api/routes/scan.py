from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List
from app.api.routes.auth import get_current_user
from app.repositories.scan_repository import ScanRepository
from app.repositories.credential_repository import CredentialRepository
from app.schemas.scan import ScanCreate, ScanResponse, ScanDetailResponse
from app.services.aws_scanner import AWSScanner
from app.services.bedrock_service import bedrock_service
from app.core.security import decrypt_credential
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def perform_scan(scan_id: str, user_id: str, credential_id: str, regions: List[str] = None):
    """Background task to perform AWS scan"""
    try:
        # Update scan status to running
        ScanRepository.update_scan(user_id, scan_id, {
            'status': 'running',
            'started_at': None  # Will be set by DynamoDB
        })
        
        # Get credentials
        credential = CredentialRepository.get_credential_by_id(credential_id)
        if not credential:
            raise Exception("Credential not found")
        
        # Decrypt credentials
        access_key = decrypt_credential(credential['encrypted_access_key'])
        secret_key = decrypt_credential(credential['encrypted_secret_key'])
        
        # Initialize scanner
        scanner = AWSScanner(access_key, secret_key)
        
        # Get regions to scan
        if not regions:
            regions = scanner.get_all_regions()
        
        # Scan each region
        all_results = {}
        for idx, region in enumerate(regions):
            logger.info(f"Scanning region: {region}")
            region_results = scanner.scan_region(region)
            all_results[region] = region_results
            
            # Update progress
            progress = int(((idx + 1) / len(regions)) * 80)  # 80% for scanning
            ScanRepository.update_scan(user_id, scan_id, {
                'progress': progress,
                'regions_scanned': list(all_results.keys()),
                'results': all_results
            })
        
        # Generate AI recommendations using multi-agent system
        logger.info("Generating AI recommendations with specialized agents")
        ScanRepository.update_scan(user_id, scan_id, {'progress': 85})
        
        # Use multi-agent system for comprehensive assessment
        from app.services.bedrock_agents_service import bedrock_agents_service
        comprehensive_assessment = bedrock_agents_service.comprehensive_assessment(all_results)
        
        # Format recommendations
        ai_recommendations = f"""EXECUTIVE SUMMARY:
{comprehensive_assessment['executive_summary']}

PILLAR ASSESSMENTS:
"""
        for pillar, assessment in comprehensive_assessment['pillar_assessments'].items():
            ai_recommendations += f"\n\n{pillar.upper().replace('_', ' ')}:\n{assessment.get('analysis', 'N/A')}\n"
        
        # Update scan as completed
        ScanRepository.update_scan(user_id, scan_id, {
            'status': 'completed',
            'progress': 100,
            'ai_recommendations': ai_recommendations,
            'completed_at': None  # Will be set by DynamoDB
        })
        
        logger.info(f"Scan {scan_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error performing scan: {e}")
        ScanRepository.update_scan(user_id, scan_id, {
            'status': 'failed',
            'error_message': str(e)
        })

@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    # Verify credential belongs to user
    credential = CredentialRepository.get_credential_by_id(scan_data.credential_id)
    if not credential or credential['user_id'] != current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    # Create scan
    scan = ScanRepository.create_scan(
        user_id=current_user['user_id'],
        credential_id=scan_data.credential_id,
        scan_name=scan_data.scan_name
    )
    
    # Start background scan
    background_tasks.add_task(
        perform_scan,
        scan['scan_id'],
        current_user['user_id'],
        scan_data.credential_id,
        scan_data.regions
    )
    
    return {
        "id": scan['scan_id'],
        "scan_name": scan['scan_name'],
        "status": scan['status'],
        "progress": scan['progress'],
        "regions_scanned": scan['regions_scanned'],
        "started_at": None,
        "completed_at": None,
        "created_at": scan['created_at']
    }

@router.get("/", response_model=List[ScanResponse])
async def list_scans(current_user = Depends(get_current_user)):
    scans = ScanRepository.get_user_scans(current_user['user_id'])
    
    return [
        {
            "id": scan['scan_id'],
            "scan_name": scan['scan_name'],
            "status": scan['status'],
            "progress": scan['progress'],
            "regions_scanned": scan.get('regions_scanned', []),
            "started_at": scan.get('started_at'),
            "completed_at": scan.get('completed_at'),
            "created_at": scan['created_at']
        }
        for scan in sorted(scans, key=lambda x: x['created_at'], reverse=True)
    ]

@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(
    scan_id: str,
    current_user = Depends(get_current_user)
):
    scan = ScanRepository.get_scan_by_id(scan_id)
    
    if not scan or scan['user_id'] != current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    return {
        "id": scan['scan_id'],
        "scan_name": scan['scan_name'],
        "status": scan['status'],
        "progress": scan['progress'],
        "regions_scanned": scan.get('regions_scanned', []),
        "started_at": scan.get('started_at'),
        "completed_at": scan.get('completed_at'),
        "created_at": scan['created_at'],
        "results": scan.get('results'),
        "ai_recommendations": scan.get('ai_recommendations'),
        "error_message": scan.get('error_message')
    }

@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: str,
    current_user = Depends(get_current_user)
):
    scan = ScanRepository.get_scan_by_id(scan_id)
    
    if not scan or scan['user_id'] != current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    ScanRepository.delete_scan(current_user['user_id'], scan_id)
    return None
