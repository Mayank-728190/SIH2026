import os
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from schemas import FaceMatchResponse
from utils import read_image_from_bytes
from services import process_and_annotate_image, compare_faces

app = FastAPI(
    title="Face Pattern Matching API", 
    description="Advanced Face Detection with Oval Face Shapes and similarity matching."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r") as f:
        return f.read()

@app.post("/compare", response_model=FaceMatchResponse)
async def compare_two_faces(
    image1: UploadFile = File(...), 
    image2: UploadFile = File(...)
):
    try:
        # Read image files
        bytes1 = await image1.read()
        bytes2 = await image2.read()
        
        img1 = read_image_from_bytes(bytes1)
        img2 = read_image_from_bytes(bytes2)
        
        if img1 is None or img2 is None:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid image format uploaded."}
            )
            
        # Process images (returns list of embeddings now)
        b64_1, embs1 = process_and_annotate_image(img1, label_prefix="Face 1")
        b64_2, embs2 = process_and_annotate_image(img2, label_prefix="Face 2")
        
        if not embs1 or not embs2:
            return JSONResponse(
                status_code=400,
                content={"error": "Could not detect face in one or both images."}
            )
            
        # Compare all pairwise combinations to find the matches
        matches = []
        for label1, e1 in embs1:
            for label2, e2 in embs2:
                score = compare_faces(e1, e2)
                
                # Determine status based on notebook logic
                if score < 0.3:
                    status = 'No Match'
                elif score < 0.5:
                    status = 'Weak Match'
                elif score < 0.7:
                    status = 'Moderate Match'
                else:
                    status = 'Strong Match'
                    
                matches.append({
                    "face1_id": label1,
                    "face2_id": label2,
                    "score": float(score),
                    "status": status
                })
                
        # Sort matches by score descending
        matches.sort(key=lambda x: x["score"], reverse=True)
            
        return FaceMatchResponse(
            matches=matches,
            image1_processed=b64_1,
            image2_processed=b64_2
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
