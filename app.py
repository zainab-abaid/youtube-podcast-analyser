import os
import enum
import uuid
import uvicorn
from fastapi import FastAPI, Query, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse
from typing import Dict
from main import process_video

app = FastAPI()

# Store processing status and file paths
processing_tasks: Dict[str, dict] = {}


class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


def process_video_background(task_id: str, youtube_url: str, output_filename: str):
    try:
        output_path = f"output/{output_filename}.xlsx"
        os.makedirs("output", exist_ok=True)

        # Update task status
        processing_tasks[task_id]["status"] = "processing"

        # Process the video
        process_video(youtube_url, output_path)

        # Update task status and store output path
        processing_tasks[task_id].update({
            "status": "completed",
            "output_path": output_path,
            "output_filename": f"{output_filename}.xlsx"
        })
    except Exception as e:
        processing_tasks[task_id].update({
            "status": "error",
            "error": str(e)
        })


@app.post("/api/process")
async def process_youtube_video(
        youtube_url: str = Query(..., description="YouTube video URL"),
        output_filename: str = Query(..., description="Name for the output file (without extension)"),
        background_tasks: BackgroundTasks = None
):
    # Generate a unique task ID
    task_id = str(uuid.uuid4())

    # Initialize task status
    processing_tasks[task_id] = {
        "status": "queued",
        "youtube_url": youtube_url,
        "output_filename": f"{output_filename}.xlsx"
    }

    # Start background task
    background_tasks.add_task(process_video_background, task_id, youtube_url, output_filename)

    return {
        "task_id": task_id,
        "status": "processing_started",
        "youtube_url": youtube_url,
        "output_filename": f"{output_filename}.xlsx"
    }


@app.get("/api/tasks", response_model=Dict[str, dict])
async def list_all_tasks():
    """
    List all tasks with their current status and details
    """
    return processing_tasks


@app.get("/api/status/{task_id}")
async def get_processing_status(task_id: str):
    task = processing_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    response = {"task_id": task_id, "status": task["status"]}

    if task["status"] == "completed":
        response["download_url"] = f"/api/download/{task_id}"
    elif task["status"] == "error":
        response["error"] = task.get("error", "Unknown error occurred")

    return response


@app.get("/api/download/{task_id}")
async def download_file(task_id: str):
    task = processing_tasks.get(task_id)
    if not task or task["status"] != "completed":
        raise HTTPException(status_code=404, detail="File not found or not ready for download")

    if not os.path.exists(task["output_path"]):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        task["output_path"],
        filename=task["output_filename"],
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
