from fastapi import APIRouter, HTTPException, Depends
from app.schema import UnstructuredDataModel
from app.db_adapter import insert_into_sqlite
from app.usecase import evaluate_question_complexity
from dependencies.elevenlabs_client import ElevenLabsClient, get_elevenlabs
from fastapi.responses import Response

router = APIRouter()

@router.post("/process_data")
async def process_data(payload: UnstructuredDataModel):
    try:
        payload_dict = payload.model_dump()
        question_text = payload_dict['questionText']
        
        # Evaluate question complexity
        evaluated_complexity = await evaluate_question_complexity(question_text)
        
        structured_data = {
            **payload_dict,
            'questionComplexityEnum': evaluated_complexity
        }
        
        insert_into_sqlite(structured_data)
        
        return {"message": "Data processed and inserted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
@router.post("/")
    
    


@router.post("/generate_voice")
async def generate_voice(text: str, elevenlabs_client: ElevenLabsClient = Depends(get_elevenlabs)):
    try:
        audio_data = await elevenlabs_client.generate_voice(text)
        if audio_data:
            return Response(content=audio_data, media_type="audio/mpeg")
        else:
            raise HTTPException(status_code=500, detail="Failed to generate voice")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
