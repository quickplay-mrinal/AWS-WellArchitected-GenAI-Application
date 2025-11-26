from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.api.routes.auth import get_current_user
from app.repositories.scan_repository import ScanRepository
from app.services.report_service import generate_pdf_report, generate_excel_report
import io

router = APIRouter()

@router.get("/{scan_id}/pdf")
async def download_pdf_report(
    scan_id: str,
    current_user = Depends(get_current_user)
):
    scan = ScanRepository.get_scan_by_id(scan_id)
    
    if not scan or scan['user_id'] != current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    if scan['status'] != 'completed':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scan not completed yet"
        )
    
    # Generate PDF
    pdf_buffer = generate_pdf_report(scan)
    
    return StreamingResponse(
        io.BytesIO(pdf_buffer),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=wellarchitected_report_{scan_id}.pdf"
        }
    )

@router.get("/{scan_id}/excel")
async def download_excel_report(
    scan_id: str,
    current_user = Depends(get_current_user)
):
    scan = ScanRepository.get_scan_by_id(scan_id)
    
    if not scan or scan['user_id'] != current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    if scan['status'] != 'completed':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scan not completed yet"
        )
    
    # Generate Excel
    excel_buffer = generate_excel_report(scan)
    
    return StreamingResponse(
        io.BytesIO(excel_buffer),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=wellarchitected_report_{scan_id}.xlsx"
        }
    )
